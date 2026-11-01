# Hướng dẫn tạo tài khoản kie.ai và lấy API key

kie.ai là trang bán lại nhiều mô hình AI (tạo ảnh, giọng đọc, nhạc) với giá rẻ, trả tiền theo lượt dùng.
Skill `video-ve-tay` cần **1 API key** của kie.ai.

## Bước 1 – Đăng ký
1. Mở trình duyệt, vào **https://kie.ai**
2. Bấm **Sign in / Get started** (góc trên bên phải).
3. Chọn **Continue with Google** → chọn Gmail của bạn. (Hoặc đăng ký bằng email + mật khẩu.)

## Bước 2 – Nạp tiền (tối thiểu khoảng 5 USD)
1. Bấm vào ảnh đại diện / **Billing** (hoặc **Credits**, **Top up**).
2. Chọn gói nhỏ nhất (~5 USD), thanh toán bằng thẻ Visa/Mastercard.
   - Thẻ ghi nợ quốc tế của ngân hàng Việt Nam (VCB, TCB, MB…) thường dùng được; cần bật thanh toán trực tuyến/quốc tế trên app ngân hàng.
3. 5 USD đủ làm khoảng 6–15 video ngắn để thử.

## Bước 3 – Tạo API key
1. Vào mục **API Key** (menu bên trái hoặc trong trang tài khoản).
2. Bấm **Create / New API Key**, đặt tên dễ nhớ (vd. `kcp-video`), thời hạn: tuỳ chọn (có thể "Never expire").
3. Bấm **Copy** để sao chép key.

⚠️ **Giữ bí mật key** – ai có key sẽ dùng được tiền trong tài khoản của bạn. Không dán key vào email, Zalo, GitHub.
Nếu lỡ để lộ: vào lại mục API Key → xoá key cũ → tạo key mới.

## Bước 4 – Đưa key cho Claude dùng
**Cách A – Làm trên máy tính (Claude Code desktop):**
1. Trong thư mục dự án, copy file `.env.example` thành `.env`.
2. Mở `.env`, thay `dan_api_key_vao_day` bằng key vừa copy → lưu lại.
   File `.env` đã được chặn không đưa lên GitHub.

**Cách B – Làm trên Claude Code web/điện thoại (phiên chạy trên cloud):**
1. Vào cài đặt **Environment** của phiên → mục **Environment variables / Secrets**.
2. Thêm biến tên `KIE_API_KEY`, giá trị là key của bạn.
3. Trong **Network access**, cho phép các tên miền: `api.kie.ai`, `kie.ai`, `docs.kie.ai`, và nơi tải file kết quả (thường là `tempfile.aiquickdraw.com`, `*.redpandaai.co` – nếu báo lỗi tải file, Claude sẽ cho biết tên miền cần thêm).
4. Mở phiên mới để cài đặt có hiệu lực.

## Bước 5 – Kiểm tra
Nói với Claude: **"kiểm tra API key kie.ai"** – Claude sẽ chạy
`python3 .claude/skills/video-ve-tay/scripts/kie_client.py check`.
