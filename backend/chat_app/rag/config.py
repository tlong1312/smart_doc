from pathlib import Path

# Đường dẫn
UPLOAD_DIR = Path("uploads")
INDEX_DIR = Path("faiss_index")

# Model
EMBEDDING_MODEL = "mxbai-embed-large"
LLM_MODEL = "llama3.2:3b"  # Thay nếu dùng model khác

# Chunking params
CHUNK_SIZE = 700
CHUNK_OVERLAP = 150

# Retrieval params
RETRIEVER_K = 4

# Tạo thư mục nếu chưa có
UPLOAD_DIR.mkdir(exist_ok=True)
INDEX_DIR.mkdir(exist_ok=True)