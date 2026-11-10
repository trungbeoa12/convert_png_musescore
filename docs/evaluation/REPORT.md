# Điều tra mẫu test4 — 10/11/2026

**Đã sửa cơ chế lựa chọn/kiểm chứng và bổ sung thử nghiệm chỉnh nghiêng, nhưng chưa khắc phục được nhận dạng bản scan một cách đáng tin cậy.** Bản chỉnh nghiêng khôi phục cấu trúc 24 ô và cải thiện chuỗi nốt so với kết quả được báo lỗi, nhưng vẫn mất nốt/chấm dôi và tăng một số dấu nối giả. Không chọn nó làm mặc định cho mọi ảnh.

## Pipeline thực tế

```text
PNG/JPG/TIFF/BMP/WebP một trang
 → sao chép nguyên byte original.*
 → EXIF + ghép alpha lên nền trắng + ảnh xám
 → [legacy/auto: autocontrast cutoff=0.1%, 2x bicubic nếu cạnh lớn nhất <2000, lề trắng 30px]
 → input.png (PNG không mất dữ liệu; DPI=300 chỉ là metadata)
 → Audiveris: LOAD → BINARY → SCALE → GRID → … → RHYTHMS → PAGE
 → .omr (có BINARY.png, hình học, ký hiệu) + .mxl nguyên bản
 → [bản cũ: nền tối tự kích hoạt sửa cong dọc rồi nhận dạng lại]
 → [bản mới: sửa cong chỉ khi chọn photo; deskew là lựa chọn độc lập]
 → kiểm tra nhịp chỉ đọc, không điền/xóa nốt
 → nếu trang quá thấp: bản sao MusicXML chỉ đổi layout, kiểm tra bất biến ngữ nghĩa
 → MuseScore .mscz → xuất lại MusicXML + ảnh PNG → đối chiếu
```

Không có bước AI sửa nốt. Không có đường render PDF trong `score_omr/converter.py` hoặc `score_omr/app.py`; không tìm thấy file `.pdf` trong dự án. Các mẫu gọi là “clear_pdf” ở đánh giá trước là PNG, chưa xác nhận được nguồn PDF gốc. Không thêm hỗ trợ PDF mới trong đợt sửa này.

## Bằng chứng nguyên nhân

