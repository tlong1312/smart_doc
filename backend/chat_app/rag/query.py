import os

from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from .config import EMBEDDING_MODEL, LLM_MODEL, INDEX_DIR, RETRIEVER_K
from pathlib import Path

def ask_documents(faiss_path: str, question: str, history: str = "", doc_ids: list = []):
    """Hỏi đáp dựa trên FAISS index của từng file cụ thể"""
    if not os.path.exists(faiss_path):
        raise ValueError("Chưa có FAISS index cho tài liệu này. Vui lòng kiểm tra lại.")

    try:
        embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
        vector_store = FAISS.load_local(
            folder_path=faiss_path,
            embeddings=embeddings,
            allow_dangerous_deserialization=True
        )
        search_kwargs = {"k": RETRIEVER_K}
        if doc_ids:
            search_kwargs["filter"] = lambda metadata: metadata.get("doc_id") in doc_ids

        retriever = vector_store.as_retriever(search_kwargs=search_kwargs)

        llm = ChatOllama(model=LLM_MODEL, temperature=0.3)

        prompt = PromptTemplate.from_template(
            """You are a helpful and precise legal AI assistant. Your task is to answer the user's question based ONLY on the provided context.

INSTRUCTIONS:
1. COMPREHENSION: Read the provided Context carefully. If the user asks for a comparison, clearly state the differences or similarities found in the Context.
2. REWRITE, DO NOT COPY: The Context may contain OCR errors or missing diacritics. DO NOT copy-paste the text exactly. You must paraphrase the information into clear, natural, and grammatically correct Vietnamese.
3. STRICT GROUNDING: If the Context does NOT contain the information needed to answer the question, output EXACTLY: "Không có thông tin". Do not explain further.
4. LANGUAGE: Your final response MUST be in Vietnamese.

Context:
{context}

Conversation History:
{history}

Question: {input}
Answer (in Vietnamese):"""
        )

        question_answer_chain = create_stuff_documents_chain(llm, prompt)
        rag_chain = create_retrieval_chain(retriever, question_answer_chain)

        response = rag_chain.invoke({
            "input": question,
            "history": history,
        })

        print("\n===== TÀI LIỆU FAISS TÌM ĐƯỢC VÀ MỚM CHO AI =====")
        for i, doc in enumerate(response["context"]):
            print(f"Đoạn {i + 1}: {doc.page_content}")
        print("==================================================\n")

        return response["answer"].strip()

    except Exception as e:
        raise RuntimeError(f"Lỗi query: {str(e)}")