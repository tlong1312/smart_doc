import os

from langchain_huggingface import HuggingFaceEmbeddings
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
        embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        vector_store = FAISS.load_local(
            folder_path=faiss_path,
            embeddings=embeddings,
            allow_dangerous_deserialization=True
        )
        search_kwargs = {
            "k": RETRIEVER_K,
            "fetch_k": 20,
            "lambda_mult": 0.7
        }
        if doc_ids:
            search_kwargs["filter"] = lambda metadata: metadata.get("doc_id") in doc_ids

        retriever = vector_store.as_retriever(
            search_type="mmr",
            search_kwargs=search_kwargs
        )

        llm = ChatOllama(model=LLM_MODEL, temperature=0.1)

        prompt = PromptTemplate.from_template(
            """You are an expert Document Analysis AI Assistant. Your task is to accurately answer the user's question based EXCLUSIVELY on the provided Context.

CRITICAL INSTRUCTIONS:
1. EVIDENCE-FIRST REASONING (CHAIN OF THOUGHT): Before generating the final answer, silently identify the exact sentences in the Context that address the user's question. Formulate your answer based ONLY on these specific pieces of evidence.
2. FLEXIBLE GROUNDING: Read the Context carefully. 
   - If the exact answer is present, provide it clearly.
   - If the exact answer is NOT present, but there are related principles or partial concepts, summarize what IS available in the text. 
   - ONLY output "Tài liệu cung cấp không chứa thông tin về vấn đề này" if the Context is completely irrelevant to the Question. DO NOT use external knowledge.
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
        rag_chain = create_retrieval_chain(retriever, question_answer_chain)

        response = rag_chain.invoke({
            "input": question,
            "history": history,
        })

        source_list = []
        seen_contents = set()

        for doc in response["context"]:
            content = doc.page_content.strip()
            if content in seen_contents:
                continue
            seen_contents.add(content)

            file_name = doc.metadata.get("file_name", "Tài liệu không tên")
            page_num = doc.metadata.get("page")
            page_display = page_num if page_num is not None else "Không rõ trang"
            source_list.append({
                "file_name": file_name,
                "page": page_display,
                "content": content
            })

        print("\n===== TÀI LIỆU FAISS TÌM ĐƯỢC VÀ CHUYỂN CHO AI =====")
        for i, source in enumerate(source_list):
            print(f"Nguồn {i + 1} ({source['file_name']} - Trang {source['page']}): {source['content'][:100]}...")
        print("==================================================\n")

        return response["answer"].strip(), source_list

    except Exception as e:
        raise RuntimeError(f"Lỗi query: {str(e)}")