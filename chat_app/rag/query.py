import os

from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from .config import EMBEDDING_MODEL, LLM_MODEL, INDEX_DIR, RETRIEVER_K
from pathlib import Path

def ask_document(faiss_path: str, question: str, history: str = "", file_name: str = ""):
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
        retriever = vector_store.as_retriever(search_kwargs={"k": RETRIEVER_K})

        llm = ChatOllama(model=LLM_MODEL, temperature=0.3)

        prompt = PromptTemplate.from_template(
            """You are a highly capable and logical AI assistant. Your task is to answer the user's question based ONLY on the provided conversation history and context snippets.

Document Name: {file_name}

CRITICAL INSTRUCTIONS:
1. ANALYZE CONTEXT: Read the Document Name and extracted context snippets carefully. 
2. LOGICAL DEDUCTION: Connect the dots intelligently. Resolve pronouns (e.g., "he", "they", "that place") by looking at the Conversation History.
3. STRICT GROUNDING: If the context does NOT contain the answer, reply EXACTLY with: "Không có thông tin".
4. OUTPUT LANGUAGE: Your final answer MUST be entirely in natural, clear, and concise VIETNAMESE.

Conversation History:
{history}

Context (Extracted Document Snippets):
{context}

User Question: {input}
AI Answer (in Vietnamese):"""
        )

        question_answer_chain = create_stuff_documents_chain(llm, prompt)
        rag_chain = create_retrieval_chain(retriever, question_answer_chain)

        response = rag_chain.invoke({
            "input": question,
            "history": history,
            "file_name": file_name
        })

        print("\n===== TÀI LIỆU FAISS TÌM ĐƯỢC VÀ MỚM CHO AI =====")
        for i, doc in enumerate(response["context"]):
            print(f"Đoạn {i + 1}: {doc.page_content}")
        print("==================================================\n")

        return response["answer"].strip()

    except Exception as e:
        raise RuntimeError(f"Lỗi query: {str(e)}")