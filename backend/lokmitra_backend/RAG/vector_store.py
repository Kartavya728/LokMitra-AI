import os
from pinecone import Pinecone

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))

def upsert_chunk(
    chunk_id: str,
    embedding: list[float],
    metadata: dict
):
    index.upsert(
        vectors=[{
            "id": chunk_id,
            "values": embedding,
            "metadata": metadata
        }]
    )


def query_chunks(
    embedding: list[float],
    top_k: int = 5
):
    return index.query(
        vector=embedding,
        top_k=top_k,
        include_metadata=True
    )
