import os, torch
torch.set_num_threads(2)

from transformers import AutoTokenizer, AutoModel
import numpy as np

DEFAULT_MODEL_PATH = os.getenv(
    "BGE_M3_PATH",
    r"D:\Pycharm\mini_rag\model\bge-small-zh-v1.5"
)


class Embedder:
    def __init__(self, model_name: str = ""):
        path = model_name or DEFAULT_MODEL_PATH
        print(f"[Embedder] 加载模型: {path}")
        self.tokenizer = AutoTokenizer.from_pretrained(path)
        self.model = AutoModel.from_pretrained(path, attn_implementation="sdpa")
        self.model.eval()
        print("[Embedder] 模型加载完成")

    def encode_batch(self, texts: list[str], batch_size: int = 4) -> np.ndarray:
        all_vecs = []
        total = len(texts)
        for i in range(0, total, batch_size):
            batch = texts[i : i + batch_size]
            inputs = self.tokenizer(
                batch, return_tensors="pt", padding=True,
                truncation=True, max_length=512
            )
            with torch.no_grad():
                outputs = self.model(**inputs)
                vecs = outputs.last_hidden_state[:, 0].float()
                vecs = torch.nn.functional.normalize(vecs, p=2, dim=1)
            all_vecs.append(vecs.numpy())
            print(f"  → 向量化 {min(i + batch_size, total)}/{total}")
        return np.vstack(all_vecs)
