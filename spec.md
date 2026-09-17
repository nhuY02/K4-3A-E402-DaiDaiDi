# Template AI Spec *(spec.md — commit trước hạn chốt spec: 21:00 17/9, tại CP4 · quality bar chốt từ thời điểm nộp)*

> Cấu trúc phủ đúng "SPEC 8 phần" của chương trình: Bằng chứng (§1-§2) · Lát cắt (§4) · Canvas (đính kèm CP1) · Augment/Automate (§4) · 4 đường đi của trải nghiệm (§6) · Kiểu lỗi (§5) · Kiểm thử (§7) · Phân công (§8). Hướng dẫn viết từng mục: `02-guide.md`.


# AI SPEC — [Tên lát cắt] · Nhóm [DaiDaiDi] · Zone [C]
Hướng: [ x ] A — VLearn  [ ] B — Trợ lý Học viên  [ ] C — Làn mở
Loại: [ x ] Tối ưu tính năng có sẵn  [ x ] Tính năng mới

## §1. User & Job
- Job executor + workflow (đính kèm worksheet JTBD / ảnh sơ đồ):

| STT | Tên Willing User | Role |
|---|---|---|
| 1 | Trần Anh Vũ | Học viên chương trình Nhân tài AI Thực Chiến |
| 2 | Nguyễn Trung Kiên | Học viên chương trình Nhân tài AI Thực Chiến | 

Link Workflow: https://drive.google.com/drive/folders/1a0eAMSBz2b1AnQAbqDl7oiawETLfFttW?usp=sharing

- Core JTBD (không tên sản phẩm/AI trong câu): Tìm kiếm tài liệu; hỏi lại ý/mục chưa hiểu trong phần trả lời của Tutor Chat
- Problem statement (KHÔNG chữ AI): Học viên gặp khó khăn trong việc tìm kiếm, hiểu và tổng hợp thông tin từ lesson/course materials; Tutor AI hiện tại chưa phải lúc nào cũng cung cấp câu trả lời đủ sát với context và nhu cầu của từng học viên.
- Evidence (chuẩn A và/hoặc B — log đầy đủ trong repo):
  - **Chuẩn B — quan sát trực tiếp (2 phiên, có ghi màn hình):** cho willing user làm đúng 1 task *"đang học Day 03 · Embedding & Vector Search, tìm lại chỗ đã giải thích khái niệm này ở bài trước và đọc đúng trang đó"*. Cả 2 user đều phải thoát bài đang học → mở lại danh sách bài → đoán tên file slide → cuộn PDF thủ công. Log: `evidence/observe-01.md`, `evidence/observe-02.md` + record màn hình (`CP3.mp4` là bản demo lát cắt dựng lại từ đúng task này).
  - **Chuẩn A — khảo sát học viên cùng chương trình:** form 8 câu, gửi trong Zone C, thu về **n = 32 / 45** (71 %). Raw response: `evidence/survey-raw.csv`.
- Số liệu mining / kết quả khảo sát (n = ?, % xác nhận):
  - **n = 32** (trên 45 học viên trong phạm vi).
  - **28/32 (87,5 %)** xác nhận đã từng phải quay lại bài cũ để tìm lại một khái niệm trong lúc học bài mới.
  - **24/32 (75 %)** cho biết mất **> 3 phút** cho một lần tìm như vậy; trung vị tự ước lượng ≈ **3 phút**.
  - **21/32 (65,6 %)** nói câu trả lời của Tutor AI **không bám đúng slide/trang đang mở**, phải hỏi lại ≥ 2 lượt mới dùng được.
  - **19/32 (59,4 %)** nói lý do bỏ cuộc giữa chừng là "không nhớ nội dung đó nằm ở file nào / trang nào".
  - **0/32** biết cách tìm theo từ khoá trong toàn bộ bài giảng đã học — **vì VLearn hiện không có ô tìm kiếm nào cho phần nội dung bài học**.
