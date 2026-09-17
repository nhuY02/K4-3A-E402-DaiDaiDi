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

- Core JTBD (không tên sản phẩm/AI trong câu): Hỏi lại ý/mục chưa hiểu trong phần trả lời của Tutor Chat
- Problem statement (KHÔNG chữ AI): Học viên gặp khó khăn trong việc hiểu và tổng hợp thông tin từ lesson/course materials; Tutor AI hiện tại chưa phải lúc nào cũng cung cấp câu trả lời đủ sát với context và nhu cầu của từng học viên. 
- Evidence (chuẩn A và/hoặc B — log đầy đủ trong repo):
- Số liệu mining / kết quả khảo sát (n = ?, % xác nhận):
- ≥5 quote/ví dụ nguyên văn + nguồn:

## §2. Impact & quyết định chọn
**Xây dựng một AI learning assistant hỗ trợ học viên khai thác course materials, trả lời câu hỏi theo context của khóa học và hỗ trợ quá trình tự học.**
**Value:** Giảm thời gian tìm kiếm thông tin, giúp học viên hiểu bài nhanh hơn và hỗ trợ việc tự học hiệu quả hơn.

### Bảng impact ≥3 ứng viên

| # | Giải pháp | Người dùng (người) | Tần suất (%) | Chi phí / lần ($) | Khả thi (1–10) | Score |
|---|-----------|-------------------|--------------|-------------------|--------------|-------|
| 1 | **Context‑aware Q&A** | 45 | 30 | 0.03 | 8 | 3600 |
| 2 | Auto‑completion trong chat | 40 | 20 | 0.01 | 9 | 7200 |
| 3 | Knowledge‑graph navigation | 32 | 15 | 0.02 | 7 | 3000 |
> *Score được tính theo công thức: (Người dùng × Tần suất × Khả thi) ÷ Chi phí.*

### Ứng viên ĐÃ LOẠI + vì sao

| Giải pháp | Lý do loại bỏ |
|-----------|----------------|
| Knowledge‑graph navigation | Chi phí xây dựng cao, dữ liệu cần được chuẩn bị cẩn thận, lâu hạn triển khai |
| Auto‑completion trong chat | Mô hình chính xác trong những thông tin rời rạc, đáp ứng kém trong trường hợp câu hỏi ngữ cảnh đa dạng; làm giảm độ chính xác và gây nhầm lẫn. |

### Ứng viên CHỌN + vì sao (bằng số)

| Giải pháp | Score | Kết luận |
|-----------|-------|----------|
| **Context‑aware Q&A** | 3600 | Đúng mục tiêu "giảm thời gian tìm kiếm, tối ưu tự học"; tăng trải nghiệm người dùng (đáp ứng ngay, chính xác); chi phí thấp, triển khai nhanh, khả thi cao. |

## §3. Giải pháp tương tự đã nghiên cứu
- [Sản phẩm 1]: flow / đáng học / đáng né / mình khác gì
- [Sản phẩm 2]: ...

## §4. Thiết kế
- Lát cắt MỘT CÂU (1 user · 1 việc · 1 quyết định AI · 1 kết quả):
- Non-goals (≥3 thứ KHÔNG build):
- Mức prototype nhắm tới: [ ] Sketch [ ] Mock [ ] Working — phần nào mock, phần nào thật:
- Automation: [ ] augment [ ] conditional [ ] automate — lý do theo cost-of-error:
- §4b. Nguyên tắc đã áp dụng (≥4 — HAX/PAIR, xem guide):
  | Nguyên tắc | Áp cụ thể vào đâu trong prototype |
  |---|---|

## §5. Kiểu lỗi — 4 lớp chỗ khó + kịch bản (≥8) [bảng theo guide §2.5]

## §6. Bốn đường đi của trải nghiệm
- Happy path: · Low-confidence (②): · Failure/không căn cứ (①): · Correction (user sửa):
- Khi bị đòi ngoài phạm vi (③): · Case đặc thù domain (④):

## §7. Kiểm thử
- Chiều chất lượng + định nghĩa kiểm chứng được:
- Golden set (≥20 case theo cơ cấu trong guide §2.6, file trong eval/):
- Quality bar (chốt từ hạn chốt spec của khoá, giữ nguyên sau đó): "Đạt khi ≥ ___% qua bộ, và ___"
- Kết quả các lượt chạy (bảng % — cập nhật đến trước CP6):

## §8. Phân công & kế hoạch
- Phân công có tên: spec / evidence / prompt / code / demo
- Willing users (≥2 tên) + kế hoạch vòng validation *(bonus, nếu làm)*:
- Multi-prototype (nếu làm): trục khác biệt của ≥2 phương án + lý do chọn:

## §9. Changelog
| Thời điểm | Đổi gì | Vì sao (trỏ về feedback/case nào) |

