# TNSuite BridgeX

TNSuite BridgeX là ứng dụng desktop truyền tệp an toàn dành cho **Windows x64**, được phát triển độc lập từ nền tảng **FileZilla Client 3.70.6** và điều chỉnh cho hệ sinh thái TNSuite.

README này là **điểm vào của repository**: giúp người mới hiểu nhanh project là gì, phạm vi ở đâu, cách chuẩn bị môi trường, chạy QA/build và cần đọc tài liệu nào tiếp theo. README **không phải** runtime evidence, release evidence hoặc source of truth duy nhất cho trạng thái hiện tại của sản phẩm.

## 1. Tổng quan project

| Thuộc tính | Giá trị |
| --- | --- |
| Project | TNSuite BridgeX |
| Loại sản phẩm | Ứng dụng desktop truyền tệp an toàn |
| Nền tảng | Windows x64 |
| Baseline hiện tại | `v0.5 Build12-Hotfix16` |
| Nền tảng upstream | FileZilla Client 3.70.6 |
| UI framework | wxWidgets 3.3.3 |
| Build environment | MSYS2 UCRT64 |
| Source authority | Nhánh `main` của repository này |
| Database | Không áp dụng cho baseline hiện tại |

Trạng thái kỹ thuật, CI, release và các capability đã/ chưa được chứng minh phải đọc tại [`docs/90_GOVERNANCE/CURRENT_STATE.md`](docs/90_GOVERNANCE/CURRENT_STATE.md).

## 2. Mục đích

BridgeX cung cấp một client desktop cho các luồng truyền tệp an toàn, với branding và trải nghiệm phù hợp TNSuite. Baseline hiện tại bao gồm giao diện BridgeX, Light/Dark mode, giao diện tiếng Anh/tiếng Việt, SFTP/transfer, installer Windows và CLI automation có phạm vi giới hạn.

Mục tiêu của repository này là duy trì **canonical source**, build tooling, QA contracts và governance cho BridgeX; không dùng repository như nơi lưu các binary build tạm, secret, signing key hoặc runtime evidence không được kiểm soát.

## 3. Product boundary

BridgeX là một sản phẩm **độc lập**. Project được phát triển dựa trên FileZilla Client 3.70.6 nhưng **không phải sản phẩm chính thức của FileZilla Project**, không được mô tả là FileZilla thương mại/chính thức và không được làm mất attribution hoặc nghĩa vụ license của upstream.

Phạm vi baseline hiện tại:

- ứng dụng GUI Windows x64;
- truyền tệp/SFTP theo capability hiện có của BridgeX;
- Light/Dark mode;
- giao diện EN/VI và persistence tương ứng;
- CLI automation có phạm vi giới hạn;
- installer Windows, Start Menu và uninstall lifecycle;
- source/static regression gates phục vụ Governed Agentic Engineering.

Các capability tương lai như auto-update, signed update manifest hoặc production distribution chỉ được xem là hoạt động khi có authority và evidence tương ứng. Xem [`CURRENT_STATE.md`](docs/90_GOVERNANCE/CURRENT_STATE.md) và [`ROADMAP.md`](docs/00_PRODUCT/ROADMAP.md).

## 4. Phiên bản hiện tại

Baseline source được chấp nhận hiện tại:

```text
v0.5 Build12-Hotfix16
```

Baseline này được pin bằng manifest machine-verifiable tại:

[`/.release/build12-hotfix16-source-manifest.sha256`](.release/build12-hotfix16-source-manifest.sha256)

Lịch sử thay đổi xem tại [`CHANGELOG.md`](CHANGELOG.md).

## 5. Technology stack

| Thành phần | Công nghệ / vai trò |
| --- | --- |
| Desktop core | C++ / codebase phát triển từ FileZilla Client 3.70.6 |
| UI | wxWidgets 3.3.3 |
| Target | Windows x64 |
| Toolchain | MSYS2 UCRT64 |
| Build orchestration | PowerShell + Bash |
| Installer | NSIS |
| CLI | BridgeX CLI + Windows OpenSSH/SFTP integration |
| Source/static QA | Python + shell checks |
| CI cho public PR | GitHub-hosted runner |

