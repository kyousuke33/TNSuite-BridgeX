# TNSuite BridgeX

[![Governance CI](https://github.com/kyousuke33/TNSuite-BridgeX/actions/workflows/governance-gates.yml/badge.svg)](https://github.com/kyousuke33/TNSuite-BridgeX/actions/workflows/governance-gates.yml)
![Windows x64](https://img.shields.io/badge/Windows-x64-0078D4)
![Baseline](https://img.shields.io/badge/baseline-v0.5%20Build12--Hotfix16-4C8BF5)
[![GPL v2](https://img.shields.io/badge/license-GPL%20v2-blue)](LICENSE)

**TNSuite BridgeX** là ứng dụng desktop truyền tệp/SFTP cho Windows x64, có giao diện Light/Dark, tiếng Anh/tiếng Việt, installer riêng và CLI automation có phạm vi giới hạn.

BridgeX được phát triển độc lập từ **FileZilla Client 3.70.6**. Đây **không phải sản phẩm chính thức của FileZilla Project** và không được đại diện như một bản FileZilla thương mại/chính thức.

**Đi nhanh:** [Tải xuống](#tải-xuống) · [An toàn & xác minh](#an-toàn-và-xác-minh) · [Tính năng](#tính-năng-chính) · [Bắt đầu](#bắt-đầu-nhanh) · [Build](#build-trên-windows) · [QA](#qa-và-ci) · [Tài liệu](#tài-liệu-project)

> README là tài liệu định hướng và quick-start. Trạng thái kỹ thuật thực tế, QA, release và các capability đã được chứng minh nằm trong [`docs/90_GOVERNANCE/CURRENT_STATE.md`](docs/90_GOVERNANCE/CURRENT_STATE.md) cùng authority tương ứng.

## Tải xuống

Kênh phân phối binary chính thức của BridgeX là **[GitHub Releases](https://github.com/kyousuke33/TNSuite-BridgeX/releases)**.

Hiện GitHub Releases **chưa có bản phát hành nhị phân cho Windows**. `v0.5 Build12-Hotfix16` là baseline source/build đã được chấp nhận; không nên hiểu đây là một GitHub Release đã được phát hành.

| Kênh | Trạng thái | Mục đích |
| --- | --- | --- |
| [`main`](https://github.com/kyousuke33/TNSuite-BridgeX) | Canonical | Source, build tooling, QA và governance |
| [GitHub Releases](https://github.com/kyousuke33/TNSuite-BridgeX/releases) | Chưa có binary release | Installer/portable artifact đã qua release gate |
| GitHub Packages | Không sử dụng | Hiện chưa có nhu cầu phát hành qua registry như npm, NuGet hoặc container |

Khi release chính thức được publish, release notes phải chỉ rõ artifact, SHA-256 và bằng chứng xác minh tương ứng. Không nên tải installer từ nguồn bên thứ ba nếu không đối chiếu được với release chính thức.

## An toàn và xác minh

Với một ứng dụng Windows có file thực thi, badge CI hoặc tên file không đủ để xác minh độ tin cậy. Mỗi release nên có tối thiểu:

- **SHA-256** của installer và portable archive;
- exact source/tag dùng để build;
- trạng thái build/release gate;
- **VirusTotal report** cho từng artifact khi report đó thực sự tồn tại.

VirusTotal là một **tín hiệu bổ sung**, không phải chứng nhận tuyệt đối rằng file an toàn. Antivirus có thể false-positive; ngược lại, một report sạch cũng không thay thế source review, hash verification và release governance.

BridgeX không hiển thị badge kiểu “VirusTotal: Safe” khi chưa có artifact/report cụ thể. Khi có release đầu tiên, link VirusTotal nên đặt ngay trong release notes, cạnh SHA-256 của đúng file được quét.

Public pull request và fork PR của repository này chỉ chạy trên **GitHub-hosted infrastructure**. Shared runner `tn-ci-01` không nằm trong execution path của public contributor code.

## Tính năng chính

| Khả năng | Mô tả |
| --- | --- |
| **Desktop GUI** | Client truyền tệp dành cho Windows x64 |
| **SFTP / transfer** | Luồng truyền tệp theo capability hiện có của BridgeX |
| **Light / Dark** | Giao diện sáng/tối với persistence |
| **EN / VI** | Giao diện tiếng Anh và tiếng Việt |
| **CLI automation** | CLI có phạm vi giới hạn cho các luồng automation/SFTP |
| **Windows installer** | NSIS setup, Start Menu và uninstall lifecycle |
| **Portable build** | Build pipeline tạo portable ZIP cùng installer |
| **Governed QA** | Exact source manifest, regression gates và protected `main` |

Product scope và requirement chi tiết: [`docs/00_PRODUCT/`](docs/00_PRODUCT/).

## Bắt đầu nhanh

### Dành cho người dùng

Khi có release chính thức:

1. mở trang **[Releases](https://github.com/kyousuke33/TNSuite-BridgeX/releases)**;
2. tải installer hoặc portable archive của release cần dùng;
3. đối chiếu SHA-256 trong release notes;
4. mở VirusTotal report của **đúng artifact** nếu release có cung cấp;
5. cài đặt/chạy BridgeX từ artifact đã xác minh.

Cho tới khi GitHub Releases có binary được publish, repository này nên được xem là **source distribution**, không phải trang tải executable chính thức.

### Dành cho developer / contributor

```bash
git clone https://github.com/kyousuke33/TNSuite-BridgeX.git
cd TNSuite-BridgeX
```

Trước khi sửa source, CI, security hoặc release behavior, đọc tối thiểu:

1. [`AGENTS.md`](AGENTS.md)
2. [`docs/90_GOVERNANCE/CURRENT_STATE.md`](docs/90_GOVERNANCE/CURRENT_STATE.md)
3. authority docs của khu vực chuẩn bị thay đổi.

## Yêu cầu build

Baseline hiện tại cần:

- Windows 64-bit;
- PowerShell;
- Git;
- kết nối mạng khi build environment cần tải MSYS2/dependency;
- Windows OpenSSH Client có `sftp.exe` cho CLI runtime doctor;
- MSYS2 UCRT64 / wxWidgets 3.3.3 theo build tooling của project.

Build script quản lý isolated MSYS2 environment; compiler tree, cache và generated artifact không được commit vào canonical source.

Dependency authority: [`docs/10_ARCHITECTURE/DEPENDENCIES.md`](docs/10_ARCHITECTURE/DEPENDENCIES.md).

## Build trên Windows

Cách đơn giản nhất:

```bat
Build.cmd
```

Hoặc gọi PowerShell orchestration trực tiếp:

```powershell
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File .\Build-TNSuiteBridgeX.ps1
```

Build pipeline chuẩn bị hoặc tái sử dụng isolated MSYS2 UCRT64, build BridgeX, tạo portable ZIP và NSIS installer trong `dist/`, rồi chạy các verification được định nghĩa trong build script.

Một máy local tạo được `.zip` hoặc `Setup.exe` **không có nghĩa artifact đó đã trở thành release chính thức**. Publication phải đi qua release authority tại [`docs/80_RELEASE/`](docs/80_RELEASE/).

## CLI

Sau khi có build artifact:

```bat
bin\BridgeX-CLI.exe --help
```

CLI là capability automation có phạm vi giới hạn; không được mô tả như một “FileZilla commercial CLI” hoặc capability upstream chính thức.

## QA và CI

Source/static regression gate chính:

```bash
bash .release/source-gates.sh
```

Gate xác minh exact source manifest của Build12-Hotfix16 và chạy các regression/source checks tương ứng.

Public PR CI chạy bằng **GitHub-hosted runner**. Workflow không được route untrusted PR/fork code sang shared TNSuite self-hosted infrastructure.

Tài liệu QA:

- [`docs/60_QUALITY/TESTING.md`](docs/60_QUALITY/TESTING.md)
- [`docs/60_QUALITY/QA_MATRIX.md`](docs/60_QUALITY/QA_MATRIX.md)
- [`docs/60_QUALITY/REGRESSION.md`](docs/60_QUALITY/REGRESSION.md)
- [`docs/60_QUALITY/ACCEPTANCE_CRITERIA.md`](docs/60_QUALITY/ACCEPTANCE_CRITERIA.md)

**Source/static QA PASS không đồng nghĩa Windows compile, installer runtime hoặc GUI runtime PASS.** Mỗi lớp acceptance cần đúng loại evidence của nó.

## Kiến trúc tổng quan

```text
Core phát triển từ FileZilla Client 3.70.6
        ↓
Patch và tùy biến sản phẩm BridgeX
        ↓
Branding + locale + hành vi GUI/CLI
        ↓
Windows build pipeline
        ↓
Portable ZIP + NSIS installer
        ↓
QA / release / governance gates
```

README chỉ giữ sơ đồ ở mức định hướng. Module, dependency, integration và data flow chi tiết nằm trong [`docs/10_ARCHITECTURE/`](docs/10_ARCHITECTURE/).

## Cấu trúc repository

```text
.
├── AGENTS.md                  # Luật dành cho AI/coding agent
├── README.md                  # Entry point cho người đọc
├── CHANGELOG.md               # Lịch sử thay đổi
├── CONTRIBUTING.md            # Quy trình đóng góp
├── Build.cmd                  # Windows build entry point
├── Build-TNSuiteBridgeX.ps1   # Build orchestration
├── .release/                  # Source manifest và release/source gates
├── assets/                    # Branding/build assets
├── cli/                       # BridgeX CLI
├── installer/                 # NSIS installer source
├── locales/                   # Locale resources
├── patches/                   # Patch set
├── qa/                        # Source/regression QA
├── scripts/                   # Build/QA helpers
├── skills/                    # Project-local agent skills
└── docs/                      # Product → governance authority docs
```

Generated installer, portable archive, object/cache tree và transient QA evidence không phải canonical source.

## Skill cho agent

Project-local skills nằm trong [`skills/`](skills/).

Repository có thêm [`skills/clean-user-facing-text/`](skills/clean-user-facing-text/) để làm final text-hygiene pass cho nội dung người dùng sở hữu hoặc được phép chỉnh sửa.

Skill được vendor từ `guillaumemeyer/watermarks-remover`, pin tại upstream commit:

```text
1cc278342ea9d9d2a78dd2768def20df279f4b7b
```

Provenance và MIT license được giữ ngay trong subtree của skill. Skill không thay đổi license của BridgeX core và không được dùng để tuyên bố chắc chắn rằng văn bản do con người viết hoặc “không thể bị phát hiện là AI”.

## Development workflow

```text
Work Item
→ short-lived branch
→ source/local QA
→ commit/push
→ Pull Request
→ required GitHub-hosted CI
→ merge exact green head
→ governed artifact/release flow khi áp dụng
```

Không sửa trực tiếp `main` cho engineering change thông thường. Không force-push hoặc bypass required checks để tạo trạng thái green giả.

Xem [`AGENTS.md`](AGENTS.md) và [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Tài liệu project

| Khu vực | Nội dung |
| --- | --- |
| [`AGENTS.md`](AGENTS.md) | Luật làm việc cho AI/coding agent |
| [`docs/00_PRODUCT/`](docs/00_PRODUCT/) | Product definition, requirements, roadmap |
| [`docs/10_ARCHITECTURE/`](docs/10_ARCHITECTURE/) | Architecture, dependency, integration, data flow |
| [`docs/20_DATA/`](docs/20_DATA/) | Data/database authority khi áp dụng |
| [`docs/30_API/`](docs/30_API/) | API/contracts khi áp dụng |
| [`docs/40_UI/`](docs/40_UI/) | UI/UX authority |
| [`docs/50_SECURITY/`](docs/50_SECURITY/) | Security, secrets, threat model, security testing |
| [`docs/60_QUALITY/`](docs/60_QUALITY/) | Testing, regression và acceptance |
| [`docs/70_OPERATIONS/`](docs/70_OPERATIONS/) | Operations, observability, incident/recovery |
| [`docs/80_RELEASE/`](docs/80_RELEASE/) | Release, deployment và rollback |
| [`docs/90_GOVERNANCE/`](docs/90_GOVERNANCE/) | Current state, decisions, known issues, tech debt |
| [`docs/adr/`](docs/adr/) | Architecture Decision Records |
| [`skills/`](skills/) | Project-local agent skills |
| [`CHANGELOG.md`](CHANGELOG.md) | Lịch sử thay đổi |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Cách đóng góp vào repository |

## Authority map

README giúp định hướng; khi cần quyết định hoặc xác minh, dùng đúng authority:

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

Nếu README khác với authority/evidence chuyên biệt, không dùng README để override nguồn chuyên biệt đó.

## Security

Nguyên tắc tối thiểu:

- không commit password, token, private key hoặc signing key;
- không nhúng secret vào desktop client;
- public PR/fork không chạy trên shared trusted TNSuite self-hosted CI;
- không đưa generated installer, portable package, cache hoặc transient runtime evidence vào canonical source;
- artifact verification phải fail closed trước khi artifact được xem là hợp lệ cho release flow.

Security authority: [`docs/50_SECURITY/SECURITY.md`](docs/50_SECURITY/SECURITY.md).

## Trạng thái hiện tại và known limitations

README không giữ danh sách bug/evidence dài để tránh documentation drift. Xem:

- [`docs/90_GOVERNANCE/CURRENT_STATE.md`](docs/90_GOVERNANCE/CURRENT_STATE.md)
- [`docs/90_GOVERNANCE/KNOWN_ISSUES.md`](docs/90_GOVERNANCE/KNOWN_ISSUES.md)
- [`docs/00_PRODUCT/ROADMAP.md`](docs/00_PRODUCT/ROADMAP.md)

Đặc biệt, đừng suy ra Windows compile/runtime PASS chỉ vì source gate hoặc README đang green.

## License và upstream

BridgeX chứa code được phát triển từ FileZilla Client 3.70.6 và phải giữ attribution/nghĩa vụ license upstream. License chính của repository xem tại [`LICENSE`](LICENSE) (**GNU GPL v2**).

Project **không phải sản phẩm chính thức của FileZilla Project**.

Một số project-local tooling/skill được vendor có thể có license riêng; license và provenance của chúng được giữ trong subtree tương ứng.

---

**Project:** TNSuite BridgeX  
**Baseline:** `v0.5 Build12-Hotfix16`  
**Platform:** Windows x64  
**Canonical source:** `main`  
**Download:** [GitHub Releases](https://github.com/kyousuke33/TNSuite-BridgeX/releases)
