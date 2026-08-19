// TNSuite BridgeX CLI
// Independent companion CLI for the custom TNSuite BridgeX build.
// This is NOT the commercial/official FileZilla CLI product.
//
// P0 backend: Windows OpenSSH sftp.exe.
// Security defaults:
// - public-key / SSH-agent authentication only; passwords are not stored.
// - StrictHostKeyChecking=yes unless the site is explicitly configured accept-new.
// - BatchMode=yes; no unattended password/passphrase prompts.
// - no private key material is copied into the portable bundle.

#ifndef UNICODE
#define UNICODE
#endif
#ifndef _UNICODE
#define _UNICODE
#endif

#include <windows.h>

#include <algorithm>
#include <cctype>
#include <cstddef>
#include <cwctype>
#include <cerrno>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <optional>
#include <sstream>
#include <string>
#include <stdexcept>
#include <vector>

namespace fs = std::filesystem;

static constexpr wchar_t kVersion[] = L"0.5-Build12-Hotfix16";

enum ExitCode {
    EXIT_OK = 0,
    EXIT_USAGE = 2,
    EXIT_CONFIG = 3,
    EXIT_DEPENDENCY = 4,
    EXIT_LOCAL_IO = 5,
    EXIT_BACKEND = 10,
    EXIT_PROCESS = 11,
    EXIT_SELFTEST = 12
};

struct Site {
    std::wstring name;
    std::wstring host;
    std::wstring user;
    std::wstring key;
    int port = 22;
    bool accept_new = false;
};

struct ProcessResult {
    bool started = false;
    DWORD exit_code = 0xffffffffu;
    std::string out;
    std::string err;
};

static std::string utf8(const std::wstring& s) {
    if (s.empty()) return {};
    int n = WideCharToMultiByte(CP_UTF8, WC_ERR_INVALID_CHARS, s.data(), static_cast<int>(s.size()),
                                nullptr, 0, nullptr, nullptr);
    if (n <= 0) return {};
    std::string out(static_cast<size_t>(n), '\0');
    WideCharToMultiByte(CP_UTF8, WC_ERR_INVALID_CHARS, s.data(), static_cast<int>(s.size()),
                        out.data(), n, nullptr, nullptr);
    return out;
}

static std::wstring widen_utf8(const std::string& s) {
    if (s.empty()) return {};
    int n = MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, s.data(), static_cast<int>(s.size()),
                                nullptr, 0);
    if (n <= 0) {
        n = MultiByteToWideChar(CP_ACP, 0, s.data(), static_cast<int>(s.size()), nullptr, 0);
        if (n <= 0) return {};
        std::wstring out(static_cast<size_t>(n), L'\0');
        MultiByteToWideChar(CP_ACP, 0, s.data(), static_cast<int>(s.size()), out.data(), n);
        return out;
    }
    std::wstring out(static_cast<size_t>(n), L'\0');
    MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, s.data(), static_cast<int>(s.size()),
                        out.data(), n);
    return out;
}

static std::string json_escape(const std::string& s) {
    std::string out;
    out.reserve(s.size() + 16);
    static const char hex[] = "0123456789abcdef";
    for (unsigned char c : s) {
        switch (c) {
            case '"': out += "\\\""; break;
            case '\\': out += "\\\\"; break;
            case '\b': out += "\\b"; break;
            case '\f': out += "\\f"; break;
            case '\n': out += "\\n"; break;
            case '\r': out += "\\r"; break;
            case '\t': out += "\\t"; break;
            default:
                if (c < 0x20) {
                    out += "\\u00";
                    out += hex[(c >> 4) & 0x0f];
                    out += hex[c & 0x0f];
                } else {
                    out.push_back(static_cast<char>(c));
                }
        }
    }
    return out;
}

