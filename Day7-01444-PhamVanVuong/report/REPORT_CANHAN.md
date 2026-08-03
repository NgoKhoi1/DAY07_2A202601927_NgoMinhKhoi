# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Phạm Văn Vượng -01444
**Nhóm: 36899998**
**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**

> Cosine similarity đo góc giữa hai vector embedding thay vì khoảng cách tuyệt đối giữa chúng; giá trị càng gần 1 nghĩa là hai vector "chỉ cùng một hướng" trong không gian embedding, tức hai đoạn văn bản mang ý nghĩa/ngữ cảnh càng gần nhau.

**Ví dụ có độ tương tự CAO:**

- Câu A: "Tôi thích ăn phở."
- Câu B: "Tôi rất thích món phở."
- Tại sao tương đồng: hai câu diễn đạt lại cùng một ý (sở thích ăn phở) bằng từ ngữ gần như đồng nghĩa, chỉ khác cách hành văn.

**Ví dụ có độ tương tự THẤP:**

- Câu A: "Python là ngôn ngữ lập trình."
- Câu B: "Con mèo đang ngủ trên ghế."
- Tại sao khác: hai câu thuộc hai chủ đề hoàn toàn không liên quan (công nghệ vs. đời sống thú cưng), không chia sẻ khái niệm hay ngữ cảnh nào.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**

> Cosine similarity chuẩn hóa theo độ dài vector nên chỉ so sánh *hướng* (ý nghĩa) mà không bị ảnh hưởng bởi *độ lớn* của vector — vốn thường bị lệch do độ dài văn bản hoặc số lần lặp từ. Euclidean distance thì nhạy với magnitude, nên hai câu cùng ý nhưng một câu dài/embedding có norm lớn hơn vẫn có thể bị coi là "xa" nhau dù hướng vector gần như trùng nhau.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**

> *Trình bày phép tính:*
> `step = chunk_size - overlap = 500 - 50 = 450`
> Số chunk ≈ `ceil((10000 - 500) / step) + 1 = ceil(9500 / 450) + 1 = 22 + 1 = 23`
> *Đáp án:* **23 chunks** (đã xác minh lại bằng cách chạy trực tiếp `FixedSizeChunker(chunk_size=500, overlap=50).chunk("a"*10000)` trong `src/chunking.py` → trả về đúng 23 phần tử).

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**

> Khi overlap = 100, `step = 400`, số chunk tăng lên **25** (đã chạy thực tế để kiểm chứng: 23 → 25). Overlap lớn hơn làm bước trượt (step) nhỏ hơn nên cần nhiều chunk hơn để phủ hết văn bản, đổi lại mỗi ranh giới chunk được "đệm" thêm ngữ cảnh từ chunk liền kề — giảm rủi ro một câu/ý quan trọng bị cắt đứt ngay tại điểm chia, giúp truy xuất (retrieval) giữ được ngữ cảnh trọn vẹn hơn, dù phải đánh đổi bằng số lượng embedding/lưu trữ nhiều hơn.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:

> Dùng regex `(?<=[.!?])\s+` (lookbehind) để tách câu ngay sau dấu `.`, `!`, `?` theo sau bởi khoảng trắng bất kỳ — vì `\s` bao gồm cả `\n` nên một biểu thức này phủ được cả 4 dấu hiệu yêu cầu (". ", "! ", "? ", ".\n") mà vẫn giữ nguyên dấu câu ở cuối mỗi câu. Sau khi tách, tôi lọc bỏ các phần tử rỗng/khoảng trắng thừa (`strip()`) để tránh câu rỗng khi văn bản kết thúc bằng dấu câu, rồi nhóm `max_sentences_per_chunk` câu liên tiếp thành một chunk.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:

> Thuật toán duyệt danh sách separator theo thứ tự ưu tiên (`["\n\n", "\n", ". ", " ", ""]`), tách văn bản bằng separator hiện tại rồi gộp tham lam (greedy) các phần liền kề lại với nhau miễn tổng độ dài chưa vượt `chunk_size`. Nếu một phần đơn lẻ đã dài hơn `chunk_size`, hàm gọi đệ quy `_split` trên phần đó với danh sách separator còn lại (bỏ separator vừa dùng). Base case: văn bản hiện tại đã `<= chunk_size` (trả về nguyên văn) hoặc hết separator để thử (cắt cứng theo `chunk_size`).

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:

