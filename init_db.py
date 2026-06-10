import os
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer

def initialize_vector_database():
    print("[DB_INIT] Connecting to local Qdrant engine (localhost:6333)...")
    
    client = QdrantClient(url="http://localhost:6333")
    
    collection_name = "knowledge_base"
    
  
    print(f"[DB_INIT] Creating collection '{collection_name}'...")
    client.recreate_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=384,  
            distance=Distance.COSINE  
        ),
    )
    print(f"[DB_INIT] Collection blueprint armed successfully.")

   
    print("[DB_INIT] Loading BAAI/bge-small-en-v1.5 onto CPU memory...")
    encoder = SentenceTransformer('BAAI/bge-small-en-v1.5')

    
    sample_corpus = [
        "QuantumCorp was officially founded on August 4, 2002, specializing in enterprise machine learning infrastructure.",
        "The security protocol code-named Watchdog was deployed in 2026 to monitor systemic token performance and data leaks.",
        "SRE-Pilot is a distributed event-driven system built using Go and C++20 utilizing Redpanda and Qdrant backend stores.",
        "The maximum throughput of the proprietary C++ inference server reached a optimized metric baseline of 2240 tokens per second.",
        "For corporate compliance standards, any employee document containing credit card data or explicit SSNs must trigger an immediate block."
    ]

   
    print(f"[DB_INIT] Translating and uploading {len(sample_corpus)} text chunks...")
    points = []
    for idx, text in enumerate(sample_corpus):
        
        vector_embedding = encoder.encode(text).tolist()
        
        
        points.append(
            PointStruct(
                id=idx,
                vector=vector_embedding,
                payload={"text_content": text}  
            )
        )
    
   
    client.upsert(collection_name=collection_name, points=points)
    print("[DB_INIT] Database seeding completed cleanly. Knowledge base is ready.")

if __name__ == "__main__":
    initialize_vector_database()