static std::wstring get_env(const wchar_t* name) {
    DWORD n = GetEnvironmentVariableW(name, nullptr, 0);
    if (!n) return {};
    std::wstring v(static_cast<size_t>(n), L'\0');
    DWORD got = GetEnvironmentVariableW(name, v.data(), n);
    if (!got || got >= n) return {};
    v.resize(got);
    return v;
}

static fs::path config_root() {
    std::wstring appdata = get_env(L"APPDATA");
    if (appdata.empty()) {
        throw std::runtime_error("APPDATA is not available");
    }
    return fs::path(appdata) / L"TNSuite" / L"BridgeX" / L"CLI" / L"sites";
}

static bool valid_site_name(const std::wstring& name) {
    if (name.empty() || name.size() > 80) return false;
    for (wchar_t c : name) {
        if (!(std::iswalnum(c) || c == L'-' || c == L'_' || c == L'.')) return false;
    }
    return true;
}

static fs::path site_path(const std::wstring& name) {
    if (!valid_site_name(name)) {
        throw std::runtime_error("invalid site name");
    }
    return config_root() / (name + L".ini");
}

static std::wstring ini_get(const fs::path& p, const wchar_t* key, const wchar_t* def = L"") {
    std::vector<wchar_t> buf(32768);
    DWORD n = GetPrivateProfileStringW(L"site", key, def, buf.data(),
                                       static_cast<DWORD>(buf.size()), p.c_str());
    return std::wstring(buf.data(), n);
}

static bool ini_set(const fs::path& p, const wchar_t* key, const std::wstring& value) {
    return WritePrivateProfileStringW(L"site", key, value.c_str(), p.c_str()) != FALSE;
}

static std::optional<Site> load_site(const std::wstring& name, std::wstring* why = nullptr) {
    try {
        fs::path p = site_path(name);
        if (!fs::is_regular_file(p)) {
            if (why) *why = L"site does not exist";
            return std::nullopt;
        }
        Site s;
        s.name = name;
        s.host = ini_get(p, L"host");
        s.user = ini_get(p, L"user");
        s.key = ini_get(p, L"key");
        std::wstring port = ini_get(p, L"port", L"22");
        std::wstring accept = ini_get(p, L"accept_new", L"0");
        try {
            s.port = std::stoi(port);
        } catch (...) {
            if (why) *why = L"invalid port";
            return std::nullopt;
        }
        s.accept_new = (accept == L"1" || accept == L"true" || accept == L"yes");
        if (s.host.empty() || s.user.empty() || s.port < 1 || s.port > 65535) {
            if (why) *why = L"incomplete site configuration";
            return std::nullopt;
        }
        return s;
    } catch (const std::exception&) {
        if (why) *why = L"site configuration error";
        return std::nullopt;
    }
}

static std::optional<fs::path> find_exe(const wchar_t* name) {
    std::vector<wchar_t> buf(32768);
    DWORD n = SearchPathW(nullptr, name, nullptr, static_cast<DWORD>(buf.size()), buf.data(), nullptr);
    if (!n || n >= buf.size()) return std::nullopt;
    return fs::path(std::wstring(buf.data(), n));
}

// Windows CreateProcess command-line quoting based on the documented argv parsing rules.
static std::wstring quote_win_arg(const std::wstring& arg) {
    if (arg.empty()) return L"\"\"";
    bool need_quotes = false;
    for (wchar_t c : arg) {
        if (iswspace(c) || c == L'"') {
            need_quotes = true;
            break;
        }
    }
    if (!need_quotes) return arg;

    std::wstring out = L"\"";
    size_t slashes = 0;
    for (wchar_t c : arg) {
        if (c == L'\\') {
            ++slashes;
        } else if (c == L'"') {
            out.append(slashes * 2 + 1, L'\\');
            out.push_back(L'"');
            slashes = 0;
        } else {
            out.append(slashes, L'\\');
            slashes = 0;
            out.push_back(c);
        }
    }
    out.append(slashes * 2, L'\\');
    out.push_back(L'"');
    return out;
}

