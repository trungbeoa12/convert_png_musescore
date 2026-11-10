#!/bin/zsh
cd "$(dirname "$0")" || exit 1
if [[ ! -x .venv/bin/python ]]; then
  echo 'Chưa có môi trường Python. Xem README.md để cài đặt.'
  read '?Nhấn Enter để đóng.'
  exit 1
fi
./.venv/bin/python app.py
if [[ $? -ne 0 ]]; then
  read '?Ứng dụng gặp lỗi. Nhấn Enter để đóng.'
fi
