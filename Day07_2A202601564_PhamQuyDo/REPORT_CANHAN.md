# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Phạm Quý Đô - 2A202601564
**Nhóm:** 36899998
**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao có nghĩa là hướng của hai vector nhúng (embeddings) trong không gian nhiều chiều gần như trùng khớp với nhau (góc giữa hai vector rất nhỏ, tiệm cận 0 độ, khiến $\cos\theta \approx 1$). Về mặt ngữ nghĩa, điều này thể hiện hai đoạn văn bản có sự tương đồng rất lớn về nội dung hoặc ngữ cảnh, bất kể độ dài ngắn khác nhau của hai văn bản.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Chính sách đổi trả hàng cho phép người mua trả lại sản phẩm trong vòng 30 ngày."
- Câu B: "Khách hàng có quyền hoàn trả hàng hóa và nhận lại tiền trong thời hạn 30 ngày kể từ khi nhận hàng."
- Tại sao tương đồng: Cả hai câu đều cùng mô tả về quy định thời hạn và quyền lợi đổi trả sản phẩm trong thương mại điện tử, mặc dù sử dụng từ ngữ và cách diễn đạt khác nhau.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Chính sách đổi trả hàng cho phép người mua trả lại sản phẩm trong vòng 30 ngày."
- Câu B: "Cơ sở dữ liệu vector hỗ trợ lưu trữ và tìm kiếm ngữ nghĩa theo thuật toán Cosine Similarity."
- Tại sao khác: Hai câu thuộc hai chủ đề hoàn toàn độc lập (một bên là quy trình kinh doanh/CSKH thương mại điện tử, một bên là kiến trúc kỹ thuật của cơ sở dữ liệu vector).

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Khoảng cách Euclid đo độ dài đường thẳng giữa hai điểm ngọn vector nên bị ảnh hưởng mạnh bởi độ dài văn bản (văn bản dài hơn sẽ tạo ra vector có độ lớn lớn hơn, làm tăng khoảng cách Euclid dù cùng chủ đề). Ngược lại, độ tương tự Cosine chỉ đo góc giữa hai vector và tự động chuẩn hóa theo độ dài, giúp so sánh chính xác bản chất ngữ nghĩa của văn bản mà không bị biến dạng bởi độ dài văn bản.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*
> - Công thức: $\text{số lượng chunk} = \lceil (\text{độ\_dài\_tài\_liệu} - \text{độ\_chồng\_chéo}) / (\text{kích\_thước\_chunk} - \text{độ\_chồng\_chéo}) \rceil$
> - Phép tính: $\lceil (10000 - 50) / (500 - 50) \rceil = \lceil 9950 / 450 \rceil = \lceil 22.11 \rceil = 23$
> *Đáp án:* 23 chunks.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> - Phép tính khi overlap = 100: $\lceil (10000 - 100) / (500 - 100) \rceil = \lceil 9900 / 400 \rceil = \lceil 24.75 \rceil = 25$ chunks (tăng thêm 2 chunks).
> - Lý do muốn tăng độ chồng chéo: Tránh mất mát ngữ cảnh tại các ranh giới cắt chia (chunk boundaries), đảm bảo các câu hoặc ý nghĩa nằm ở điểm giáp ranh giữa 2 chunk không bị ngắt đôi, giúp nâng cao độ chính xác khi truy xuất thông tin.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Sử dụng biểu thức chính quy `re.split(r'(?<=[.!?])\s+|\.\n', text)` kết hợp kỹ thuật lookbehind `(?<=[.!?])` để tách câu mà vẫn giữ lại các dấu kết thúc câu (`.`, `!`, `?`). Xử lý ngoại lệ loại bỏ các chuỗi rỗng và khoảng trắng thừa bằng `[s.strip() for s in ... if s.strip()]`, sau đó gom các câu thành các chunk chứa tối đa `max_sentences_per_chunk` câu.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Áp dụng thuật toán chia đệ quy theo danh sách phân cách ưu tiên `["\n\n", "\n", ". ", " ", ""]`. Trường hợp cơ sở (base case) là khi văn bản rỗng, độ dài $\le$ `chunk_size`, hoặc đã duyệt hết danh sách dấu phân cách (lúc này cắt nhỏ theo `chunk_size`). Khi một đoạn bị chia vẫn dài hơn `chunk_size`, hàm đệ quy `_split` sẽ tiếp tục được gọi với danh sách dấu phân cách còn lại để đảm bảo mọi chunk trả về đều thỏa mãn giới hạn độ dài.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Chuẩn hóa từng document thông qua `_make_record` để tính vector embedding bằng `self._embedding_fn` và lưu vào `self._store` (hoặc ChromaDB nếu có). Khi thực hiện `search`, mã nhúng câu truy vấn thành vector query, tính Cosine Similarity với toàn bộ vector đã lưu bằng `compute_similarity`, sau đó sắp xếp giảm dần theo score và lấy top $k$ kết quả.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Trong `search_with_filter`, tiến hành tiền lọc (pre-filtering) các bản ghi trong `self._store` có metadata trùng khớp với toàn bộ cặp key-value trong `metadata_filter`, sau đó mới chạy `_search_records` trên tập bản ghi đã lọc. Với `delete_document`, lọc bỏ tất cả các chunk có `id == doc_id` hoặc `metadata['doc_id'] == doc_id` và trả về `True` nếu số lượng phần tử bị giảm.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Gọi `self.store.search(question, top_k=top_k)` để truy xuất $k$ chunk liên quan nhất. Ghép nội dung `content` của các chunk thành một khối văn bản `Context information`, sau đó tạo prompt theo mẫu tiêu chuẩn RAG: `"Context information:\n{context}\n\nGiven the context information above, answer the question: {question}"` và truyền vào `self.llm_fn(prompt)` để nhận câu trả lời.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```text
============================= test session starts =============================
platform win32 -- Python 3.13.8, pytest-8.3.4, pluggy-1.6.0
rootdir: D:\VinLab\Day07\DAY07_2A202601564_PhamQuyDo
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================= 42 passed in 0.07s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Khách hàng có thể đổi trả hàng trong 30 ngày. | Người mua được phép trả sản phẩm trong vòng 30 ngày. | cao | 0.068 (Mock) / 0.892 (Local) | Đúng |
| 2 | Khách hàng có thể đổi trả hàng trong 30 ngày. | Mô hình vector database lưu trữ embedding để tìm kiếm. | thấp | -0.044 (Mock) / 0.115 (Local) | Đúng |
| 3 | Người bán chịu trách nhiệm đăng thông tin chính xác. | Sản phẩm bị cấm không được bán trên sàn. | cao | 0.010 (Mock) / 0.614 (Local) | Đúng |
| 4 | Python là ngôn ngữ lập trình phổ biến. | Python được sử dụng rộng rãi cho trí tuệ nhân tạo. | cao | -0.066 (Mock) / 0.785 (Local) | Đúng |
| 5 | Quyền riêng tư của người dùng được bảo vệ. | Thuật toán sắp xếp nhanh có độ phức tạp O(n log n). | thấp | -0.075 (Mock) / 0.084 (Local) | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Kết quả bất ngờ nhất là khi dùng `MockEmbedder`, điểm tương đồng gần như ngẫu nhiên do chỉ băm MD5 chuỗi ký tự. Tuy nhiên khi dùng mô hình nhúng thật (`LocalEmbedder`), các câu có cùng ngữ cảnh nhưng từ ngữ khác nhau đều đạt điểm số tương đồng rất cao (> 0.7). Điều này chứng minh rằng vector embeddings biểu diễn văn bản trong không gian ngữ nghĩa ẩn (semantic latent space) chứ không phụ thuộc vào việc khớp từ khóa chính xác (exact word matching).

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Khách hàng có thể trả hàng trong bao nhiêu ngày kể từ khi nhận? | Người mua có thể yêu cầu trả hàng trong vòng 7 ngày kể từ khi nhận... | 0.785 | Có | Theo chính sách, khách hàng có quyền trả hàng trong vòng 7 ngày kể từ khi nhận hàng. |
| 2 | Trách nhiệm của người bán đối với thông tin sản phẩm là gì? | Người bán chịu trách nhiệm cung cấp thông tin sản phẩm chính xác... | 0.812 | Có | Người bán chịu trách nhiệm hoàn toàn về tính chính xác của thông tin sản phẩm đăng bán. |
| 3 | Điều kiện để yêu cầu hoàn tiền khi đổi trả là gì? | Hàng hóa phải còn nguyên tem mác, chưa qua sử dụng và có hóa đơn... | 0.743 | Có | Điều kiện hoàn tiền gồm hàng nguyên tem mác, chưa sử dụng và kèm hóa đơn mua hàng. |
| 4 | [Filter: customer_role=seller] Quy định về phí dịch vụ đăng bán áp dụng thế nào? | Người bán phải thanh toán phí dịch vụ sàn là 5% trên mỗi đơn thành công... | 0.829 | Có | Phí dịch vụ dành cho người bán là 5% tính trên tổng giá trị đơn hàng thành công. |
| 5 | Các mặt hàng nào bị cấm đăng bán trên sàn thương mại điện tử? | Danh mục hàng cấm gồm vũ khí, chất cháy nổ, hàng giả và thực phẩm hết hạn... | 0.796 | Có | Các mặt hàng cấm gồm vũ khí, hàng giả, chất nổ và thực phẩm không bảo đảm an toàn. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Việc kết hợp lọc theo Siêu dữ liệu (Metadata Filtering) trước khi thực hiện tìm kiếm Vector (Pre-filtering) giúp loại bỏ toàn bộ các chunk gây nhiễu từ vai trò khác (ví dụ: tách biệt quy định dành riêng cho Seller và Buyer). Điều này làm tăng rõ rệt độ chính xác Retrieval Precision và tránh tình trạng LLM bị hallucination khi tổng hợp câu trả lời.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **60 / 60** |
