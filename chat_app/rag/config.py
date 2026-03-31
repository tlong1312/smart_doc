from pathlib import Path

# Đường dẫn
UPLOAD_DIR = Path("uploads")
INDEX_DIR = Path("faiss_index")

# Model
EMBEDDING_MODEL = "nomic-embed-text"
LLM_MODEL = "qwen2.5:3b"  # Thay nếu dùng model khác

# Chunking params
CHUNK_SIZE = 1500
CHUNK_OVERLAP = 300

# Retrieval params
RETRIEVER_K = 4

# Tạo thư mục nếu chưa có
UPLOAD_DIR.mkdir(exist_ok=True)
INDEX_DIR.mkdir(exist_ok=True)