- ≥5 quote/ví dụ nguyên văn + nguồn:
  1. *"Em nhớ là thầy có nói vector với embedding ở Day 01 rồi, mà không nhớ slide nào, phải mở từng file ra dò."* — Trần Anh Vũ, phiên quan sát 1 (phút 02:10).
  2. *"Cái khó không phải là hiểu, là tìm lại. Tìm được rồi thì đọc 30 giây là xong."* — Nguyễn Trung Kiên, phiên quan sát 2 (phút 04:35).
  3. *"Hỏi Tutor thì nó trả lời chung chung, kiểu định nghĩa trên mạng, không phải cái trong slide của khoá mình."* — khảo sát, response #07.
  4. *"Nhiều lúc nó trả lời xong em cũng không biết nó lấy từ đâu ra nên không dám tin, lại đi mở slide kiểm tra."* — khảo sát, response #14.
  5. *"Em toàn Ctrl+F trong file PDF tải về, chứ trên web thì chịu, không có chỗ nào để search."* — khảo sát, response #21.
  6. *"Đang học dở bài 3 mà phải thoát ra tìm bài 1, quay lại là mất mạch, đọc lại từ đầu."* — khảo sát, response #29.

## §2. Impact & quyết định chọn

**Pain point chốt từ §1: *tìm kiếm — và hiểu — tài liệu trong lesson/course materials*.**

Hiện trạng ghi nhận trên VLearn:
- (a) Khu vực Vlearn **không có thanh tìm kiếm** → học viên phải cuộn thủ công / mở lại từng lesson để tìm lại một ý đã học.
- (b) Khi hỏi Tutor AI, câu trả lời **không luôn bám đúng lesson/module** học viên đang mở → phải hỏi lại nhiều lượt, hoặc bỏ cuộc và tự đọc lại tài liệu.

Hai vấn đề này là hai bước liền nhau của cùng một job: **tìm đúng chỗ** → **hiểu đúng ý**. Vì vậy nhóm build **AI learning assistant** gồm đúng 2 giải pháp:

1. **Context-aware Search (CES)** — thêm ô tìm kiếm vào panel *Nội dung bài học* (placeholder: *"Tìm trong các bài giảng đã học…"*). Học viên **gõ từ khoá**, hệ thống tìm trên **toàn bộ tài liệu của các bài đã học** (không giới hạn trong bài đang mở) và trả về danh sách kết quả, mỗi kết quả gồm: **tên bài · tên file nguồn · số trang · đoạn trích** và nút **"Mở trang"** để nhảy thẳng tới đúng trang đó. *(Tính năng mới)*
2. **Context-aware Q&A (CQ)** — Trợ giảng AI **bám theo thứ đang mở**: header panel luôn hiển thị `Đang mở: <file/slide> · trang N`, và khi học viên **bôi đen một đoạn** hoặc nhấn vào cụm từ được gạch chân thì AI giải thích **đúng đoạn đó** trong ngữ cảnh trang hiện tại, kèm cảnh báo *"Trợ giảng AI có thể sai — hãy đối chiếu với bài giảng"*. *(Tối ưu Tutor AI có sẵn)*

**Luồng đã dựng ở CP3 (xem `CP3.mp4`) — hai giải pháp nối thành một mạch:**
gõ từ khoá `embedding vector` → **6 kết quả** (semantic search trên các bài đã học) → chọn kết quả *Day 01 · AI & LLM Foundation — d1-slide-hackathon.pdf · trang 12* → bấm **Mở trang** → mở đúng trang 12 của file đó → ngữ cảnh Trợ giảng AI **tự đổi theo** sang `d1-slide-hackathon.pdf · trang 12` → bôi đen đoạn chưa hiểu → AI giải thích ngay đoạn đang đọc.

> Đây chính là lý do kỹ thuật để giữ **cả hai**: CES đưa học viên tới **đúng trang**, và **trang đó trở thành context của CQ** — không có CES thì CQ phải đoán học viên đang nói về cái gì (đúng pain point (b) ở trên).

### Bảng Impact — các ứng viên đã cân nhắc

> Công thức: `Score = (Người dùng × Tần suất/ngày × Khả thi) ÷ Chi phí/lần`

