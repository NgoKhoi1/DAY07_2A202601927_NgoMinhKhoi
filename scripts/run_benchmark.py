"""
run_benchmark.py — Chạy 5 câu hỏi đánh giá (benchmark queries) của nhóm cho Bài tập 3.4.

Nạp bộ tài liệu bằng `build_knowledge_base()` (ingest.py), sau đó với từng câu hỏi trong
QUESTIONS: chạy `search()` (hoặc `search_with_filter()` nếu có metadata_filter) để lấy
top-3 chunk, rồi gọi `KnowledgeBaseAgent.answer()`. Output in ra đủ dữ liệu để điền vào
REPORT_CANHAN.md — Phần 5 và REPORT_NHOM.md — Phần 3.

Chạy: python scripts/run_benchmark.py
Yêu cầu: đã cài `requirements-local.txt` (dùng LocalEmbedder cho kết quả có ý nghĩa;
mock embedder không phản ánh ngữ nghĩa nên không dùng để đánh giá retrieval).
"""
from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingest import build_knowledge_base
from src.agent import KnowledgeBaseAgent
from src.embeddings import LocalEmbedder

load_dotenv(override=False)

# Đổi thành thư mục dữ liệu thật của nhóm (vd. "data/k4_ecommerce" sau khi đã bổ sung tài liệu thật).
DATA_DIR = "data/k4_ecommerce"

# Mỗi phần tử: (câu hỏi, metadata_filter hoặc None).
# K4 yêu cầu: ít nhất 1 câu phải cần metadata_filter={"customer_role": "seller"} hoặc "buyer".
QUESTIONS: list[tuple[str, dict | None]] = [
    ("Câu hỏi 1 ...", None),
    ("Câu hỏi 2 ...", None),
    ("Câu hỏi 3 ...", {"customer_role": "seller"}),
    ("Câu hỏi 4 ...", None),
    ("Câu hỏi 5 ...", None),
]


def demo_llm(prompt: str) -> str:
    """LLM giả lập đơn giản — đổi bằng OpenAI/LLM thật nếu nhóm có API key."""
    preview = prompt[:200].replace("\n", " ")
    return f"[DEMO LLM] {preview}..."


def main() -> None:
    if not Path(DATA_DIR).exists():
        print(f"Không tìm thấy thư mục dữ liệu: {DATA_DIR}")
        print("Thu thập tài liệu vào thư mục này trước (xem docs/DATA_COLLECTION.md).")
        raise SystemExit(1)

    embedder = LocalEmbedder()
    store = build_knowledge_base(DATA_DIR, embedding_fn=embedder)
    agent = KnowledgeBaseAgent(store=store, llm_fn=demo_llm)
    print(f"Backend nhúng: {embedder._backend_name}")
    print(f"Đã nạp {store.get_collection_size()} chunk từ {DATA_DIR}\n")

    for index, (question, metadata_filter) in enumerate(QUESTIONS, start=1):
        print(f"=== Câu {index}: {question} ===")
        if metadata_filter:
            print(f"(lọc metadata: {metadata_filter})")
            results = store.search_with_filter(question, top_k=3, metadata_filter=metadata_filter)
        else:
            results = store.search(question, top_k=3)

        if not results:
            print("  (không có kết quả)")
        for rank, result in enumerate(results, start=1):
            content_preview = result["content"][:150].replace("\n", " ")
            print(f"  {rank}. score={result['score']:.3f} doc_id={result['metadata'].get('doc_id')}")
            print(f"     {content_preview!r}")

        print(f"  Agent answer: {agent.answer(question, top_k=3)}\n")


if __name__ == "__main__":
    main()
