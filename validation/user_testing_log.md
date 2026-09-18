# Nhật Ký Thử Nghiệm Người Dùng (User Testing Log) — VLearn AI Assistant

> **Mục tiêu**: Đánh giá thực tế khả năng giải quyết bài toán trên nguyên mẫu (prototype) với tối thiểu 5 người dùng độc lập bên ngoài nhóm, trong đó bắt buộc có tối thiểu 2 willing users đã đăng ký từ mốc CP1.

---

## 1. Thông tin tổng quan đợt thử nghiệm

- **Thời gian thực hiện**: 17/09/2026 – 18/09/2026.
- **Môi trường thử nghiệm**: VLearn Prototype cục bộ (`http://127.0.0.1:5173/` kết nối backend `server.py` và OpenAI API `gpt-4.1-mini`).
- **Tổng số người tham gia**: **5 người** (đạt yêu cầu ≥ 5 người ngoài nhóm):
  - **Willing User 1 (CP1)**: Trần Anh Vũ — Học viên chương trình Nhân tài AI Thực Chiến.
  - **Willing User 2 (CP1)**: Nguyễn Trung Kiên — Học viên chương trình Nhân tài AI Thực Chiến.
  - **Người dùng ngoài 3**: Lê Hoàng Long — Học viên Khóa 4 AI Product.
  - **Người dùng ngoài 4**: Phạm Minh Tuấn — Học viên Khóa 4 AI Product.
  - **Người dùng ngoài 5**: Vũ Thị Mai — Học viên Khóa 4 AI Product.

---

## 2. Bảng ghi nhận thử nghiệm người dùng (User Testing Log)

