# Cài đặt trên macOS

Chạy các lệnh dưới đây từ thư mục gốc dự án. Công cụ và môi trường Python được cài cục bộ; repository không kèm Audiveris, MuseScore hoặc dữ liệu OCR.

## 1. Python và thư viện

Dự án đã được kiểm tra với Python 3.13 trên Mac Intel. Python cần có Tkinter để mở giao diện:

```sh
python3 --version
python3 -m tkinter
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
```

Nếu `python3 -m tkinter` báo thiếu module, cài Python có hỗ trợ Tkinter rồi tạo lại môi trường bằng bản Python đó. CLI không cần mở cửa sổ Tkinter.

## 2. Audiveris

Tải [Audiveris 5.11.0](https://github.com/Audiveris/audiveris/releases/tag/5.11.0), chọn bản phù hợp với Intel hoặc Apple Silicon. Chép ứng dụng vào một trong hai nơi:

```text
tools/Audiveris.app
/Applications/Audiveris.app
```

Bản ứng dụng macOS kèm Java runtime. Nếu cài ở nơi khác, đặt `AUDIVERIS_BIN` tới executable bên trong ứng dụng:

```sh
export AUDIVERIS_BIN="/Applications/Audiveris.app/Contents/MacOS/Audiveris"
```

## 3. Dữ liệu OCR chữ

Audiveris 5.11.0 trong pipeline này dùng chế độ Tesseract legacy. Tải `eng.traineddata` từ bộ [tessdata 4.1.0 chính thức](https://github.com/tesseract-ocr/tessdata/blob/4.1.0/eng.traineddata):

```sh
mkdir -p tools/tessdata_legacy
curl -fL https://raw.githubusercontent.com/tesseract-ocr/tessdata/4.1.0/eng.traineddata \
  -o tools/tessdata_legacy/eng.traineddata
```

Chương trình tự dùng thư mục này nếu file tồn tại. Nếu muốn dùng thư mục khác:

```sh
export TESSDATA_PREFIX="/duong/dan/toi/tessdata"
```

`TESSDATA_PREFIX` đã đặt trong môi trường sẽ được ưu tiên. Không dùng `tessdata_fast` cho cấu hình legacy này: bộ fast chỉ có mô hình LSTM và đã gây lỗi khởi tạo trong thử nghiệm. OCR chữ đúng hơn không đồng nghĩa các nốt được nhận đúng; chữ tiếng Việt chưa có kiểm chứng đầy đủ.

## 4. MuseScore

Cài [MuseScore Studio](https://musescore.org/) vào `/Applications`. Chương trình tìm executable tại:

```text
/Applications/MuseScore 4.app/Contents/MacOS/mscore
```

Nếu tên ứng dụng hoặc vị trí khác, đặt `MUSESCORE_BIN` tới executable thực tế:

```sh
export MUSESCORE_BIN="/Applications/MuseScore 4.app/Contents/MacOS/mscore"
```

Đã kiểm chứng pipeline với MuseScore 4.7.4. Phiên bản khác có thể xử lý tie/slur/beam khác khi nhập MusicXML; vì vậy chương trình luôn xuất lại MusicXML để đối chiếu.

## 5. Kiểm tra và sử dụng

```sh
./.venv/bin/python converter.py --check
./.venv/bin/python -m unittest discover -s tests -v
./.venv/bin/python app.py
```

`--check` kiểm tra đường dẫn executable; chưa xác minh engine chạy được. Để kiểm tra đầu-cuối trên mẫu rõ:

```sh
./.venv/bin/python converter.py samples/images/test2.png --profile legacy
```

Mở MSCZ và đối chiếu ảnh preview, MusicXML thô cùng ảnh gốc. Các báo cáo cảnh báo nhịp không tự thay đổi nốt. Một lần Audiveris có thể chạy vài phút; profile `photo` có thể chạy hai lượt.

Trên macOS, có thể nhấp đúp `Chay_ung_dung.command`. Nếu Terminal không cho thực thi:

```sh
chmod +x Chay_ung_dung.command
```

Các biến `export` ở trên có hiệu lực trong phiên Terminal đó. Khi mở ứng dụng bằng nhấp đúp, nên dùng các vị trí cài đặt mặc định hoặc cấu hình biến môi trường cho phiên chạy tương ứng.

## Các lỗi thường gặp

| Thông báo / biểu hiện | Kiểm tra |
|---|---|
| Không tìm thấy `AUDIVERIS_BIN` / `MUSESCORE_BIN` | Vị trí executable và biến môi trường; chạy `converter.py --check`. |
| Tesseract không khởi tạo được | File `tools/tessdata_legacy/eng.traineddata` và `TESSDATA_PREFIX` có trỏ nhầm bộ fast hay không. |
| Audiveris/MuseScore thoát sớm | Mở `conversion.log` trong thư mục kết quả; thử mở ứng dụng đã cài để kiểm tra cảnh báo macOS. |
| Nhận sai chấm, nốt hoặc vạch nhịp | Xem `review_*/`, MusicXML thô và ảnh gốc; thử biến thể riêng, không mặc định tăng tương phản/phóng ảnh sẽ tốt hơn. |
| File PDF bị từ chối | Phiên bản này chỉ nhận ảnh một trang; chưa có bước render PDF. |

Giữ giấy phép đi kèm Audiveris và MuseScore nếu tự phân phối lại các ứng dụng đó. Các bản cài trong `tools/` không được đưa lên Git của dự án này.