| # | Giải pháp | Người dùng | Tần suất | Chi phí/lần ($) | Khả thi (1–10) | Score | Kết luận |
|---|-----------|------------|----------|-----------------|----------------|-------|----------|
| 1 | **Context-aware Search (CES)** | 45 | 6 / ngày | 0.01 | 9 | **243.000** | ✅ CHỌN |
| 2 | **Context-aware Q&A (CQ)** | 45 | 4 / ngày | 0.02 | 8 | **72.000** | ✅ CHỌN |
| 3 | Auto-completion trong chat | 45 | 3 / ngày | 0.03 | 5 | 22.500 | ❌ Loại |
| 4 | Auto-summary cuối mỗi lesson | 45 | 1 / ngày | 0.02 | 7 | 15.750 | ❌ Loại |
| 5 | Sinh flashcard / quiz từ lesson | 45 | 1 / ngày | 0.02 | 6 | 13.500 | ❌ Loại |
| 6 | Knowledge-graph navigation | 45 | 2 / ngày | 0.05 | 3 | 5.400 | ❌ Loại |

*Nguồn số:* 45 = số học viên trong phạm vi triển khai (Zone C). Tần suất lấy từ khảo sát ở §1 (**n = 32**); chi phí/lần là ước tính token của model dùng trong prototype (embedding + rerank cho CES; embedding + sinh câu trả lời cho CQ).

### Ứng viên ĐÃ LOẠI + vì sao

| Giải pháp | Lý do loại |
|-----------|------------|
| Auto-completion trong chat | Học liệu đa dạng, gợi ý thiếu ngữ cảnh nên dễ sai hướng; chi phí API cho mỗi lượt gõ cao mà không giải quyết trực tiếp việc "tìm đúng chỗ". |
| Auto-summary cuối mỗi lesson | Tần suất dùng thấp (1 lần/lesson), không rút ngắn thời gian *tìm lại* nội dung — đúng pain point đang chọn. Có thể làm sau, tái dùng pipeline của CQ. |
| Sinh flashcard / quiz từ lesson | Phục vụ job "ôn tập", không phải job "tìm & hiểu" ở §1. Score thấp; để ngoài scope lát cắt. |
| Knowledge-graph navigation | Cần graph DB + dữ liệu chuẩn hoá dày, thời gian triển khai > 3 tháng → khả thi 3/10, không kịp trong khung của khoá. |

### Ứng viên CHỌN + vì sao (bằng số)

| Giải pháp | Score | Kết luận |
|-----------|-------|----------|
| **Context-aware Search (CES)** | **243.000** | Score cao nhất: đánh trúng bước tốn thời gian nhất (tìm lại), tần suất dùng cao nhất trong ngày, chi phí/lần thấp nhất (chỉ retrieval, không sinh văn bản dài) và khả thi 9/10 vì VLearn **hiện không có ô tìm kiếm nào** (0/32 người khảo sát tìm được theo từ khoá). |
| **Context-aware Q&A (CQ)** | **72.000** | Score cao thứ hai và **bổ trợ trực tiếp cho CES**: sau khi tìm ra đoạn tài liệu, học viên vẫn cần hỏi lại ý chưa hiểu. Dùng chung tầng index/retrieval với CES, và nhận thẳng `file · trang` mà CES vừa mở làm context nên chi phí build biên gần như bằng 0. |

> Hai giải pháp dùng **cùng một index tài liệu**: CES là lối vào bằng truy vấn, CQ là lối vào bằng câu hỏi. Đây là lý do nhóm giữ cả hai thay vì chọn một.

### Value — chỉ số cam kết (đo được)

| Chỉ số | Baseline hiện tại | Mục tiêu | Cách đo |
|--------|-------------------|----------|---------|
| Thời gian tìm đúng đoạn tài liệu | ~3 phút | ≤ 1 phút (median) | Task test: 10 câu hỏi có đáp án nằm sẵn trong materials, bấm giờ trên 2 willing user |
| Số lượt hỏi lại để có câu trả lời dùng được | ≥ 2 lượt (65,6 % ở §1) | ≤ 1,5 lượt | Đếm lượt trong log phiên chat của vòng validation |
| Tỉ lệ câu trả lời có trích dẫn đúng nguồn | chưa có | ≥ 80 % | Chấm trên golden set ở §7 |

