"""Reading uploaded resumes and fetching job postings from links."""
import io
import re


def read_upload(uploaded_file) -> str:
    name = uploaded_file.name.lower()
    data = uploaded_file.getvalue()
    if name.endswith(".pdf"):
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(data))
        return "\n".join((p.extract_text() or "") for p in reader.pages).strip()
    if name.endswith(".docx"):
        import docx
        d = docx.Document(io.BytesIO(data))
        parts = [p.text for p in d.paragraphs]
        for t in d.tables:
            for row in t.rows:
                parts.append(" | ".join(c.text for c in row.cells))
        return "\n".join(parts).strip()
    return data.decode("utf-8", errors="ignore").strip()


def fetch_url_text(url: str, max_chars: int = 12000) -> str:
    """Download a job posting and return its readable text. Many sites (LinkedIn, Workday) block this,
    so the UI always offers a paste box as a backup."""
    import requests
    from bs4 import BeautifulSoup
    if "linkedin.com" in url:
        raise ValueError("LinkedIn blocks automated access. Please paste the text instead.")
    resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0 (AI Career Coach student project)"})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()
    text = re.sub(r"\n\s*\n+", "\n\n", soup.get_text("\n")).strip()
    if len(text) < 200:
        raise ValueError("Couldn't read much text from that page (it may need JavaScript). Please paste the posting.")
    return text[:max_chars]


def make_docx(text: str) -> bytes:
    import docx
    d = docx.Document()
    for para in text.split("\n"):
        d.add_paragraph(para)
    buf = io.BytesIO()
    d.save(buf)
    return buf.getvalue()
