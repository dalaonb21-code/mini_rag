import json, csv, sys
from pathlib import Path

RESULT_PATH = Path("eval/eval_results.json")


def generate_report(results: list[dict], output: str = "eval/report.md"):
    """从评估结果生成 Markdown 报告"""
    lines = ["# Mining RAG 评估报告\n"]

    # 汇总指标
    recall_vals = [r.get("context_recall", 0) for r in results]
    faith_vals = [r.get("faithfulness", 0) for r in results]
    avg_recall = sum(recall_vals) / len(recall_vals) if recall_vals else 0
    avg_faith = sum(faith_vals) / len(faith_vals) if faith_vals else 0

    lines.append(f"## 汇总\n")
    lines.append(f"| 指标 | 值 |")
    lines.append(f"|------|------|")
    lines.append(f"| 样本数 | {len(results)} |")
    lines.append(f"| 平均 Recall@5 | {avg_recall:.3f} |")
    lines.append(f"| 平均 Faithfulness | {avg_faith:.3f} |")
    lines.append(f"| Recall≥0.8 占比 | {sum(1 for v in recall_vals if v >= 0.8) / len(recall_vals):.1%} |")
    lines.append(f"| Faith≥0.85 占比 | {sum(1 for v in faith_vals if v >= 0.85) / len(faith_vals):.1%} |")
    lines.append("")

    # 逐条明细
    lines.append("## 逐条明细\n")
    lines.append("| # | 问题 | Recall | Faith | 命中来源 |")
    lines.append("|---|------|--------|-------|----------|")
    for i, r in enumerate(results):
        q = r.get("question", "")[:30]
        rec = r.get("context_recall", 0)
        faith = r.get("faithfulness", 0)
        src = ", ".join(r.get("hit_sources", [])[:3])
        lines.append(f"| {i+1} | {q} | {rec:.2f} | {faith:.2f} | {src} |")

    report = "\n".join(lines)
    Path(output).write_text(report, encoding="utf-8")
    print(f"报告已写入 {output}")
    print(report)
