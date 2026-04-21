import os
import pickle
import threading

import torch
from langchain_classic.retrievers import EnsembleRetriever, ContextualCompressionRetriever
from langchain_classic.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain_community.retrievers import BM25Retriever
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from .config import EMBEDDING_MODEL, LLM_MODEL, INDEX_DIR


_CACHE_LOCK = threading.Lock()
_EMBEDDINGS = None
_LLM = None
_CROSS_ENCODER = None
_BM25_ALL = None
_VECTOR_STORE = None
_FAISS_PATH_LOADED = None
_BM25_MTIME = None
_FAISS_MTIME = None
_BM25_FILTERED_CACHE = {}
_BM25_FILTERED_CACHE_MAX_SIZE = 64


def _get_device():
    return "cuda" if torch.cuda.is_available() else "cpu"

def _get_embeddings():
    global _EMBEDDINGS
    if _EMBEDDINGS is None:
        device = _get_device()
        _EMBEDDINGS = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={"device": device},
            encode_kwargs={"normalize_embeddings": True},
        )
    return _EMBEDDINGS

def _get_llm():
    global _LLM
    if _LLM is None:
        _LLM = ChatOllama(
            model=LLM_MODEL,
            temperature=0.1,
            base_url=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
        )
    return _LLM

def _get_cross_encoder():
    global _CROSS_ENCODER
    if _CROSS_ENCODER is None:
        device = _get_device()
        _CROSS_ENCODER = HuggingFaceCrossEncoder(
            model_name="cross-encoder/ms-marco-MiniLM-L-6-v2",
            model_kwargs={"device": device},
        )
    return _CROSS_ENCODER

def _load_faiss_if_needed(faiss_path: str):
    global _FAISS_PATH_LOADED, _VECTOR_STORE, _FAISS_MTIME
    faiss_file = os.path.join(faiss_path, "index.faiss")
    current_mtime = os.path.getmtime(faiss_file) if os.path.exists(faiss_file) else None
    if (
        _VECTOR_STORE is None
        or _FAISS_PATH_LOADED != faiss_path
        or _FAISS_MTIME != current_mtime
    ):
        _VECTOR_STORE = FAISS.load_local(
            folder_path=faiss_path,
            embeddings=_get_embeddings(),
            allow_dangerous_deserialization=True,
        )
        _FAISS_PATH_LOADED = faiss_path
        _FAISS_MTIME = current_mtime
    return _VECTOR_STORE

def _load_bm25_if_needed():
    global _BM25_ALL, _BM25_MTIME, _BM25_FILTERED_CACHE
    bm25_path = os.path.join(INDEX_DIR, "bm25_index.pkl")
    if not os.path.exists(bm25_path):
        raise ValueError("Không tìm thấy file bm25_index.pkl, vui lòng xóa index và up lại file!")

    current_mtime = os.path.getmtime(bm25_path)

    if _BM25_ALL is None or _BM25_MTIME != current_mtime:
        with open(bm25_path, "rb") as f:
            _BM25_ALL = pickle.load(f)
        _BM25_MTIME = current_mtime
        _BM25_FILTERED_CACHE.clear()

    return _BM25_ALL


def _get_filtered_bm25(full_bm25, doc_ids):
    if not doc_ids:
        return full_bm25

    key = tuple(sorted(str(x) for x in set(doc_ids)))

    cached = _BM25_FILTERED_CACHE.get(key)
    if cached is not None:
        return cached

    filtered_docs = [doc for doc in full_bm25.docs if str(doc.metadata.get("doc_id")) in key]
    retriever = BM25Retriever.from_documents(filtered_docs) if filtered_docs else full_bm25

    if len(_BM25_FILTERED_CACHE) >= _BM25_FILTERED_CACHE_MAX_SIZE:
        first_key = next(iter(_BM25_FILTERED_CACHE))
        _BM25_FILTERED_CACHE.pop(first_key, None)

    _BM25_FILTERED_CACHE[key] = retriever
    return retriever

