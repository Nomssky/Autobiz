#!/usr/bin/env python3
"""Retrain embeddings script — updates the vector store with new knowledge."""
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def collect_business_knowledge(db_session):
    """Collect business data to embed in vector store."""
    from app.models.agent_task import AgentTask
    from app.models.business import Business
    from sqlalchemy import select

    businesses = db_session.execute(select(Business)).scalars().all()
    documents = []

    for business in businesses:
        documents.append(
            {
                "id": f"business-{business.id}",
                "vector": None,  # Will be computed by embedding model
                "payload": {
                    "type": "business",
                    "name": business.name,
                    "description": business.description,
                    "status": business.status,
                    "sector": (
                        business.metadata.get("industry", "general")
                        if hasattr(business, "metadata")
                        else "general"
                    ),
                },
            }
        )

        tasks = (
            db_session.execute(select(AgentTask).where(AgentTask.business_id == business.id))
            .scalars()
            .all()
        )

        for task in tasks:
            if task.output_data:
                documents.append(
                    {
                        "id": f"task-output-{task.id}",
                        "vector": None,
                        "payload": {
                            "type": "task_output",
                            "business_id": str(business.id),
                            "role": task.role_name,
                            "task_type": task.task_type,
                            "status": task.status,
                            "output_summary": str(task.output_data)[:500],
                        },
                    }
                )

    logger.info(f"Collected {len(documents)} documents for embedding")
    return documents


def generate_embeddings(documents: list, dimension: int = 1536) -> list:
    """Generate real embeddings using configured provider (Ollama or OpenAI)."""
    from app.config import settings as s

    provider = (s.EMBEDDING_PROVIDER or "ollama").lower()
    model = s.EMBEDDING_MODEL or s.OPENAI_EMBEDDING_MODEL or "nomic-embed-text"
    api_key = s.EMBEDDING_API_KEY or s.OPENAI_API_KEY or s.LLM_API_KEY or ""
    base_url = s.EMBEDDING_BASE_URL or ""

    texts = [doc["text"] for doc in documents]
    logger.info(f"Generating {len(texts)} embeddings via {provider}/{model}")

    if provider == "ollama":
        import httpx
        url = (base_url or s.OLLAMA_BASE_URL or "http://localhost:11434") + "/api/embed"
        embeddings = []
        for i, doc in enumerate(documents):
            try:
                resp = httpx.post(url, json={"model": model, "input": doc["text"]}, timeout=60)
                resp.raise_for_status()
                vector = resp.json()["embeddings"][0]
                embeddings.append({**doc, "vector": vector})
                if (i + 1) % 10 == 0:
                    logger.info(f"  Embedded {i + 1}/{len(texts)}")
            except Exception as e:
                raise RuntimeError(f"Failed to embed doc {doc['id']}: {e}")
        return embeddings

    else:
        import openai as _openai
        if not api_key:
            raise ValueError("API key required for OpenAI embeddings. Set EMBEDDING_API_KEY or OPENAI_API_KEY in .env")
        client = _openai.OpenAI(api_key=api_key, base_url=base_url or None)
        embeddings = []
        for i, doc in enumerate(documents):
            try:
                resp = client.embeddings.create(model=model, input=doc["text"])
                vector = resp.data[0].embedding
                embeddings.append({**doc, "vector": vector})
                if (i + 1) % 10 == 0:
                    logger.info(f"  Embedded {i + 1}/{len(texts)}")
            except Exception as e:
                raise RuntimeError(f"Failed to embed doc {doc['id']}: {e}")
        return embeddings


def main():
    """Main retraining pipeline."""
    from app.database import SessionLocal, get_engine
    from app.infrastructure.vector_store import VectorStore

    # Initialize DB
    try:
        get_engine()
    except Exception:
        print("Database not configured. Run with DATABASE_URL set.")
        sys.exit(1)

    db = SessionLocal()

    try:
        # 1. Collect knowledge
        print("📊 Collecting business knowledge...")
        documents = collect_business_knowledge(db)

        if not documents:
            print("No documents found to embed.")
            return

        # 2. Generate embeddings
        print("🧠 Generating embeddings...")
        embedded_docs = generate_embeddings(documents)

        # 3. Initialize vector store
        print("💾 Connecting to vector store...")
        vs_config = {
            "backend": os.environ.get("VECTOR_STORE", "qdrant").lower(),
            "collection_name": "autobiz_knowledge",
            "dimension": 1536,
        }
        vector_store = VectorStore(vs_config)

        # 4. Upsert vectors
        print(f"📥 Upserting {len(embedded_docs)} vectors...")
        batch = [
            {
                "id": doc["id"],
                "vector": doc["vector"],
                "payload": doc["payload"],
            }
            for doc in embedded_docs
        ]
        vector_store.upsert(batch)

        print(f"✅ Retraining complete! {len(embedded_docs)} vectors stored.")
        print(f"   Backend: {vs_config['backend']}")
        print(f"   Collection: {vs_config['collection_name']}")

    except Exception as e:
        logger.error(f"Retraining failed: {e}", exc_info=True)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
