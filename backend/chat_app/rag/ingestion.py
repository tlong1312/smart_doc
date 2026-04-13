import os
import pickle

import fitz
import torch
from langchain_community.document_loaders import (
    Docx2txtLoader,
    PyMuPDFLoader,
    TextLoader,
    UnstructuredImageLoader,
)
from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .config import CHUNK_OVERLAP, CHUNK_SIZE, EMBEDDING_MODEL, INDEX_DIR
from .ocr_service import normalize_text, ocr_page, select_pages_for_ocr

_EMBEDDINGS = None


def _get_embeddings():
    global _EMBEDDINGS
    if _EMBEDDINGS is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        _EMBEDDINGS = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={"device": device},
            encode_kwargs={"normalize_embeddings": True},
        )
    return _EMBEDDINGS


def ingest_file(file_path: str, doc_id: str):
    """Xử lý upload file -> trích xuất text -> chunk -> embed -> lưu FAISS/BM25."""
    try:
        ext = os.path.splitext(file_path)[1].lower()
        file_name = os.path.basename(file_path)

        if ext == ".pdf":
            loader = PyMuPDFLoader(file_path)
            docs = loader.load()

            total_text = "".join([(d.page_content or "") for d in docs]).strip()
            avg_chars_per_page = len(total_text) / len(docs) if docs else 0.0
            pages_to_ocr = select_pages_for_ocr(docs, avg_chars_per_page)

            if pages_to_ocr:
                print(
                    f"[{file_name}] OCR có điều kiện: avg={avg_chars_per_page:.0f}, "
                    f"ocr_pages={len(pages_to_ocr)}"
                )
                pdf_document = fitz.open(file_path)
                try:
                    for page_num in pages_to_ocr:
                        page = pdf_document.load_page(page_num)

                        # Trang không có ảnh thường là text gốc, skip OCR để giữ chất lượng + tốc độ
                        if not page.get_images(full=True):
                            continue

                        original_text = normalize_text(docs[page_num].page_content)
                        ocr_text = normalize_text(ocr_page(page))

                        # Chỉ ghi đè khi OCR có lợi rõ rệt
                        should_replace = (
                            (len(original_text) < 40 and len(ocr_text) >= 40)
                            or (len(original_text) > 0 and len(ocr_text) >= int(len(original_text) * 1.3))
                        )
                        if should_replace:
                            docs[page_num].page_content = ocr_text
                finally:
                    pdf_document.close()

        elif ext in [".txt", ".csv", ".json", ".md"]:
            loader = TextLoader(file_path, encoding="utf-8")
            docs = loader.load()

        elif ext in [".doc", ".docx"]:
            loader = Docx2txtLoader(file_path)
            docs = loader.load()

        elif ext in [".png", ".jpg", ".jpeg"]:
            loader = UnstructuredImageLoader(file_path)
            docs = loader.load()
        else:
            return {"status": "error", "msg": f"He thong chua ho tro dinh dang {ext}"}

        if not docs:
            return {"status": "error", "msg": "File rong hoac khong trich xuat duoc noi dung."}

        for doc in docs:
            doc.page_content = normalize_text(doc.page_content)

            raw_page = doc.metadata.get("page")
            if isinstance(raw_page, int):
                doc.metadata["page"] = raw_page + 1 if raw_page >= 0 else 1
            else:
                doc.metadata["page"] = 1

            doc.metadata["doc_id"] = str(doc_id)
            doc.metadata["file_name"] = file_name

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", ".", "!", "?", " ", ""],
        )
        chunks = text_splitter.split_documents(docs)

        if not chunks:
            return {
                "status": "error",
                "msg": "Khong tim thay noi dung van ban trong tai lieu. Vui long kiem tra lai file tai len!",
            }

        embeddings = _get_embeddings()

        global_save_path = os.path.join(INDEX_DIR, "global_index")
        if os.path.exists(global_save_path):
            vector_store = FAISS.load_local(
                global_save_path,
                embeddings,
                allow_dangerous_deserialization=True,
            )
            vector_store.add_documents(chunks)
        else:
            vector_store = FAISS.from_documents(chunks, embeddings)

        vector_store.save_local(global_save_path)

        bm25_save_path = os.path.join(INDEX_DIR, "bm25_index.pkl")
        if os.path.exists(bm25_save_path):
            with open(bm25_save_path, "rb") as f:
                old_bm25 = pickle.load(f)
            bm25_retriever = BM25Retriever.from_documents(old_bm25.docs + chunks)
        else:
            bm25_retriever = BM25Retriever.from_documents(chunks)

        with open(bm25_save_path, "wb") as f:
            pickle.dump(bm25_retriever, f)

        return {
            "status": "success",
            "faiss_path": global_save_path,
            "pages": len(docs),
            "chunks": len(chunks),
            "file": file_name,
        }

    except Exception as e:
        return {"status": "error", "msg": f"Loi xu ly file RAG: {str(e)}"}