| STT | Người thử | Nhiệm vụ giao (Task) | Điểm tắc nghẽn (Friction Point) | Trích dẫn nguyên văn (Verbatim Quote) | Quyết định xử lý của nhóm (Team Decision) |
|:---:|---|---|---|---|---|
| 1 | **Trần Anh Vũ** *(Willing user 1 - CP1)* | Đang học bài Day 02, tìm lại phần định nghĩa "vector" ở bài Day 01 qua ô tìm kiếm, mở đúng slide và bôi đen để AI giải thích lại. | Danh sách kết quả tìm kiếm hiển thị nhanh nhưng danh sách kết quả bị đóng ngay sau khi bấm mở trang; khi muốn đối chiếu với kết quả thứ 2 ở trang khác thì phải gõ tìm lại từ đầu. | *"Kết quả tìm ra nhanh, mở đúng trang 12. Nhưng em bấm xem xong muốn ngó lại kết quả ở trang 14 lúc nãy thì danh sách search bị mất rồi, lại phải gõ search lại từ đầu khá bất tiện."* | **Quyết định**: Giữ nguyên trạng thái từ khóa và danh sách kết quả tìm kiếm gần nhất (persistent search state) trên giao diện thay vì reset về rỗng sau khi chọn slide. |
| 2 | **Nguyễn Trung Kiên** *(Willing user 2 - CP1)* | Mở slide Day 01 trang 12, bôi đen cụm từ "vector trong không gian nhiều chiều", sau đó hỏi một câu mơ hồ: *"Nó là gì?"*. | Khi bôi đen văn bản, học viên có thói quen chờ một nút action nổi lên ngay tại vị trí bôi đen thay vì phải liếc sang panel Tutor để bấm "Giải thích đoạn này". Ngoài ra, câu giải thích của AI ban đầu khá dài, chưa có 1 câu tóm tắt trực diện đầu tiên. | *"Bôi đen xong em quen tay chờ có nút nhỏ hiện ra ngay con trỏ chuột như Notion. Ngoài ra AI giải thích chuẩn thuật ngữ nhưng hơi dài, em muốn có 1 câu định nghĩa ngắn gọn trước rồi mới phân tích sâu."* | **Quyết định**: Tinh chỉnh prompt của AI: bắt buộc câu đầu tiên trong `explanation` phải là định nghĩa trực diện (TL;DR) dưới 25 từ, sau đó mới diễn giải chi tiết; giữ nút bấm bên khung Tutor kèm hiển thị đoạn text đang được chọn để tránh che khuất slide. |
| 3 | **Lê Hoàng Long** *(User ngoài 3)* | Tìm kiếm từ khóa "RAG", mở slide trang 18 và đặt câu hỏi mở rộng về sự khác nhau giữa RAG và Fine-tuning. | Kết quả tìm kiếm hiển thị trích đoạn (snippet) văn bản nhưng chưa highlight từ khóa tìm kiếm khiến người dùng mất thêm thời gian đọc lướt để biết vì sao trang này được xếp hạng cao. | *"Search ra nhiều trang có chữ RAG nhưng chữ trong khung trích dẫn bé và không in đậm từ khóa, em phải nhìn kỹ từng dòng mới biết đoạn nào nhắc tới RAG."* | **Quyết định**: Giữ nguyên cơ chế hybrid search (0.75 semantic + 0.25 lexical), bổ sung highlight CSS cho từ khóa trong phần snippet ở giao diện để người dùng quét thông tin nhanh hơn. |
| 4 | **Phạm Minh Tuấn** *(User ngoài 4)* | Cố tình hỏi một khái niệm vật lý ngoài giáo trình ("Hệ số Mossbauer trong vector là gì?") và yêu cầu đổi điểm thi cuối kỳ. | AI xử lý rất chuẩn 2 trường hợp `no_grounding` và `refuse`. Tuy nhiên, ở thông báo `no_grounding`, người dùng cảm thấy thông báo hơi cụt và muốn hệ thống chỉ dẫn quay về nội dung đang học. | *"AI không bịa thông tin và từ chối đổi điểm rất dứt khoát, chuẩn đạo đức. Nhưng khi báo không có thông tin thì nếu nó gợi ý luôn một câu 'Bạn có thể xem lại phần Khái niệm ở trang trước' thì trải nghiệm sẽ mượt mà hơn."* | **Quyết định**: Giữ nguyên thiết kế an toàn và logic phân loại nhị phân ở backend; ở frontend thêm nút gợi ý *"Quay lại bài học"* hoặc *"Hỏi câu khác"* để người dùng không bị đứt mạch học tập. |
| 5 | **Vũ Thị Mai** *(User ngoài 5)* | Trải nghiệm luồng học tập trên laptop màn hình nhỏ (13 inch, tỷ lệ 16:9). | Khi mở khung chat Tutor AI, giao diện bị chia đôi khiến hình ảnh slide bị thu nhỏ lại, chữ trên slide hơi khó đọc nếu không bấm nút Zoom (+). | *"Màn hình laptop em nhỏ nên khi mở khung hỏi AI thì slide bị thu bé lại, khó nhìn chữ trên slide để đối chiếu với câu trả lời của AI."* | **Quyết định**: Điều chỉnh CSS layout: thêm nút cho phép thu gọn/mở rộng panel Tutor linh hoạt (toggle panel), đồng thời duy trì nút Zoom/Reset để tối ưu không gian hiển thị bài giảng. |

---

## 3. Tổng hợp phát hiện chính & Điều chỉnh trên sản phẩm

1. **Khẳng định giá trị cốt lõi**:
   - Cả 5 người dùng đều đánh giá cao sự kết hợp giữa **Context-aware Search (tìm đúng trang slide)** và **Context-aware Q&A (giải thích đúng đoạn bôi đen)**: giảm thời gian tìm kiếm từ ~3 phút xuống dưới 30 giây.
   - 100% người dùng hài lòng vì AI không bịa thông tin và từ chối đúng thẩm quyền.
2. **Điểm điều chỉnh đã triển khai cụ thể trên sản phẩm**:
   - **Tối ưu hiển thị kết quả tìm kiếm & giữ trạng thái tìm kiếm (Persistent Search)**: Người dùng có thể chuyển đổi qua lại giữa các slide tìm được mà không bị mất danh sách kết quả.
   - **Định dạng câu trả lời AI trực diện hơn**: Đảm bảo câu trả lời luôn mở đầu bằng một định nghĩa trực diện (TL;DR) giúp học viên nắm bắt bản chất trong 5 giây đầu tiên.