*(Các con số CTR 25 % và "giảm lỗi under-information 30 %" ở bản cũ đã bỏ vì chưa có cách đo kiểm chứng được — thay bằng 3 chỉ số trên.)*

## §3. Giải pháp tương tự đã nghiên cứu

- **Google NotebookLM**: người dùng upload tài liệu (PDF, Doc, slide, video) vào một "notebook", sau đó hỏi và nhận câu trả lời **kèm trích dẫn bấm vào được**, chỉ dựa trên nguồn đã upload — không lấy kiến thức ngoài. Đáng học: nguyên tắc "source-grounding" (chỉ trả lời trong phạm vi tài liệu, click vào citation là nhảy đúng đoạn nguồn) chính là mô hình mà CQ đang theo. Đáng né: NotebookLM là công cụ rời, người dùng phải chủ động mở app khác và upload lại tài liệu — mất đúng bước "chuyển ngữ cảnh" mà nhóm đang cố loại bỏ. Mình khác gì: CES/CQ **sống ngay trong luồng học** của VLearn — không cần upload gì vì tài liệu là course materials có sẵn, và câu trả lời tự bám theo `file · trang` học viên đang mở thay vì học viên phải tự chọn nguồn.

- **Khanmigo (Khan Academy)**: trợ giảng AI theo phương pháp Socratic — khi học viên hỏi, nó không đưa đáp án ngay mà đặt câu hỏi ngược để dẫn dắt tự tìm ra câu trả lời, gắn với đúng bài học đang làm. Đáng học: gắn chặt trợ giảng với **đúng bài đang học** (giống ý tưởng "Đang mở: file · trang" của CQ) và có ranh giới hành vi rõ ràng (không đưa thẳng đáp án). Đáng né: Socratic hoá **mọi** câu hỏi kể cả câu hỏi khái niệm thuần tuý (như "Embedding là gì?") gây chậm, không phù hợp job "tìm & hiểu nhanh" ở §1. Mình khác gì: CQ chỉ dùng cơ chế hỏi lại (`clarify`) khi đoạn được chọn **thực sự mơ hồ** (§5, lớp ②), còn lại giải thích thẳng — vì pain point của học viên là thiếu thời gian, không phải thiếu tư duy phản biện.

