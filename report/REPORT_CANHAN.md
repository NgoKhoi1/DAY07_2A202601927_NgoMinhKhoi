# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Ngô Minh Khôi
**Nhóm:** [Tên nhóm]
**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> *Viết 1-2 câu:*
> Cosine similarity gần 1 nghĩa là góc giữa hai vector embedding rất nhỏ — hai đoạn văn bản trỏ về cùng một "hướng ngữ nghĩa" trong không gian vector, tức nội dung/chủ đề tương đồng, dù cách diễn đạt (từ ngữ) có thể khác nhau.

**Ví dụ có độ tương tự CAO:** *(điểm thực tế đo bằng `LocalEmbedder` — `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, qua `compute_similarity` đã implement)*
- Câu A: "Người mua cần gửi yêu cầu đổi trả trong thời hạn quy định."
- Câu B: "Khách hàng có thể yêu cầu hoàn trả sản phẩm trong thời gian cho phép."
- Điểm thực tế: **0.5396**
- Tại sao tương đồng: cùng nói về chính sách đổi trả (return policy) — chỉ khác từ đồng nghĩa (`đổi trả`/`hoàn trả`, `người mua`/`khách hàng`), cùng chủ đề nên embedding gần nhau về hướng.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Người mua cần gửi yêu cầu đổi trả trong thời hạn quy định."
- Câu B: "Người bán chịu trách nhiệm cung cấp thông tin sản phẩm chính xác."
- Điểm thực tế: **0.4820**
- Tại sao khác: hai chủ đề khác nhau trong cùng domain TMĐT — một câu về quyền của người mua khi đổi trả, một câu về nghĩa vụ của người bán khi đăng bán — không chia sẻ nhiều ngữ nghĩa cốt lõi.
- *Lưu ý:* khoảng cách giữa hai điểm không lớn (0.54 so với 0.48) vì cả hai câu vẫn cùng domain thương mại điện tử tiếng Việt (chia sẻ nhiều từ vựng như "người mua/người bán", "sản phẩm") — cosine similarity phản ánh đúng hướng (cao hơn khi cùng chủ đề) nhưng không tách bạch mạnh như khi so hai domain hoàn toàn khác nhau (vd. chính sách đổi trả và một câu về nấu ăn).

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> *Viết 1-2 câu:*
> Cosine chỉ đo góc/hướng giữa hai vector, không quan tâm độ dài (magnitude) của chúng — nên không bị lệch khi văn bản dài ngắn khác nhau làm vector có độ lớn khác nhau. Euclidean distance đo khoảng cách tuyệt đối nên nhạy với magnitude, dễ đánh giá sai hai đoạn văn cùng chủ đề nhưng độ dài khác nhau là "không giống nhau".

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*
> Với `FixedSizeChunker`, mỗi bước trượt (step) = `chunk_size - overlap` = 500 - 50 = 450 ký tự.
> Số chunk ≈ ceil((L - chunk_size) / step) + 1 = ceil((10000 - 500) / 450) + 1 = ceil(21.11) + 1 = 22 + 1 = **23**.
> Đã xác minh bằng code thật: `FixedSizeChunker(chunk_size=500, overlap=50).chunk("x"*10000)` → `len(...) == 23`.
>
> **Đáp án: 23 chunks.**

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> *Viết 1-2 câu:*
> Overlap tăng lên 100 → step giảm còn 400 → số chunk tăng lên **25** (đã xác minh bằng code: `chunk_size=500, overlap=100` → 25 chunks). Overlap nhiều hơn giúp giữ lại ngữ cảnh ở ranh giới cắt — tránh trường hợp một câu/ý quan trọng bị cắt đứt giữa chừng và mất hoàn toàn khỏi cả hai chunk liền kề, đổi lại là tốn thêm dung lượng lưu trữ và chi phí embedding do nội dung bị lặp.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Dùng một regex duy nhất `(?<=[.!?])\s+` với lookbehind để tách câu: lookbehind khớp vị trí ngay sau dấu `.`, `!`, `?` mà không "ăn mất" dấu câu đó, còn `\s+` khớp khoảng trắng theo sau (gồm cả dấu cách và `\n`) — nhờ vậy một pattern gộp được cả 4 kiểu phân cách yêu cầu (`". "`, `"! "`, `"? "`, `".\n"`). Sau khi tách, `strip()` từng câu và lọc câu rỗng để tránh chunk rác khi văn bản có khoảng trắng thừa ở cuối. Giới hạn: đây không phải sentence tokenizer chuẩn nên sẽ tách sai với viết tắt hoặc số thập phân (`"3.14"`), nhưng đủ dùng cho phạm vi lab.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán đệ quy kiểu `RecursiveCharacterTextSplitter`: thử cắt theo ranh giới thô nhất trước (`\n\n`), nếu một phần vẫn dài hơn `chunk_size` thì lùi xuống ranh giới mịn hơn (`\n` → `. ` → `" "` → `""`) bằng cách gọi lại `_split` với danh sách separator còn lại. Base case là khi `current_text` đã ≤ `chunk_size` (trả nguyên văn) hoặc hết separator (cắt cứng theo cửa sổ ký tự — lưới an toàn cuối cùng). Giữa hai lần đệ quy, các phần được gộp tham lam (greedy) lại với nhau miễn tổng độ dài không vượt `chunk_size`, để tận dụng tối đa không gian chunk thay vì tạo nhiều chunk nhỏ lẻ tẻ.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> `add_documents` gọi `_make_record` cho từng `Document`: embed nội dung bằng `self._embedding_fn`, lưu kèm `id`, `content`, `metadata` (đảm bảo luôn có `doc_id` bằng `setdefault`) vào danh sách in-memory `self._store`. `search` embed câu truy vấn rồi tính điểm bằng **dot product** (`_dot`) giữa vector truy vấn và từng embedding đã lưu — dùng dot product thuần thay vì công thức cosine đầy đủ vì cả 3 embedder (mock/local/OpenAI) đều trả vector đã chuẩn hoá (norm = 1), nên dot product tương đương cosine similarity nhưng rẻ hơn. Kết quả được sắp xếp giảm dần theo điểm và cắt `top_k`.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> `search_with_filter` **lọc trước, search sau**: duyệt `self._store`, chỉ giữ lại record có toàn bộ cặp key-value trong `metadata_filter` khớp với `record["metadata"]`, rồi mới chạy chung hàm `_search_records` trên tập đã lọc — tránh việc phải tính điểm tương đồng cho các record chắc chắn bị loại. `delete_document` xóa bằng cách xây một danh sách mới chỉ giữ record có `metadata["doc_id"] != doc_id`, so sánh độ dài trước/sau để biết có gì bị xóa hay không (trả về `True`/`False`).

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> `__init__` chỉ lưu tham chiếu `store` và `llm_fn`. `answer` làm đúng 3 bước RAG: (1) gọi `store.search(question, top_k=top_k)` để lấy các chunk liên quan; (2) nối nội dung các chunk (`result["content"]`) thành một khối "Context", ghép với câu hỏi gốc theo template `"Context:\n{context}\n\nQuestion: {question}\nAnswer:"`; (3) gọi `llm_fn(prompt)` — hàm sinh câu trả lời được tiêm từ bên ngoài (dependency injection), giúp agent không phụ thuộc cụ thể vào một LLM provider nào.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
$ pytest tests/ -v
================================ test session starts =================================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED

================================= 42 passed in 0.11s ==================================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

> *Đo bằng `compute_similarity()` + `LocalEmbedder` (`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`), 5 cặp câu lấy từ dữ liệu thật trong `data/`. Dự đoán được ghi trước khi chạy code, theo đúng quy trình ở `exercises.md` — Bài tập 3.3.*

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | "Chất lượng của hệ thống truy xuất phụ thuộc rất lớn vào chất lượng của các đoạn (chunks)." *(vector_store_notes.md)* | "Việc truy xuất tốt là kết quả của khâu chuẩn bị dữ liệu cẩn thận, chứ không chỉ là việc chọn cơ sở dữ liệu." *(vector_store_notes.md)* | cao | 0.7745 | ✓ |
| 2 | "Metadata... các bộ lọc metadata có thể thu hẹp không gian tìm kiếm và cải thiện độ chính xác." *(vector_store_notes.md)* | "Metadata cần phân biệt giữa các bài viết dành cho khách hàng, ghi chú nội bộ, và tài liệu sự cố chỉ dành cho kỹ sư." *(customer_support_playbook.txt)* | cao | 0.4486 | ✗ |
| 3 | "Nhúng từng đoạn (embed each chunk) thành một vector số học dày đặc." *(vector_store_notes.md)* | "Người mua cần gửi yêu cầu đổi trả trong thời hạn được nêu trên trang sản phẩm hoặc chính sách của sàn." *(k4_ecommerce/returns-policy.md)* | thấp | 0.4136 | ✓ |
| 4 | "Một trợ lý hỗ trợ chất lượng cao cũng cần nhận ra khi nào việc truy xuất là không đủ; hệ thống nên đề xuất chuyển tuyến thay vì tự bịa ra một câu trả lời rủi ro." *(customer_support_playbook.txt)* | "Người bán chịu trách nhiệm cung cấp thông tin sản phẩm chính xác, bao gồm giá, mô tả và tình trạng hàng." *(k4_ecommerce/seller-listing.md)* | thấp | 0.7308 | ✗ |
| 5 | "Python là một ngôn ngữ lập trình bậc cao được sử dụng rộng rãi cho tự động hóa, dịch vụ backend, phân tích dữ liệu..." *(python_intro.txt)* | "Người mua cần gửi yêu cầu đổi trả trong thời hạn được nêu trên trang sản phẩm hoặc chính sách của sàn." *(k4_ecommerce/returns-policy.md)* | thấp | 0.4825 | ✓ |

**Số dự đoán đúng: 3/5**

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> *Viết 2-3 câu:*
> Cặp 4 gây bất ngờ nhất: hai câu thuộc hai domain hoàn toàn khác nhau (độ tin cậy của trợ lý hỗ trợ AI vs. trách nhiệm người bán TMĐT) nhưng lại có điểm cao thứ nhì (0.7308), gần bằng cặp 1 vốn là hai câu diễn giải cùng một ý. Ngược lại cặp 2 — hai câu cùng nói về "tầm quan trọng của metadata" — lại chỉ đạt điểm trung bình-thấp (0.4486), ngang với các cặp khác chủ đề hoàn toàn. Điều này cho thấy cosine similarity trên câu văn không chỉ đo "cùng chủ đề" hay không, mà còn bị ảnh hưởng bởi văn phong/cấu trúc câu (cả cặp 4 đều là câu dài, mang tính quy định/trách nhiệm, dùng nhiều từ trừu tượng như "chịu trách nhiệm", "chính xác", "đáng tin cậy") — nghĩa là điểm số cao không đảm bảo hai đoạn thực sự trả lời cùng một câu hỏi, một rủi ro cần lưu ý khi dùng độ tương tự thuần túy để đánh giá độ liên quan trong RAG.

> ⚠️ *Đây là bộ ví dụ do trợ lý AI chuẩn bị để minh họa quy trình (câu, dự đoán, và tính điểm thật). Nếu bạn muốn điểm số phần này phản ánh đúng trực giác cá nhân, hãy tự thay 5 cặp câu và cột "Dự đoán" bằng suy nghĩ của chính bạn trước khi nộp — cột "Điểm thực tế" vẫn tính đúng bằng code thật nên bạn chỉ cần đổi câu và dự đoán rồi chạy lại.*

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

> Cấu hình: `RecursiveChunker(chunk_size=500)` (chiến lược cá nhân đã chọn, xem Mục 2 `REPORT_NHOM.md`) + `LocalEmbedder`, chạy qua `scripts/run_benchmark.py` trên corpus `data/_test_crawl`.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Thời hạn trả hàng/hoàn tiền | "3.2. Người Mua có thể gửi yêu cầu trả hàng/hoàn tiền trong vòng 15 (mười lăm) ngày kể từ lúc đơn hàng được cập nhật giao hàng thành công" (`k4-returns-policy`) | 0.808 | Có — khớp chính xác câu gold answer | Context trích đúng đoạn 15 ngày; agent demo echo lại đúng nội dung |
| 2 | Yêu cầu hình ảnh khi đăng bán *(lọc `customer_role=seller`)* | "a. Hình ảnh sản phẩm phải là ảnh chụp rõ, chi tiết tình trạng sản phẩm..." (`k4-seller-listing`) | 0.689 | Có — đúng chủ đề, đúng tài liệu | Context về yêu cầu hình ảnh sản phẩm |
| 3 | Vũ khí/vật dụng bị cấm | "e. Cung cấp các dịch vụ như: nạp tiền điện tử, tuyển dụng..." (`k4-operating-regulations`) — câu boilerplate trùng lặp, **lạc chủ đề** | 0.731 | Một phần — top-1/2 lạc sang câu trùng lặp về "dịch vụ bị cấm", top-3 mới đúng (súng hơi nước, kiếm/mác/lê/dao găm) | Context sai chủ đề ở top-1 (xem phân tích lỗi ở `REPORT_NHOM.md`) |
| 4 | Trách nhiệm bảo hành | "Người Bán có trách nhiệm tiếp nhận bảo hành sản phẩm, dịch vụ cho Người Mua như cam kết trong Chính sách bảo hành sản phẩm của Người bán..." (`k4-operating-regulations`) | 0.788 | Có — khớp chính xác câu gold answer (chiến lược **duy nhất** trong 3 chiến lược làm được điều này, xem Mục 3 `REPORT_NHOM.md`) | Context trích đúng câu trả lời về bảo hành |
| 5 | Hoàn phí Dịch Vụ Hiển Thị | "d. Thanh Toán Phí Dịch Vụ Hiển Thị Trang Chủ - Tối Ưu Độ Phủ Thương Hiệu..." (`k4-terms-of-use-for-display-services`) | 0.736 | Có — đúng tài liệu; top-3 có thêm câu "không thể hủy/hoàn tiền" | Context về cách thanh toán phí, đúng chủ đề nhưng chưa trích câu "không hoàn tiền" ở top-1 |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5 (câu 3 chỉ đúng ở top-3, các câu còn lại đúng ngay từ top-1)

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *Viết 2-3 câu:*

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | / 5 |
| Hướng tiếp cận của tôi (My Approach) | / 10 |
| Hoàn thiện code (Core Implementation — tests) | / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | / 5 |
| Kết quả truy xuất của tôi (Competition Results) | / 10 |
| **Tổng phần cá nhân** | **/ 60** |