static bool safe_batch_arg(const std::wstring& s) {
    return s.find(L'\r') == std::wstring::npos &&
           s.find(L'\n') == std::wstring::npos &&
           s.find(L'"') == std::wstring::npos;
}

static std::wstring batch_quote(std::wstring s, bool local_path) {
    if (!safe_batch_arg(s)) {
        throw std::runtime_error("path contains unsupported quote/newline");
    }
    if (local_path) {
        std::replace(s.begin(), s.end(), L'\\', L'/');
    }
    std::wstring out = L"\"";
    for (wchar_t c : s) {
        if (c == L'\\') out += L"\\\\";
        else out.push_back(c);
    }
    out += L"\"";
    return out;
}

static fs::path make_temp_file(const wchar_t* prefix) {
    std::vector<wchar_t> dir(32768);
    DWORD n = GetTempPathW(static_cast<DWORD>(dir.size()), dir.data());
    if (!n || n >= dir.size()) throw std::runtime_error("GetTempPathW failed");
    wchar_t file[MAX_PATH + 1]{};
    if (!GetTempFileNameW(dir.data(), prefix, 0, file)) {
        throw std::runtime_error("GetTempFileNameW failed");
    }
    return fs::path(file);
}

static std::string read_bytes(const fs::path& p) {
    std::ifstream f(p, std::ios::binary);
    if (!f) return {};
    std::ostringstream ss;
    ss << f.rdbuf();
    return ss.str();
}

static void write_utf8_file(const fs::path& p, const std::wstring& text) {
    std::ofstream f(p, std::ios::binary | std::ios::trunc);
    if (!f) throw std::runtime_error("cannot create temporary batch file");
    std::string u = utf8(text);
    f.write(u.data(), static_cast<std::streamsize>(u.size()));
    if (!f) throw std::runtime_error("cannot write temporary batch file");
}

