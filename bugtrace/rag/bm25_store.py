from pathlib import Path
from rank_bm25 import BM25Okapi
import json
import re


class BM25Store:
    """
    Persistent BM25 keyword index for code retrieval.
    """

    def __init__(self, persist_dir: Path):
        self.persist_dir = persist_dir
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        self.docs_path = self.persist_dir / "documents.json"

        self.documents = []
        self.tokenized_documents = []
        self.bm25 = None

        self._load()

    def _tokenize(self, text: str):
        """
        Better tokenizer for code + stacktraces.
        """
        text = text.lower()

        # split on non-word chars
        tokens = re.split(r'[^a-zA-Z0-9_\.]+', text)

        return [t for t in tokens if t]

    def _load(self):
        if not self.docs_path.exists():
            return

        with open(self.docs_path, "r", encoding="utf-8") as f:
            self.documents = json.load(f)

        self.tokenized_documents = [
            self._tokenize(doc["text"])
            for doc in self.documents
        ]

        if self.tokenized_documents:
            self.bm25 = BM25Okapi(self.tokenized_documents)

    def save(self):
        with open(self.docs_path, "w", encoding="utf-8") as f:
            json.dump(self.documents, f)

    def rebuild(self):
        self.tokenized_documents = [
            self._tokenize(doc["text"])
            for doc in self.documents
        ]

        self.bm25 = BM25Okapi(self.tokenized_documents)

    def add_chunks(self, chunks):
        """
        Add chunks to BM25 index.
        """

        for chunk in chunks:
            self.documents.append({
                "text": chunk["text"],
                "metadata": chunk["metadata"]
            })

        self.rebuild()
        self.save()

    def delete_file_chunks(self, filepath: str):
        filepath = str(Path(filepath).resolve())

        self.documents = [
            doc
            for doc in self.documents
            if doc["metadata"].get("file") != filepath
        ]

        self.rebuild()
        self.save()

    def search(self, query: str, k: int = 5):
        if not self.bm25:
            return []

        tokenized_query = self._tokenize(query)

        scores = self.bm25.get_scores(tokenized_query)

        ranked = sorted(
            zip(self.documents, scores),
            key=lambda x: x[1],
            reverse=True
        )

        # -----------------------------
        # NORMALIZE USING ALL DOCUMENTS
        # -----------------------------

        all_scores = [
            score
            for _, score in ranked
        ]

        min_score = min(all_scores)
        max_score = max(all_scores)


        results = []

        seen = set()

        for doc, score in ranked:
            key = (
                doc["metadata"].get("file"),
                str(doc["metadata"].get("chunk_id"))
            )

            if key in seen:
                continue

            seen.add(key)

            if len(results) >= k:
                break

            if max_score == min_score:
                normalized = 1.0
            else:
                normalized = (
                    (score - min_score)
                    /
                    (max_score - min_score)
                )

            normalized = 0.1 + (0.9 * normalized)

            results.append({
                    "text": doc["text"],
                    "metadata": doc["metadata"],
                    "score": float(normalized),
                    "bm25_score": float(normalized),
                    "source": "bm25"
                })

        return results
