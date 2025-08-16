from typing import List, Dict
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from .vector import get_vectorstore
import hashlib
import asyncio


def build_documents(parsed_logs: List[Dict]) -> List[Document]:
    docs = []
    for i, log in enumerate(parsed_logs):
        content = (log.get("message") or log.get("raw") or "").strip()
        if not content:
            continue
        metadata = {
            "timestamp": log.get("timestamp", ""),
            "source": log.get("source", "Unknown"),
            "level": log.get("level", ""),
            "raw": log.get("raw", ""),
            "oid": str(i)  # original index within batch (optional)
        }
        # this text is what will be embedded/searched
        docs.append(Document(page_content=content, metadata=metadata))
    return docs


def chunk_documents(docs: List[Document]) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600, chunk_overlap=60, separators=["\n", " ", ""]
    )
    return splitter.split_documents(docs)


def make_doc_id(content: str, metadata: dict) -> str:
    """Create a deterministic unique ID for a document chunk."""
    raw = content + str(metadata)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def ingest_parsed_logs(parsed_logs: List[Dict]) -> int:
    docs = build_documents(parsed_logs)
    if not docs:
        return 0

    chunks = chunk_documents(docs)

    # ✅ Ensure asyncio loop exists (fix for Flask threads)
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())

    vs = get_vectorstore()

    # Generate IDs for each chunk
    ids = [make_doc_id(doc.page_content, doc.metadata) for doc in chunks]

    # ✅ Use add_texts instead of add_documents
    vs.add_texts(
        texts=[doc.page_content for doc in chunks],
        metadatas=[doc.metadata for doc in chunks],
        ids=ids
    )

    return len(chunks)
