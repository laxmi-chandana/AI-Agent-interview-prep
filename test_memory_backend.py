import os
import tempfile
import unittest

from main import FileMemoryStore, Mem0MemoryAdapter


class MemoryBackendTests(unittest.TestCase):
    def test_file_memory_store_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileMemoryStore(os.path.join(tmpdir, "memory.json"))
            store.add([{"role": "user", "content": "I am preparing for backend engineer interviews"}], user_id="user-1", metadata={"type": "profile"})
            results = store.search("backend engineer", user_id="user-1", top_k=5)
            self.assertTrue(any("backend engineer" in item["memory"].lower() for item in results))

    def test_mem0_adapter_falls_back_to_file_store(self):
        class FailingPrimary:
            def add(self, *args, **kwargs):
                raise RuntimeError("vector mismatch")

            def search(self, *args, **kwargs):
                raise RuntimeError("vector mismatch")

        with tempfile.TemporaryDirectory() as tmpdir:
            fallback = FileMemoryStore(os.path.join(tmpdir, "fallback.json"))
            adapter = Mem0MemoryAdapter(FailingPrimary(), fallback)
            adapter.add([{"role": "user", "content": "I am learning DSA"}], user_id="user-2", metadata={"type": "profile"})
            results = adapter.search("DSA", user_id="user-2", top_k=5)
            self.assertTrue(any("dsa" in item["memory"].lower() for item in results))


if __name__ == "__main__":
    unittest.main()