static ProcessResult run_process_capture(const fs::path& exe, const std::vector<std::wstring>& args) {
    ProcessResult r;
    fs::path outp = make_temp_file(L"fzo");
    fs::path errp = make_temp_file(L"fze");
    HANDLE hout = INVALID_HANDLE_VALUE;
    HANDLE herr = INVALID_HANDLE_VALUE;
    HANDLE hin = INVALID_HANDLE_VALUE;

    auto cleanup = [&]() {
        if (hout != INVALID_HANDLE_VALUE) CloseHandle(hout);
        if (herr != INVALID_HANDLE_VALUE) CloseHandle(herr);
        if (hin != INVALID_HANDLE_VALUE) CloseHandle(hin);
        std::error_code ec;
        fs::remove(outp, ec);
        fs::remove(errp, ec);
    };

    SECURITY_ATTRIBUTES sa{};
    sa.nLength = sizeof(sa);
    sa.bInheritHandle = TRUE;

    hout = CreateFileW(outp.c_str(), GENERIC_WRITE, FILE_SHARE_READ | FILE_SHARE_WRITE, &sa,
                       CREATE_ALWAYS, FILE_ATTRIBUTE_TEMPORARY, nullptr);
    herr = CreateFileW(errp.c_str(), GENERIC_WRITE, FILE_SHARE_READ | FILE_SHARE_WRITE, &sa,
                       CREATE_ALWAYS, FILE_ATTRIBUTE_TEMPORARY, nullptr);
    hin = CreateFileW(L"NUL", GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE, &sa,
                      OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (hout == INVALID_HANDLE_VALUE || herr == INVALID_HANDLE_VALUE || hin == INVALID_HANDLE_VALUE) {
        cleanup();
        return r;
    }

    std::wstring cmd = quote_win_arg(exe.wstring());
    for (const auto& a : args) {
        cmd += L" ";
        cmd += quote_win_arg(a);
    }
    std::vector<wchar_t> mutable_cmd(cmd.begin(), cmd.end());
    mutable_cmd.push_back(L'\0');

    STARTUPINFOW si{};
    si.cb = sizeof(si);
    si.dwFlags = STARTF_USESTDHANDLES;
    si.hStdInput = hin;
    si.hStdOutput = hout;
    si.hStdError = herr;

    PROCESS_INFORMATION pi{};
    BOOL ok = CreateProcessW(exe.c_str(), mutable_cmd.data(), nullptr, nullptr, TRUE,
                             CREATE_NO_WINDOW, nullptr, nullptr, &si, &pi);
    if (!ok) {
        cleanup();
        return r;
    }
    r.started = true;
    WaitForSingleObject(pi.hProcess, INFINITE);
    GetExitCodeProcess(pi.hProcess, &r.exit_code);
    CloseHandle(pi.hThread);
    CloseHandle(pi.hProcess);

    CloseHandle(hout); hout = INVALID_HANDLE_VALUE;
    CloseHandle(herr); herr = INVALID_HANDLE_VALUE;
    CloseHandle(hin); hin = INVALID_HANDLE_VALUE;

    r.out = read_bytes(outp);
    r.err = read_bytes(errp);
    cleanup();
    return r;
}

static ProcessResult run_sftp(const Site& site, const std::wstring& batch) {
    ProcessResult r;
    auto sftp = find_exe(L"sftp.exe");
    if (!sftp) {
        r.err = "Windows OpenSSH sftp.exe was not found in PATH.";
        return r;
    }

    fs::path batch_file;
    try {
        batch_file = make_temp_file(L"fzb");
        write_utf8_file(batch_file, batch);
    } catch (const std::exception& e) {
        r.err = e.what();
        return r;
    }

    std::vector<std::wstring> args;
    args.emplace_back(L"-q");
    args.emplace_back(L"-b");
    args.emplace_back(batch_file.wstring());
    args.emplace_back(L"-o");
    args.emplace_back(L"BatchMode=yes");
    args.emplace_back(L"-o");
    args.emplace_back(site.accept_new ? L"StrictHostKeyChecking=accept-new" : L"StrictHostKeyChecking=yes");
    args.emplace_back(L"-o");
    args.emplace_back(L"ConnectTimeout=15");
    args.emplace_back(L"-o");
    args.emplace_back(L"ServerAliveInterval=30");
    if (!site.key.empty()) {
        args.emplace_back(L"-i");
        args.emplace_back(site.key);
    }
    args.emplace_back(L"-P");
    args.emplace_back(std::to_wstring(site.port));
    args.emplace_back(site.user + L"@" + site.host);

    r = run_process_capture(*sftp, args);
    std::error_code ec;
    fs::remove(batch_file, ec);
    return r;
}

static void print_help() {
    std::cout <<
R"(TNSuite BridgeX CLI 0.5-Build12-Hotfix16
Independent companion CLI; not the official/commercial FileZilla CLI.

Usage:
  BridgeX-CLI.exe --version
  BridgeX-CLI.exe --selftest [--json]
  BridgeX-CLI.exe doctor [SITE] [--json]

  BridgeX-CLI.exe site add NAME --host HOST --user USER [--port 22] [--key PATH] [--accept-new]
  BridgeX-CLI.exe site list [--json]
  BridgeX-CLI.exe site show NAME [--json]
  BridgeX-CLI.exe site remove NAME

  BridgeX-CLI.exe ls NAME [REMOTE_PATH] [--json]
  BridgeX-CLI.exe get NAME REMOTE [LOCAL] [--json]
  BridgeX-CLI.exe put NAME LOCAL [REMOTE] [--json]
  BridgeX-CLI.exe rget NAME REMOTE [LOCAL] [--json]
  BridgeX-CLI.exe rput NAME LOCAL [REMOTE] [--json]
  BridgeX-CLI.exe mkdir NAME REMOTE [--json]
  BridgeX-CLI.exe rm NAME REMOTE [--json]
  BridgeX-CLI.exe rename NAME OLD_REMOTE NEW_REMOTE [--json]
  BridgeX-CLI.exe script NAME FILE [--allow-local-shell] [--json]

Security:
  - Passwords are not accepted or stored.
  - Uses Windows OpenSSH sftp.exe with BatchMode=yes.
  - Host keys are strict by default. --accept-new is explicit per site.
  - Site profiles store host/user/port/key-path only under %APPDATA%\TNSuite\BridgeX\CLI\sites.
)";
}

