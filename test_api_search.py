import sys
sys.path.insert(0, 'src')
from rag_pipeline import LocalRAGPipeline

print("Initializing RAG pipeline...")
p = LocalRAGPipeline()

print("\nSearching for 'API key 401 unauthorized'...")
results = p.retrieve_context('API key 401 unauthorized')

print(f"\nFound {len(results)} results:")
for r in results:
    print(f"  Source: {r['source']}, Score: {r['score']:.3f}")
    print(f"  Preview: {r['text'][:100]}...")
    print()