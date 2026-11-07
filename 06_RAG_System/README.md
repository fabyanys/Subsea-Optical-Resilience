# 06 - RAG System (Retrieval-Augmented Generation)

Modul ini mengimplementasikan inferensi LLM lokal (`Llama-3.2-1B-Instruct` format GGUF via `llama-cpp-python`) dan retrieval konteks dari FAISS database.

### File Komponen:
1. `download_model.py`: Mengunduh model GGUF dari Hugging Face Hub (otomatis ke folder `../models/`).
2. `rag_engine.py`: Engine RAG utama untuk memuat model, melakukan semantic search top-k chunks, menyusun prompt berlandaskan sumber hukum/standar, dan menghasilkan jawaban.
3. `test_rag.py`: Script pengujian cepat untuk menguji respons RAG secara interaktif di terminal.