Project hiện không có backend service, web runtime hay database application cần khởi động để phát triển baseline desktop này.

## 6. Kiến trúc tổng quan

Ở mức cao, repository gồm các lớp sau:

```text
Upstream-derived desktop core
        ↓
BridgeX patches / product customizations
        ↓
Branding + locale + GUI/CLI behavior
        ↓
Windows build pipeline
        ↓
Portable artifact + NSIS installer
        ↓
QA / release / governance gates
```

README chỉ mô tả kiến trúc ở mức định hướng. Kiến trúc chi tiết, module, dependency, data flow và integration nằm trong [`docs/10_ARCHITECTURE/`](docs/10_ARCHITECTURE/).

## 7. Cấu trúc repository

Các khu vực quan trọng:

```text
.
├── AGENTS.md                  # Luật dành cho AI/coding agent
├── README.md                  # Entry point và quick-start
├── CHANGELOG.md               # Lịch sử thay đổi
├── CONTRIBUTING.md            # Quy trình đóng góp
├── Build.cmd                  # Entry point build Windows thuận tiện
├── Build-TNSuiteBridgeX.ps1   # Build orchestration chính trên Windows
├── .release/                  # Source manifest và release/source gates
├── assets/                    # Branding/build assets được quản lý
├── cli/                       # BridgeX CLI
├── installer/                 # NSIS installer source
├── locales/                   # Locale resources
├── patches/                   # BridgeX/upstream patch set
├── qa/                        # Regression/source QA
├── scripts/                   # Build và QA helper scripts
└── docs/                      # Product/architecture/security/quality/release/governance docs
```

Generated installer, portable archive, object/cache tree và transient QA evidence không phải canonical source và không nên commit vào repository.

## 8. Yêu cầu môi trường

Để build baseline hiện tại:

- Windows 64-bit;
- PowerShell;
- quyền chạy script/build tool cần thiết trên máy local;
- kết nối mạng khi build environment cần tải MSYS2/dependency;
- Windows OpenSSH Client có `sftp.exe` để hoàn tất CLI runtime doctor trong build pipeline;
- Git để clone và làm việc theo branch/PR flow.

Build script quản lý isolated MSYS2 environment và sử dụng UCRT64. Dependency/build authority chi tiết xem [`docs/10_ARCHITECTURE/DEPENDENCIES.md`](docs/10_ARCHITECTURE/DEPENDENCIES.md).

## 9. Bắt đầu làm việc

Clone repository:

```bash
git clone https://github.com/kyousuke33/TNSuite-BridgeX.git
cd TNSuite-BridgeX
```

Trước khi sửa source, CI, security hoặc release behavior, đọc tối thiểu:

1. [`AGENTS.md`](AGENTS.md)
2. [`docs/90_GOVERNANCE/CURRENT_STATE.md`](docs/90_GOVERNANCE/CURRENT_STATE.md)
3. tài liệu authority tương ứng với phần chuẩn bị thay đổi.

Không dùng README để suy ra rằng một capability runtime/release đã PASS nếu `CURRENT_STATE.md`, QA evidence hoặc release contract chưa chứng minh điều đó.

## 10. Configuration

Baseline hiện tại không dùng `.env` application kiểu web/backend làm nguồn cấu hình runtime chung.

Nguyên tắc:

- không commit password, private key, token, signing key hoặc credential;
- không đưa production/staging/internal TNSuite secret vào public CI;
- build-time environment variable chỉ được dùng theo build tooling đã quản lý;
- thay đổi cấu hình có ảnh hưởng security/release phải đọc [`docs/50_SECURITY/`](docs/50_SECURITY/) và [`docs/80_RELEASE/`](docs/80_RELEASE/).

