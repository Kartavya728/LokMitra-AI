import os
from google import genai
from google.genai.types import EmbedContentConfig

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

EMBED_MODEL = "gemini-embedding-001"

def embed_document(text: str) -> list[float]:
    resp = client.models.embed_content(
        model=EMBED_MODEL,
        contents=[text],
        config=EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
    )
    return resp.embeddings[0].embedding


def embed_query(text: str) -> list[float]:
    resp = client.models.embed_content(
        model=EMBED_MODEL,
        contents=[text],
        config=EmbedContentConfig(task_type="RETRIEVAL_QUERY")
    )
    return resp.embeddings[0].embedding
