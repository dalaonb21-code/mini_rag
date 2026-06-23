"""矿业 RAG 管线 — 一键入口"""
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["PYTORCH_NO_SHARED_MEMORY"] = "1"

from dotenv import load_dotenv
load_dotenv()

import sys
from pathlib import Path

# 确保项目根目录在 sys.path 中
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import argparse
import uvicorn


def main():
    parser = argparse.ArgumentParser(description="Mining RAG Pipeline")
    sub = parser.add_subparsers(dest="cmd")

    # pipeline
    p_pipe = sub.add_parser("pipeline", help="采集 → 清洗 → 去重 → 入库")
    p_pipe.add_argument("--days", type=int, default=30)
    p_pipe.add_argument("--limit", type=int, default=200)

    # serve
    p_serve = sub.add_parser("serve", help="启动 FastAPI 服务")
    p_serve.add_argument("--host", default="0.0.0.0")
    p_serve.add_argument("--port", type=int, default=8000)

    # eval
    sub.add_parser("eval", help="运行评估")

    args = parser.parse_args()

    if args.cmd == "pipeline":
        from pipeline.run_pipeline import run_pipeline
        run_pipeline(days=args.days, limit=args.limit)
    elif args.cmd == "serve":
        uvicorn.run("serve.main:app", host=args.host, port=args.port)
    elif args.cmd == "eval":
        from eval.run_eval import run
        run()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
