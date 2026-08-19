# TNSuite BridgeX

[![Governance CI](https://github.com/kyousuke33/TNSuite-BridgeX/actions/workflows/governance-gates.yml/badge.svg)](https://github.com/kyousuke33/TNSuite-BridgeX/actions/workflows/governance-gates.yml)
![Platform](https://img.shields.io/badge/platform-Windows%20x64-0078D4)
![Baseline](https://img.shields.io/badge/baseline-v0.5%20Build12--Hotfix16-4C8BF5)
[![License](https://img.shields.io/badge/license-GPL--2.0-blue)](LICENSE)

**TNSuite BridgeX** là ứng dụng desktop truyền tệp/SFTP cho Windows x64, có giao diện Light/Dark, tiếng Anh/tiếng Việt, installer riêng và CLI automation có phạm vi giới hạn.

BridgeX được phát triển độc lập từ **FileZilla Client 3.70.6**. Đây **không phải sản phẩm chính thức của FileZilla Project** và không được đại diện như một bản FileZilla thương mại/chính thức.

> README này dành cho việc định hướng và bắt đầu nhanh. Trạng thái kỹ thuật thực tế, QA, release và các capability đã được chứng minh nằm trong [`docs/90_GOVERNANCE/CURRENT_STATE.md`](docs/90_GOVERNANCE/CURRENT_STATE.md) cùng các authority tương ứng.

## Tải xuống

Kênh phân phối binary chính thức của BridgeX là **[GitHub Releases](https://github.com/kyousuke33/TNSuite-BridgeX/releases)**.

Hiện repository **chưa publish Windows binary release trên GitHub**. Baseline `v0.5 Build12-Hotfix16` là baseline source/build được chấp nhận, không nên hiểu thành một GitHub Release đã phát hành.

| Kênh | Trạng thái | Dùng để làm gì |
| --- | --- | --- |
| [`main`](https://github.com/kyousuke33/TNSuite-BridgeX) | Canonical source | Source, build tooling, QA và governance |
| [GitHub Releases](https://github.com/kyousuke33/TNSuite-BridgeX/releases) | Chưa có binary release | Installer/portable artifact đã qua release gate |
| GitHub Packages | Không sử dụng | BridgeX hiện không có package-registry use case như npm/NuGet/container |

Khi release chính thức được publish, release notes phải chỉ rõ artifact, SHA-256 và các bằng chứng xác minh tương ứng. Không tải installer từ nguồn bên thứ ba nếu không đối chiếu được với release chính thức.

## An toàn và xác minh artifact

Đối với một ứng dụng Windows có file thực thi, chỉ nhìn tên file hoặc badge CI là chưa đủ. Mỗi release nên cung cấp tối thiểu:

- **SHA-256** của installer và portable archive;
- link về exact source/tag đã dùng để build;
- trạng thái build/release gate;
- **VirusTotal report** cho từng artifact khi report đó thực sự tồn tại.

VirusTotal là một **tín hiệu kiểm tra bổ sung**, không phải chứng nhận tuyệt đối rằng file an toàn. Antivirus có thể false-positive, và một report sạch cũng không thay thế source review, reproducible identity, hash verification hay release governance.

BridgeX không hiển thị badge kiểu “VirusTotal: Safe” khi chưa có artifact/report cụ thể. Khi release đầu tiên được publish, link VirusTotal nên nằm ngay trong release notes cạnh SHA-256 của đúng file được quét.

Public pull request và fork PR của repository này chỉ chạy trên **GitHub-hosted infrastructure**. Shared runner `tn-ci-01` không nằm trong execution path của public contributor code.

## BridgeX có gì?

| Khả năng | Mô tả |
| --- | --- |
| **Desktop GUI** | Client truyền tệp cho Windows x64 |
| **SFTP / transfer** | Luồng truyền tệp theo capability hiện có của BridgeX |
| **Light / Dark** | Giao diện sáng/tối với persistence |
| **EN / VI** | Giao diện tiếng Anh và tiếng Việt |
| **CLI automation** | CLI có phạm vi giới hạn cho luồng automation/SFTP |
| **Windows installer** | NSIS setup, Start Menu và uninstall lifecycle |
| **Portable artifact** | Build pipeline tạo portable ZIP cùng installer |
| **Governed QA** | Exact source manifest, source regression gates và protected `main` |

Chi tiết product scope và requirement: [`docs/00_PRODUCT/`](docs/00_PRODUCT/).

## Bắt đầu nhanh

### Người dùng

Khi có release chính thức:

1. mở trang **[Releases](https://github.com/kyousuke33/TNSuite-BridgeX/releases)**;
2. tải installer hoặc portable archive của release cần dùng;
3. đối chiếu SHA-256 trong release notes;
4. mở VirusTotal report của **đúng artifact** nếu release có cung cấp;
5. cài đặt/chạy BridgeX theo artifact đã xác minh.

Cho tới khi GitHub Releases có binary được publish, repository này nên được xem là **source distribution**, không phải trang tải executable chính thức.

### Developer / contributor

```bash
git clone https://github.com/kyousuke33/TNSuite-BridgeX.git
cd TNSuite-BridgeX
```

Trước khi thay đổi source, CI, security hoặc release behavior, đọc:

1. [`AGENTS.md`](AGENTS.md)
2. [`docs/90_GOVERNANCE/CURRENT_STATE.md`](docs/90_GOVERNANCE/CURRENT_STATE.md)
3. authority docs của khu vực chuẩn bị sửa.

## Yêu cầu build

Baseline hiện tại nhắm tới:

- Windows 64-bit;
- PowerShell;
- Git;
- kết nối mạng khi build environment cần tải MSYS2/dependency;
- Windows OpenSSH Client có `sftp.exe` cho CLI runtime doctor;
- MSYS2 UCRT64 / wxWidgets 3.3.3 theo build tooling của project.

Build script quản lý isolated MSYS2 environment; không cần commit compiler tree, cache hoặc generated artifact vào repository.

Dependency authority: [`docs/10_ARCHITECTURE/DEPENDENCIES.md`](docs/10_ARCHITECTURE/DEPENDENCIES.md).

## Build trên Windows

Entry point đơn giản nhất:

```bat
Build.cmd
```

Hoặc chạy trực tiếp PowerShell orchestration:

```powershell
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File .\Build-TNSuiteBridgeX.ps1
```

Build pipeline chuẩn bị/tái sử dụng isolated MSYS2 UCRT64, build BridgeX, tạo portable ZIP và NSIS installer trong `dist/`, sau đó chạy các verification đã được định nghĩa trong build script.

Việc một máy local tạo được `.zip` hoặc `Setup.exe` **không tự biến artifact đó thành release chính thức**. Publication phải đi qua release authority tại [`docs/80_RELEASE/`](docs/80_RELEASE/).

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

Gate này kiểm exact source manifest của Build12-Hotfix16 và chạy các regression/source checks tương ứng.

Public PR CI chạy bằng **GitHub-hosted runner**. Workflow không được route untrusted PR/fork code sang shared TNSuite self-hosted infrastructure.

Tài liệu QA:

- [`docs/60_QUALITY/TESTING.md`](docs/60_QUALITY/TESTING.md)
- [`docs/60_QUALITY/QA_MATRIX.md`](docs/60_QUALITY/QA_MATRIX.md)
- [`docs/60_QUALITY/REGRESSION.md`](docs/60_QUALITY/REGRESSION.md)
- [`docs/60_QUALITY/ACCEPTANCE_CRITERIA.md`](docs/60_QUALITY/ACCEPTANCE_CRITERIA.md)

**Source/static QA PASS không đồng nghĩa Windows compile, installer runtime hoặc GUI runtime PASS.** Mỗi lớp acceptance cần đúng loại evidence của nó.

## Kiến trúc tổng quan

```text
FileZilla Client 3.70.6 derived core
        ↓
BridgeX patches / product customization
        ↓
Branding + locale + GUI/CLI behavior
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

## Agent skills

Project-local skills nằm trong [`skills/`](skills/).

Ngoài các skill engineering của TNSuite, repository vendor `clean-user-facing-text` để làm final text-hygiene pass cho nội dung người dùng được phép chỉnh sửa:

[`skills/clean-user-facing-text/`](skills/clean-user-facing-text/)

Skill này được pin từ `guillaumemeyer/watermarks-remover` tại upstream commit `1cc278342ea9d9d2a78dd2768def20df279f4b7b`, kèm provenance và MIT license riêng. Nó không thay đổi license của BridgeX core và không được dùng để tuyên bố chắc chắn rằng văn bản là do con người viết hoặc “không thể bị phát hiện là AI”.

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

## Documentation map

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

README là tài liệu định hướng, không phải authority cao nhất cho mọi thông tin.

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

## Trạng thái và giới hạn hiện tại

README không duy trì danh sách bug/evidence dài để tránh documentation drift.

Nguồn cần đọc:

- [`docs/90_GOVERNANCE/CURRENT_STATE.md`](docs/90_GOVERNANCE/CURRENT_STATE.md)
- [`docs/90_GOVERNANCE/KNOWN_ISSUES.md`](docs/90_GOVERNANCE/KNOWN_ISSUES.md)
- [`docs/00_PRODUCT/ROADMAP.md`](docs/00_PRODUCT/ROADMAP.md)

Đặc biệt, đừng suy ra Windows compile/runtime PASS chỉ vì source gate hoặc README đang green.

## License và upstream

BridgeX chứa code được phát triển từ FileZilla Client 3.70.6 và phải giữ attribution/nghĩa vụ license upstream. License chính của repository xem tại [`LICENSE`](LICENSE) (**GNU GPL v2**).

Project **không phải sản phẩm chính thức của FileZilla Project**.

Một số project-local tooling/skill được vendor có thể có license riêng; license và provenance của chúng được giữ ngay trong subtree tương ứng.

---

**Project:** TNSuite BridgeX  
**Baseline:** `v0.5 Build12-Hotfix16`  
**Platform:** Windows x64  
**Canonical source:** `main`  
**Download channel:** [GitHub Releases](https://github.com/kyousuke33/TNSuite-BridgeX/releases)
