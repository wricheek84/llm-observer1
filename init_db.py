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
    knowledge_dir="knowledge_source"
    sample_corpus = []
    print(f"Scanning '{knowledge_dir}' for documentation files...")
    for file_name in os.listdir(knowledge_dir):
        if file_name.endswith(".txt") or file_name.endswith(".md"):
            file_path = os.path.join(knowledge_dir, file_name)
            
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
                
                paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
                sample_corpus.extend(paragraphs)
                
    print(f"[DB_INIT] Total chunks processed and gathered into memory: {len(sample_corpus)}")

    
   

   
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