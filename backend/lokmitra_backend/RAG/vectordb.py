from pinecone import Pinecone, ServerlessSpec
import os
from pathlib import Path
from dotenv import load_dotenv

# load_dotenv()
# PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")


PINECONE_API_KEY = " pcsk_3YpsBL_QPZyiGNUHEMEQQew1YwpWBuGhbmLqcKYzn53xTZfYjEjEMK2sgQr42vipbfozjn"
INDEX_NAME = 'vapi-gemini-kb'

pc = Pinecone(api_key=PINECONE_API_KEY)

existing_indexes = [idx["name"] for idx in pc.list_indexes()]

if INDEX_NAME not in existing_indexes:
    pc.create_index(
        name=INDEX_NAME,
        dimension=768,          # Gemini embedding size
        metric="cosine",
        spec=ServerlessSpec(
            cloud="aws",         # or "gcp"
            region="us-east-1"   # choose closest to backend
        )
    )
    print(f"Created Pinecone index: {INDEX_NAME}")
else:
    print(f"Index already exists: {INDEX_NAME}")

import time

while not pc.describe_index(INDEX_NAME).status["ready"]:
    print("Waiting for index to be ready...")
    time.sleep(2)

print("Pinecone index is ready")
index = pc.Index(INDEX_NAME)
print("Connected to index:", INDEX_NAME)