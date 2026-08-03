# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** 
**Thành viên:**
 - Ngô Minh Khôi - 01927
 - Phạm Văn Vượng - 01444
 - Phạm Quý Đô - 01564
**Ngày:** 03/08/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K4):** Chính sách thương mại điện tử / hỗ trợ khách hàng (thanh toán, đổi trả, giao hàng, quyền riêng tư, điều kiện người bán…).

**Phạm vi cụ thể nhóm tập trung:** Chính sách của sàn Shopee bao trùm cả vòng đời giao dịch — điều khoản dịch vụ chung, quy chế hoạt động, đăng bán sản phẩm, sản phẩm cấm/hạn chế, trả hàng/hoàn tiền, và dịch vụ hiển thị trả phí cho người bán.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Điều khoản dịch vụ | [help.shopee.vn/.../77243](https://help.shopee.vn/portal/4/article/77243) | 2026-08-03 / not-stated | ~30.000 | `doc_id`, `customer_role: both`, `category: info-library`, `language: vi` |
| 2 | Quy chế hoạt động | [help.shopee.vn/.../77245](https://help.shopee.vn/portal/4/article/77245) | 2026-08-03 / not-stated | ~43.000 | `doc_id`, `customer_role: both`, `category: promotions`, `language: vi` |
| 3 | Chính sách cấm/hạn chế sản phẩm | [help.shopee.vn/.../77247](https://help.shopee.vn/portal/4/article/77247) | 2026-08-03 / not-stated (hiệu lực 28/4/2025 trong nội dung) | 12.850 | `doc_id`, `customer_role: both`, `category: reviews`, `language: vi` |
| 4 | Chính sách trả hàng và hoàn tiền | [help.shopee.vn/.../77251](https://help.shopee.vn/portal/4/article/77251) | 2026-08-03 / not-stated (hiệu lực 11/3/2026 trong nội dung) | 19.609 | `doc_id`, `customer_role: buyer`, `category: returns`, `language: vi` |
| 5 | Quy định về đăng bán sản phẩm | [help.shopee.vn/.../77246](https://help.shopee.vn/portal/4/article/77246) | 2026-08-03 / not-stated (cập nhật 14/8/2024 trong nội dung) | 21.532 | `doc_id`, `customer_role: seller`, `category: listing`, `language: vi` |
| 6 | Điều khoản sử dụng Dịch vụ Hiển thị | [help.shopee.vn/.../77252](https://help.shopee.vn/portal/4/article/77252) | 2026-08-03 / not-stated (hiệu lực 23/5/2026 trong nội dung) | ~7.000 | `doc_id` — ⚠️ **thiếu `customer_role`**, `language` |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai (Shopee Trung tâm trợ giúp, `license_or_permission: public-page`/`public-source` trong `sources.csv`), không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [ ] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata. — **Chưa đạt đầy đủ**: `document_version` đang để `"not-stated"` ở cả 6 tài liệu dù 4/6 tài liệu có ngày hiệu lực/cập nhật rõ ràng trong nội dung (xem cột trên); nên cập nhật lại giá trị này. Tài liệu #6 còn thiếu hẳn `customer_role` — cần bổ sung (`"seller"`, vì Dịch Vụ Hiển Thị chỉ dành cho Người Bán).

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `customer_role` | string enum | `buyer` / `seller` / `both` | Lọc đúng đối tượng áp dụng — tránh trả lời câu hỏi của người mua bằng chính sách dành cho người bán (và ngược lại), bắt buộc theo K4_VARIANT.md. |
| `category` | string | `returns`, `listing`, `promotions`, `reviews`, `info-library` | Thu hẹp phạm vi tìm kiếm theo chủ đề chính sách khi câu hỏi đã xác định rõ nhóm nội dung. |
| `language` | string | `vi` | Dự phòng cho corpus đa ngôn ngữ trong tương lai (hiện tất cả đều `vi`). |
| `document_version` / `retrieved_at` | string / date | ngày hiệu lực chính sách, ngày crawl | Truy vết độ mới của câu trả lời — chính sách Shopee thay đổi theo thời gian nên cần biết đang trả lời theo phiên bản nào. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare(chunk_size=500)` trên 3 tài liệu (nội dung sau khi bỏ front matter):

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| Chính sách trả hàng và hoàn tiền (19.609 ký tự) | FixedSizeChunker (`fixed_size`) | 44 | 494.5 | Không đảm bảo — cắt cứng theo ký tự nên có thể chia giữa câu/giữa điều khoản. |
| | SentenceChunker (`by_sentences`) | 48 | 405.6 | Giữ trọn câu, nhưng các câu trong văn bản pháp lý rất dài (nhiều mệnh đề) nên chunk vẫn lớn/không đều. |
| | RecursiveChunker (`recursive`) | 62 | 314.3 | Tốt nhất trong 3 — ưu tiên cắt theo đoạn/câu trước khi cắt cứng, chunk nhỏ và đều hơn. |
| Quy định về đăng bán sản phẩm (21.532 ký tự) | FixedSizeChunker (`fixed_size`) | 48 | 497.5 | Không đảm bảo — dễ cắt giữa các mục liệt kê (a, b, c...). |
| | SentenceChunker (`by_sentences`) | 79 | 269.7 | Nhiều câu ngắn dạng liệt kê nên tạo ra rất nhiều chunk nhỏ, có thể mất ngữ cảnh giữa các mục liên quan. |
| | RecursiveChunker (`recursive`) | 53 | 404.3 | Cân bằng — gộp được các mục liệt kê liền kề trong cùng đoạn. |
| Chính sách cấm/hạn chế sản phẩm (12.850 ký tự) | FixedSizeChunker (`fixed_size`) | 29 | 491.4 | Không đảm bảo — văn bản có cấu trúc liệt kê dày đặc (4.1–4.28), dễ cắt giữa danh mục. |
| | SentenceChunker (`by_sentences`) | 56 | 227.1 | Rất mảnh do các mục liệt kê ngắn được tách thành câu riêng — mất liên kết với tiêu đề mục cha. |
| | RecursiveChunker (`recursive`) | 30 | 426.4 | Tốt nhất — giữ được các mục liệt kê trong cùng ngữ cảnh đoạn văn. |

**Quan sát chung**: với văn bản pháp lý/chính sách nhiều mục liệt kê như corpus này, `RecursiveChunker` cho kết quả cân bằng nhất (chunk vừa phải, ưu tiên ranh giới đoạn/câu tự nhiên); `SentenceChunker` tạo quá nhiều chunk nhỏ vì các mục liệt kê thường là câu ngắn đứng độc lập, dễ mất ngữ cảnh của mục cha khi tách riêng.

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người). ⚠️ Chỉ Thành viên 1 (Ngô Minh Khôi) đã có kết quả chạy thật — đây là người đã build baseline và chạy `scripts/run_benchmark.py` so sánh cả 3 chiến lược có sẵn. **Các thành viên còn lại cần tự chạy chiến lược riêng (khuyến nghị: ít nhất 1 người thử `CustomChunker` chia theo điều/khoản, theo yêu cầu riêng của K4) và điền vào đây.**

**Thành viên 1 — Ngô Minh Khôi - 01927**
- **Loại chiến lược:** Recursive (`RecursiveChunker(chunk_size=500)`)
- **Mô tả & lý do chọn cho chủ đề này:** Corpus là văn bản pháp lý/chính sách với cấu trúc phân đoạn rõ (điều/khoản, mục liệt kê a/b/c) — `RecursiveChunker` ưu tiên cắt theo ranh giới đoạn văn (`\n\n`) trước khi lùi xuống câu/từ, nên giữ nguyên vẹn từng điều khoản thay vì cắt cứng giữa chừng như `FixedSizeChunker`. Chạy `scripts/run_benchmark.py` trên 5 câu hỏi benchmark cho điểm tổng **9/10** (theo rubric `docs/SCORING.md`), cao nhất trong 3 chiến lược — đặc biệt là chiến lược **duy nhất** trả lời đúng câu 4 (bảo hành sản phẩm), nơi cả `fixed_size` và `by_sentences` đều thất bại hoàn toàn.
- **Code snippet (nếu custom):** *(không dùng custom, dùng chiến lược có sẵn)*

***Thành viên 2 — Phạm Văn Vượng - 01444**
- **Loại chiến lược:** Fixed Size (`FixedSizeChunker`)
- **Mô tả & lý do chọn:** Dùng chiến lược có sẵn `FixedSizeChunker(chunk_size=500, overlap=50)` làm đường cơ sở (baseline) để đối chiếu với các chiến lược khác trong nhóm. Ưu điểm là đơn giản, chunk có độ dài đồng đều, không phụ thuộc cấu trúc câu/đoạn của văn bản — phù hợp để so sánh "chi phí" (số lượng chunk, thời gian embed) so với các chiến lược phức tạp hơn. Nhược điểm với văn bản chính sách TMĐT nhiều điều/khoản: dễ cắt cứng giữa chừng một quy định, làm loãng ngữ nghĩa của chunk khi câu trả lời nằm gần ranh giới 500 ký tự.
- **Code snippet (nếu custom):** *(không dùng custom — dùng `FixedSizeChunker` có sẵn trong `src/chunking.py`)*

**Thành viên 3 — Phạm Quý Đô - 01564**
- **Loại chiến lược:** By Sentences (`SentenceChunker`)
- **Mô tả & lý do chọn:** Dùng `SentenceChunker(max_sentences_per_chunk=3)` — chia theo ranh giới câu thay vì ký tự, phù hợp với văn bản chính sách vì mỗi câu thường diễn đạt trọn một quy định/điều kiện. Ưu điểm: chunk luôn kết thúc trọn câu, không bao giờ cắt giữa chừng một câu như Fixed Size; đặc biệt chính xác khi gold answer nằm gọn trong 1 câu. Nhược điểm: các mục liệt kê (a, b, c...) trong văn bản pháp lý thường là câu ngắn đứng độc lập — nhóm 3 câu liên tiếp có thể ghép các mục liệt kê không liên quan với nhau, hoặc tách một câu quan trọng khỏi ngữ cảnh của cả đoạn/mục cha.
- **Code snippet (nếu custom):** *(không dùng custom — dùng `SentenceChunker` có sẵn trong `src/chunking.py`)*

### So Sánh Giữa Các Thành Viên

> Điểm truy xuất tính theo rubric `docs/SCORING.md` (2đ/câu × 5 câu = 10đ), chạy bằng `scripts/run_benchmark.py` trên cùng bộ 5 câu hỏi ở Mục 3.

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Ngô Minh Khôi | Recursive | 9 | Duy nhất thành công ở câu 4 (bảo hành) nhờ giữ trọn đoạn văn chứa câu trả lời; ổn định nhất trên cả 5 câu (không có câu nào điểm 0). | Ở câu 3 (vũ khí bị cấm), top-1/2 bị lạc sang một câu trùng lặp về "dịch vụ bị cấm" xuất hiện ở 2 tài liệu khác nhau — chỉ top-3 mới đúng. |
| *(baseline tham khảo)* | Fixed Size | 7 | Chunk lớn đồng đều nên câu 3 (vũ khí) lại là chiến lược **duy nhất** không bị lạc — ngữ cảnh xung quanh giúp giữ tín hiệu đúng. | Thất bại hoàn toàn ở câu 4 (bảo hành) — cắt cứng 500 ký tự làm loãng đoạn văn cần tìm. |
| *(baseline tham khảo)* | By Sentences | 6 | Chính xác nhất ở câu 1, 2, 5 — chunk ngắn, tập trung đúng 1 ý nên khớp rất sát câu hỏi khi câu hỏi trùng với đúng 1 câu trong tài liệu. | Thất bại ở cả câu 3 và câu 4 — chunk quá ngắn (3 câu) dễ bị "nuốt" bởi 1 câu boilerplate lạc chủ đề đứng gần đó. |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> *Bản nháp dựa trên dữ liệu thật — nhóm review/bổ sung sau khi có thêm chiến lược của thành viên 2, 3:* `RecursiveChunker` cho kết quả tổng thể tốt nhất (9/10) vì corpus là văn bản pháp lý có cấu trúc đoạn/điều khoản rõ ràng — việc ưu tiên cắt theo ranh giới đoạn văn giúp mỗi chunk giữ trọn một ý pháp lý hoàn chỉnh thay vì bị cắt cứng (`fixed_size`) hoặc bị vỡ vụn thành từng câu rời rạc (`by_sentences`). Ví dụ rõ nhất là câu 4: chỉ `RecursiveChunker` tách được đúng đoạn "Người Bán có trách nhiệm tiếp nhận bảo hành..." thành 1 chunk độc lập, trong khi 2 chiến lược kia làm loãng hoặc vỡ vụn tín hiệu ngữ nghĩa của đoạn này. Tuy nhiên `by_sentences` lại chính xác hơn ở các câu có gold answer nằm trọn trong 1 câu duy nhất (câu 1, 2, 5) — gợi ý rằng lựa chọn tối ưu có thể phụ thuộc vào việc câu trả lời trong tài liệu là 1 câu đơn hay cả 1 đoạn nhiều câu.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Người mua có bao nhiêu ngày để gửi yêu cầu trả hàng/hoàn tiền, và trường hợp thực phẩm tươi sống thì sao? | 15 ngày kể từ khi đơn hàng cập nhật giao hàng thành công; riêng thực phẩm tươi sống/đông lạnh chỉ có 24 giờ. | `k4-returns-policy` (Điều 3.2) |
| 2 | Người bán cần đáp ứng những yêu cầu gì về hình ảnh khi đăng bán sản phẩm? *(cần `metadata_filter={"customer_role": "seller"}`)* | Ít nhất 1 ảnh thật do chính người bán chụp, sản phẩm chiếm tối thiểu 40% diện tích ảnh; ngôn ngữ trên phông nền là tiếng Việt; tuyệt đối không ảnh khỏa thân/khiêu gợi/phản cảm. | `k4-seller-listing` (Mục C.1) |
| 3 | Những loại vũ khí hoặc vật dụng có hình dạng giống vũ khí nào bị cấm bán trên Shopee? | Súng đồ chơi giống thật (trừ đồ chơi phun nước/bong bóng), kiếm/mác/lê/dao găm/cung nỏ, hơi cay, dùi cui, dao bấm/dao bướm, và các bộ phận/đạn dược cho súng. | `k4-prohibited-restricted-products-policy` (Mục 4.5) |
| 4 | Ai chịu trách nhiệm bảo hành sản phẩm cho người mua — Shopee hay người bán? | Người Bán chịu trách nhiệm bảo hành theo chính sách đã công bố của mình/nhà sản xuất; Shopee không phải bên thực hiện nghĩa vụ bảo hành, trừ sản phẩm do chính Shopee đăng bán. | `k4-operating-regulations` (Mục 4 — Chính sách bảo hành) |
| 5 | Người bán có được hoàn Phí Dịch Vụ Hiển Thị đã thanh toán nếu muốn hủy không? | Không — trừ khi có quy định khác trong Điều Khoản Sử Dụng Dịch Vụ Hiển Thị, người bán không được hủy/hoàn tiền sau khi đã thanh toán. | `k4-terms-of-use-for-display-services` (Mục 4) |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).
>
> Chạy `scripts/run_benchmark.py` với cả 3 chiến lược (`fixed_size`, `by_sentences`, `recursive`, tất cả `chunk_size=500`) + `LocalEmbedder` trên cùng corpus `data/_test_crawl`.

| # | Câu hỏi | fixed_size | by_sentences | recursive | Chiến lược tốt nhất cho câu này |
|---|---------|:---:|:---:|:---:|---------|
| 1 | Thời hạn trả hàng/hoàn tiền | 2 | 2 | 2 | Ngang nhau — cả `by_sentences` và `recursive` khớp chính xác tuyệt đối câu "3.2. Người Mua có thể gửi yêu cầu trả hàng/hoàn tiền trong vòng 15 ngày..." ở top-1. |
| 2 | Yêu cầu hình ảnh khi đăng bán (có filter) | 1 | 2 | 2 | `by_sentences` — top-1/2 khớp chính xác từng câu yêu cầu về ảnh; `fixed_size` đúng tài liệu nhưng top-1 lệch sang đoạn giá cả. |
| 3 | Sản phẩm/vũ khí bị cấm | 2 | 0 | 1 | `fixed_size` — chunk lớn giữ được ngữ cảnh nên không bị lạc; `by_sentences` thất bại hoàn toàn (xem phân tích lỗi). |
| 4 | Trách nhiệm bảo hành | 0 | 0 | 2 | `recursive` — **chiến lược duy nhất** trả lời đúng (xem phân tích lỗi). |
| 5 | Hoàn phí Dịch Vụ Hiển Thị | 2 | 2 | 2 | `by_sentences` — top-1/2/3 đều khớp rất sát nội dung không hoàn phí. |
| **Tổng /10** | **7** | **6** | **9** | |

**Phân tích lỗi (chuẩn bị cho Bài tập 3.5):**
- **Câu 4 (bảo hành) — `fixed_size` và `by_sentences` cùng thất bại (0 điểm), chỉ `recursive` thành công.** Đoạn gold answer ("Người Bán có trách nhiệm tiếp nhận bảo hành sản phẩm...") nằm gọn trong 1 đoạn văn riêng ở Mục 4 của `k4-operating-regulations`, kẹp giữa Mục 3 ("Thời gian giao hàng", rất dài) và Mục 5 ("Chính sách Trả hàng/Hoàn tiền"). `FixedSizeChunker` cắt cứng 500 ký tự nên nhiều khả năng trộn lẫn đoạn này với nội dung mục lân cận, làm loãng tín hiệu ngữ nghĩa; `SentenceChunker` gộp tối đa 3 câu/chunk nên có thể ghép câu bảo hành với câu mở đầu/kết thúc của mục khác, cũng làm loãng embedding. Chỉ `RecursiveChunker` — ưu tiên cắt theo ranh giới đoạn văn (`\n\n`) — mới tách được đúng đoạn này thành 1 chunk độc lập, giữ nguyên tín hiệu ngữ nghĩa "trách nhiệm bảo hành".
- **Câu 3 (vũ khí bị cấm) — `by_sentences` thất bại hoàn toàn (0 điểm), `recursive` chỉ đạt 1 điểm.** Nguyên nhân: `k4-operating-regulations` và `k4-prohibited-restricted-products-policy` chứa một câu gần như trùng lặp ("Cung cấp các dịch vụ như: nạp tiền điện tử, tuyển dụng, môi giới bất động sản, bảo hiểm... đặc biệt là các dịch vụ bất hợp pháp... bị cấm trên nền tảng của Shopee") xuất hiện ở cả 2 tài liệu, ngay trước đoạn về vũ khí. Khi tách thành chunk riêng (theo câu hoặc theo đoạn ngắn), câu boilerplate này có cụm từ "bị cấm" trùng với câu hỏi nên vô tình được xếp hạng cao hơn nội dung thực sự về vũ khí. `FixedSizeChunker` gộp chung câu này với đoạn liệt kê vũ khí thành 1 chunk lớn hơn nên giữ được tín hiệu đúng — đây là ví dụ cho thấy **chunk quá nhỏ có thể phản tác dụng** khi 2 tài liệu có nội dung trùng lặp cục bộ.

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Có, rõ rệt ở câu 2 — kiểm chứng trên cả 3 chiến lược: `k4-operating-regulations` (customer_role `both`) cũng có đoạn mô tả quy trình đăng bán (giới hạn 3.000 ký tự, tối đa 9 ảnh...) khá giống chủ đề câu hỏi. Với `metadata_filter={"customer_role": "seller"}`, top-3 của cả 3 chiến lược đều sạch hoàn toàn, chỉ còn `k4-seller-listing` — nếu không lọc, nhiều khả năng `k4-operating-regulations` sẽ chen vào top-3 do nội dung tương tự.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> *Liệt kê 2-3 ý:*

**Bài học rút ra khi so sánh trong nhóm:**
> *Viết 2-3 câu — cùng tài liệu nhưng chiến lược khác nhau dẫn tới khác biệt gì?*

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> *Viết 2-3 câu:*

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | / 10 |
| Thiết kế chiến lược (Strategy Design) | / 15 |
| Chất lượng truy xuất (Retrieval Quality) | / 10 |
| Thuyết trình (Demo) | / 5 |
| **Tổng phần nhóm** | **/ 40** |
