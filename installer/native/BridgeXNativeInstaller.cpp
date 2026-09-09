#define UNICODE
#define _UNICODE
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <shlobj.h>
#include <shobjidl.h>
#include <shellapi.h>
#include <objbase.h>
#include <filesystem>
#include <fstream>
#include <string>
#include <system_error>
#include <stdexcept>

#pragma comment(lib, "Ole32.lib")
#pragma comment(lib, "Shell32.lib")
#pragma comment(lib, "User32.lib")

#include "payload_manifest.h"

namespace fs = std::filesystem;

static constexpr wchar_t kProductName[] = L"TNSuite BridgeX";
static constexpr wchar_t kMarkerName[] = L".tnsuite-bridgex-install";

static void ShowError(std::wstring const& message) {
    MessageBoxW(nullptr, message.c_str(), kProductName, MB_OK | MB_ICONERROR);
}

static fs::path KnownFolder(REFKNOWNFOLDERID id) {
    PWSTR raw = nullptr;
    HRESULT hr = SHGetKnownFolderPath(id, KF_FLAG_DEFAULT, nullptr, &raw);
    if (FAILED(hr) || !raw) {
        throw std::runtime_error("SHGetKnownFolderPath failed");
    }
    fs::path value(raw);
    CoTaskMemFree(raw);
    return value;
}

static fs::path InstallRoot() {
    return KnownFolder(FOLDERID_ProgramFiles) / L"TNSuite" / L"BridgeX";
}

static bool WriteResourceToFile(HINSTANCE instance, int id, fs::path const& output) {
    HRSRC resource = FindResourceW(instance, MAKEINTRESOURCEW(id), RT_RCDATA);
    if (!resource) return false;
    HGLOBAL loaded = LoadResource(instance, resource);
    if (!loaded) return false;
    DWORD size = SizeofResource(instance, resource);
    void const* data = LockResource(loaded);
    if (!data && size) return false;

    std::error_code ec;
    fs::create_directories(output.parent_path(), ec);
    if (ec) return false;

    HANDLE file = CreateFileW(output.c_str(), GENERIC_WRITE, 0, nullptr, CREATE_ALWAYS,
                              FILE_ATTRIBUTE_NORMAL, nullptr);
    if (file == INVALID_HANDLE_VALUE) return false;

    BYTE const* cursor = static_cast<BYTE const*>(data);
    DWORD remaining = size;
    bool ok = true;
    while (remaining) {
        DWORD chunk = remaining > (16u * 1024u * 1024u) ? (16u * 1024u * 1024u) : remaining;
        DWORD written = 0;
        if (!WriteFile(file, cursor, chunk, &written, nullptr) || written != chunk) {
            ok = false;
            break;
        }
        cursor += written;
        remaining -= written;
    }
    FlushFileBuffers(file);
    CloseHandle(file);
    return ok;
}

static bool CreateShortcut(fs::path const& shortcut,
                           fs::path const& target,
                           fs::path const& workingDirectory,
                           fs::path const& icon) {
    IShellLinkW* link = nullptr;
    HRESULT hr = CoCreateInstance(CLSID_ShellLink, nullptr, CLSCTX_INPROC_SERVER,
                                  IID_IShellLinkW, reinterpret_cast<void**>(&link));
    if (FAILED(hr) || !link) return false;

    link->SetPath(target.c_str());
    link->SetWorkingDirectory(workingDirectory.c_str());
    link->SetDescription(L"TNSuite BridgeX");
    link->SetIconLocation(icon.c_str(), 0);

    IPersistFile* persist = nullptr;
    hr = link->QueryInterface(IID_IPersistFile, reinterpret_cast<void**>(&persist));
    if (SUCCEEDED(hr) && persist) {
        std::error_code ec;
        fs::create_directories(shortcut.parent_path(), ec);
        if (!ec) {
            hr = persist->Save(shortcut.c_str(), TRUE);
        } else {
            hr = E_FAIL;
        }
        persist->Release();
    }
    link->Release();
    return SUCCEEDED(hr);
}

static int Install(HINSTANCE instance) {
    try {
        fs::path root = InstallRoot();
        fs::path marker = root / kMarkerName;

        std::error_code ec;
        if (fs::exists(root, ec)) {
            if (!fs::exists(marker, ec)) {
                ShowError(L"An existing TNSuite\\BridgeX folder was found without the BridgeX install marker. Setup will not remove an unverified directory.");
                return 20;
            }
            fs::remove_all(root, ec);
            if (ec || fs::exists(root)) {
                ShowError(L"Setup could not clean the previous BridgeX installation. Close BridgeX and any program using its files, then run Setup again.");
                return 21;
            }
        }

        fs::create_directories(root, ec);
        if (ec) {
            ShowError(L"Could not create the BridgeX installation directory.");
            return 22;
        }

        for (size_t i = 0; i < kPayloadCount; ++i) {
            fs::path output = root / kPayload[i].relativePath;
            if (!WriteResourceToFile(instance, kPayload[i].resourceId, output)) {
                std::error_code cleanup;
                fs::remove_all(root, cleanup);
                ShowError(L"Setup could not write the complete BridgeX runtime payload. No partial installation was kept.");
                return 23;
            }
        }

        {
            std::ofstream markerFile(marker, std::ios::binary | std::ios::trunc);
            markerFile << "TNSuite BridgeX native installer\n";
        }

        fs::path app = root / L"bin" / L"BridgeX.exe";
        fs::path bin = root / L"bin";
        if (!fs::exists(app)) {
            std::error_code cleanup;
            fs::remove_all(root, cleanup);
            ShowError(L"BridgeX.exe is missing after extraction.");
            return 24;
        }

        fs::path startMenu = KnownFolder(FOLDERID_CommonPrograms) / L"TNSuite BridgeX" / L"TNSuite BridgeX.lnk";
        fs::path desktop = KnownFolder(FOLDERID_PublicDesktop) / L"TNSuite BridgeX.lnk";

        if (!CreateShortcut(startMenu, app, bin, app)) {
            ShowError(L"BridgeX was installed, but the Start Menu shortcut could not be created.");
            return 25;
        }
        (void)CreateShortcut(desktop, app, bin, app);

        int launch = MessageBoxW(nullptr,
            L"TNSuite BridgeX was installed successfully.\n\nLaunch BridgeX now?",
            kProductName, MB_YESNO | MB_ICONINFORMATION);
        if (launch == IDYES) {
            HINSTANCE result = ShellExecuteW(nullptr, L"open", app.c_str(), nullptr, bin.c_str(), SW_SHOWNORMAL);
            if (reinterpret_cast<INT_PTR>(result) <= 32) {
                ShowError(L"BridgeX was installed, but Windows could not launch it.");
                return 26;
            }
        }
        return 0;
    }
    catch (...) {
        ShowError(L"Setup failed because Windows returned an unexpected installation error.");
        return 99;
    }
}

int WINAPI wWinMain(HINSTANCE instance, HINSTANCE, PWSTR, int) {
    HRESULT co = CoInitializeEx(nullptr, COINIT_APARTMENTTHREADED);
    int result = Install(instance);
    if (SUCCEEDED(co)) CoUninitialize();
    return result;
}
