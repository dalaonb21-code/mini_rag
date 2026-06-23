import json, requests, jieba
from pathlib import Path

GROUND_TRUTH_PATH = Path("eval/ground_truth.jsonl")
API_URL = "http://localhost:8001/query"
RESULT_PATH = Path("eval/eval_results.json")


def load_gt():
    with open(GROUND_TRUTH_PATH, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def run():
    gt = load_gt()
    results = []

    print(f"加载 {len(gt)} 条 ground truth")
    print("=" * 60)

    for i, item in enumerate(gt):
        q = item["question"]
        expected = item["answer"]
        print(f"[{i+1}/{len(gt)}] {q}")

        try:
            resp = requests.post(API_URL, json={"query": q, "top_k": 5}, timeout=30)
            data = resp.json()
        except Exception as e:
            print(f"  → 请求失败: {e}")
            results.append({
                "question": q,
                "ground_truth": expected,
                "answer": "",
                "contexts": [],
                "context_recall": 0.0,
                "faithfulness": 0.0,
                "hit_sources": [],
            })
            continue

        answer = data.get("answer", "")
        sources = data.get("sources", [])
        contexts = [s["title"] for s in sources]

        # recall@5：ground_truth 关键词是否出现在 top5 context 中（用 jieba 分词）
        gt_keywords = set(w for w in jieba.cut(expected) if len(w) > 1)
        hit = False
        for src in sources:
            src_text = src.get("title", "") + " " + src.get("content", "")[:500]
            if any(kw in src_text for kw in gt_keywords):
                hit = True
                break
        recall = 1.0 if hit else 0.0

        # faithfulness：answer 中的关键内容是否在 context 中出现
        answer_keywords = set(w for w in jieba.cut(answer) if len(w) > 1)
        all_context = " ".join(contexts)
        matched = sum(1 for kw in answer_keywords if kw in all_context and len(kw) > 1)
        faith = min(matched / max(len(answer_keywords), 1), 1.0)

        results.append({
            "question": q,
            "ground_truth": expected,
            "answer": answer,
            "contexts": contexts,
            "context_recall": recall,
            "faithfulness": faith,
            "hit_sources": [s.get("title", "") for s in sources],
        })
        print(f"  → recall={recall:.1f}, faith={faith:.2f}")

    # 保存结果
    RESULT_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{'=' * 60}")
    print(f"结果已保存到 {RESULT_PATH}")

    # 汇总
    avg_recall = sum(r["context_recall"] for r in results) / len(results)
    avg_faith = sum(r["faithfulness"] for r in results) / len(results)
    print(f"平均 Recall@5: {avg_recall:.3f}")
    print(f"平均 Faithfulness: {avg_faith:.3f}")

    # 生成报告
    from eval.report import generate_report
    generate_report(results)


if __name__ == "__main__":
    run()
