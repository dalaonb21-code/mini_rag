from datasketch import MinHash, MinHashLSH

class Deduplicator:
    def __init__(self, threshold: float = 0.85, num_perm: int = 128):
        self.lsh = MinHashLSH(threshold=threshold, num_perm=num_perm)
        self.seen_ids = set()

    def is_duplicate(self, doc_id: str, text: str) -> bool:
        m = MinHash(num_perm=128)
        for word in text.lower().split():
            m.update(word.encode("utf-8"))

        if self.lsh.query(m):
            return True
        self.lsh.insert(doc_id, m)
        return False

    def filter(self, docs) -> list:
        unique = []
        for doc in docs:
            key = doc.url
            if not self.is_duplicate(key, doc.title + doc.content[:200]):
                unique.append(doc)
        return unique