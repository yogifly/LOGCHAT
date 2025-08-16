import os
import pinecone
from langchain_pinecone import PineconeVectorStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings

def get_vectorstore(embeddings=None):
    # ✅ Ensure embeddings always exist
    if embeddings is None:
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=os.getenv("GEMINI_API_KEY"),
        )

    # ✅ Init Pinecone client
    pc = pinecone.Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index_name = os.getenv("PINECONE_INDEX_NAME", "logchat-index")

    # ✅ Ensure index exists (create if missing)
    existing_indexes = [idx["name"] for idx in pc.list_indexes()]
    if index_name not in existing_indexes:
        pc.create_index(
            name=index_name,
            dimension=768,  # embedding size for models/embedding-001
            metric="cosine",
            spec=pinecone.ServerlessSpec(  # 🔹 safer for serverless setups
                cloud="aws", region="us-east-1"
            ),
        )

    # ✅ Load the index
    index = pc.Index(index_name)

    # ✅ Return a real vectorstore object
    return PineconeVectorStore(
        index=index,
        embedding=embeddings,
        text_key="text"  # keep consistent with your docs
    )