Chi tiết về secret handling xem [`docs/50_SECURITY/SECRETS.md`](docs/50_SECURITY/SECRETS.md).

## 11. Development workflow

BridgeX dùng Governed Agentic Engineering flow:

```text
Work Item
→ short-lived branch
→ source/local QA
→ commit/push
→ Pull Request
→ required CI
→ merge exact green head
→ governed artifact/release flow khi áp dụng
```

Không sửa trực tiếp `main` cho engineering change thông thường. Không force-push để vượt qua review/CI state. Quy tắc dành cho agent nằm trong [`AGENTS.md`](AGENTS.md); quy trình đóng góp nằm trong [`CONTRIBUTING.md`](CONTRIBUTING.md).

Vì repository là public, untrusted PR/fork code chỉ được chạy trên **GitHub-hosted infrastructure**; không được route sang shared `tn-ci-01`.

## 12. QA / Validation

Source/static regression gate chính:

```bash
bash .release/source-gates.sh
```

Gate này xác minh exact source manifest và chạy regression/source checks tương ứng với baseline Build12-Hotfix16.

Tài liệu QA:

- [`docs/60_QUALITY/TESTING.md`](docs/60_QUALITY/TESTING.md)
- [`docs/60_QUALITY/QA_MATRIX.md`](docs/60_QUALITY/QA_MATRIX.md)
- [`docs/60_QUALITY/REGRESSION.md`](docs/60_QUALITY/REGRESSION.md)
- [`docs/60_QUALITY/ACCEPTANCE_CRITERIA.md`](docs/60_QUALITY/ACCEPTANCE_CRITERIA.md)

**Lưu ý:** source/static QA PASS không đồng nghĩa Windows compile, installer runtime hoặc GUI runtime PASS. Mỗi lớp acceptance cần evidence đúng loại của nó.

## 13. Build

Trên Windows, entry point thuận tiện:

```bat
Build.cmd
```

Hoặc chạy build orchestration trực tiếp:

```powershell
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File .\Build-TNSuiteBridgeX.ps1
```

Build pipeline sẽ chuẩn bị hoặc tái sử dụng isolated MSYS2, chạy UCRT64 build, tạo portable ZIP và NSIS setup trong `dist/`, sau đó thực hiện các verification được định nghĩa trong build script.

Artifact sinh ra từ local build **không tự động trở thành release được phê duyệt**. Build/release authority nằm trong [`docs/80_RELEASE/`](docs/80_RELEASE/).

## 14. Cài đặt, phát hành và phân phối

Repository này là **source authority**, không phải download page cho binary chưa được kiểm chứng.

Đối với release chính thức, artifact phải đi qua build, verification và release flow tương ứng trước khi được phân phối. Không coi việc tạo được file `Setup.exe` hoặc ZIP trên một máy local là production release.

Tài liệu liên quan:

- [`docs/80_RELEASE/RELEASE.md`](docs/80_RELEASE/RELEASE.md)
- [`docs/80_RELEASE/DEPLOYMENT.md`](docs/80_RELEASE/DEPLOYMENT.md)
- [`docs/80_RELEASE/ENVIRONMENTS.md`](docs/80_RELEASE/ENVIRONMENTS.md)
- [`docs/80_RELEASE/ROLLBACK.md`](docs/80_RELEASE/ROLLBACK.md)

Trạng thái distribution/signing/auto-update hiện tại phải lấy từ [`CURRENT_STATE.md`](docs/90_GOVERNANCE/CURRENT_STATE.md), không lấy từ README.

## 15. Documentation map

