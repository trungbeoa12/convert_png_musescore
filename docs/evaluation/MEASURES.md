# Đối chiếu từng ô theo dữ liệu xuất

Tham chiếu đọc từ ảnh, chỉ dùng để đánh giá; số ô engine có thể lệch sau khi gộp/mất vạch nhịp.

Đơn vị trường độ: phách đen. A:0:4 là La4; R là lặng; dấu #/b nằm ở trường alter (+1/-1).

## reference

| Ô | Chuỗi ký hiệu: cao độ / trường độ (chấm, bè, nối) |
|---|---|
| 1 | R / 1/2 [v1]; A:0:4 / 1/2 [v1]; A:0:4 / 3/4. [v1]; B:0:4 / 1/4 [v1] |
| 2 | C:1:5 / 1 [v1]; E:0:5 / 1 [v1] |
| 3 | C:1:5 / 1 [v1]; C:1:5 / 3/4. [v1]; B:0:4 / 1/4 [v1] |
| 4 | C:1:5 / 2 [v1] |
| 5 | R / 1 [v1]; A:0:4 / 3/4. [v1]; B:0:4 / 1/4 [v1] |
| 6 | C:1:5 / 1 [v1]; A:0:4 / 1 [v1] |
| 7 | B:0:4 / 3/4. [v1]; C:1:5 / 1/4 [v1]; A:0:4 / 3/4. [v1]; G:1:4 / 1/4 [v1] |
| 8 | A:0:4 / 2 [v1] |
| 9 | R / 1/2 [v1]; A:0:4 / 1/2 [v1]; A:0:4 / 3/4. [v1]; B:0:4 / 1/4 [v1] |
| 10 | C:1:5 / 1 [v1]; E:0:5 / 1 [v1] |
| 11 | C:1:5 / 1 [v1]; C:1:5 / 3/4. [v1]; B:0:4 / 1/4 [v1] |
| 12 | C:1:5 / 2 [v1] |
| 13 | R / 1 [v1]; A:0:4 / 3/4. [v1]; B:0:4 / 1/4 [v1] |
| 14 | C:1:5 / 1 [v1]; A:0:4 / 1 [v1] |
| 15 | B:0:4 / 3/4. [v1]; C:1:5 / 1/4 [v1]; A:0:4 / 3/4. [v1]; G:1:4 / 1/4 [v1] |
| 16 | A:0:4 / 2 [v1] |
| 17 | R / 1/2 [v1]; C:1:5 / 1/2 [v1]; C:1:5 / 3/4. [v1]; D:0:5 / 1/4 [v1] |
| 18 | E:0:5 / 2 [v1] |
| 19 | R / 1/2 [v1]; B:0:4 / 1/2 [v1]; B:0:4 / 3/4. [v1]; C:1:5 / 1/4 [v1] |
| 20 | D:0:5 / 2 [v1] |
| 21 | R / 1/2 [v1]; A:0:4 / 1/2 [v1]; B:0:4 / 3/4. [v1]; G:1:4 / 1/4 [v1] |
| 22 | A:0:4 / 1 [v1]; C:1:5 / 1 [v1] |
| 23 | B:0:4 / 1 [v1]; A:0:4 / 3/4. [v1]; G:1:4 / 1/4 [v1] |
| 24 | A:0:4 / 2 [v1] |

## before_geometry

