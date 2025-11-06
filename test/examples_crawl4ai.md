# Hướng dẫn nhanh — examples_crawl4ai.py

Tệp này mô tả ngắn gọn mục đích của 9 ví dụ trong `examples_crawl4ai.py` và cách chạy từ dòng lệnh.

## Mục đích chung
Mỗi ví dụ là một hàm độc lập (1–9) minh hoạ các tính năng cơ bản của Crawl4AI / Playwright:
- Kiểm tra cài đặt
- Kiểm tra Playwright
- Crawl cơ bản
- Xử lý nội dung động
- Sinh và lọc Markdown
- Phân tích liên kết
- Trích xuất media
- Hook tuỳ chỉnh
- Chiến lược trích xuất (Json/CSS)

## Danh sách ví dụ (1–9)
1. example_1_check_installation  
   - Kiểm tra xem `crawl4ai` có import được không, in phiên bản nếu có, in hướng dẫn cài đặt khi thiếu.

2. example_2_test_browser  
   - Dùng Playwright (chromium headless) mở `https://example.com` và in title trang — kiểm tra tích hợp trình duyệt.

3. example_3_simple_crawl  
   - Crawl trang đơn giản (`https://www.example.com`) bằng `AsyncWebCrawler`. In một đoạn markdown nếu có, hoặc HTML/raw nếu không.

4. example_4_dynamic_content  
   - Ví dụ xử lý nội dung động bằng cách chèn `js_code` (ví dụ click nút "Load More") rồi crawl trang có nội dung tải động.

5. example_5_clean_content  
   - Dùng `DefaultMarkdownGenerator` + `PruningContentFilter` để sinh `raw_markdown` (full) và `fit_markdown` (đã thu gọn). Lưu `cleaned_full.md` và `cleaned_fit.md`. Nếu `fit_markdown` rỗng, script tạo fallback cắt ngắn từ `full`.

6. example_6_link_analysis  
   - Crawl và thu thập liên kết (internal / external). In số lượng và một vài link mẫu.

7. example_7_media_handling  
   - Trích xuất media (images) từ kết quả crawl, in `src`, `alt`, `score` (nếu có) cho vài ảnh đầu.

8. example_8_hooks  
   - Ví dụ hook `before_goto` (đặt header tuỳ chỉnh, log). Gắn hook nếu crawler hỗ trợ và chạy crawl minh hoạ.

9. example_9_extraction_demo  
   - Dùng `JsonCssExtractionStrategy` với một schema đơn giản để trích xuất cấu trúc từ HTML (ví dụ title).

## Cách chạy
- Liệt kê ví dụ:
  - Windows (cmd/PowerShell):
    - python test\examples_crawl4ai.py --list
- Chạy ví dụ N (1..9):
  - python test\examples_crawl4ai.py --example N
- Chạy tương tác:
  - python test\examples_crawl4ai.py
  - Sau đó nhập số ví dụ khi được nhắc.

## Ghi chú
- Cần cài `crawl4ai` và `playwright` để chạy đầy đủ chức năng:
  - pip install "crawl4ai[playwright]"
  - pip install playwright
  - playwright install --with-deps chromium
- Nếu `fit_markdown` bằng 0, nguyên nhân thông thường:
  - Cấu hình bộ lọc/threshold loại bỏ nội dung khi tạo "fit".
  - Markdown generator không tạo phiên bản `fit` cho trang đó.
  - Phiên bản thư viện thay đổi hành vi.
  - Kiểm tra debug output in ra khi chạy ví dụ 5 để biết chi tiết.

Nếu cần, có thể mở rộng README này bằng các ví dụ cấu hình (thay threshold, dùng session, v.v.).