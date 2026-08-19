# TNSuite BridgeX

![Windows x64](https://img.shields.io/badge/Windows-x64-0078D4)
![Dark Mode](https://img.shields.io/badge/Dark%20Mode-Yes-111827)
![Free](https://img.shields.io/badge/Free-100%25-16A34A)
[![GPL v2](https://img.shields.io/badge/license-GPL%20v2-blue)](LICENSE)

**File transfer quen thuộc như FileZilla, nhưng có Dark Mode.**

BridgeX bắt đầu từ một nhu cầu rất đơn giản: tôi đã dùng FileZilla trong thời gian dài và quen với cách nó hoạt động, nhưng luôn khó chịu vì ứng dụng không có giao diện tối. Sau khi tìm khá nhiều mà vẫn không thấy một bản Dark Mode phù hợp để dùng hằng ngày, tôi quyết định tự build một bản cho mình.

Nếu bạn cũng thích FileZilla nhưng muốn một giao diện tối dễ chịu hơn, BridgeX được chia sẻ ở đây để bạn có thể dùng thử. **Dự án hoàn toàn miễn phí và mã nguồn mở.**

BridgeX được phát triển độc lập từ **FileZilla Client 3.70.6**. Đây không phải sản phẩm chính thức của FileZilla Project và không có liên kết chính thức với FileZilla Project.

## Tải xuống

Bản cài đặt chính thức sẽ được phát hành tại:

**[GitHub Releases →](https://github.com/kyousuke33/TNSuite-BridgeX/releases)**

Hiện repository chưa publish binary release đầu tiên. Baseline phát triển hiện tại là **v0.5 Build12-Hotfix16**.

Khi một bản release được phát hành, trang release sẽ kèm:

- file cài đặt Windows;
- bản portable nếu có;
- mã **SHA-256** để đối chiếu file;
- link **VirusTotal** của đúng file phát hành để người dùng có thể kiểm tra nhanh trước khi cài.

> Chỉ nên tải BridgeX từ trang Releases của repository này. Link VirusTotal sẽ được gắn theo từng release artifact thực tế, không dùng một badge “safe” chung cho mọi phiên bản.

## BridgeX có gì khác?

Mục tiêu của BridgeX không phải viết lại FileZilla thành một ứng dụng hoàn toàn khác. Tôi muốn giữ trải nghiệm quen thuộc mà mình đã dùng nhiều năm, đồng thời bổ sung những thứ tôi muốn có khi sử dụng hằng ngày.

| Tính năng | BridgeX |
| --- | --- |
| **Dark Mode** | Có |
| **Light Mode** | Có |
| **Ghi nhớ giao diện đã chọn** | Có |
| **Tiếng Anh** | Có |
| **Tiếng Việt** | Có |
| **SFTP / truyền tệp** | Có |
| **Windows x64** | Có |
| **Installer riêng** | Có |
| **Portable build** | Có |
| **CLI hỗ trợ automation** | Có, phạm vi giới hạn |

## Dark Mode

Dark Mode là lý do chính BridgeX tồn tại.

Thay vì thay đổi hoàn toàn cách sử dụng, BridgeX giữ hướng trải nghiệm quen thuộc của FileZilla nhưng bổ sung giao diện tối để dễ dùng hơn trong môi trường thiếu sáng hoặc khi phần lớn ứng dụng trên Windows đang chạy Dark Mode.

Bạn vẫn có thể chuyển lại **Light Mode** khi muốn. Lựa chọn giao diện được lưu lại để lần mở sau không phải thiết lập lại.

## Ngôn ngữ

BridgeX hỗ trợ:

- **English**;
- **Tiếng Việt**.

Ngôn ngữ đã chọn được lưu lại giữa các lần khởi động.

## Cài đặt

Khi release đầu tiên được publish:

1. mở **[Releases](https://github.com/kyousuke33/TNSuite-BridgeX/releases)**;
2. tải file cài đặt của phiên bản mới nhất;
3. nếu muốn kiểm tra trước khi chạy, đối chiếu SHA-256 và mở link VirusTotal trong release notes;
4. chạy installer và sử dụng BridgeX như một ứng dụng Windows thông thường.

Nếu không muốn cài đặt, hãy dùng bản portable khi release đó có cung cấp.

## Build từ source

Nếu bạn muốn tự build BridgeX thay vì tải binary:

```bash
git clone https://github.com/kyousuke33/TNSuite-BridgeX.git
cd TNSuite-BridgeX
```

Trên Windows, entry point đơn giản nhất là:

```bat
Build.cmd
```

Hoặc chạy trực tiếp PowerShell build orchestration:

```powershell
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File .\Build-TNSuiteBridgeX.ps1
```

Build hiện sử dụng **MSYS2 UCRT64** và **wxWidgets 3.3.3**. Script build được thiết kế để ưu tiên tái sử dụng môi trường isolated hiện có và chuẩn bị dependency còn thiếu khi cần.

## CLI

BridgeX có một CLI nhỏ phục vụ một số luồng automation/SFTP:

```bat
bin\BridgeX-CLI.exe --help
```

CLI này là phần mở rộng của BridgeX và có phạm vi giới hạn. BridgeX không tự nhận là một bản FileZilla CLI chính thức hay thương mại.

## Dành cho ai?

BridgeX có thể phù hợp nếu bạn:

- đã quen dùng FileZilla và không muốn đổi sang một client hoàn toàn khác;
- muốn có **Dark Mode**;
- muốn giao diện **tiếng Việt**;
- cần một bản Windows x64 có installer/portable rõ ràng;
- thích dùng phần mềm miễn phí và có thể xem source code.

Nếu FileZilla hiện tại đã đáp ứng đầy đủ nhu cầu của bạn, bạn không nhất thiết phải chuyển sang BridgeX.

## VirusTotal có cần thiết không?

Có — nhưng theo cách đơn giản.

Vì BridgeX là ứng dụng Windows được chia sẻ dưới dạng file thực thi, tôi muốn người dùng có thể nhìn vào release và kiểm tra nhanh file trước khi tải hoặc cài. Vì vậy mỗi binary release sẽ cố gắng cung cấp **link VirusTotal của chính artifact đó** cùng với SHA-256.

VirusTotal ở đây chỉ giúp người dùng có thêm một bước kiểm tra dễ thấy và dễ hiểu. Nó không thay thế việc tải file từ đúng nguồn hoặc đối chiếu hash.

## Miễn phí và mã nguồn mở

BridgeX được chia sẻ **miễn phí**.

Project được phát triển từ FileZilla Client và tuân theo **GNU General Public License v2 (GPL v2)**. Xem [`LICENSE`](LICENSE) và [`NOTICE.md`](NOTICE.md) để biết thông tin license/attribution đầy đủ.

Không có bản “Pro”, không khóa Dark Mode sau paywall và không yêu cầu trả phí để dùng các tính năng được phát hành trong repository này.

## Đóng góp

Nếu bạn gặp lỗi, có ý tưởng cải thiện giao diện hoặc muốn đóng góp code:

- mở một [Issue](https://github.com/kyousuke33/TNSuite-BridgeX/issues);
- gửi Pull Request;
- xem [`CONTRIBUTING.md`](CONTRIBUTING.md) nếu bạn muốn tham gia phát triển.

Các bug cụ thể nên được ghi ở Issues thay vì làm README ngày càng dài.

## Credits

BridgeX được phát triển dựa trên **FileZilla Client 3.70.6** và sử dụng các thành phần mã nguồn mở theo license tương ứng.

- FileZilla Project: nguồn gốc upstream của phần client core;
- wxWidgets: UI framework;
- MSYS2 / MinGW-w64: Windows build environment;
- NSIS: Windows installer tooling.

BridgeX là một fork/rebrand độc lập được làm ra trước hết vì nhu cầu sử dụng cá nhân, sau đó được chia sẻ lại cho cộng đồng nếu có người cần cùng một thứ: **một trải nghiệm FileZilla quen thuộc nhưng có Dark Mode.**