| Ô | Chuỗi ký hiệu: cao độ / trường độ (chấm, bè, nối) |
|---|---|
| 1 | R / 1/2 [v1]; A:0:4 / 1/2 [v1]; A:0:4 / 1/2 [v1]; R / 3/2 [v2] |
| 2 | C:1:5 / 1 [v1]; E:0:5 / 1 [v1] |
| 3 | C:1:5 / 1 [v1]; C:1:5 / 1/2 [v1, slur=start]; B:0:4 / 1/4 [v1] |
| 4 | C:1:5 / 2 [v1] |
| 5 | R / 1 [v1]; A:0:4 / 1/2 [v1, slur=stop]; B:0:4 / 1/4 [v1, slur=start]; C:1:5 / 1 [v1] |
| 6 | R / 1/2 [v1]; B:0:4 / 1/2 [v2] |
| 7 | A:0:4 / 2 [v1] |
| 8 | R / 1/2 [v1]; A:0:4 / 1/2 [v1, slur=start]; A:0:4 / 1/2 [v1, slur=start,start]; B:0:4 / 1/4 [v1, slur=stop,stop] |
| 9 | C:1:5 / 1 [v1, slur=stop]; E:0:5 / 1 [v1] |
| 10 | C:1:5 / 1 [v1]; C:1:5 / 1/2 [v1]; B:0:4 / 1/4 [v1] |
| 11 | C:1:5 / 2 [v1] |
| 12 | R / 1 [v1]; A:0:4 / 1/2 [v1]; B:0:4 / 1/4 [v1] |
| 13 | C:1:5 / 1 [v1]; A:0:4 / 1 [v1] |
| 14 | B:0:4 / 1/2 [v1]; C:1:5 / 1/4 [v1, slur=start]; A:0:4 / 1/2 [v1, slur=stop]; G:-1:4 / 1/4 [v1] |
| 15 | A:0:4 / 2 [v1] |
| 16 | R / 1/2 [v1]; C:1:5 / 1/2 [v1, tie=start]; C:1:5 / 1/2 [v1, tie=stop]; D:0:5 / 1/4 [v1] |
| 17 | E:0:5 / 2 [v1] |
| 18 | R / 1/2 [v1]; D:0:4 / 1 [v1]; B:0:4 / 1 [v1, slur=start,start]; B:0:4 / 1 [v1] |
| 19 | D:0:5 / 2 [v1] |
| 20 | R / 1/2 [v1]; A:0:4 / 1/2 [v1, slur=start]; B:0:4 / 1/2 [v1, slur=start,stop]; G:1:4 / 1/4 [v1, slur=stop] |
| 21 | A:0:4 / 1 [v1, slur=start]; C:1:5 / 1 [v1, slur=stop] |
| 22 | B:0:4 / 1 [v1]; A:0:4 / 1/2 [v1]; G:1:4 / 1/4 [v1] |
| 23 | A:0:4 / 2 [v1] |

## after_raw

| Ô | Chuỗi ký hiệu: cao độ / trường độ (chấm, bè, nối) |
|---|---|
| 1 | R / 1/2 [v1]; A:0:4 / 1/2 [v1]; A:0:4 / 1/2 [v1]; R / 3/2 [v2] |
| 2 | C:1:5 / 1 [v1]; E:0:5 / 1 [v1] |
| 3 | C:1:5 / 1 [v1]; C:1:5 / 1/2 [v1, slur=start]; B:0:4 / 1/2 [v1] |
| 4 | C:1:5 / 2 [v1, slur=stop] |
| 5 | R / 1 [v1]; A:0:4 / 1/2 [v1, slur=start]; B:0:4 / 1/4 [v1, slur=stop] |
| 6 | C:1:5 / 1 [v1, slur=start]; A:0:4 / 1 [v1, slur=stop] |
| 7 | B:0:4 / 1/2 [v1]; C:1:5 / 1/4 [v1]; A:0:4 / 1/2 [v1]; G:1:4 / 1/4 [v1] |
| 8 | A:0:4 / 2 [v1] |
| 9 | R / 1/2 [v1]; A:0:4 / 1/2 [v1, tie=start,start]; A:0:4 / 1/2 [v1, slur=start,start,start, tie=stop,stop]; B:0:4 / 1/4 [v1, slur=stop] |
| 10 | C:1:5 / 1 [v1, slur=stop,stop]; E:0:5 / 1 [v1, slur=start,start] |
| 11 | C:1:5 / 1 [v1, slur=stop,stop, tie=start]; C:1:5 / 1 [v1, slur=start, tie=stop] |
| 12 | C:1:5 / 2 [v1, slur=stop] |
| 13 | R / 1 [v1]; A:0:4 / 1/2 [v1]; B:-1:4 / 1/4 [v1] |
| 14 | C:1:5 / 1 [v1]; A:0:4 / 1 [v1] |
| 15 | B:0:4 / 1/2 [v1, slur=start,start]; C:1:5 / 1/4 [v1, slur=stop]; A:0:4 / 1/2 [v1, slur=start,stop]; G:1:4 / 1/4 [v1, slur=stop] |
| 16 | A:0:4 / 2 [v1] |
| 17 | R / 1/2 [v1]; C:1:5 / 1/2 [v1]; C:1:5 / 1/2 [v1]; D:0:5 / 1/4 [v1] |
| 18 | E:0:5 / 2 [v1] |
| 19 | R / 1/2 [v1]; B:0:4 / 1/2 [v1]; B:0:4 / 1/2 [v1]; C:1:5 / 1/4 [v1] |
| 20 | D:0:5 / 2 [v1] |
| 21 | R / 1/2 [v1]; A:0:4 / 1/2 [v1, slur=start,start]; B:0:4 / 1/2 [v1, slur=start,stop]; G:1:4 / 1/4 [v1, slur=stop,stop] |
| 22 | A:0:4 / 1 [v1]; C:1:5 / 1 [v1, slur=start] |
| 23 | B:0:4 / 1 [v1, slur=start,stop]; A:0:4 / 1/2 [v1, slur=stop]; G:1:4 / 1/4 [v1] |
| 24 | A:0:4 / 2 [v1] |