static bool has_flag(std::vector<std::wstring>& args, const std::wstring& flag) {
    auto it = std::find(args.begin(), args.end(), flag);
    if (it == args.end()) return false;
    args.erase(it);
    return true;
}

static std::optional<std::wstring> option_value(std::vector<std::wstring>& args, const std::wstring& flag) {
    for (size_t i = 0; i < args.size(); ++i) {
        if (args[i] == flag) {
            if (i + 1 >= args.size()) return std::nullopt;
            std::wstring v = args[i + 1];
            args.erase(args.begin() + static_cast<std::ptrdiff_t>(i),
                       args.begin() + static_cast<std::ptrdiff_t>(i + 2));
            return v;
        }
    }
    return std::nullopt;
}

static int emit_backend(const std::string& command, const Site& site, const ProcessResult& r, bool json) {
    bool ok = r.started && r.exit_code == 0;
    if (json) {
        std::cout << "{"
                  << "\"ok\":" << (ok ? "true" : "false") << ","
                  << "\"command\":\"" << json_escape(command) << "\","
                  << "\"site\":\"" << json_escape(utf8(site.name)) << "\","
                  << "\"backend\":\"windows-openssh-sftp\","
                  << "\"backend_started\":" << (r.started ? "true" : "false") << ","
                  << "\"backend_exit_code\":" << (r.started ? std::to_string(r.exit_code) : "null") << ","
                  << "\"stdout\":\"" << json_escape(r.out) << "\","
                  << "\"stderr\":\"" << json_escape(r.err) << "\""
                  << "}\n";
    } else {
        if (!r.out.empty()) std::cout << r.out;
        if (!r.err.empty()) std::cerr << r.err;
    }
    if (!r.started) return EXIT_PROCESS;
    return r.exit_code == 0 ? EXIT_OK : EXIT_BACKEND;
}

