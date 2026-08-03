from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot, compute_similarity
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

        try:
            import chromadb  # type: ignore # noqa: F401

            client = chromadb.Client()
            self._collection = client.get_or_create_collection(name=collection_name)
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        embedding = self._embedding_fn(doc.content)
        return {
            "id": doc.id,
            "content": doc.content,
            "metadata": dict(doc.metadata),
            "embedding": embedding,
        }

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        if not records:
            return []
        query_emb = self._embedding_fn(query)
        scored_records = []
        for rec in records:
            score = compute_similarity(query_emb, rec["embedding"])
            scored_records.append({
                "id": rec["id"],
                "content": rec["content"],
                "metadata": rec["metadata"],
                "score": score,
            })
        scored_records.sort(key=lambda r: r["score"], reverse=True)
        return scored_records[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        if not docs:
            return
        if self._use_chroma and self._collection is not None:
            ids = [doc.id for doc in docs]
            contents = [doc.content for doc in docs]
            embeddings = [self._embedding_fn(doc.content) for doc in docs]
            metadatas = [doc.metadata for doc in docs]
            self._collection.add(
                ids=ids,
                documents=contents,
                embeddings=embeddings,
                metadatas=metadatas,
            )
        else:
            for doc in docs:
                rec = self._make_record(doc)
                self._store.append(rec)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        if self._use_chroma and self._collection is not None:
            query_emb = self._embedding_fn(query)
            res = self._collection.query(
                query_embeddings=[query_emb],
                n_results=min(top_k, self._collection.count() or 1),
            )
            results = []
            if res and res.get("ids") and res["ids"][0]:
                for i in range(len(res["ids"][0])):
                    doc_id = res["ids"][0][i]
                    content = res["documents"][0][i] if res.get("documents") else ""
                    metadata = res["metadatas"][0][i] if res.get("metadatas") else {}
                    distance = res["distances"][0][i] if res.get("distances") else 0.0
                    score = 1.0 - distance if res.get("distances") else 1.0
                    results.append({
                        "id": doc_id,
                        "content": content,
                        "metadata": metadata,
                        "score": score,
                    })
            return results[:top_k]
        else:
            return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        if self._use_chroma and self._collection is not None:
            return self._collection.count()
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        if not metadata_filter:
            return self.search(query, top_k=top_k)

        if self._use_chroma and self._collection is not None:
            query_emb = self._embedding_fn(query)
            res = self._collection.query(
                query_embeddings=[query_emb],
                n_results=min(top_k, self._collection.count() or 1),
                where=metadata_filter,
            )
            results = []
            if res and res.get("ids") and res["ids"][0]:
                for i in range(len(res["ids"][0])):
                    doc_id = res["ids"][0][i]
                    content = res["documents"][0][i] if res.get("documents") else ""
                    metadata = res["metadatas"][0][i] if res.get("metadatas") else {}
                    distance = res["distances"][0][i] if res.get("distances") else 0.0
                    score = 1.0 - distance if res.get("distances") else 1.0
                    results.append({
                        "id": doc_id,
                        "content": content,
                        "metadata": metadata,
                        "score": score,
                    })
            return results[:top_k]
        else:
            filtered_records = []
            for rec in self._store:
                match = True
                rec_meta = rec.get("metadata", {})
                for k, v in metadata_filter.items():
                    if rec_meta.get(k) != v:
                        match = False
                        break
                if match:
                    filtered_records.append(rec)
            return self._search_records(query, filtered_records, top_k)

    def delete_document(self, doc_id: str) -> bool:
        if self._use_chroma and self._collection is not None:
            try:
                existing = self._collection.get(where={"doc_id": doc_id})
                if existing and existing.get("ids"):
                    self._collection.delete(where={"doc_id": doc_id})
                    return True
                existing_id = self._collection.get(ids=[doc_id])
                if existing_id and existing_id.get("ids"):
                    self._collection.delete(ids=[doc_id])
                    return True
                return False
            except Exception:
                return False
        else:
            initial_count = len(self._store)
            self._store = [
                rec for rec in self._store
                if rec["id"] != doc_id and rec.get("metadata", {}).get("doc_id") != doc_id
            ]
            return len(self._store) < initial_count

