import os
from pinecone import Pinecone
from google import genai
from google.genai.types import EmbedContentConfig
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv

class RAGIngestionPipeline:
    def __init__(
        self,
        gemini_api_key: str,
        pinecone_api_key: str,
        pinecone_index_name: str,
        chunk_size: int = 500,
        chunk_overlap: int = 100,
    ):
        # ---- Gemini client ----
        self.genai_client = genai.Client(api_key=gemini_api_key)
        self.embedding_model = "gemini-embedding-001"

        # ---- Pinecone client ----
        self.pc = Pinecone(api_key=pinecone_api_key)
        self.index = self.pc.Index(pinecone_index_name)

        # ---- Chunker ----
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ".", " ", ""]
        )

    # -----------------------------
    # 1️⃣ Load text
    # -----------------------------
    def load_text_from_file(self, path: str) -> str:
        if not os.path.exists(path):
            raise FileNotFoundError(path)

        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    # -----------------------------
    # 2️⃣ Chunk text
    # -----------------------------
    def chunk_text(self, text: str) -> list[str]:
        return self.splitter.split_text(text)

    # -----------------------------
    # 3️⃣ Embed ONE chunk
    # -----------------------------
    def embed_chunk(self, text: str) -> list[float]:
        response = self.genai_client.models.embed_content(
            model=self.embedding_model,
            contents=[text],
            config=EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
        )
        return response.embeddings[0].values

    # -----------------------------
    # 4️⃣ Upsert ONE chunk
    # -----------------------------
    def upsert_chunk(
        self,
        chunk_id: str,
        embedding: list[float],
        metadata: dict
    ):
        self.index.upsert(
            vectors=[{
                "id": chunk_id,
                "values": embedding,
                "metadata": metadata
            }]
        )


    def embed_query(self, text: str) -> list[float]:
        """
        Embed a query for similarity search
        """
        response = self.genai_client.models.embed_content(
            model=self.embedding_model,
            contents=[text],
            config=EmbedContentConfig(task_type="RETRIEVAL_QUERY")
        )
        return response.embeddings[0].values
    

    def query_similar_chunks(
    self,
    query: str,
    top_k: int = 5,
    min_score: float = 0.0
    ) -> list[dict]:
        """
        Perform similarity search over the vector DB
        """
        query_vector = self.embed_query(query)

        response = self.index.query(
            vector=query_vector,
            top_k=top_k,
            include_metadata=True
        )

        results = []
        for match in response["matches"]:
            if match["score"] >= min_score:
                results.append({
                    "id": match["id"],
                    "score": match["score"],
                    "content": match["metadata"]["content"],
                    "source": match["metadata"].get("source"),
                    "chunk_index": match["metadata"].get("chunk_index"),
                })

        return results



    def describe_index(self):
        """
        Inspect index stats (for sanity checks)
        """
        return self.index.describe_index_stats()



    # -----------------------------
    # 5️⃣ FULL PIPELINE (TEXT)
    # -----------------------------
    def ingest_text(self, text: str, source_name: str):
        chunks = self.chunk_text(text)

        print(f"[INFO] Total chunks created: {len(chunks)}")

        for i, chunk in enumerate(chunks):
            embedding = self.embed_chunk(chunk)

            self.upsert_chunk(
                chunk_id=f"{source_name}_{i}",
                embedding=embedding,
                metadata={
                    "content": chunk,
                    "source": source_name,
                    "chunk_index": i
                }
            )

            print(f"[OK] Inserted chunk {i}")

    # -----------------------------
    # 6️⃣ FULL PIPELINE (FILE)
    # -----------------------------
    def ingest_file(self, file_path: str):
        source_name = os.path.splitext(os.path.basename(file_path))[0]
        text = self.load_text_from_file(file_path)
        self.ingest_text(text, source_name)


load_dotenv()  # Load environment variables from .env file
pipeline = RAGIngestionPipeline(
    gemini_api_key="AIzaSyBgLLaWF4CvKxxbDOdxi1UGpCjY331eYnY",
    pinecone_api_key="pcsk_3YpsBL_QPZyiGNUHEMEQQew1YwpWBuGhbmLqcKYzn53xTZfYjEjEMK2sgQr42vipbfozjn",
    pinecone_index_name="vapi-gemini-kb"
)

# pipeline.ingest_file(r"C:\Users\Noor\Desktop\IIT Mandi\voice-agent\LokMitra-AI\backend\teleop_robot.txt")  # Example file path 

# ---- Inspect DB ----
print("Index stats:")
print(pipeline.describe_index())

# ---- Test queries ----
queries = [
    "What is Project SHIELD?",
    "How does the robot communicate?",
    "What control modes are supported?",
    "Does the system deal with document forgery?"
]

for q in queries:
    print("\n==============================")
    print("QUERY:", q)
    results = pipeline.query_similar_chunks(q, top_k=3)

    for i, r in enumerate(results):
        print(f"\nResult {i+1}")
        print("Score:", r["score"])
        print("Source:", r["source"])
        print("Text:", r["content"])