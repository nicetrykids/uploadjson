import webview
import os
from api import ComicAPI

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_PATH = os.path.join(BASE_DIR, 'managermentTruyen', 'dist', 'index.html')

if not os.path.exists(HTML_PATH):
    raise FileNotFoundError(f'Không tìm thấy file giao diện: {HTML_PATH}')

api = ComicAPI()

# Tạo cửa sổ pywebview
webview.create_window(
    'Truyen Managerment',
    HTML_PATH,
    js_api=api,
    width=1600,
    height=900,
    min_size=(1200, 800),
    confirm_close=True
)

webview.start(debug=True)