| Khu vực | Nội dung authority |
| --- | --- |
| [`AGENTS.md`](AGENTS.md) | Luật làm việc cho AI/coding agent |
| [`docs/00_PRODUCT/`](docs/00_PRODUCT/) | Product definition, requirements, glossary, roadmap |
| [`docs/10_ARCHITECTURE/`](docs/10_ARCHITECTURE/) | Architecture, module, dependency, integration, data flow |
| [`docs/20_DATA/`](docs/20_DATA/) | Data/database authority khi áp dụng |
| [`docs/30_API/`](docs/30_API/) | API/contracts khi áp dụng |
| [`docs/40_UI/`](docs/40_UI/) | UI/UX authority |
| [`docs/50_SECURITY/`](docs/50_SECURITY/) | Security, secrets, threat model, security testing |
| [`docs/60_QUALITY/`](docs/60_QUALITY/) | Testing, QA matrix, regression, acceptance |
| [`docs/70_OPERATIONS/`](docs/70_OPERATIONS/) | Operations, observability, incident/recovery |
| [`docs/80_RELEASE/`](docs/80_RELEASE/) | Build/release/deployment/rollback authority |
| [`docs/90_GOVERNANCE/`](docs/90_GOVERNANCE/) | Current state, decisions, known issues, tech debt, AI governance |
| [`docs/adr/`](docs/adr/) | Architecture Decision Records |
| [`CHANGELOG.md`](CHANGELOG.md) | Lịch sử thay đổi |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Cách đóng góp/thay đổi repository |

## 16. Authority map

README là **orientation document**, không phải authority cao nhất cho mọi thông tin.

Khi cần quyết định hoặc xác minh một vấn đề, dùng đúng nguồn:

```text
Luật agent / engineering        → AGENTS.md
Product scope / requirement     → docs/00_PRODUCT/
Architecture / dependency       → docs/10_ARCHITECTURE/
Security                        → docs/50_SECURITY/
QA / acceptance                 → docs/60_QUALITY/
Build / release / rollback      → docs/80_RELEASE/
Trạng thái thực tế hiện tại     → docs/90_GOVERNANCE/CURRENT_STATE.md
Exact source baseline           → .release/*manifest* + machine-verifiable gates
Lịch sử thay đổi                → CHANGELOG.md
Định hướng ban đầu              → README.md
```

Central TNSuite/RCP authority và repository governance được áp dụng theo [`AGENTS.md`](AGENTS.md). Nếu README khác với authority/evidence chuyên biệt, **không dùng README để override authority đó**.

## 17. Security notes

Các nguyên tắc tối thiểu:

- không commit secret, credential hoặc signing private key;
- không nhúng secret vào desktop client;
- public PR/fork không được chạy trên shared trusted TNSuite self-hosted CI;
- không đưa generated installer, portable package, cache hoặc transient runtime evidence vào canonical source;
- artifact verification phải fail closed trước khi artifact được xem là hợp lệ cho release flow.

Security authority đầy đủ: [`docs/50_SECURITY/SECURITY.md`](docs/50_SECURITY/SECURITY.md).

## 18. Known limitations / Current state

README không duy trì danh sách bug hoặc evidence dài để tránh documentation drift.

Đọc:

- [`docs/90_GOVERNANCE/CURRENT_STATE.md`](docs/90_GOVERNANCE/CURRENT_STATE.md) — trạng thái hiện tại;
- [`docs/90_GOVERNANCE/KNOWN_ISSUES.md`](docs/90_GOVERNANCE/KNOWN_ISSUES.md) — vấn đề đã biết;
- [`docs/90_GOVERNANCE/TECH_DEBT.md`](docs/90_GOVERNANCE/TECH_DEBT.md) — technical debt;
- [`docs/00_PRODUCT/ROADMAP.md`](docs/00_PRODUCT/ROADMAP.md) — hướng phát triển.

## 19. License / Copyright

BridgeX giữ các nghĩa vụ attribution/licensing áp dụng từ upstream và các thành phần liên quan.

Xem:

- [`LICENSE`](LICENSE)
- [`COPYING`](COPYING)
- [`NOTICE.md`](NOTICE.md)

TNSuite BridgeX không liên kết, không được bảo trợ và không được chứng thực bởi FileZilla Project.