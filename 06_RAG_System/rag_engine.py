import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

import pickle
from typing import List, Dict, Any, Optional
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import torch
from llama_cpp import Llama

from config import (
    MODEL_PATH,
    INDEX_FILE,
    METADATA_FILE,
    EMBEDDING_MODEL_NAME,
    TOP_K,
    MAX_TOKENS,
    TEMPERATURE,
    N_CTX,
    N_THREADS
)

class LocalRAGEngine:
    """Local RAG Engine adapting the official ITU AI for Good notebook."""

    def __init__(self, auto_load_llm: bool = True):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.embedder: Optional[SentenceTransformer] = None
        self.index: Optional[faiss.Index] = None
        self.documents: List[Dict[str, Any]] = []
        self.llm: Optional[Llama] = None

        self._load_vector_store()
        if auto_load_llm:
            self._load_llm()

    def _load_vector_store(self):
        """Load FAISS index and documents metadata."""
        if not INDEX_FILE.exists() or not METADATA_FILE.exists():
            print(f"[!] FAISS index not found at {INDEX_FILE}. Run ingest.py first.")
            return

        print(f"Loading FAISS index from {INDEX_FILE.name}...")
        self.index = faiss.read_index(str(INDEX_FILE))
        
        with open(METADATA_FILE, "rb") as f:
            self.documents = pickle.load(f)

        print(f"Loading embedding model '{EMBEDDING_MODEL_NAME}' on {self.device.upper()}...")
        self.embedder = SentenceTransformer(EMBEDDING_MODEL_NAME, device=self.device)
        print(f"[OK] Vector store loaded: {self.index.ntotal} vectors indexed.")

    def _load_llm(self):
        """Load GGUF local model via llama-cpp-python."""
        if not MODEL_PATH.exists():
            print(f"[!] Local model file not found at {MODEL_PATH}.")
            print("    Please run: python 06_RAG_System/download_model.py")
            return

        use_gpu = torch.cuda.is_available()
        print(f"Loading Local Llama LLM from {MODEL_PATH.name} (GPU offload: {use_gpu})...")
        self.llm = Llama(
            model_path=str(MODEL_PATH),
            n_ctx=N_CTX,
            n_threads=N_THREADS,
            n_gpu_layers=-1 if use_gpu else 0,
            verbose=False,
        )
        print("[OK] Local LLM loaded successfully.")

    def retrieve_context(
        self,
        query: str,
        top_k: Optional[int] = None,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant context chunks with optional category filtering."""
        if self.embedder is None or self.index is None:
            raise RuntimeError("Knowledge base is not initialized. Run ingest.py first.")

        top_k = top_k or TOP_K
        # If filtering by category, search with a wider initial pool
        fetch_k = top_k * 4 if category else top_k

        q_emb = self.embedder.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True
        ).astype("float32")

        scores, ids = self.index.search(q_emb, fetch_k)

        results = []
        for score, idx in zip(scores[0], ids[0]):
            if idx == -1 or idx >= len(self.documents):
                continue
            item = self.documents[idx]
            
            if category and item.get("category") != category:
                continue

            results.append({
                "score": float(score),
                "category": item.get("category", "General"),
                "source": item["source"],
                "chunk_id": item["chunk_id"],
                "text": item["text"],
            })

            if len(results) >= top_k:
                break

        return results

    def build_prompt(self, query: str, contexts: List[Dict[str, Any]]) -> str:
        """Construct prompt with strict grounding and regulatory citations."""
        context_parts = []
        for c in contexts:
            context_parts.append(
                f"[Source: {c['source']} | Category: {c.get('category', 'N/A')} | Chunk: {c['chunk_id']}]\n{c['text']}"
            )
        context_text = "\n\n".join(context_parts)

        prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are an expert Telecom & Critical Infrastructure Resilience AI assistant.
Your task is to provide precise, legally and technically grounded advice based strictly on the provided Knowledge Base context (CBUAE, TDRA, ITU-T, ICPC).

Rules:
1. Ground your answer strictly in the provided Context.
2. If the information is not present in the context, explicitly state: "Information not found in the official knowledge base."
3. Cite the exact document source name and chunk number for every claim or recommendation.
4. Keep technical and regulatory terms precise.<|eot_id|><|start_header_id|>user<|end_header_id|>
Context:
{context_text}

Question:
{query}<|eot_id|><|start_header_id|>assistant<|end_header_id|>
"""
        return prompt

    def ask(
        self,
        query: str,
        top_k: Optional[int] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """Full RAG cycle: Retrieve -> Assemble Prompt -> Generate Local Answer."""
        if self.llm is None:
            self._load_llm()
            if self.llm is None:
                raise RuntimeError("Local LLM model is not available.")

        top_k = top_k or TOP_K
        max_tokens = max_tokens or MAX_TOKENS
        temperature = TEMPERATURE if temperature is None else temperature

        contexts = self.retrieve_context(query, top_k=top_k, category=category)
        
        if not contexts:
            return {
                "query": query,
                "answer": "No relevant context found in the Knowledge Base.",
                "contexts": [],
                "prompt": ""
            }

        prompt = self.build_prompt(query, contexts)

        response = self.llm(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=["<|eot_id|>", "<|end_of_text|>"],
        )

        answer = response["choices"][0]["text"].strip()
        return {
            "query": query,
            "answer": answer,
            "contexts": contexts,
            "prompt": prompt,
        }

if __name__ == "__main__":
    engine = LocalRAGEngine(auto_load_llm=False)
    print("Local RAG Engine test initialization successful.")
