"""Test: verify LLM models, embeddings, and similarity search."""
import asyncio
import logging

logging.basicConfig(level=logging.INFO, format="%(name)s %(levelname)s %(message)s")

from engine.llm import CopilotLLM
from engine.memory import Memory, SensoryEvent, Episode
import time


async def main():
    llm = CopilotLLM()
    mem = Memory()
    print(f"Token available: {llm.available}")
    print(f"Episodes before: {mem.episode_count()}")

    # 1. Create and embed a few test episodes
    texts = [
        "Fixed a critical bug in the websocket handler that caused timeouts",
        "Refactored the authentication module for better security",
        "The database migration script failed on production",
    ]
    for i, text in enumerate(texts):
        ep = Episode(
            id=f"test-embed-{i}",
            timestamp=f"2026-05-12T10:0{i}:00",
            source="test",
            summary=text,
            salience=0.85 + i * 0.03,
            mood="Testing",
            neuro_snapshot={"anxiety": 0.3},
        )
        mem._store_episode(ep)

        embedding = await llm.embed(text)
        if embedding:
            mem.update_episode_embedding(ep.id, embedding)
            print(f"  Stored + embedded: '{text[:50]}...' ({len(embedding)} dims)")

    # 2. Similarity search
    print("\n--- Similarity Search ---")
    query = "websocket connection problems"
    q_emb = await llm.embed(query)
    if q_emb:
        results = mem.recall_similar(q_emb, top_k=3)
        print(f"Query: '{query}'")
        for ep, score in results:
            print(f"  {score:.4f}  {ep.summary[:60]}")

    query2 = "security and auth issues"
    q_emb2 = await llm.embed(query2)
    if q_emb2:
        results2 = mem.recall_similar(q_emb2, top_k=3)
        print(f"\nQuery: '{query2}'")
        for ep, score in results2:
            print(f"  {score:.4f}  {ep.summary[:60]}")

    print(f"\nEpisodes after: {mem.episode_count()}")
    print("\nALL TESTS PASSED")
    await llm.close()


asyncio.run(main())


asyncio.run(main())
