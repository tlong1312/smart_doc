import re

from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader, UnstructuredImageLoader, \
    PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from .config import CHUNK_SIZE, CHUNK_OVERLAP, EMBEDDING_MODEL, INDEX_DIR
import os

def ingest_file(file_path: str, doc_id: str):
    """Xử lý upload PDF → chunk → embed → lưu FAISS index"""
    try:
        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".pdf":
            loader = PyMuPDFLoader(file_path)
        elif ext in ['.txt', '.csv', '.json', '.md']:
            loader = TextLoader(file_path, encoding='utf-8')
        elif ext in ['.doc', '.docx']:
            loader = Docx2txtLoader(file_path)
        elif ext in ['.png', '.jpg', '.jpeg']:
            loader = UnstructuredImageLoader(file_path)
        else:
            return {"status": "error", "msg": f"Hệ thống chưa hỗ trợ định dạng {ext}"}

        docs = loader.load()
        if not docs:
            return {"status": "error", "msg": "File rỗng hoặc không trích xuất được nội dung."}
        for doc in docs:
            clean_text = re.sub(r' {2,}', ' ', doc.page_content)
            clean_text = clean_text.replace("..", ".")
            doc.page_content = clean_text.strip()

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", ".", "!", "?", " ", ""]
        )
        chunks = text_splitter.split_documents(docs)

        embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
        vector_store = FAISS.from_documents(chunks, embeddings)
        save_path = os.path.join(INDEX_DIR, str(doc_id))
        vector_store.save_local(save_path)

        return {
            "status": "success",
            "faiss_path": save_path,
            "pages": len(docs),
            "chunks": len(chunks),
            "file": os.path.basename(file_path)
        }
    except Exception as e:
        return {"status": "error", "msg": f"Lỗi xử lý file RAG: {str(e)}"}