## after_roundtrip

| Ô | Chuỗi ký hiệu: cao độ / trường độ (chấm, bè, nối) |
|---|---|
| 1 | R / 1/2 [v1]; A:0:4 / 1/2 [v1]; A:0:4 / 1/2 [v1]; R / 3/2 [v2] |
| 2 | C:1:5 / 1 [v1]; E:0:5 / 1 [v1] |
| 3 | C:1:5 / 1 [v1]; C:1:5 / 1/2 [v1, slur=start]; B:0:4 / 1/2 [v1] |
| 4 | C:1:5 / 2 [v1, slur=stop] |
| 5 | R / 1 [v1]; A:0:4 / 1/2 [v1, slur=start]; B:0:4 / 1/4 [v1, slur=stop] |
| 6 | C:1:5 / 1 [v1, slur=start]; A:0:4 / 1 [v1, slur=stop] |
| 7 | B:0:4 / 1/2 [v1]; C:1:5 / 1/4 [v1]; A:0:4 / 1/2 [v1]; G:1:4 / 1/4 [v1] |
| 8 | A:0:4 / 2 [v1] |
| 9 | R / 1/2 [v1]; A:0:4 / 1/2 [v1, tie=start]; A:0:4 / 1/2 [v1, slur=start,start,start, tie=stop]; B:0:4 / 1/4 [v1, slur=stop] |
| 10 | C:1:5 / 1 [v1, slur=stop,stop]; E:0:5 / 1 [v1, slur=start,start] |
| 11 | C:1:5 / 1 [v1, slur=stop,stop, tie=start]; C:1:5 / 1 [v1, tie=stop] |
| 12 | C:1:5 / 2 [v1] |
| 13 | R / 1 [v1]; A:0:4 / 1/2 [v1]; B:-1:4 / 1/4 [v1] |
| 14 | C:1:5 / 1 [v1]; A:0:4 / 1 [v1] |
| 15 | B:0:4 / 1/2 [v1, slur=start,start]; C:1:5 / 1/4 [v1, slur=stop]; A:0:4 / 1/2 [v1, slur=start,stop]; G:1:4 / 1/4 [v1, slur=stop] |
| 16 | A:0:4 / 2 [v1] |
| 17 | R / 1/2 [v1]; C:1:5 / 1/2 [v1]; C:1:5 / 1/2 [v1]; D:0:5 / 1/4 [v1] |
| 18 | E:0:5 / 2 [v1] |
| 19 | R / 1/2 [v1]; B:0:4 / 1/2 [v1]; B:0:4 / 1/2 [v1]; C:1:5 / 1/4 [v1] |
| 20 | D:0:5 / 2 [v1] |
| 21 | R / 1/2 [v1]; A:0:4 / 1/2 [v1, slur=start,start]; B:0:4 / 1/2 [v1, slur=start,stop]; G:1:4 / 1/4 [v1, slur=stop,stop] |
| 22 | A:0:4 / 1 [v1]; C:1:5 / 1 [v1, slur=start] |
| 23 | B:0:4 / 1 [v1, slur=start,stop]; A:0:4 / 1/2 [v1, slur=stop]; G:1:4 / 1/4 [v1] |
| 24 | A:0:4 / 2 [v1] |
