"""Vector store interface — supports Pinecone and Qdrant backends."""
import os
from typing import Dict, List, Optional
from uuid import UUID


class VectorStore:
    """Abstract vector store interface with backend-agnostic operations."""

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.backend = self.config.get("backend", "qdrant")
        self._client = None
        self._collection = self.config.get("collection_name", "autobiz_knowledge")

    def connect(self):
        """Establish connection to vector store backend."""
        if self.backend == "pinecone":
            self._connect_pinecone()
        elif self.backend == "qdrant":
            self._connect_qdrant()
        else:
            raise ValueError(f"Unknown vector store backend: {self.backend}")

    def _connect_pinecone(self):
        """Connect to Pinecone."""
        try:
            import pinecone
            api_key = os.environ.get("PINECONE_API_KEY", self.config.get("api_key", ""))
            environment = os.environ.get("PINECONE_ENV", self.config.get("environment", "us-east1-gcp"))
            pinecone.init(api_key=api_key, environment=environment)

            index_name = self.config.get("index_name", self._collection)
            if index_name not in pinecone.list_indexes():
                pinecone.create_index(
                    name=index_name,
                    dimension=self.config.get("dimension", 1536),
                    metric=self.config.get("metric", "cosine"),
                )
            self._client = pinecone.Index(index_name)
        except ImportError:
            print("Warning: pinecone-client not installed. Using mock mode.")

    def _connect_qdrant(self):
        """Connect to Qdrant."""
        try:
            from qdrant_client import QdrantClient

            url = os.environ.get("QDRANT_URL", self.config.get("url", "http://localhost:6333"))
            api_key = os.environ.get("QDRANT_API_KEY", self.config.get("api_key", ""))

            self._client = QdrantClient(url=url, api_key=api_key or None)

            # Create collection if it doesn't exist
            from qdrant_client.http import models as rest

            if not self._client.collection_exists(self._collection):
                self._client.create_collection(
                    collection_name=self._collection,
                    vectors_config=rest.VectorParams(
                        size=self.config.get("dimension", 1536),
                        distance=rest.Distance.COSINE,
                    ),
                )
        except ImportError:
            print("Warning: qdrant-client not installed. Using mock mode.")

    def upsert(self, vectors: List[Dict]) -> bool:
        """Insert or update vectors in the store.

        Args:
            vectors: List of dicts with keys: id, vector, payload
        """
        if not self._client:
            self.connect()

        if self.backend == "pinecone":
            items = [(v["id"], v["vector"], v.get("payload", {})) for v in vectors]
            self._client.upsert(vectors=items)
        elif self.backend == "qdrant":
            from qdrant_client.http import models as rest

            points = [
                rest.PointStruct(
                    id=v["id"],
                    vector=v["vector"],
                    payload=v.get("payload", {}),
                )
                for v in vectors
            ]
            self._client.upsert(collection_name=self._collection, points=points)
        return True

    def search(self, query_vector: List[float], top_k: int = 5, filters: Dict = None) -> List[Dict]:
        """Search for similar vectors.

        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            filters: Optional metadata filters

        Returns:
            List of dicts with keys: id, score, payload
        """
        if not self._client:
            self.connect()

        if self.backend == "pinecone":
            result = self._client.query(
                vector=query_vector,
                top_k=top_k,
                filter=filters,
                include_metadata=True,
            )
            return [
                {"id": m.id, "score": m.score, "payload": m.metadata}
                for m in result.get("matches", [])
            ]
        elif self.backend == "qdrant":
            from qdrant_client.http import models as rest

            search_result = self._client.search(
                collection_name=self._collection,
                query_vector=query_vector,
                limit=top_k,
                query_filter=filters,
                with_payload=True,
            )
            return [
                {"id": str(point.id), "score": point.score, "payload": point.payload}
                for point in search_result
            ]
        return []

    def delete(self, ids: List[str]) -> bool:
        """Delete vectors by IDs."""
        if not self._client:
            self.connect()

        if self.backend == "pinecone":
            self._client.delete(ids=ids)
        elif self.backend == "qdrant":
            from qdrant_client.http import models as rest

            self._client.delete(
                collection_name=self._collection,
                points_selector=rest.Filter(
                    must=[
                        rest.FieldCondition(
                            key="id",
                            match=rest.MatchAny(any=ids),
                        )
                    ]
                ),
            )
        return True

    def get(self, vector_id: str) -> Optional[Dict]:
        """Retrieve a specific vector by ID."""
        if not self._client:
            self.connect()

        if self.backend == "pinecone":
            result = self._client.fetch(ids=[vector_id])
            vectors = result.get("vectors", {})
            if vector_id in vectors:
                v = vectors[vector_id]
                return {"id": v.id, "values": v.values, "metadata": v.metadata}
        elif self.backend == "qdrant":
            from qdrant_client.http import models as rest

            results = self._client.retrieve(
                collection_name=self._collection,
                ids=[vector_id],
                with_payload=True,
                with_vectors=True,
            )
            if results:
                r = results[0]
                return {"id": str(r.id), "values": r.vector, "payload": r.payload}
        return None

    def count(self) -> int:
        """Count total vectors in the store."""
        if not self._client:
            self.connect()

        if self.backend == "pinecone":
            stats = self._client.describe_index_stats()
            return stats.get("total_vector_count", 0)
        elif self.backend == "qdrant":
            info = self._client.get_collection(self._collection)
            return info.points_count or 0
        return 0

    def close(self):
        """Close connections."""
        if self.backend == "pinecone":
            pinecone.deinit()
        self._client = None