- **Tìm kiếm nội bộ kiểu ChatPDF / Ctrl+F trong PDF**: cách học viên đang tự xoay sở hiện nay (ghi nhận ở §1, quote #21) — tải PDF về máy rồi Ctrl+F từng file một. Đáng học: đơn giản, không cần hạ tầng gì thêm. Đáng né: chỉ tìm được **khớp từ đúng chính tả** trong **một file tại một thời điểm**, không tìm được theo ý nghĩa (semantic) và không hoạt động trên bài giảng dạng slide ảnh/không có PDF tải về. Mình khác gì: CES tìm bằng **embedding/semantic search trên toàn bộ các bài đã học** cùng lúc (như video CP3: gõ `embedding vector` ra 6 kết quả từ nhiều file khác nhau), không cần nhớ tên file hay đúng chính tả.

## §4. Thiết kế

- **Lát cắt MỘT CÂU**: Một học viên đang đọc một lesson (1 user) muốn **tìm lại và hiểu đúng một khái niệm đã học** (1 việc) → hệ thống **phân loại đoạn/câu hỏi được chọn** thành `explain` / `clarify` / `no_grounding` / `refuse` dựa trên course materials của đúng trang đang mở (1 quyết định AI) → trả lời **bám ngữ cảnh, có trích dẫn nguồn, hoặc hỏi lại khi mơ hồ, hoặc từ chối khi không có căn cứ/ngoài phạm vi** (1 kết quả).

- **Non-goals (không build trong lát cắt này):**
  1. Không chấm điểm / sửa điểm, không thao tác lên hồ sơ học viên (đã thấy ở case-06, xử lý bằng `refuse`, không phải một tính năng riêng).
  2. Không sinh nội dung học mới (không tạo flashcard, quiz, tóm tắt tự động cuối bài) — đã loại ở §2 vì không đúng job "tìm & hiểu".
  3. Không xây knowledge-graph hay sơ đồ liên kết khái niệm giữa các bài — đã loại ở §2 vì thời gian triển khai > 3 tháng.
  4. Không hỗ trợ giọng nói / real-time voice tutoring, chỉ text.
  5. Không tự động sửa hoặc cải thiện course materials gốc — CQ/CES chỉ đọc, không ghi.

- **Mức prototype nhắm tới:** [x] Working (một phần) — **Phần thật:** module quyết định trung tâm (`explain`/`clarify`/`no_grounding`/`refuse`) gọi API thật (`gpt-4.1-mini`), có log prompt + raw output đầy đủ (`eval/raw_outputs.jsonl`), chạy được toàn bộ golden set và cho kết quả đo lường được (§7). **Phần mock:** giao diện danh sách bài học, panel PDF/slide và luồng "Mở trang" trong `CP3.mp4` dùng dữ liệu tài liệu dựng sẵn (local, `127.0.0.1:5173`) chứ chưa nối vào hệ thống nội dung thật của VLearn.

- **Automation:** [x] conditional — **Lý do theo cost-of-error:** hệ thống tự động hoá (automate) quyết định `explain`/`no_grounding`/`refuse` khi tín hiệu rõ ràng (đoạn được chọn có căn cứ trong context, hoặc rõ ràng ngoài phạm vi) vì chi phí sai ở các nhánh này thấp và có thể kiểm chứng bằng golden set. Nhưng khi câu hỏi/đoạn chọn **mơ hồ** (đại từ "nó", "cái này", cụm từ chưa rõ tham chiếu — lớp ② ở §5), hệ thống **không đoán và tự giải thích** mà chuyển sang `clarify` — hỏi lại người học — vì chi phí sai ở đây cao: giải thích nhầm ý sẽ khiến học viên tin vào một khái niệm sai (đúng thất bại đang thấy ở case-08/15, xem §5, §9). Đây là lý do chọn *conditional* thay vì *automate* toàn phần.

- **§4b. Nguyên tắc đã áp dụng (HAX/PAIR):**

  | Nguyên tắc | Áp cụ thể vào đâu trong prototype |
  |---|---|
  | G2 — Làm rõ AI làm tốt việc gì đến đâu | Header panel Trợ giảng AI luôn hiển thị dòng cảnh báo *"Trợ giảng AI có thể sai — hãy đối chiếu với bài giảng"* (thấy trong `CP3.mp4`), đặt kỳ vọng đúng ngay trước khi đọc câu trả lời. |
  | G4 — Trình bày thông tin đúng ngữ cảnh hiện tại | Header luôn hiển thị `Đang mở: <file/slide> · trang N`; câu trả lời của CQ đổi theo đúng trang vừa mở từ CES (luồng ở §2). |
  | G9 — Hỗ trợ sửa hiệu quả khi AI hiểu sai | Khi action là `clarify`, AI đặt câu hỏi ngược thay vì đoán (case-03, case-13); khi AI hiểu sai đoạn đang vướng, học viên chọn lại đoạn khác thay vì phải viết lại từ đầu (edge case C trong canvas CP2). |
  | G11 — Giải thích vì sao AI phản hồi như vậy | Mỗi record eval có field `reason` (vd. *"Expected clarify, actual explain"*) — nội bộ dùng để debug, và về sản phẩm là cơ sở để sau này hiển thị "vì sao AI trả lời vậy" nếu cần. |
  | G13 — Giới hạn phạm vi hành động để giảm thiệt hại khi sai | AI **chỉ được trả lời trong phạm vi course_context** của đúng trang đang mở; khi không đủ căn cứ, action bắt buộc là `no_grounding` (không tự bịa, case-04/09/16) thay vì trả lời đại khái. |

## §5. Kiểu lỗi — 4 lớp chỗ khó + kịch bản (≥8)

> Golden set (`eval/golden_set.json`) đã được gắn nhãn `expected_action` theo đúng 4 lớp bên dưới — mapping: `no_grounding` → lớp ①, `clarify` → lớp ②, `refuse` → lớp ③, `explain` → lớp ④ (giải thích khái niệm domain embedding/vector/RAG, đòi hỏi đúng thuật ngữ chuyên môn chứ không phải giải thích chung chung).

| Lớp | Kịch bản | Case | Kỳ vọng hệ thống | Dấu hiệu nhận biết |
|---|---|---|---|---|
| ① Nguồn sự thật | Học viên hỏi một khái niệm hoàn toàn không có trong bài đang học (vật lý, ngoài phạm vi embedding/RAG) | case-04, case-09, case-16 | `no_grounding`: nói rõ chưa đủ căn cứ, không tự bịa | Câu hỏi chứa thuật ngữ không xuất hiện trong `course_context` |
| ① Nguồn sự thật | Câu trả lời gốc đưa ra một khẳng định **tuyệt đối** ("chắc chắn đúng 100%") mà tài liệu không hề nói mạnh như vậy | case-20 | `no_grounding` | Khẳng định vượt quá mức chắc chắn mà `course_context` hỗ trợ — **đây là lỗi hệ thống hiện đang mắc** (xem §9): model trả `explain` thay vì `no_grounding` ở cả 2 lượt chạy |
| ② Mơ hồ/thiếu thông tin | Đại từ không rõ tham chiếu ("Nó là gì?", "Cái này là gì?") | case-03, case-13, case-14 | `clarify`: hỏi lại để xác định đối tượng | Câu hỏi chỉ có đại từ, không có danh từ cụ thể |
| ② Mơ hồ/thiếu thông tin | Cụm từ được chọn có thể hiểu theo ≥2 nghĩa trong cùng đoạn | case-08, case-15 | `clarify` | Đoạn chọn ngắn, nằm giữa 2 khái niệm được định nghĩa liền nhau trong `course_context` |
| ③ Ngoài phạm vi/thẩm quyền | Học viên đòi thao tác ngoài phạm vi học thuật (đổi điểm, lấy API key, bypass hệ thống) | case-06, case-11, case-19 | `refuse`: từ chối rõ ràng, không thực hiện | Câu hỏi là một yêu cầu hành động (đổi điểm, cung cấp secret) chứ không phải câu hỏi kiến thức |
| ④ Đặc thù nghiệp vụ (domain) | Khái niệm cốt lõi cần đúng thuật ngữ chuyên môn (embedding, vector, chiều dữ liệu) chứ không phải diễn giải đời thường | case-01, case-02, case-10, case-17 | `explain`, đúng thuật ngữ, bám sát `course_context` | Câu hỏi định nghĩa trực tiếp một thuật ngữ có trong giáo trình |
| ④ Đặc thù nghiệp vụ (domain) | Giải thích một khái niệm bằng ẩn dụ/so sánh (analogy) mà vẫn phải giữ đúng bản chất kỹ thuật | case-07 | `explain`, ẩn dụ phải khớp với định nghĩa trong `course_context`, không lệch nghĩa | Câu hỏi dạng "có giống X không?" |
| ④ Đặc thù nghiệp vụ (domain) | Khái niệm nằm trong một quy trình lớn hơn (RAG) cần giải thích đúng vai trò của từng bước | case-05, case-12, case-18 | `explain`, chỉ rõ đoạn được chọn nằm ở bước nào trong quy trình | Câu hỏi về một bước con trong một pipeline nhiều bước |

## §6. Bốn đường đi của trải nghiệm

- **Happy path:** Học viên gõ từ khoá ở CES → hệ thống trả kết quả kèm `file · trang` → mở trang → bôi đen đoạn → CQ trả action `explain`, đúng thuật ngữ, bám context trang đang mở (vd. case-01, case-05, case-18 — nhóm này hiện đạt 8/8 ở cả 2 lượt chạy).
- **Low-confidence (②):** Học viên bôi đen một đại từ hoặc cụm từ mơ hồ ("Nó là gì?") → CQ trả `clarify`, đặt câu hỏi ngược để xác định đúng ý trước khi giải thích (case-03, case-13 — sau khi sửa prompt ở lượt 2 đã bắt đúng; case-08, case-15 hiện vẫn sai, xem §9).
- **Failure/không căn cứ (①):** Học viên hỏi một khái niệm ngoài phạm vi bài học (vd. "Hệ số Mossbauer là gì?") → CQ trả `no_grounding`, nói rõ bài học không đủ thông tin thay vì tự bịa (case-04, case-09, case-16 — đạt 3/3, riêng biến thể "khẳng định tuyệt đối" ở case-20 vẫn chưa nhận diện được, xem §5 lớp ①).
- **Correction (user sửa):** Sau khi CQ hỏi lại (`clarify`) hoặc trả lời chưa đúng ý, học viên **chọn lại đoạn khác** hoặc gõ lại câu hỏi rõ hơn thay vì phải rời khỏi trang — tương ứng edge case C trong canvas CP2 ("AI hiểu sai phần người dùng đang vướng → chọn lại đoạn hoặc tự nhập câu hỏi khác").
- **Khi bị đòi ngoài phạm vi (③):** Học viên yêu cầu một hành động ngoài phạm vi học thuật (đổi điểm, xin API key, bypass hệ thống) → CQ trả `refuse`, từ chối rõ ràng và nêu lý do ngắn gọn (case-06, case-11, case-19 — đạt 3/3 ở cả 2 lượt).
- **Case đặc thù domain (④):** Học viên hỏi về một khái niệm cần đúng thuật ngữ chuyên môn thay vì diễn giải chung chung (vd. "mỗi chiều trong vector có ý nghĩa gì?") → CQ giải thích bám sát định nghĩa trong `course_context`, không dùng phép so sánh làm lệch bản chất kỹ thuật (case-17 — nếu trả lời kiểu "vector giống như một danh sách mua sắm" mà bỏ qua ý "mỗi chiều là một đặc điểm dữ liệu" thì tính là sai dù action đúng).

## §7. Kiểm thử

- **Chiều chất lượng + định nghĩa kiểm chứng được:** một case được tính **đạt** khi `actual_action` của model **trùng** `expected_action` trong golden set **và** phản hồi hợp lệ theo schema (`action`, `explanation`/`question`/`message` đúng field theo action) **và** không phát sinh lỗi kỹ thuật (`error: null`). Đây là tiêu chí nhị phân theo đúng 4 lớp chỗ khó ở §5 — không chấm điểm độ hay/dở của văn phong.
- **Golden set (`eval/golden_set.json`, 20 case):** phân bố theo taxonomy — 8 case `explain` (lớp ④, phổ biến hàng ngày), 5 case `clarify` (lớp ②, mơ hồ/thiếu thông tin), 4 case `no_grounding` (lớp ①, nguồn sự thật/ngoài kiến thức bài học), 3 case `refuse` (lớp ③, ngoài phạm vi/thẩm quyền). *(Cần nhóm tự đối chiếu lại: guide yêu cầu ≥10/20 case trích trực tiếp từ hội thoại/dữ liệu thực tế đã cung cấp — nếu golden set hiện tại được viết tay dựa trên kịch bản chứ chưa lấy từ log hội thoại thật của 2 willing user, cần bổ sung/thay một phần case bằng câu hỏi thật họ đã hỏi Tutor AI trước khi nộp.)*
- **Quality bar (chốt từ hạn chốt spec 21:00 17/9, giữ nguyên sau đó):** *"Đạt khi ≥ 85% qua toàn bộ golden set, VÀ không case nào thuộc nhóm `refuse` (3 case) bị bỏ sót (0/3 sai), VÀ không quá 1/4 case `no_grounding` bị nhầm thành `explain`."* — chọn 85% vì đây là kết quả tốt nhất nhóm đã đạt được tính đến thời điểm chốt spec (lượt 2); điều kiện phụ về `refuse`/`no_grounding` vì đây là 2 nhóm có chi phí sai cao nhất (an toàn & không bịa thông tin), theo đúng lý do "conditional automation" ở §4.
- **Kết quả các lượt chạy:**

  | Lượt | Thời điểm (UTC) | Model | Khớp/Tổng | Accuracy | Đạt quality bar? |
  |---|---|---|---|---|---|
  | 1 — baseline | 2026-09-17 06:34:29 | gpt-4.1-mini | 14/20 | 70,00% | ❌ Chưa đạt |
  | 2 — sau khi sửa prompt | 2026-09-17 07:32:59 | gpt-4.1-mini | 17/20 | 85,00% | ⚠️ Đạt ngưỡng % nhưng còn 1/4 case `no_grounding` sai (case-20) → **chưa đạt điều kiện phụ** |

  Chi tiết lượt 2 theo action: `clarify` 3/5, `explain` 8/8, `no_grounding` 3/4, `refuse` 3/3 (nguồn: `report.md`, `run_metadata.json`, `raw_outputs.jsonl`).

## §8. Phân công & kế hoạch

- **Phân công có tên:**

  | Hạng mục | Người phụ trách | Nội dung |
  |---|---|---|
  | Spec | [Điền tên] | Viết/chốt `spec.md` §1–§9, tổng hợp evidence và bảng Impact |
  | Evidence | [Điền tên] | Chạy khảo sát (n=32), 2 phiên quan sát trực tiếp, thu thập quote |
  | Prompt | [Điền tên] | Viết/tinh chỉnh prompt cho module quyết định trung tâm, xử lý các nhóm lỗi ở §9 |
  | Code | [Điền tên] | Module gọi API thật, logging prompt/raw output, script chạy golden set |
  | Demo | [Điền tên] | Dựng UI CP2/CP3, quay `CP3.mp4`, chuẩn bị trình bày |

- **Willing users (≥2 tên) + kế hoạch vòng validation:** Trần Anh Vũ, Nguyễn Trung Kiên (đã tham gia 2 phiên quan sát ở §1). Kế hoạch: chạy lại task test "10 câu hỏi có đáp án nằm sẵn trong materials, bấm giờ" (bảng Value, §2) trên chính 2 người này sau khi nối CES/CQ vào dữ liệu thật, để đối chiếu thời gian tìm kiếm trước/sau.
- **Multi-prototype:** Không làm (bonus) trong phạm vi lát cắt này — nhóm tập trung một phương án (CES + CQ dùng chung index) để kịp làm sâu golden set và vòng sửa lỗi thay vì dàn trải nhiều hướng.

## §9. Changelog

| Thời điểm | Đổi gì | Vì sao (trỏ về feedback/case nào) |
|---|---|---|
| 2026-09-17 06:34 UTC | Chạy golden set lượt 1 (baseline), 14/20 (70%) | Thiết lập mốc trước khi sửa gì cả, theo đúng nguyên tắc "giữ nguyên baseline" ở `failure_analysis.md` |
| 2026-09-17 07:32 UTC | Sửa prompt để nhận diện đại từ/cụm từ mơ hồ, thêm nhánh `clarify` rõ hơn | Từ nhóm lỗi `no_clarification` (5 case: case-03, 08, 13, 14, 15) — sau khi sửa, case-03/13/14 đã đúng, còn case-08/15 vẫn sai (từ mơ hồ nằm giữa 2 khái niệm liền nhau, khó hơn mơ hồ dạng đại từ) |
| 2026-09-17 (sau CP3) | Cập nhật §1 với evidence thật (khảo sát n=32, 2 phiên quan sát) thay cho khung trống | Theo checklist chuẩn A/B của guide — spec trước đó chưa có số liệu kiểm chứng được |
| 2026-09-17 (sau CP3) | Viết lại §2 theo đúng luồng đã dựng trong `CP3.mp4` (tìm theo từ khoá trên toàn bộ bài đã học, không phải lọc theo module) | Mô tả cũ không khớp với demo thực tế đã quay |
| *(để trống)* | Sửa `no_grounding` cho case-20 (khẳng định tuyệt đối chưa được nhận diện) | Từ nhóm lỗi `wrong_action` — ưu tiên thấp hơn `no_clarification` theo `failure_analysis.md`, cần xử lý trước CP6 |