static int command_site(std::vector<std::wstring> args, bool json) {
    if (args.empty()) {
        std::cerr << "site subcommand required\n";
        return EXIT_USAGE;
    }
    std::wstring sub = args[0];
    args.erase(args.begin());

    if (sub == L"list") {
        try {
            fs::path root = config_root();
            std::error_code ec;
            fs::create_directories(root, ec);
            std::vector<std::wstring> names;
            for (const auto& e : fs::directory_iterator(root, ec)) {
                if (!e.is_regular_file()) continue;
                if (e.path().extension() == L".ini") names.push_back(e.path().stem().wstring());
            }
            std::sort(names.begin(), names.end());
            if (json) {
                std::cout << "{\"ok\":true,\"sites\":[";
                for (size_t i = 0; i < names.size(); ++i) {
                    if (i) std::cout << ",";
                    std::cout << "\"" << json_escape(utf8(names[i])) << "\"";
                }
                std::cout << "]}\n";
            } else {
                for (const auto& n : names) std::cout << utf8(n) << "\n";
            }
            return EXIT_OK;
        } catch (const std::exception& e) {
            std::cerr << e.what() << "\n";
            return EXIT_CONFIG;
        }
    }

    if (sub == L"show") {
        if (args.size() != 1) return EXIT_USAGE;
        std::wstring why;
        auto site = load_site(args[0], &why);
        if (!site) {
            std::cerr << "Cannot load site: " << utf8(why) << "\n";
            return EXIT_CONFIG;
        }
        if (json) {
            std::cout << "{"
                      << "\"ok\":true,"
                      << "\"name\":\"" << json_escape(utf8(site->name)) << "\","
                      << "\"host\":\"" << json_escape(utf8(site->host)) << "\","
                      << "\"user\":\"" << json_escape(utf8(site->user)) << "\","
                      << "\"port\":" << site->port << ","
                      << "\"key\":\"" << json_escape(utf8(site->key)) << "\","
                      << "\"accept_new\":" << (site->accept_new ? "true" : "false")
                      << "}\n";
        } else {
            std::cout << "name=" << utf8(site->name) << "\n"
                      << "host=" << utf8(site->host) << "\n"
                      << "user=" << utf8(site->user) << "\n"
                      << "port=" << site->port << "\n"
                      << "key=" << utf8(site->key) << "\n"
                      << "accept_new=" << (site->accept_new ? "true" : "false") << "\n";
        }
        return EXIT_OK;
    }

    if (sub == L"remove") {
        if (args.size() != 1) return EXIT_USAGE;
        try {
            fs::path p = site_path(args[0]);
            std::error_code ec;
            bool removed = fs::remove(p, ec);
            if (ec) {
                std::cerr << "Cannot remove site profile\n";
                return EXIT_CONFIG;
            }
            if (json) {
                std::cout << "{\"ok\":true,\"removed\":" << (removed ? "true" : "false") << "}\n";
            }
            return EXIT_OK;
        } catch (...) {
            return EXIT_CONFIG;
        }
    }

    if (sub == L"add") {
        if (args.empty()) return EXIT_USAGE;
        std::wstring name = args[0];
        args.erase(args.begin());
        if (!valid_site_name(name)) {
            std::cerr << "Invalid site name. Use letters, digits, dot, dash or underscore only.\n";
            return EXIT_USAGE;
        }

        auto host = option_value(args, L"--host");
        auto user = option_value(args, L"--user");
        auto port_s = option_value(args, L"--port");
        auto key = option_value(args, L"--key");
        bool accept_new = has_flag(args, L"--accept-new");
        if (!host || !user || !args.empty()) {
            std::cerr << "site add requires --host and --user; unknown/missing arguments detected\n";
            return EXIT_USAGE;
        }

        int port = 22;
        if (port_s) {
            try { port = std::stoi(*port_s); }
            catch (...) { return EXIT_USAGE; }
        }
        if (port < 1 || port > 65535) return EXIT_USAGE;
        if (key && !key->empty() && !fs::is_regular_file(fs::path(*key))) {
            std::cerr << "Key file does not exist: " << utf8(*key) << "\n";
            return EXIT_LOCAL_IO;
        }

        try {
            fs::path root = config_root();
            fs::create_directories(root);
            fs::path p = site_path(name);
            bool ok = true;
            ok = ok && ini_set(p, L"host", *host);
            ok = ok && ini_set(p, L"user", *user);
            ok = ok && ini_set(p, L"port", std::to_wstring(port));
            ok = ok && ini_set(p, L"key", key.value_or(L""));
            ok = ok && ini_set(p, L"accept_new", accept_new ? L"1" : L"0");
            if (!ok) {
                std::cerr << "Failed to save site profile\n";
                return EXIT_CONFIG;
            }
            if (json) {
                std::cout << "{\"ok\":true,\"site\":\"" << json_escape(utf8(name)) << "\"}\n";
            } else {
                std::cout << "SITE_SAVED=" << utf8(name) << "\n";
            }
            return EXIT_OK;
        } catch (const std::exception& e) {
            std::cerr << e.what() << "\n";
            return EXIT_CONFIG;
        }
    }

    std::cerr << "Unknown site subcommand\n";
    return EXIT_USAGE;
}