- Audiveris **5.11.0**, build `9e1e55cd2746037d059345881c53e6a6754bffbd`; MuseScore **4.7.4**. Python 3.13.13, Mac Intel. Lệnh gốc: `Audiveris -batch -transcribe -export -save -output <omr> -- <input.png>`; không có override nhận dạng. OCR dùng `tools/tessdata_legacy/eng.traineddata` trừ khi đặt `TESSDATA_PREFIX`.
- Ảnh gốc **1788×954 RGBA**, metadata khoảng 144 DPI. Ảnh thực đưa vào Audiveris **3636×1968**. Không thu nhỏ, không JPEG, không nhị phân hóa trong code tiền xử lý. Có tăng tương phản, phóng 2x bicubic và thêm lề. Audiveris mới là bước nhị phân hóa. Hệ số nguồn 5.11.0: mean **0.7**, std **0.9**; tham khảo [mã nguồn Audiveris 5.11.0](https://github.com/Audiveris/audiveris/blob/5.11.0/app/src/main/java/org/audiveris/omr/image/AdaptiveDescriptor.java).
- `input.png` của lượt đối chứng mới giống từng pixel với lượt người dùng. Bản `original.png` sau chạy giống SHA256 với bản gốc. Biến thể deskew trong thử nghiệm và đầu-cuối cũng giống từng pixel.
- Trong `input.omr`, khoảng khuông chính 38px, độ dày đường 11px, beam 20px. `artifacts/test4/binary_first.png` cho thấy chấm dôi ô đầu vẫn có trong ảnh nhị phân nhưng chạm đường khuông; cả đầu nốt Si và nét móc vẫn có trong ảnh. Kết luận có căn cứ là **lỗi phân đoạn/diễn giải ký hiệu và nhịp của engine**, không phải code đã xóa nốt trong MusicXML. Không thể xác định duy nhất một bộ phân loại bên trong chỉ từ bằng chứng này.
- MusicXML lượt đầu đã có 23 ô, 47 nốt, 9 lặng, **0 chấm**, 1 giáng, 2 voice; lượt sửa cong cũ có 23 ô, 48 nốt, 9 lặng, 0 chấm, 1 giáng. Cả hai thiếu Si4 ô đầu và thêm lặng ở voice 2. `Tempo dim` nằm trong `credit-words` của MusicXML sửa cong, trước MuseScore.
- Vòng nhập/xuất bản cũ giữ nguyên chuỗi cao độ/trường độ, lặng, chấm và dấu hóa; slur thay đổi 2 vị trí. Vì vậy các lỗi nốt chính có trước MuseScore. Với bản mới, cao độ/trường độ và cấu trúc cũng giữ nguyên, nhưng tie/slur và beam thay đổi: xem `data/audit.json`. Đã mở/đọc lại MSCZ bằng executable MuseScore thật và render cả hai trang; chưa kiểm chứng thao tác GUI bằng tay.

## Thử nghiệm có đối chứng

Thử nghiệm mới chạy bằng `scripts/run_trials.py` từ thư mục gốc. Log, lệnh, hash và MusicXML của sáu biến thể lịch sử được giữ ở `logs/`; hai dự án Audiveris đối chứng/chỉnh nghiêng ở `projects/`. Ảnh mẫu gốc chỉ lưu một bản ở `samples/images/test4.png`; ảnh trung gian/crop lặp đã được dọn. Log lịch sử giữ thông tin các lần Audiveris bị dừng mã -6 trong sandbox rồi chạy lại thành công ngoài sandbox. Các đường dẫn `${PROJECT_ROOT}` trong log/data mô tả vị trí tại thời điểm thử nghiệm, không phải đường dẫn hiện tại.

Tham chiếu `samples/references/test4_manual.musicxml` là bản chép tay đã có trong dự án, đã đọc lại với ảnh: **24 ô, 53 nốt, 7 lặng, 14 chấm**, không giáng cục bộ, không tie/slur. Chỉ dùng trong evaluation, không được converter đọc, không dùng để vá nốt. Đây chưa phải bản chuẩn do nhà xuất bản xác nhận.

Bảng số liệu đầy đủ ở [TRIALS.md](TRIALS.md). Khoảng cách chỉnh sửa chuỗi cao độ–trường độ: kết quả người dùng **21**, đối chứng legacy **23**, chỉnh nghiêng **18**, giảm nhiễu Gaussian 3×3 sigma=0.4 **23**, giảm ảnh legacy xuống 75% bằng INTER_AREA **28**, hệ số std=0.3 **36**, std=0.5 **31**. Đây không phải phần trăm chính xác hay số nốt sai; mất/thừa sự kiện và cấu trúc bè ảnh hưởng phép đo.

Chỉnh nghiêng đo từ 75 đoạn thẳng dài, median **−0.53435°**, MAD 0.12923°. Không dùng tọa độ riêng của mẫu; có kiểm tra thiếu bằng chứng/góc không nhất quán/nguy cơ cắt mất nét. Không thêm sửa phối cảnh. Thử cân bằng nền và Otsu từ lần điều tra cũ cũng đã được đọc: lần lượt khoảng cách 24 và 44, Otsu sau cân bằng nền 42; đây là kết quả lịch sử, không gộp thành lượt chạy mới.

## Đối chiếu trực tiếp các lỗi

| Vị trí trong ảnh gốc | Kết quả cũ được báo lỗi | Bản deskew mới | Kết luận |
|---|---|---|---|
| Ô 1: lặng móc đơn, La4 móc đơn, La4 móc đơn chấm, Si4 móc kép | Chỉ 2 nốt La, mất Si/chấm; lặng voice 2 | Vẫn như vậy | Chưa sửa |
| Ô 3: Đô#5 đen, Đô#5 móc đơn chấm, Si4 móc kép | Mất chấm | Mất chấm, Si thành móc đơn | Có chỗ xấu hơn |
| Cuối dòng 1, ô 5–6 | Gộp/sai ranh giới; dòng đầu chỉ 5 ô | Phân lại đủ 6 ô; cả trang 24 ô | Cải thiện cấu trúc, chưa đúng toàn bộ nhịp |
| Ô 7, đầu dòng 2 | Mất nhiều nốt, nhịp sai | Đủ Si4–Đô#5–La4–Sol#4; thiếu hai chấm | Cải thiện nốt, chưa sửa chấm |
| Ô 15, dòng 3: Sol#4 cuối nhóm | Giáng thừa thành Sol♭4 (ô xuất 14) | Trở lại Sol#4 | Vị trí này được cải thiện |
| Ô 13, đầu dòng 3 | Không có giáng tại Si4 | Lại phát sinh Si♭4 | Chưa giải quyết giáng thừa tổng thể |
| Đường nối/lặng giả | 11 slur-start, 1 tie-start; 9 lặng | 17 slur-start, 3 tie-start; 8 lặng | Nối giả tăng; vẫn thừa lặng ô 1 |
| Chấm dôi toàn trang | 0/14 | 0/14 | Chưa sửa |
| Chữ đầu bài | `Tempo dim` | `Tanpo di march` | Vẫn sai, không thay bằng chuỗi hard-code |

[MEASURES.md](MEASURES.md) ghi toàn bộ nốt/trường độ/voice/tie/slur theo từng ô. Ảnh preview trước và sau đã được xem đối chiếu; số ô cũ lệch sau vị trí gộp nên không ghép máy móc cùng số ô. Không coi tổng nốt tăng là bằng chứng mọi nốt đúng.

## Thay đổi mã

- Không tự chọn sửa cong vì nền tối và vì lượt hai xuất được file. Profile `photo` giữ lại như lựa chọn thử nghiệm chủ động; `auto` giữ lượt legacy. Do đó auto trên mẫu này có thể kém bản photo cũ; mục đích là bỏ lựa chọn không có bằng chứng tổng quát, không tuyên bố auto mới tốt hơn.
- Thêm `deskew` có đo góc/kiểm tra an toàn và lưu ảnh trước biến đổi; thêm `--adaptive-std` để thí nghiệm ngưỡng có log, không chọn mặc định theo mẫu.
- Lưu kích thước/mode/DPI gốc, hash ảnh và biến thể, phiên bản package, phiên bản/build engine từ `.omr`, hash ảnh nhị phân. Xuất thêm `*_audiveris.musicxml` nguyên nội dung giải nén để xem dễ.
- Audit thêm onset, beam, ranh giới ô, barline, chữ hướng dẫn và credit OCR. Chuỗi nốt giống nhau nhưng di chuyển vạch nhịp sẽ không còn bị coi là cùng cấu trúc.
- Không sửa nội dung nốt/lặng/dấu hóa/đường nối. Kiểm tra nhịp tiếp tục xử lý backup/forward, chord, grace, nhịp cộng; ô thiếu phách được báo có thể là lấy đà, không tự điền. Chưa có bộ xác minh nhịp nhiều bè hoàn chỉnh.
- **13 tests đạt**, gồm phát hiện đổi vạch nhịp với chuỗi nốt giữ nguyên và đổi OCR. Hồi quy Audiveris + MuseScore trên **test2/test3**: mọi thuộc tính so sánh và cấu trúc giữ nguyên; xem `data/regression.json`. Đây là hồi quy trên PNG rõ, không phải xác nhận PDF gốc hay mọi nốt đã đúng.

## HOMR

Đã xem [mã và tài liệu chính thức HOMR](https://github.com/liebharc/homr), yêu cầu được kiểm tra từ README và pyproject.toml tại thời điểm điều tra. Bản main yêu cầu CPU `onnxruntime>=1.24.1`; kiểm tra pip trên môi trường Mac Intel/Python 3.13 hiện tại chỉ tìm được đến 1.23.2. Dry-run yêu cầu chính xác thất bại: [homr_feasibility.log](logs/homr_feasibility.log). **Chưa chạy được HOMR trên mẫu, chưa chứng minh lợi ích**, không đổi engine hoặc cài phụ thuộc lớn. Có thể thử tiếp trong môi trường Linux/ARM được runtime hỗ trợ hoặc một release HOMR cũ tương thích, tách khỏi môi trường ứng dụng; không suy ra rằng tất cả phiên bản HOMR đều không chạy được trên Mac này.

## File và chạy lại

Sau khi tổ chức lại dự án, các file cần đối chiếu có đường dẫn ổn định:

- [Ảnh gốc](../../samples/images/test4.png).
- [MusicXML trước sửa, sau lượt sửa cong cũ](artifacts/test4/before_geometry.musicxml).
- [MusicXML lượt đầu cũ](artifacts/test4/before_raw.musicxml) và [sau MuseScore cũ](artifacts/test4/before_roundtrip.musicxml).
- [MSCZ chỉnh nghiêng](artifacts/test4/after.mscz), [MusicXML thô](artifacts/test4/after_raw.musicxml), [MusicXML sau MuseScore](artifacts/test4/after_roundtrip.musicxml).
- Ảnh dựng lại: [trang 1](artifacts/test4/after_preview-1.png), [trang 2](artifacts/test4/after_preview-2.png).
- [Báo cáo máy của lượt chỉnh nghiêng](artifacts/test4/report.json); [đối chiếu đầy đủ](data/audit.json).
- Hai dự án `.omr` giữ ảnh nhị phân và hình học thật ở `projects/`.

Thư mục output/test4 gốc đã không còn trước đợt dọn dự án. Vì vậy file MSCZ cũ không được liên kết như thể còn tồn tại; các MusicXML đã lưu ở trên giữ bằng chứng trước/sau. Bản sao mã cũ, ảnh lặp, cache và các script phụ thuộc timestamp cố định đã được bỏ. Hai kết quả chạy gần nhất của người dùng vẫn được giữ cục bộ trong `output/`, ngoài Git.

Chạy từ thư mục gốc sau khi cài công cụ theo [SETUP](../SETUP.md):

```sh
./.venv/bin/python converter.py samples/images/test4.png --profile deskew
./.venv/bin/python converter.py samples/images/test4.png --profile legacy
./.venv/bin/python scripts/run_trials.py samples/images/test4.png \
  --reference samples/references/test4_manual.musicxml
./.venv/bin/python scripts/run_regression.py
./.venv/bin/python -m unittest discover -s tests -v
```

Mỗi lần chạy tạo thư mục riêng trong `output/`. Các file đánh giá lịch sử là bằng chứng của phiên bản trước khi dọn folder; hash mã trong data không mô tả phiên bản đã di chuyển vào package.

Hướng tiếp theo có cơ sở: sửa ký hiệu tại các vị trí đã đánh dấu trong Audiveris/MuseScore nếu cần bản dùng ngay; thử HOMR trong môi trường riêng rồi chấm cùng bộ tham chiếu; bổ sung scan độc lập và PDF gốc có MusicXML chuẩn trước khi đổi mặc định. Không tiếp tục thêm lọc mạnh chỉ vì ảnh nhìn trắng/đẹp hơn.

Sau tổ chức lại folder: 13 unit tests đạt; hai lượt chạy thật test2/test3 qua script mới đều PASS. Chi tiết ở [reorganization_checks.json](data/reorganization_checks.json).
