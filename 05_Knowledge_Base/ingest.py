import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

import re
import json
import pickle
from typing import List, Dict, Any
import numpy as np
import pypdf
import faiss
from sentence_transformers import SentenceTransformer
import torch

from config import (
    DOC_DIRS,
    SUPPORTED_EXTENSIONS,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    MIN_CHUNK_CHARS,
    EMBEDDING_MODEL_NAME,
    INDEX_FILE,
    METADATA_FILE,
    CONFIG_FILE,
    PROCESSED_CHUNKS_DIR
)

def read_pdf_text(path: Path) -> str:
    """Extract text from a PDF file page by page."""
    text_parts = []
    try:
        reader = pypdf.PdfReader(str(path))
        for page_num, page in enumerate(reader.pages):
            try:
                page_text = page.extract_text() or ""
                text_parts.append(page_text)
            except Exception as e:
                text_parts.append(f"\n[Page {page_num+1} extraction error: {e}]\n")
    except Exception as e:
        print(f"Error opening PDF {path.name}: {e}")
    return "\n".join(text_parts)

def read_text_file(path: Path) -> str:
    """Read plain text or markdown file."""
    return path.read_text(encoding="utf-8", errors="ignore")

def normalize_text(text: str) -> str:
    """Normalize whitespace while preserving paragraph boundaries (from ITU notebook)."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[^\S\n]+", " ", text)
    return text.strip()

def chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    """Split text into overlapping chunks, breaking at word boundaries."""
    text = text.strip()
    if not text:
        return []
    chunks = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + chunk_size, n)
        if end < n:
            ws = text.rfind(" ", start + int(chunk_size * 0.9), end)
            if ws != -1:
                end = ws
        chunk = text[start:end].strip()
        if len(chunk) >= MIN_CHUNK_CHARS:
            chunks.append(chunk)
        if end >= n:
            break
        start = max(end - overlap, start + 1)
    return chunks

def build_knowledge_base():
    """Scan all regulation & technical directories, chunk documents, and build FAISS index."""
    print("=" * 60)
    print("Telecom Resilience AI - Knowledge Base Ingestion")
    print("=" * 60)

    documents: List[Dict[str, Any]] = []
    supported = set(SUPPORTED_EXTENSIONS)

    for category, folder in DOC_DIRS.items():
        if not folder.exists():
            continue
        
        doc_files = [f for f in sorted(folder.glob("*")) if f.suffix.lower() in supported and f.is_file()]
        print(f"\nScanning [{category}] in {folder.name}: found {len(doc_files)} file(s).")
        
        for path in doc_files:
            if path.name.lower() == "readme.md":
                continue  # Skip instructional READMEs
                
            print(f"  -> Parsing: {path.name}")
            if path.suffix.lower() == ".pdf":
                raw_text = read_pdf_text(path)
            else:
                raw_text = read_text_file(path)
                
            clean_text = normalize_text(raw_text)
            chunks = chunk_text(clean_text, CHUNK_SIZE, CHUNK_OVERLAP)
            
            for idx, chunk in enumerate(chunks):
                documents.append({
                    "category": category,
                    "source": path.name,
                    "chunk_id": idx,
                    "text": chunk
                })

    if not documents:
        print("\n[!] No regulatory/technical documents found in folders 01 to 04.")
        print("    Please put your PDF/TXT files in:")
        for cat, f in DOC_DIRS.items():
            print(f"      - {f.name}/ ({cat})")
        return

    print(f"\n[OK] Extracted total of {len(documents)} text chunks.")

    # Save processed chunks as JSON for auditing and inspection
    processed_json = PROCESSED_CHUNKS_DIR / "chunks_summary.json"
    with open(processed_json, "w", encoding="utf-8") as f:
        json.dump(documents, f, indent=2, ensure_ascii=False)
    print(f"[OK] Saved chunks JSON to {processed_json.name}")

    # Embeddings & FAISS Indexing
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"\nLoading Embedding model: '{EMBEDDING_MODEL_NAME}' on {device.upper()}...")
    embedder = SentenceTransformer(EMBEDDING_MODEL_NAME, device=device)

    chunk_texts = [d["text"] for d in documents]
    print(f"Computing embeddings for {len(chunk_texts)} chunks...")
    embeddings = embedder.encode(
        chunk_texts,
        batch_size=32,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    dimension = embeddings.shape[1]
    print(f"Building FAISS IndexFlatIP (Dimension: {dimension})...")
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings.astype("float32"))

    # Save FAISS Index & Metadata
    faiss.write_index(index, str(INDEX_FILE))
    with open(METADATA_FILE, "wb") as f:
        pickle.dump(documents, f)

    config_record = {
        "embedding_model_name": EMBEDDING_MODEL_NAME,
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
        "total_chunks": len(documents),
        "dimension": dimension
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config_record, f, indent=2)

    print("\n" + "=" * 60)
    print("[SUCCESS] Knowledge Base build complete!")
    print(f"  Index file   : {INDEX_FILE}")
    print(f"  Metadata file: {METADATA_FILE}")
    print(f"  Total Vectors: {index.ntotal}")
    print("=" * 60)

if __name__ == "__main__":
    build_knowledge_base()
