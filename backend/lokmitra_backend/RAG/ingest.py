from .chunking import chunk_text
from .embeddings import embed_document
from .vector_store import upsert_chunk

def ingest_text_document(
    raw_text: str,
    source_name: str
):
    chunks = chunk_text(raw_text)

    for i, chunk in enumerate(chunks):
        embedding = embed_document(chunk)

        upsert_chunk(
            chunk_id=f"{source_name}_{i}",
            embedding=embedding,
            metadata={
                "content": chunk,
                "source": source_name,
                "chunk_index": i
            }
        )