static int command_doctor(const std::vector<std::wstring>& args, bool json) {
    bool sftp_ok = find_exe(L"sftp.exe").has_value();
    bool appdata_ok = !get_env(L"APPDATA").empty();
    bool site_ok = true;
    bool key_ok = true;
    std::string site_name;
    std::string detail;

    if (args.size() > 1) return EXIT_USAGE;
    if (args.size() == 1) {
        site_name = utf8(args[0]);
        std::wstring why;
        auto s = load_site(args[0], &why);
        site_ok = s.has_value();
        if (!site_ok) detail = utf8(why);
        if (s && !s->key.empty()) {
            key_ok = fs::is_regular_file(fs::path(s->key));
            if (!key_ok) detail = "configured key file does not exist";
        }
    }

    bool ok = sftp_ok && appdata_ok && site_ok && key_ok;
    if (json) {
        std::cout << "{"
                  << "\"ok\":" << (ok ? "true" : "false") << ","
                  << "\"sftp_found\":" << (sftp_ok ? "true" : "false") << ","
                  << "\"appdata\":" << (appdata_ok ? "true" : "false") << ","
                  << "\"site_ok\":" << (site_ok ? "true" : "false") << ","
                  << "\"key_ok\":" << (key_ok ? "true" : "false") << ","
                  << "\"site\":\"" << json_escape(site_name) << "\","
                  << "\"detail\":\"" << json_escape(detail) << "\""
                  << "}\n";
    } else {
        std::cout << "SFTP_EXE=" << (sftp_ok ? "PASS" : "FAIL") << "\n"
                  << "APPDATA=" << (appdata_ok ? "PASS" : "FAIL") << "\n"
                  << "SITE=" << (site_ok ? "PASS" : "FAIL") << "\n"
                  << "KEY=" << (key_ok ? "PASS" : "FAIL") << "\n";
        if (!detail.empty()) std::cerr << detail << "\n";
    }
    return ok ? EXIT_OK : EXIT_DEPENDENCY;
}

static int selftest(bool json) {
    bool ok = true;
    ok = ok && json_escape("a\"b\nc") == "a\\\"b\\nc";
    ok = ok && quote_win_arg(L"abc") == L"abc";
    ok = ok && quote_win_arg(L"a b") == L"\"a b\"";
    ok = ok && safe_batch_arg(L"/tmp/a b");
    ok = ok && !safe_batch_arg(L"bad\npath");
    try {
        fs::path p = make_temp_file(L"fzt");
        write_utf8_file(p, L"selftest\n");
        ok = ok && read_bytes(p) == "selftest\n";
        std::error_code ec;
        fs::remove(p, ec);
    } catch (...) {
        ok = false;
    }

    if (json) {
        std::cout << "{\"ok\":" << (ok ? "true" : "false")
                  << ",\"selftest\":\"" << (ok ? "PASS" : "FAIL")
                  << "\",\"version\":\"" << utf8(kVersion) << "\"}\n";
    } else {
        std::cout << "CLI_SELFTEST=" << (ok ? "PASS" : "FAIL") << "\n";
    }
    return ok ? EXIT_OK : EXIT_SELFTEST;
}

