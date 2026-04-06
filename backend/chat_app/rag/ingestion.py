import pickle
import re

import cv2
import fitz
import numpy as np
from PIL import Image
from django.conf import settings
from langchain_community.retrievers import BM25Retriever
from langchain_huggingface import HuggingFaceEmbeddings
from paddleocr import PaddleOCR
from langchain_core.documents import Document as LcDocument
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
        file_name = os.path.basename(file_path)
        if ext == ".pdf":
            loader = PyMuPDFLoader(file_path)
            docs = loader.load()
            total_text = "".join([d.page_content for d in docs]).strip()
            avg_chars_per_page = len(total_text) / len(docs) if len(docs) > 0 else 0


            if avg_chars_per_page < 100:
                print(f"[{file_name}] Chữ quá ít (TB: {avg_chars_per_page:.0f} ký tự/trang). Phát hiện PDF scan/watermark, đang chạy PaddleOCR...")
                docs = []

                ocr_engine = PaddleOCR(
                    lang="vi",
                    use_angle_cls=True,
                    det_db_box_thresh=0.5,
                    det_limit_side_len=2500
                )
                pdf_document = fitz.open(file_path)
                for page_num in range(len(pdf_document)):
                    page = pdf_document.load_page(page_num)


                    zoom = 300/72
                    mat = fitz.Matrix(zoom,zoom)
                    pix = page.get_pixmap(matrix=mat)

                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    img_np = np.array(img)

                    img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
                    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
                    blur = cv2.bilateralFilter(gray, 9, 75, 75)
                    thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
                    img_clean = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)

                    result = ocr_engine.ocr(img_clean)

                    page_text = ""
                    if result and result[0]:
                        for line in result[0]:
                            text_content = line[1][0]

                            # 4. Lọc ngay bọn Watermark rác
                            if "luatvietnam" in text_content.lower() or "www." in text_content.lower():
                                continue

                            page_text += text_content + " "

                        # 5. Dọn dẹp khoảng trắng thừa
                    page_text = re.sub(r'\s+', ' ', page_text).strip()

                    if page_text:
                        docs.append(
                            LcDocument(page_content=page_text, metadata={"file_name": file_name, "page": page_num}))
                pdf_document.close()

        elif ext in ['.txt', '.csv', '.json', '.md']:
            loader = TextLoader(file_path, encoding='utf-8')
            docs = loader.load()
        elif ext in ['.doc', '.docx']:
            loader = Docx2txtLoader(file_path)
            docs = loader.load()
        elif ext in ['.png', '.jpg', '.jpeg']:
            loader = UnstructuredImageLoader(file_path)
            docs = loader.load()
        else:
            return {"status": "error", "msg": f"Hệ thống chưa hỗ trợ định dạng {ext}"}

        if not docs:
            return {"status": "error", "msg": "File rỗng hoặc không trích xuất được nội dung."}

            # ==========================================
            # DEBUG: LƯU TEXT RA FILE TẠM
            # ==========================================
        debug_text = f"=== KẾT QUẢ ĐỌC FILE: {file_name} ===\n\n"
        for i, d in enumerate(docs):
            debug_text += f"--- TRANG {i + 1} ---\n{d.page_content}\n\n"

        debug_path = os.path.join(settings.BASE_DIR, "debug_raw_text.txt")
        with open(debug_path, "w", encoding="utf-8") as f:
            f.write(debug_text)
        print(f"🛠️ Đã dump nội dung thô ra file: {debug_path}")
            # ==========================================




        file_name = os.path.basename(file_path)
        for doc in docs:
            clean_text = re.sub(r' {2,}', ' ', doc.page_content)
            doc.page_content = clean_text.replace("..", ".").strip()
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
            separators=["\n\n", "\n", ".", "!", "?", " ", ""]
        )
        chunks = text_splitter.split_documents(docs)

        if not chunks or len(chunks) == 0:
            return {"status": "error",
                    "msg": "Không tìm thấy nội dung văn bản nào trong tài liệu. Vui lòng kiểm tra lại chất lượng hình ảnh hoặc file tải lên!"}
        embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )

        global_save_path = os.path.join(INDEX_DIR, "global_index")

        if os.path.exists(global_save_path):
            vector_store = FAISS.load_local(global_save_path, embeddings, allow_dangerous_deserialization=True)
            vector_store.add_documents(chunks)
        else:
            vector_store = FAISS.from_documents(chunks, embeddings)

        vector_store.save_local(global_save_path)

        # bm25_save_path = os.path.join(INDEX_DIR, "bm25_index.pkl")
        # if os.path.exists(bm25_save_path):
        #     with open(bm25_save_path, "rb") as f:
        #         old_bm25 = pickle.load(f)
        #         old_docs = old_bm25.docs
        #         bm25_retriever = BM25Retriever().from_documents(old_docs + chunks)
        # else:
        #     bm25_retriever = BM25Retriever().from_documents(chunks)
        #
        # with open(bm25_save_path, "wb") as f:
        #     pickle.dump(bm25_retriever, f)

        return {
            "status": "success",
            "faiss_path": global_save_path,
            "pages": len(docs),
            "chunks": len(chunks),
            "file": file_name
        }
    except Exception as e:
        return {"status": "error", "msg": f"Lỗi xử lý file RAG: {str(e)}"}