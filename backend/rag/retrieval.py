import os
from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from .schema import QAResponse
from .vector import get_vectorstore
import asyncio

def _format_docs(docs) -> str:
    lines = []
    for d in docs:
        ts = d.metadata.get("timestamp", "")
        src = d.metadata.get("source", "")
        lvl = d.metadata.get("level", "")
        txt = d.page_content.strip().replace("\n", " ")
        lines.append(f"[{ts}] [{src}] [{lvl}] {txt}")
    return "\n".join(lines)


def build_chain():
    llm = ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_CHAT_MODEL", "gemini-2.5-flash"),
        google_api_key=os.getenv("GEMINI_API_KEY"),
        temperature=0.2,
    )
    parser = JsonOutputParser(pydantic_object=QAResponse)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a precise log analysis assistant. "
                "Use ONLY the provided context logs. If insufficient, say so clearly. "
                "Return STRICT JSON matching the schema."
            ),
            (
                "human",
                "Question: {question}\n\n"
                "Context logs (relevance-ranked):\n{context}\n\n"
                "{format_instructions}"
            ),
        ]
    ).partial(format_instructions=parser.get_format_instructions())

    return prompt | llm | parser


def answer_question(question: str, k: int = 8) -> Dict[str, Any]:
    try:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())
        # ✅ Ensure vectorstore uses correct embeddings
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=os.getenv("GEMINI_API_KEY"),
        )

        vs = get_vectorstore(embeddings=embeddings)
        retriever = vs.as_retriever(
            search_type="mmr", search_kwargs={"k": k, "fetch_k": max(20, k * 2)}
        )
        docs = retriever.invoke(question)
    except Exception as e:
        return {
            "question": question,
            "answer": f"⚠️ Retrieval failed: {str(e)}",
            "context": "NO MATCHING LOGS",
            "citations": [],
            "confidence": None,
        }

    context = _format_docs(docs) if docs else "NO MATCHING LOGS"
    chain = build_chain()

    try:
        result = chain.invoke({"question": question, "context": context})
    except Exception as e:
        # fallback if parser fails
        result = {
            "question": question,
            "answer": f"⚠️ Parsing failed: {str(e)}",
            "context": context,
            "citations": [d.page_content[:220] for d in docs[:5]],
            "confidence": None,
        }

    # attach raw evidence lines (first 5) if not already present
    if not result.get("citations"):
        result["citations"] = [d.page_content[:220] for d in docs[:5]]

    return result