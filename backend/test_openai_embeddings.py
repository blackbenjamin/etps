"""Quick test for OpenAI embeddings."""
from dotenv import load_dotenv
load_dotenv()

from services.embeddings import create_embedding_service
import asyncio

async def test():
    print("Testing OpenAI embeddings...")
    service = create_embedding_service(use_mock=False)
    print(f"✓ Using: {type(service).__name__}")
    
    match = await service.find_best_semantic_match(
        "Machine Learning Engineering",
        ["Python Developer", "ML Ops", "Data Science", "Web Dev"],
        threshold=0.7
    )
    if match:
        print(f"✓ Best match: {match[0]} (score: {match[1]:.3f})")
    else:
        print("✓ No match above threshold")
    print("✓ OpenAI embeddings working!")

if __name__ == "__main__":
    asyncio.run(test())
