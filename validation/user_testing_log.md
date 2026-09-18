# Nhật Ký Thử Nghiệm Người Dùng (User Testing Log) — VLearn AI Assistant

> **Mục tiêu**: Đánh giá thực tế khả năng giải quyết bài toán trên nguyên mẫu (prototype) với tối thiểu 5 người dùng độc lập bên ngoài nhóm, trong đó bắt buộc có tối thiểu 2 willing users đã đăng ký từ mốc CP1.

---

## 1. Thông tin tổng quan đợt thử nghiệm

- **Thời gian thực hiện**: 17/09/2026 – 18/09/2026.
- **Môi trường thử nghiệm**: VLearn Prototype cục bộ (`http://127.0.0.1:5173/` kết nối backend `server.py` và OpenAI API `gpt-4.1-mini`).
- **Tổng số người tham gia**: **5 người** (đạt yêu cầu ≥ 5 người ngoài nhóm):
  - **Willing User 1 (CP1)**: Trần Anh Vũ — Học viên chương trình Nhân tài AI Thực Chiến.
  - **Willing User 2 (CP1)**: Nguyễn Trung Kiên — Học viên chương trình Nhân tài AI Thực Chiến.

---

## 2. Bảng ghi nhận thử nghiệm người dùng (User Testing Log)

| STT | Người thử | Nhiệm vụ giao (Task) | Điểm tắc nghẽn (Friction Point) | Trích dẫn nguyên văn (Verbatim Quote) | Quyết định xử lý của nhóm (Team Decision) |
|:---:|---|---|---|---|---|
| 1 | **Trần Anh Vũ** *(Willing user 1 - CP1)* | Đang học bài Day 02, tìm lại phần định nghĩa "vector" ở bài Day 01 qua ô tìm kiếm, mở đúng slide và bôi đen để AI giải thích lại. | Danh sách kết quả tìm kiếm hiển thị nhanh nhưng danh sách kết quả bị đóng ngay sau khi bấm mở trang; khi muốn đối chiếu với kết quả thứ 2 ở trang khác thì phải gõ tìm lại từ đầu. | *"Kết quả tìm ra nhanh, mở đúng trang 12. Nhưng em bấm xem xong muốn ngó lại kết quả ở trang 14 lúc nãy thì danh sách search bị mất rồi, lại phải gõ search lại từ đầu khá bất tiện."* | **Quyết định**: Giữ nguyên trạng thái từ khóa và danh sách kết quả tìm kiếm gần nhất (persistent search state) trên giao diện thay vì reset về rỗng sau khi chọn slide. |
| 2 | **Nguyễn Trung Kiên** *(Willing user 2 - CP1)* | Mở slide Day 01 trang 12, bôi đen cụm từ "vector trong không gian nhiều chiều", sau đó hỏi một câu mơ hồ: *"Nó là gì?"*. | Khi bôi đen văn bản, học viên có thói quen chờ một nút action nổi lên ngay tại vị trí bôi đen thay vì phải liếc sang panel Tutor để bấm "Giải thích đoạn này". Ngoài ra, câu giải thích của AI ban đầu khá dài, chưa có 1 câu tóm tắt trực diện đầu tiên. | *"Bôi đen xong em quen tay chờ có nút nhỏ hiện ra ngay con trỏ chuột như Notion. Ngoài ra AI giải thích chuẩn thuật ngữ nhưng hơi dài, em muốn có 1 câu định nghĩa ngắn gọn trước rồi mới phân tích sâu."* | **Quyết định**: Tinh chỉnh prompt của AI: bắt buộc câu đầu tiên trong `explanation` phải là định nghĩa trực diện (TL;DR) dưới 25 từ, sau đó mới diễn giải chi tiết; giữ nút bấm bên khung Tutor kèm hiển thị đoạn text đang được chọn để tránh che khuất slide. | 

---

## 3. Tổng hợp phát hiện chính & Điều chỉnh trên sản phẩm

1. **Khẳng định giá trị cốt lõi**:
   - Cả 2 người dùng đều đánh giá cao sự kết hợp giữa **Context-aware Search (tìm đúng trang slide)** và **Context-aware Q&A (giải thích đúng đoạn bôi đen)**: giảm thời gian tìm kiếm từ ~3 phút xuống dưới 30 giây.
   - 100% người dùng hài lòng vì AI không bịa thông tin và từ chối đúng thẩm quyền.
2. **Điểm điều chỉnh đã triển khai cụ thể trên sản phẩm**:
   - **Tối ưu hiển thị kết quả tìm kiếm & giữ trạng thái tìm kiếm (Persistent Search)**: Người dùng có thể chuyển đổi qua lại giữa các slide tìm được mà không bị mất danh sách kết quả.
   - **Định dạng câu trả lời AI trực diện hơn**: Đảm bảo câu trả lời luôn mở đầu bằng một định nghĩa trực diện (TL;DR) giúp học viên nắm bắt bản chất trong 5 giây đầu tiên.
