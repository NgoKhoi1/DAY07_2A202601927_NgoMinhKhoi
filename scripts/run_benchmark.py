"""
run_benchmark.py — Chạy 5 câu hỏi đánh giá (benchmark queries) của nhóm cho Bài tập 3.4,
so sánh cả 3 chiến lược chunking (fixed_size / by_sentences / recursive) trên cùng bộ câu hỏi.

Build 3 EmbeddingStore riêng biệt (1 cho mỗi chiến lược trong STRATEGIES) từ cùng bộ tài liệu,
sau đó với từng câu hỏi trong QUESTIONS: chạy search() (hoặc search_with_filter() nếu có
metadata_filter) trên cả 3 store và in top-3 song song để so sánh trực tiếp. Output đủ dữ liệu
để điền vào REPORT_CANHAN.md — Phần 5 và REPORT_NHOM.md — Phần 3 (bảng "Tổng hợp chất lượng
truy xuất") và Phần 2 ("So Sánh Giữa Các Thành Viên" nếu mỗi người đối chiếu với chiến lược
riêng của mình).

Chạy: python scripts/run_benchmark.py
Yêu cầu: đã cài `requirements-local.txt` (dùng LocalEmbedder cho kết quả có ý nghĩa;
mock embedder không phản ánh ngữ nghĩa nên không dùng để đánh giá retrieval).
"""
from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ingest import build_knowledge_base
from src.agent import KnowledgeBaseAgent
from src.chunking import FixedSizeChunker, RecursiveChunker, SentenceChunker
from src.embeddings import LocalEmbedder

load_dotenv(override=False)

# Đường dẫn tuyệt đối tính từ vị trí file này — chạy đúng dù bạn đứng ở thư mục nào khi gọi script.
# Đổi thành thư mục dữ liệu thật của nhóm (vd. "data/k4_ecommerce" sau khi đã bổ sung tài liệu thật).
DATA_DIR = str(PROJECT_ROOT / "data" / "_test_crawl")

# Mỗi phần tử: (câu hỏi, metadata_filter hoặc None).
# K4 yêu cầu: ít nhất 1 câu phải cần metadata_filter={"customer_role": "seller"} hoặc "buyer".
QUESTIONS: list[tuple[str, dict | None]] = [
    ("Người mua có bao nhiêu ngày để gửi yêu cầu trả hàng/hoàn tiền, và trường hợp thực phẩm tươi sống thì sao?", None),
    ("Người bán cần đáp ứng những yêu cầu gì về hình ảnh khi đăng bán sản phẩm?", {"customer_role": "seller"}),
    ("Những loại vũ khí hoặc vật dụng có hình dạng giống vũ khí nào bị cấm bán trên Shopee?", None),
    ("Ai chịu trách nhiệm bảo hành sản phẩm cho người mua — Shopee hay người bán?", None),
    ("Người bán có được hoàn Phí Dịch Vụ Hiển Thị đã thanh toán nếu muốn hủy không?", None),
]

# 3 chiến lược built-in cần so sánh. Đổi tham số hoặc thêm "custom": lambda: YourChunker(...)
# nếu muốn thêm chiến lược tùy chỉnh (vd. chia theo điều/khoản — yêu cầu riêng của K4).
STRATEGIES: dict[str, "callable[[], object]"] = {
    "fixed_size": lambda: FixedSizeChunker(chunk_size=500, overlap=50),
    "by_sentences": lambda: SentenceChunker(max_sentences_per_chunk=3),
    "recursive": lambda: RecursiveChunker(chunk_size=500),
}


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
    print(f"Backend nhúng: {embedder._backend_name}\n")

    stores: dict[str, object] = {}
    for strategy_name, make_chunker in STRATEGIES.items():
        store = build_knowledge_base(DATA_DIR, embedding_fn=embedder, chunker=make_chunker())
        stores[strategy_name] = store
        print(f"[{strategy_name}] đã nạp {store.get_collection_size()} chunk từ {DATA_DIR}")
    print()

    for index, (question, metadata_filter) in enumerate(QUESTIONS, start=1):
        print(f"=== Câu {index}: {question} ===")
        if metadata_filter:
            print(f"(lọc metadata: {metadata_filter})")

        for strategy_name, store in stores.items():
            print(f"  --- {strategy_name} ---")
            if metadata_filter:
                results = store.search_with_filter(question, top_k=3, metadata_filter=metadata_filter)
            else:
                results = store.search(question, top_k=3)

            if not results:
                print("    (không có kết quả)")
            for rank, result in enumerate(results, start=1):
                content_preview = result["content"][:120].replace("\n", " ")
                print(
                    f"    {rank}. score={result['score']:.3f} "
                    f"doc_id={result['metadata'].get('doc_id')} — {content_preview!r}"
                )
        print()

    # Câu trả lời RAG đầy đủ chỉ demo với 1 chiến lược (fixed_size) để tránh output quá dài.
    # Đổi "fixed_size" thành strategy bạn muốn xem câu trả lời của agent.
    print("=== Agent answer (demo với chiến lược fixed_size) ===")
    agent = KnowledgeBaseAgent(store=stores["fixed_size"], llm_fn=demo_llm)
    for index, (question, _) in enumerate(QUESTIONS, start=1):
        print(f"Câu {index}: {agent.answer(question, top_k=3)}\n")


if __name__ == "__main__":
    main()
