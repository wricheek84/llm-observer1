from qdrant_client import QdrantClient

client = QdrantClient(host="localhost", port=6333)
collection_info = client.get_collection(collection_name="knowledge_base")
print(f"Total sentences/points in database: {collection_info.points_count}")