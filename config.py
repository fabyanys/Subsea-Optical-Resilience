import os
from pathlib import Path
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Base Directories
BASE_DIR = Path(__file__).resolve().parent

# Regulatory and Technical Document Folders
DOC_DIRS = {
    "CBUAE_Banking": BASE_DIR / "01_UAE_Banking_Regulations",
    "TDRA_Telecom": BASE_DIR / "02_UAE_Telecom_Regulations",
    "ITU_T_Optical": BASE_DIR / "03_ITU_T_Optical_Standards",
    "ICPC_Submarine": BASE_DIR / "04_Submarine_Cable_Best_Practices",
}

# Knowledge Base & Vector DB Paths
KB_DIR = BASE_DIR / "05_Knowledge_Base"
PROCESSED_CHUNKS_DIR = KB_DIR / "processed_chunks"
VECTOR_DB_DIR = KB_DIR / "vector_db"
INDEX_FILE = VECTOR_DB_DIR / "index.faiss"
METADATA_FILE = VECTOR_DB_DIR / "metadata.pkl"
CONFIG_FILE = VECTOR_DB_DIR / "config.json"

# Models Directory
MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)
VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_CHUNKS_DIR.mkdir(parents=True, exist_ok=True)

# Local LLM Configuration (Reference: ITU AI for Good Notebook)
MODEL_REPO_ID = os.getenv("MODEL_REPO_ID", "bartowski/Llama-3.2-1B-Instruct-GGUF")
MODEL_FILENAME = os.getenv("MODEL_FILENAME", "Llama-3.2-1B-Instruct-Q4_K_M.gguf")
MODEL_PATH = MODELS_DIR / MODEL_FILENAME

# Embedding Configuration
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")

# Chunking Configuration
SUPPORTED_EXTENSIONS = [".pdf", ".txt", ".md"]
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 800))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 120))
MIN_CHUNK_CHARS = int(os.getenv("MIN_CHUNK_CHARS", 80))

# Generation & Retrieval Parameters
TOP_K = int(os.getenv("TOP_K", 4))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", 512))
TEMPERATURE = float(os.getenv("TEMPERATURE", 0.2))
N_CTX = int(os.getenv("N_CTX", 4096))
N_THREADS = int(os.getenv("N_THREADS", 4))
