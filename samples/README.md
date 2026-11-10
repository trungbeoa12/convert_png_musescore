# Mẫu đánh giá

- `images/`: ảnh đầu vào đã có trong dự án. `test4.png` là ảnh scan/chụp được điều tra; `test2.png`, `test3.png` là PNG rõ để kiểm tra hồi quy. Không có PDF gốc để xác nhận nguồn xuất của hai ảnh này.
- `references/test4_manual.musicxml`, `cay_truc_xinh_manual.musicxml`: tham chiếu chép tay tạm, chỉ dùng để đánh giá, chưa được nhà xuất bản xác nhận. Pipeline không đọc các file này để sửa nốt.
- `references/cay_truc_xinh.mscz`: bản MuseScore mẫu đã có trước đợt dọn folder. Bản `cay_truc_xinh.musicxml` trùng byte với `cay_truc_xinh_manual.musicxml` đã được gộp vào file tham chiếu.
- `baselines/test2.mxl`, `test3.mxl`: kết quả Audiveris 5.11.0 từ lần kiểm chứng trước; dùng phát hiện thay đổi, không đại diện ground truth.

Tên file ảnh được giữ nguyên để đối chiếu lịch sử. Xem [báo cáo scan](../docs/evaluation/REPORT.md).