static int command_transfer(const std::wstring& cmd, std::vector<std::wstring> args,
                            bool json, bool allow_local_shell) {
    if (args.empty()) return EXIT_USAGE;
    std::wstring site_name = args[0];
    args.erase(args.begin());
    std::wstring why;
    auto site = load_site(site_name, &why);
    if (!site) {
        std::cerr << "Cannot load site: " << utf8(why) << "\n";
        return EXIT_CONFIG;
    }

    try {
        std::wstring batch;
        if (cmd == L"ls") {
            if (args.size() > 1) return EXIT_USAGE;
            batch = L"ls -la";
            if (!args.empty()) batch += L" " + batch_quote(args[0], false);
            batch += L"\n";
        } else if (cmd == L"get" || cmd == L"rget") {
            if (args.size() < 1 || args.size() > 2) return EXIT_USAGE;
            batch = (cmd == L"rget" ? L"get -R " : L"get ");
            batch += batch_quote(args[0], false);
            if (args.size() == 2) batch += L" " + batch_quote(args[1], true);
            batch += L"\n";
        } else if (cmd == L"put" || cmd == L"rput") {
            if (args.size() < 1 || args.size() > 2) return EXIT_USAGE;
            batch = (cmd == L"rput" ? L"put -R " : L"put ");
            batch += batch_quote(args[0], true);
            if (args.size() == 2) batch += L" " + batch_quote(args[1], false);
            batch += L"\n";
        } else if (cmd == L"mkdir") {
            if (args.size() != 1) return EXIT_USAGE;
            batch = L"mkdir " + batch_quote(args[0], false) + L"\n";
        } else if (cmd == L"rm") {
            if (args.size() != 1) return EXIT_USAGE;
            batch = L"rm " + batch_quote(args[0], false) + L"\n";
        } else if (cmd == L"rename") {
            if (args.size() != 2) return EXIT_USAGE;
            batch = L"rename " + batch_quote(args[0], false) + L" " + batch_quote(args[1], false) + L"\n";
        } else if (cmd == L"script") {
            if (args.size() != 1) return EXIT_USAGE;
            std::ifstream f(fs::path(args[0]), std::ios::binary);
            if (!f) {
                std::cerr << "Script file cannot be opened\n";
                return EXIT_LOCAL_IO;
            }
            std::ostringstream ss;
            ss << f.rdbuf();
            std::string bytes = ss.str();
            std::wstring script = widen_utf8(bytes);
            if (script.empty() && !bytes.empty()) {
                std::cerr << "Script must be valid UTF-8 or local ANSI text\n";
                return EXIT_LOCAL_IO;
            }
            if (!allow_local_shell) {
                std::wistringstream lines(script);
                std::wstring line;
                while (std::getline(lines, line)) {
                    auto pos = line.find_first_not_of(L" \t\r");
                    if (pos != std::wstring::npos && line[pos] == L'!') {
                        std::cerr << "Local shell commands (!) are disabled. Use --allow-local-shell explicitly.\n";
                        return EXIT_USAGE;
                    }
                }
            }
            batch = script;
            if (batch.empty() || batch.back() != L'\n') batch += L"\n";
        } else {
            return EXIT_USAGE;
        }

        auto result = run_sftp(*site, batch);
        return emit_backend(utf8(cmd), *site, result, json);
    } catch (const std::exception& e) {
        if (json) {
            std::cout << "{\"ok\":false,\"command\":\"" << json_escape(utf8(cmd))
                      << "\",\"site\":\"" << json_escape(utf8(site->name))
                      << "\",\"error\":\"" << json_escape(e.what()) << "\"}\n";
        } else {
            std::cerr << e.what() << "\n";
        }
        return EXIT_LOCAL_IO;
    }
}

int wmain(int argc, wchar_t** argv) {
    std::vector<std::wstring> args;
    for (int i = 1; i < argc; ++i) args.emplace_back(argv[i]);

    bool json = has_flag(args, L"--json");
    bool allow_local_shell = has_flag(args, L"--allow-local-shell");

    if (args.empty() || args[0] == L"--help" || args[0] == L"-h" || args[0] == L"help") {
        print_help();
        return EXIT_OK;
    }
    if (args[0] == L"--version" || args[0] == L"-v") {
        std::cout << "TNSuite BridgeX CLI " << utf8(kVersion) << "\n";
        return EXIT_OK;
    }
    if (args[0] == L"--selftest") {
        return selftest(json);
    }

    std::wstring cmd = args[0];
    args.erase(args.begin());

    if (cmd == L"doctor") return command_doctor(args, json);
    if (cmd == L"site") return command_site(args, json);

    if (cmd == L"ls" || cmd == L"get" || cmd == L"put" || cmd == L"rget" ||
        cmd == L"rput" || cmd == L"mkdir" || cmd == L"rm" || cmd == L"rename" ||
        cmd == L"script") {
        return command_transfer(cmd, args, json, allow_local_shell);
    }

    std::cerr << "Unknown command. Use --help.\n";
    return EXIT_USAGE;
}