def ask_documents(faiss_path: str, question: str, history: str = "", doc_ids: list = None):

    if doc_ids is None:
        doc_ids = []

    if not os.path.exists(faiss_path):
        raise ValueError("Chưa có FAISS index cho tài liệu này. Vui lòng kiểm tra lại.")

    try:

        with _CACHE_LOCK:
            vector_store = _load_faiss_if_needed(faiss_path)
            full_bm25 = _load_bm25_if_needed()
            llm = _get_llm()
            cross_encoder = _get_cross_encoder()

        # Hybrid Search
        search_kwargs = {"k": 12}
        if doc_ids:
            search_kwargs["filter"] = lambda metadata: metadata.get("doc_id") in doc_ids
        faiss_retriever = vector_store.as_retriever(search_kwargs=search_kwargs)

        bm25_retriever = _get_filtered_bm25(full_bm25, doc_ids)
        bm25_retriever.k = 12

        ensemble_retriever = EnsembleRetriever(
            retrievers=[bm25_retriever, faiss_retriever],
            weights=[0.5, 0.5]
        )

        compressor = CrossEncoderReranker(model=cross_encoder, top_n=6)
        compression_retriever = ContextualCompressionRetriever(
            base_compressor=compressor,
            base_retriever=ensemble_retriever
        )

        prompt = PromptTemplate.from_template(
            """You are an expert Document Analysis AI Assistant. Your task is to accurately answer the user's question based EXCLUSIVELY on the provided Context.

CRITICAL INSTRUCTIONS:
1. EVIDENCE-FIRST REASONING (CHAIN OF THOUGHT): Before generating the final answer, silently identify the exact sentences in the Context that address the user's question. Formulate your answer based ONLY on these specific pieces of evidence.
2. PARTIAL-COVERAGE POLICY:
- If the context answers part of the question, answer that part first under the heading "Có trong tài liệu:".
- If something is missing, add ONE concise section "Thiếu trong tài liệu:" and list missing points once.
- Do NOT add a global statement that the whole document lacks information when any relevant evidence exists.
- Only output "Tài liệu cung cấp không chứa thông tin về vấn đề này" when all retrieved context is irrelevant.
3. INLINE CITATION: Every time you state a fact, metric, or concept from the Context, you MUST append a citation directly after the sentence using the format [file_name, Trang X]. Example: Nguyên tắc đầu tiên là không chỉ trích [Dac_Nhan_Tam.pdf, Trang 147].
4. OCR CORRECTION & TONE: The Context may contain OCR artifacts or typos. Fix them implicitly in your generated response to ensure high-quality, professional, and clear text.
5. AUTO-LANGUAGE: You MUST detect the language of the user's Question and write your ENTIRE final answer in that EXACT SAME language.

Context:
{context}

Conversation History:
{history}

Question: {input}
Answer:"""
        )
        document_prompt = PromptTemplate(
            input_variables=["page_content", "file_name", "page"],
            template="[Trích từ tài liệu: {file_name}, Trang: {page}]\n{page_content}"
        )

        question_answer_chain = create_stuff_documents_chain(
            llm,
            prompt,
            document_prompt=document_prompt
        )
        rag_chain = create_retrieval_chain(compression_retriever, question_answer_chain)

        response = rag_chain.invoke({
            "input": question,
            "history": history,
        })

        source_list = []
        seen_contents = set()
        for doc in response["context"]:
            content = doc.page_content.strip()
            if not content:
                continue
            if content in seen_contents:
                continue
            seen_contents.add(content)
            source_list.append({
                "file_name": doc.metadata.get("file_name", "Tài liệu không tên"),
                "page": doc.metadata.get("page", "Không rõ trang"),
                "content": content
            })

        return response["answer"].strip(), source_list

    except Exception as e:
        raise RuntimeError(f"Lỗi query: {str(e)}")