# Chuyển ảnh bản nhạc sang MuseScore

Ứng dụng Python chạy cục bộ: **ảnh → Audiveris → MusicXML → MuseScore (.mscz)**. Có giao diện Tkinter và dòng lệnh; lưu ảnh gốc, ảnh tiền xử lý và báo cáo để đối chiếu kết quả.

Hỗ trợ ảnh một trang PNG, JPG, TIFF, BMP và WebP. **Chưa hỗ trợ đầu vào PDF trực tiếp.** Nhận dạng scan vẫn có thể mất nốt, chấm dôi hoặc thêm dấu nối; xuất được file không có nghĩa bản nhạc đã đúng. Chương trình không tự thêm/xóa nốt để ép đủ phách.

## Cài đặt và chạy

Cần Python, Audiveris 5.11.0 và MuseScore 4. Xem [hướng dẫn cài đặt](docs/SETUP.md), gồm dữ liệu OCR chữ và cấu hình đường dẫn công cụ.

```sh
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/python converter.py --check
./.venv/bin/python app.py
```

Trên macOS có thể mở `Chay_ung_dung.command` sau khi cài đặt. Chuyển ảnh bằng CLI:

```sh
./.venv/bin/python converter.py samples/images/test4.png
./.venv/bin/python converter.py samples/images/test4.png --profile deskew
./.venv/bin/python converter.py samples/images/test2.png --profile legacy
```

Mỗi lần chạy tạo thư mục riêng trong `output/`. File cần xem gồm:

- `original.*`, `input.png`, `preprocessing/`: ảnh gốc và ảnh đã xử lý.
- `omr/`: MusicXML nén `.mxl` và dự án `.omr` của Audiveris.
- `*.mscz`, `*_audiveris.musicxml`, `*_roundtrip.musicxml`: bản MuseScore, XML thô và XML xuất lại để kiểm tra thay đổi khi nhập/xuất.
- `*_preview-*.png`, `review_*/`: ảnh dựng lại và vị trí ưu tiên đối chiếu.
- `report.json`, `Kiem_tra.txt`, `conversion.log`: tham số, hash, cảnh báo và nhật ký.

## Chọn cách xử lý ảnh

| Profile | Hành vi |
|---|---|
| `auto` / `legacy` | Giữ đường xử lý cũ: tương phản nhẹ, phóng 2× ảnh nhỏ, thêm lề. Không tự sửa cong theo nền tối. |
| `original` | Chỉ xử lý EXIF, nền trong suốt và chuyển xám; giữ độ phân giải. |
| `deskew` | Thử chỉnh nghiêng toàn trang từ các đoạn khuông đo được, có kiểm tra tránh cắt nét. |
| `photo` | Thử làm thẳng khuông ở lượt nhận dạng thứ hai; giữ cả lượt đầu. |
| `illumination` | Thử làm đều nền. |

Các biến thể thử nghiệm không được bảo đảm tốt hơn. `--no-enhance` tắt tiền xử lý tăng cường; `--no-render` bỏ ảnh preview. `--adaptive-std 0.5` thử hệ số nhị phân Audiveris, không tự chọn kết quả theo tổng phách. Xem đầy đủ bằng `converter.py --help`.

## Kiểm chứng

```sh
./.venv/bin/python -m unittest discover -s tests -v
./.venv/bin/python scripts/run_regression.py
./.venv/bin/python scripts/evaluate.py samples/images/test4.png \
  --reference samples/references/test4_manual.musicxml --profile deskew
./.venv/bin/python scripts/run_trials.py samples/images/test4.png \
  --reference samples/references/test4_manual.musicxml --output output/trials
```

Các script đánh giá dùng Audiveris/MuseScore thật; cần cài công cụ trước. `evaluate.py` nhận `--output`; `run_trials.py` nhận `--variants` để chỉ chạy những biến thể được chọn, xem `--help` để biết tên hợp lệ. Tham chiếu chép tay chỉ dùng để đánh giá, không được dùng để vá nội dung nhận dạng.

[Báo cáo điều tra scan](docs/evaluation/REPORT.md) · [Bảng thử nghiệm](docs/evaluation/TRIALS.md) · [Đối chiếu từng ô](docs/evaluation/MEASURES.md) · [File bằng chứng test4](docs/evaluation/artifacts/test4/)

Ở mẫu test4, chỉnh nghiêng khôi phục 24 ô thay vì 23 và giảm sai khác chuỗi cao độ–trường độ, nhưng vẫn mất chấm dôi, thiếu nốt đầu và tăng một số dấu nối giả. Hai PNG rõ test2/test3 đã qua đối chiếu hồi quy; đây không phải kiểm chứng trên PDF gốc. Các tham chiếu chép tay chưa được nhà xuất bản xác nhận.

## Cấu trúc dự án

```text
score_omr/                 Mã ứng dụng, chuyển đổi, tiền xử lý và audit
app.py, converter.py       Điểm chạy tương thích từ thư mục gốc
scripts/                   Đánh giá, thử nghiệm và hồi quy
samples/images/            Ảnh mẫu
samples/references/        Tham chiếu MusicXML và bản nhạc mẫu
samples/baselines/          Kết quả đối chứng test2/test3
tests/                    Kiểm thử tự động
docs/                     Hướng dẫn và bằng chứng đánh giá
output/                    Kết quả chạy, không đưa lên Git
tools/                    Audiveris/dữ liệu OCR cài cục bộ, không đưa lên Git
```

`.venv/`, `output/`, công cụ bên thứ ba và cache được giữ ngoài Git. Không gửi ảnh lên dịch vụ bên ngoài khi chạy chuyển đổi. GUI và hướng dẫn cài đặt hướng tới macOS; nền tảng khác chưa được kiểm chứng đầy đủ.
