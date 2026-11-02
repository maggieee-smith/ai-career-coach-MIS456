"""Retrieval-Augmented Generation (RAG).

The knowledge base (markdown files in /knowledge) and the student's own resume are split into chunks
and embedded. When a feature needs context, we embed the question, find the most similar chunks by
cosine similarity, and paste them into the prompt so Claude answers from our curated sources.

Embeddings: OpenAI text-embedding-3-small when an OpenAI key is available, otherwise TF-IDF vectors
(scikit-learn) so the app still works offline.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from core import config

KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent / "knowledge"
EMBED_MODEL = "text-embedding-3-small"


@dataclass
class Chunk:
    text: str
    source: str
    section: str


def chunk_markdown(text: str, source: str, max_chars: int = 900) -> list[Chunk]:
    chunks, section, buf = [], "", []
    title = ""

    def flush():
        body = "\n".join(buf).strip()
        if body:
            chunks.append(Chunk(text=f"{title} > {section}\n{body}".strip(" >"), source=source, section=section))

    for line in text.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            continue
        if line.startswith("## "):
            flush()
            buf, section = [], line[3:].strip()
            continue
        buf.append(line)
        if sum(len(b) for b in buf) > max_chars:
            flush()
            buf = []
    flush()
    return chunks


def chunk_plain(text: str, source: str, max_chars: int = 450) -> list[Chunk]:
    """Split a resume into roughly paragraph-sized chunks."""
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if len(paras) <= 2:  # PDFs often lose blank lines; fall back to line grouping
        paras = [l.strip() for l in text.splitlines() if l.strip()]
    chunks, buf = [], ""
    for p in paras:
        if len(buf) + len(p) > max_chars and buf:
            chunks.append(Chunk(buf.strip(), source, "resume"))
            buf = ""
        buf += p + "\n"
    if buf.strip():
        chunks.append(Chunk(buf.strip(), source, "resume"))
    return chunks


class Embedder:
    def __init__(self):
        self.backend = "openai" if (config.openai_key() and not config.fake_mode()) else "tfidf"
        self._tfidf = None

    def fit(self, corpus: list[str]):
        if self.backend == "tfidf":
            from sklearn.feature_extraction.text import TfidfVectorizer
            self._tfidf = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True).fit(corpus)

    def embed(self, texts: list[str]) -> np.ndarray:
        if self.backend == "openai":
            from openai import OpenAI
            resp = OpenAI(api_key=config.openai_key()).embeddings.create(model=EMBED_MODEL, input=texts)
            m = np.array([d.embedding for d in resp.data], dtype=np.float32)
        else:
            m = self._tfidf.transform(texts).toarray().astype(np.float32)
        norms = np.linalg.norm(m, axis=1, keepdims=True)
        norms[norms == 0] = 1
        return m / norms


class VectorIndex:
    def __init__(self, chunks: list[Chunk], embedder: Embedder):
        self.chunks = chunks
        self.embedder = embedder
        self.matrix = embedder.embed([c.text for c in chunks]) if chunks else np.zeros((0, 1))

    def search(self, query: str, k: int = 4) -> list[tuple[Chunk, float]]:
        if not self.chunks:
            return []
        q = self.embedder.embed([query])[0]
        if q.shape[0] != self.matrix.shape[1]:
            return []
        scores = self.matrix @ q
        top = np.argsort(-scores)[:k]
        return [(self.chunks[i], float(scores[i])) for i in top]


def load_knowledge_chunks() -> list[Chunk]:
    chunks = []
    for f in sorted(KNOWLEDGE_DIR.glob("*.md")):
        chunks += chunk_markdown(f.read_text(encoding="utf-8"), f.name)
    return chunks


def build_knowledge_index() -> VectorIndex:
    chunks = load_knowledge_chunks()
    emb = Embedder()
    emb.fit([c.text for c in chunks])
    try:
        return VectorIndex(chunks, emb)
    except Exception:
        # OpenAI embedding failed (bad key / quota): fall back to TF-IDF so the app keeps working
        emb = Embedder()
        emb.backend = "tfidf"
        emb.fit([c.text for c in chunks])
        return VectorIndex(chunks, emb)


def build_resume_index(resume_text: str, kb_index: VectorIndex) -> VectorIndex:
    """Index the resume with the same embedder as the knowledge base so vectors are comparable."""
    return VectorIndex(chunk_plain(resume_text, "your_resume"), kb_index.embedder)


def format_context(results: list[tuple[Chunk, float]]) -> str:
    return "\n\n".join(f"[Source: {c.source} | {c.section}]\n{c.text}" for c, _ in results)
