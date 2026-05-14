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


def generate_mock_embeddings(documents: list, dimension: int = 1536) -> list:
    """Generate mock embeddings for testing.

    In production, replace with real embedding model (OpenAI, Cohere, etc.).
    """
    import hashlib

    embeddings = []
    for doc in documents:
        # Deterministic mock embedding based on document ID
        seed = hashlib.md5(doc["id"].encode()).hexdigest()
        vector = [
            float(int(seed[i : i + 2], 16) % 1000) / 1000
            for i in range(0, min(len(seed), dimension * 4), 4)
        ]
        # Pad or truncate to exact dimension
        vector = (vector + [0.0] * dimension)[:dimension]
        embeddings.append({**doc, "vector": vector})

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
        embedded_docs = generate_mock_embeddings(documents)

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