> Với backend in-memory, mỗi `Document` được chuẩn hóa qua `_make_record` thành một dict `{id, content, embedding, metadata}` (embedding tính ngay bằng `embedding_fn` được inject) rồi append vào `self._store`. Khi `search`, tôi nhúng câu query bằng cùng `embedding_fn`, tính dot product giữa embedding query và embedding từng record đã lưu (các embedding của `MockEmbedder` đã được chuẩn hóa về norm 1 nên dot product tương đương cosine similarity), sắp xếp giảm dần theo score rồi cắt lấy `top_k` kết quả.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:

> `search_with_filter` lọc **trước**: chỉ giữ lại các record mà mọi cặp key/value trong `metadata_filter` khớp với `record["metadata"]`, sau đó chạy chung hàm `_search_records` trên tập con đã lọc — nhờ vậy tránh trùng lặp logic tính similarity. `delete_document` xóa bằng cách so khớp `record["metadata"]["doc_id"]` (mặc định gán bằng `doc.id` nếu tài liệu không tự khai báo `doc_id`) với `doc_id` truyền vào, giữ lại các record không khớp, và trả `True` chỉ khi kích thước store thực sự giảm.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:

> `answer` gọi `store.search(question, top_k=top_k)` để lấy các chunk liên quan nhất, nối nội dung (`content`) của chúng bằng `"\n\n"` thành một khối `Context:`, rồi ghép thêm câu hỏi và một dòng chỉ dẫn ("Answer the question using only the context above.") thành prompt cuối cùng. Prompt này được truyền cho `llm_fn` (có thể là LLM thật hoặc hàm demo) — cách làm này buộc câu trả lời phải bám vào ngữ cảnh truy xuất được thay vì để mô hình tự bịa.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
platform win32 -- Python 3.10.11, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\lab-day7\K4-Day07-01444-PhamVanVuong
collecting ... collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED         [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED  [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED   [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED        [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED               [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED          [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED      [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED                [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED               [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED   [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED         [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED          [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED         [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED    [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED     [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================= 42 passed in 0.10s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

> Thực hiện với `MockEmbedder` + `compute_similarity` hiện có trong `src` (chưa cấu hình `EMBEDDING_PROVIDER=local/openai`), nên các con số dưới đây phản ánh đúng backend mặc định của lớp học.

| Cặp | Câu A                                                            | Câu B                                               | Dự đoán | Điểm thực tế | Đúng? |
| ---- | ----------------------------------------------------------------- | ---------------------------------------------------- | ---------- | ---------------- | ------- |
| 1    | "Tôi thích ăn phở."                                           | "Tôi rất thích món phở."                        | cao        | -0.0040          | Sai     |
| 2    | "Đổi trả hàng lỗi trong 7 ngày."                            | "Chính sách hoàn tiền khi sản phẩm bị lỗi."  | cao        | -0.0321          | Sai     |
| 3    | "Python là ngôn ngữ lập trình."                              | "Con mèo đang ngủ trên ghế."                    | thấp      | 0.0918           | Đúng  |
| 4    | "Người bán phải cung cấp thông tin sản phẩm chính xác." | "Người mua cần giữ bằng chứng khi đổi trả." | thấp      | -0.1657          | Đúng  |
| 5    | "Hôm nay trời mưa rất to."                                    | "Tôi vừa mua một chiếc áo mới."                | thấp      | -0.1903          | Đúng  |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**

> Bất ngờ nhất là cặp 3 (hai câu hoàn toàn không liên quan chủ đề) lại có điểm cao nhất trong 5 cặp (0.0918), trong khi cặp 1 (hai câu paraphrase gần như đồng nghĩa) lại có điểm gần 0. Điều này cho thấy `MockEmbedder` chỉ sinh vector giả deterministic từ hash MD5 của chuỗi ký tự — nó **không** mã hoá ngữ nghĩa thật, nên cosine similarity giữa các câu gần như ngẫu nhiên quanh 0 bất kể nội dung có liên quan hay không. Bài học rút ra: muốn dự đoán "cao/thấp" có ý nghĩa và khớp với trực giác con người, bắt buộc phải chuyển sang embedding thật (`LocalEmbedder`/`OpenAIEmbedder` ở Giai đoạn 2) — mock chỉ nên dùng để kiểm thử logic pipeline, không dùng để đánh giá chất lượng truy xuất ngữ nghĩa.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

> **Cập nhật:** nhóm đã chốt corpus thật (`data/_test_crawl/` — 6 tài liệu chính sách Shopee công khai) và 5 câu hỏi đánh giá chính thức trong `REPORT_NHOM.md` — Mục 3. Bảng dưới đây chạy lại bằng **chính implementation `src/` của tôi** (không dùng code của thành viên khác), cấu hình: `RecursiveChunker(chunk_size=300)` + `LocalEmbedder` (`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`) qua `ingest.build_knowledge_base()`, thay cho bộ câu hỏi nháp + MockEmbedder trước đây.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Thời hạn trả hàng/hoàn tiền, và trường hợp thực phẩm tươi sống | "Riêng đối với các Sản Phẩm là thực phẩm tươi sống và đông lạnh, Người Mua cần gửi yêu cầu trả hàng/hoàn tiền trong vòng 24 giờ..." (`k4-returns-policy`) | 0.7979 | Có — đúng vế "thực phẩm tươi sống"; top-3 có thêm câu "15 ngày" (vế còn lại của gold answer) | Context trích đúng đoạn 24 giờ cho thực phẩm tươi sống |
| 2 | Yêu cầu hình ảnh khi đăng bán *(lọc `customer_role=seller`)* | "a. Hình ảnh sản phẩm phải là ảnh chụp rõ, chi tiết tình trạng sản phẩm..." (`k4-seller-listing`) | 0.7513 | Có — khớp đúng chủ đề | Context về yêu cầu hình ảnh sản phẩm |
| 3 | Vũ khí/vật dụng bị cấm | "Các phụ kiện súng bên ngoài như: bộ giảm thanh, báng súng, khóa nòng..." (`k4-operating-regulations`) | 0.7135 | Có — đúng chủ đề; top-2 có thêm "súng hơi nước... kiếm, mác, lê, dao găm, cung nỏ" | Context đúng về phụ kiện vũ khí bị cấm |
| 4 | Trách nhiệm bảo hành | Top-1 là 1 đoạn ngắn ít thông tin ("...pháp luật của Người Bán hoặc Người Mua như vừa đề cập", `k4-info-library`); **top-2** mới là gold chunk: "Người Bán có trách nhiệm tiếp nhận bảo hành sản phẩm..." (`k4-operating-regulations`, score 0.7943) | 0.8010 (top-1) / 0.7943 (top-2) | Có — gold chunk có mặt ở top-2, rất sát top-1 | Context ghép cả 2 đoạn nên câu trả lời agent vẫn chứa đúng thông tin bảo hành |
| 5 | Hoàn phí Dịch Vụ Hiển Thị | "d. Thanh Toán Phí Dịch Vụ Hiển Thị Trang Chủ - Tối Ưu Độ Phủ Thương Hiệu..." (`k4-terms-of-use-for-display-services`) | 0.7400 | Có — top-2 có thêm câu "không thể hủy/hoàn tiền" đúng gold answer | Context đúng chủ đề dịch vụ hiển thị |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**

> Chưa có dữ liệu — buổi demo/so sánh chiến lược giữa các thành viên trong nhóm chưa diễn ra tại thời điểm nộp bản nháp này. Mục này sẽ được cập nhật ngay sau buổi thuyết trình nhóm.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí                                           | Điểm tự đánh giá |
| ---------------------------------------------------- | ---------------------- |
| Khởi động (Warm-up)                               | 5 / 5                  |
| Hướng tiếp cận của tôi (My Approach)           | 9 / 10                 |
| Hoàn thiện code (Core Implementation — tests)     | 30 / 30                |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5                  |
| Kết quả truy xuất của tôi (Competition Results) | ⚠️ cần tự chấm lại — xem ghi chú | 
| **Tổng phần cá nhân**                      | ⚠️ cần cập nhật      |

> ⚠️ **Cần Vượng tự xem lại điểm mục 5**: bảng ở Mục 5 đã được chạy lại bằng dữ liệu thật (`data/_test_crawl`) + 5 câu hỏi chính thức của nhóm (`REPORT_NHOM.md`), kết quả 5/5 câu có chunk liên quan trong top-3 — không còn đúng với lý do trừ điểm cũ ("dữ liệu khởi động + MockEmbedder"). Điểm tự đánh giá `5/10` ở trên đang dựa trên tình trạng cũ, cần tự chấm lại theo kết quả mới.
