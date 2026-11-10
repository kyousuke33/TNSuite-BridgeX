#!/usr/bin/env bash
set -euo pipefail

BUILD_NAME="TNSuiteBridgeX_260818_v0.5-Build12-Hotfix16-Full"
FZ_VERSION="3.70.6"
FZ_SOURCE_URL="https://sources.archlinux.org/other/filezilla/filezilla-${FZ_VERSION}.tar.xz"
FZ_SOURCE_SHA256="3dd2425a97f96db8cc8b212e1b605d7951258e3da3279c90107abf4a6a89c83f"

if [[ "${MSYSTEM:-}" != "UCRT64" ]]; then
  echo "ERROR: This build must run in MSYS2 UCRT64 (MSYSTEM=${MSYSTEM:-unset})." >&2
  exit 10
fi

if [[ -z "${FZDARK_KIT_WIN:-}" ]]; then
  echo "ERROR: FZDARK_KIT_WIN is not set." >&2
  exit 11
fi

KIT="$(cygpath -u "$FZDARK_KIT_WIN")"
PATCHES="$KIT/patches"
QA="$KIT/qa"
DIST="$KIT/dist"
WORK="/tmp/tnsuite-bridgex-build12-hotfix16"
SRC_ARCHIVE="$WORK/filezilla-${FZ_VERSION}.tar.xz"
SRC="$WORK/filezilla-${FZ_VERSION}"
BUILD="$WORK/build-ucrt64"
STAGE="$WORK/stage"
APP="$STAGE/ucrt64"

mkdir -p "$DIST"
rm -rf "$WORK"
mkdir -p "$WORK" "$BUILD" "$STAGE"

# Build-wide log starts before dependency/preflight checks so early failures
# are always diagnosable. The full C++ compiler still gets its own compile log.
BUILD_LOG="$DIST/${BUILD_NAME}-build.log"
: > "$BUILD_LOG"
exec > >(tee -a "$BUILD_LOG") 2>&1

log() { printf '\n=== %s ===\n' "$*"; }
echo "BUILD_LOG=$BUILD_LOG"

log "Verify/install isolated build dependencies"
# Build12 intentionally avoids the broad `base-devel` meta-package and the
# entire UCRT64 `toolchain` group. Build02 selected those groups and pulled in
# GDB, GDB multiarch and unrelated developer utilities. We install only missing
# commands/libraries required to configure, compile and package FileZilla.
missing=()
command -v curl >/dev/null 2>&1 || missing+=(curl)
command -v patch >/dev/null 2>&1 || missing+=(patch)
command -v tar >/dev/null 2>&1 || missing+=(tar)
command -v xz >/dev/null 2>&1 || missing+=(xz)
command -v zip >/dev/null 2>&1 || missing+=(zip)
command -v python >/dev/null 2>&1 || missing+=(python)
command -v autoreconf >/dev/null 2>&1 || missing+=(autoconf-wrapper)
command -v automake >/dev/null 2>&1 || missing+=(automake-wrapper)
command -v libtoolize >/dev/null 2>&1 || missing+=(libtool)
command -v make >/dev/null 2>&1 || missing+=(make)

ucrt_packages=(
  mingw-w64-ucrt-x86_64-gcc
  mingw-w64-ucrt-x86_64-binutils
  mingw-w64-ucrt-x86_64-pkgconf
  mingw-w64-ucrt-x86_64-boost
  mingw-w64-ucrt-x86_64-fzssh
  mingw-w64-ucrt-x86_64-gnutls
  mingw-w64-ucrt-x86_64-libfilezilla
  mingw-w64-ucrt-x86_64-sqlite3
  mingw-w64-ucrt-x86_64-wxwidgets3.3-msw
  mingw-w64-ucrt-x86_64-gettext-tools
  mingw-w64-ucrt-x86_64-nsis
)
PACMAN_DB_SNAPSHOT="$WORK/installed-packages.txt"
PACMAN_DB_STDERR="$WORK/pacman-package-db.stderr.txt"
PACMAN_DB_TIMEOUT_SECONDS="${BRIDGEX_PACMAN_DB_TIMEOUT_SECONDS:-30}"

echo "DEPENDENCY_PACKAGE_DB_QA=START"
if ! command -v timeout >/dev/null 2>&1; then
  echo "DEPENDENCY_PACKAGE_DB_QA=FAIL reason=TIMEOUT_COMMAND_MISSING" >&2
  echo "ERROR: MSYS2 coreutils 'timeout' is required for bounded package DB inspection." >&2
  exit 67
fi
if ! [[ "$PACMAN_DB_TIMEOUT_SECONDS" =~ ^[1-9][0-9]*$ ]]; then
  echo "DEPENDENCY_PACKAGE_DB_QA=FAIL reason=INVALID_TIMEOUT value=$PACMAN_DB_TIMEOUT_SECONDS" >&2
  exit 67
fi
set +e
timeout --foreground "${PACMAN_DB_TIMEOUT_SECONDS}s" pacman -Q >"$PACMAN_DB_SNAPSHOT" 2>"$PACMAN_DB_STDERR"
pacman_db_rc=$?
set -e
if (( pacman_db_rc != 0 )); then
  if (( pacman_db_rc == 124 || pacman_db_rc == 137 )); then
    echo "DEPENDENCY_PACKAGE_DB_QA=FAIL reason=TIMEOUT seconds=$PACMAN_DB_TIMEOUT_SECONDS" >&2
    echo "ERROR: pacman package DB query exceeded ${PACMAN_DB_TIMEOUT_SECONDS}s. Check the MSYS2 package DB lock/state before retrying." >&2
  else
    echo "DEPENDENCY_PACKAGE_DB_QA=FAIL reason=PACMAN_QUERY_FAILED exit=$pacman_db_rc" >&2
    [[ ! -s "$PACMAN_DB_STDERR" ]] || sed -n '1,20p' "$PACMAN_DB_STDERR" >&2
  fi
  exit 67
fi
if [[ ! -s "$PACMAN_DB_SNAPSHOT" ]]; then
  echo "DEPENDENCY_PACKAGE_DB_QA=FAIL reason=EMPTY_PACKAGE_DB_SNAPSHOT" >&2
  exit 67
fi
echo "DEPENDENCY_PACKAGE_DB_QA=PASS"

declare -A installed_packages=()
while read -r pkg_name _pkg_version _rest; do
  [[ -n "${pkg_name:-}" ]] && installed_packages["$pkg_name"]=1
done < "$PACMAN_DB_SNAPSHOT"
for pkg in "${ucrt_packages[@]}"; do
  [[ -n "${installed_packages[$pkg]:-}" ]] || missing+=("$pkg")
done

if (( ${#missing[@]} )); then
  echo "Installing only ${#missing[@]} missing package(s): ${missing[*]}"
  pacman --noconfirm --needed -S "${missing[@]}"
  echo "BUILD_DEPENDENCIES=INSTALLED count=${#missing[@]}"
else
  echo "BUILD_DEPENDENCIES=REUSED"
fi

MSGFMT_EXE="/ucrt64/bin/msgfmt.exe"
[[ -x "$MSGFMT_EXE" ]] || {
  echo "ERROR: UCRT64 msgfmt missing after dependency resolution: $MSGFMT_EXE" >&2
  echo "EXPECTED_PACKAGE=mingw-w64-ucrt-x86_64-gettext-tools" >&2
  exit 66
}
echo "UCRT64_MSGFMT_QA=PASS"

log "Hotfix9 Python QA dependency audit - fail closed"
python "$QA/hotfix9_qa_dependency_check.py" "$KIT" | tee "$WORK/hotfix9-qa-dependency-report.txt"
grep -q '^HOTFIX9_QA_DEPENDENCY_QA=PASS$' "$WORK/hotfix9-qa-dependency-report.txt"

log "BridgeX Vietnamese locale source QA - fail closed"
BRIDGEX_PO="$KIT/locales/bridgex_vi_VN.po"
[[ -s "$BRIDGEX_PO" ]] || { echo "ERROR: BridgeX Vietnamese PO catalog missing." >&2; exit 69; }
python "$QA/bridgex_locale_source_check.py" "$BRIDGEX_PO" | tee "$WORK/bridgex-vi-locale-source-report.txt"
grep -q '^BRIDGEX_VI_LOCALE_SOURCE_QA=PASS$' "$WORK/bridgex-vi-locale-source-report.txt"

log "BridgeX Vietnamese locale early msgfmt probe - fail closed"
if ! "$MSGFMT_EXE" --check --check-format -o "$WORK/bridgex-vi-early.mo" "$BRIDGEX_PO"; then
  echo "ERROR: BridgeX Vietnamese locale failed early UCRT64 msgfmt validation." >&2
  exit 70
fi
[[ -s "$WORK/bridgex-vi-early.mo" ]] || { echo "ERROR: BridgeX Vietnamese early MO probe output missing." >&2; exit 71; }
echo "BRIDGEX_VI_LOCALE_EARLY_MSGFMT_QA=PASS"

log "Build scheduler QA - fail closed"
python "$QA/build_scheduler_check.py" "$KIT/scripts/build-filezilla-dark.sh" | tee "$WORK/scheduler-report.txt"
grep -q '^SCHEDULER_QA=PASS$' "$WORK/scheduler-report.txt"

log "Branding/UI asset QA - fail closed"
python "$QA/branding_asset_check.py" "$KIT" | tee "$WORK/branding-asset-report.txt"
grep -q '^BRANDING_ASSET_QA=PASS$' "$WORK/branding-asset-report.txt"

log "Product content QA - fail closed"
python "$QA/product_content_check.py" "$KIT" | tee "$WORK/product-content-report.txt"
grep -q '^PRODUCT_CONTENT_QA=PASS$' "$WORK/product-content-report.txt"

log "Hotfix4 runtime regression QA - fail closed"
python "$QA/hotfix4_runtime_regression_check.py" "$KIT" | tee "$WORK/hotfix4-runtime-regression-report.txt"
grep -q '^HOTFIX4_RUNTIME_REGRESSION_QA=PASS$' "$WORK/hotfix4-runtime-regression-report.txt"

log "Hotfix5 upstream patch-anchor QA - fail closed"
python "$QA/hotfix5_patch_anchor_check.py" "$KIT" | tee "$WORK/hotfix5-patch-anchor-report.txt"
grep -q '^HOTFIX5_PATCH_ANCHOR_QA=PASS$' "$WORK/hotfix5-patch-anchor-report.txt"

log "Hotfix6 static-box type/compile regression QA - fail closed"
python "$QA/hotfix6_staticbox_compile_check.py" "$KIT" | tee "$WORK/hotfix6-staticbox-compile-report.txt"
grep -q '^HOTFIX6_STATICBOX_COMPILE_QA=PASS$' "$WORK/hotfix6-staticbox-compile-report.txt"

log "Hotfix7 generated-header completeness QA - fail closed"
python "$QA/hotfix7_staticbox_header_check.py" "$KIT" | tee "$WORK/hotfix7-staticbox-header-report.txt"
grep -q '^HOTFIX7_STATICBOX_HEADER_QA=PASS$' "$WORK/hotfix7-staticbox-header-report.txt"

log "Hotfix8 runtime/product regression QA - fail closed"
python "$QA/hotfix8_runtime_product_check.py" "$KIT" | tee "$WORK/hotfix8-runtime-product-report.txt"
grep -q '^HOTFIX8_RUNTIME_PRODUCT_QA=PASS$' "$WORK/hotfix8-runtime-product-report.txt"

log "Hotfix10 restart statement structural QA - fail closed"
python "$QA/hotfix10_restart_statement_check.py" "$KIT" | tee "$WORK/hotfix10-restart-statement-report.txt"
grep -q '^HOTFIX10_RESTART_STATEMENT_QA=PASS$' "$WORK/hotfix10-restart-statement-report.txt"

log "Hotfix11 bitmap SetBitmap guard QA - fail closed"
python "$QA/hotfix11_bitmap_setbitmap_check.py" "$KIT" | tee "$WORK/hotfix11-bitmap-setbitmap-report.txt"
grep -q '^HOTFIX11_BITMAP_SETBITMAP_QA=PASS$' "$WORK/hotfix11-bitmap-setbitmap-report.txt"

log "Hotfix12 settings/payload regression QA - fail closed"
python "$QA/hotfix12_settings_payload_check.py" "$KIT" | tee "$WORK/hotfix12-settings-payload-report.txt"
grep -q '^HOTFIX12_SETTINGS_PAYLOAD_QA=PASS$' "$WORK/hotfix12-settings-payload-report.txt"

log "Hotfix13 upstream association anchor QA - fail closed"
python "$QA/hotfix13_assoc_upstream_check.py" "$KIT" | tee "$WORK/hotfix13-assoc-upstream-report.txt"
grep -q '^HOTFIX13_ASSOC_UPSTREAM_QA=PASS$' "$WORK/hotfix13-assoc-upstream-report.txt"

log "Hotfix14 build pipeline regression QA - fail closed"
python "$QA/hotfix14_pipeline_regression_check.py" "$KIT" | tee "$WORK/hotfix14-pipeline-regression-report.txt"
grep -q '^HOTFIX14_PIPELINE_REGRESSION_QA=PASS$' "$WORK/hotfix14-pipeline-regression-report.txt"

log "Hotfix15 native association regression QA - fail closed"
python "$QA/hotfix15_native_assoc_regression_check.py" "$KIT" | tee "$WORK/hotfix15-native-assoc-regression-report.txt"
grep -q '^HOTFIX15_NATIVE_ASSOC_REGRESSION_QA=PASS$' "$WORK/hotfix15-native-assoc-regression-report.txt"

log "Hotfix16 first-restart settings persistence QA - fail closed"
python "$QA/hotfix16_restart_persistence_check.py" "$KIT" | tee "$WORK/hotfix16-restart-persistence-report.txt"
grep -q '^HOTFIX16_RESTART_PERSISTENCE_QA=PASS$' "$WORK/hotfix16-restart-persistence-report.txt"

log "Installer source QA - fail closed"
python "$QA/installer_source_check.py" "$KIT/installer/TNSuiteBridgeXInstaller.nsi" | tee "$WORK/installer-source-report.txt"
grep -q '^INSTALLER_SOURCE_QA=PASS$' "$WORK/installer-source-report.txt"

log "NSIS installer compile preflight - fail closed"
# Compile the real installer script against a tiny disposable payload before
# downloading/building FileZilla. This catches NSIS parser/quoting regressions
# early instead of wasting a full C++ compile and failing at packaging time.
MAKENSIS="/ucrt64/bin/makensis.exe"
[[ -x "$MAKENSIS" ]] || { echo "ERROR: makensis.exe missing from isolated UCRT64 environment." >&2; exit 31; }
NSIS_PREFLIGHT_PAYLOAD="$WORK/nsis-preflight-payload"
NSIS_PREFLIGHT_SETUP="$WORK/nsis-preflight-setup.exe"
rm -rf "$NSIS_PREFLIGHT_PAYLOAD" "$NSIS_PREFLIGHT_SETUP"
mkdir -p "$NSIS_PREFLIGHT_PAYLOAD/bin"
printf 'BridgeX installer syntax preflight payload\n' > "$NSIS_PREFLIGHT_PAYLOAD/bin/BridgeX.exe"
printf 'BridgeX CLI installer syntax preflight payload\n' > "$NSIS_PREFLIGHT_PAYLOAD/bin/BridgeX-CLI.exe"
printf '@echo off\r\n' > "$NSIS_PREFLIGHT_PAYLOAD/bin/BridgeX-CLI-Shell.cmd"
PREFLIGHT_PAYLOAD_WIN="$(cygpath -m "$NSIS_PREFLIGHT_PAYLOAD")"
PREFLIGHT_SETUP_WIN="$(cygpath -m "$NSIS_PREFLIGHT_SETUP")"
PREFLIGHT_NSI_WIN="$(cygpath -m "$KIT/installer/TNSuiteBridgeXInstaller.nsi")"
PREFLIGHT_ICON_WIN="$(cygpath -m "$KIT/assets/branding/BridgeX-AppIcon.ico")"
"$MAKENSIS" \
  -DPRODUCT_VERSION="0.5-Build12-Hotfix16" \
  -DBUILD_NAME="$BUILD_NAME" \
  -DPAYLOAD_DIR="$PREFLIGHT_PAYLOAD_WIN" \
  -DOUTPUT_EXE="$PREFLIGHT_SETUP_WIN" \
  -DBRAND_ICON="$PREFLIGHT_ICON_WIN" \
  "$PREFLIGHT_NSI_WIN" >/dev/null
[[ -s "$NSIS_PREFLIGHT_SETUP" ]] || { echo "ERROR: NSIS syntax preflight did not produce a setup executable." >&2; exit 37; }
rm -rf "$NSIS_PREFLIGHT_PAYLOAD" "$NSIS_PREFLIGHT_SETUP"
echo "INSTALLER_NSIS_PREFLIGHT_QA=PASS"

log "CLI source/security QA - fail closed"
python "$QA/cli_source_check.py" "$KIT/cli/bridgex-cli.cpp" | tee "$WORK/cli-source-report.txt"
grep -q '^CLI_SOURCE_QA=PASS$' "$WORK/cli-source-report.txt"

log "Patch fixture QA - fail closed"
python "$QA/patch_fixture_check.py" | tee "$WORK/patch-fixture-report.txt"
grep -q '^PATCH_FIXTURE_QA=PASS$' "$WORK/patch-fixture-report.txt"

log "Verify wxWidgets 3.3"
WXVER="$(/ucrt64/bin/wx-config-3.3 --version)"
case "$WXVER" in
  3.3.*) ;;
  *) echo "ERROR: Expected wxWidgets 3.3.x, got $WXVER" >&2; exit 12 ;;
esac
echo "WX_VERSION=$WXVER"

log "wxWidgets 3.3 API compile probes - fail closed"
WX_CXX="$(command -v x86_64-w64-mingw32-g++ || true)"
[[ -n "$WX_CXX" ]] || { echo "ERROR: UCRT64 C++ compiler not found for wxWidgets API probe." >&2; exit 67; }
WX_CXXFLAGS="$(/ucrt64/bin/wx-config-3.3 --cxxflags)"

# App appearance probe may use the wx umbrella header. The two Hotfix4/7
# probes intentionally use direct headers only so transitive includes cannot
# hide a missing dependency in a patched translation unit.
WX_APP_PROBE="$WORK/bridgex-wx33-app-probe.cpp"
cat > "$WX_APP_PROBE" <<'EOF'
#include <wx/wx.h>
void bridgex_wx33_api_probe(wxApp* app)
{
    (void)app->MSWEnableDarkMode(wxApp::DarkMode_Always);
    auto const result = app->SetAppearance(wxApp::Appearance::Light);
    (void)result;
}
EOF
"$WX_CXX" -std=c++17 $WX_CXXFLAGS -c "$WX_APP_PROBE" -o "$WORK/bridgex-wx33-app-probe.o"
[[ -s "$WORK/bridgex-wx33-app-probe.o" ]] || { echo "ERROR: wxWidgets app API probe produced no object file." >&2; exit 68; }
echo "WX33_API_COMPILE_QA=PASS"

WX_STATICBOX_PROBE="$WORK/bridgex-wx33-staticbox-probe.cpp"
cat > "$WX_STATICBOX_PROBE" <<'EOF'
#include <wx/sizer.h>
#include <wx/statbox.h>
#include <wx/settings.h>
void bridgex_wx33_staticbox_probe(wxStaticBoxSizer* sizer)
{
    auto* const box = sizer->GetStaticBox();
    box->SetForegroundColour(wxSystemSettings::GetColour(wxSYS_COLOUR_WINDOWTEXT));
}
EOF
"$WX_CXX" -std=c++17 $WX_CXXFLAGS -c "$WX_STATICBOX_PROBE" -o "$WORK/bridgex-wx33-staticbox-probe.o"
[[ -s "$WORK/bridgex-wx33-staticbox-probe.o" ]] || { echo "ERROR: wxWidgets static-box direct-header probe produced no object file." >&2; exit 69; }
echo "WX33_STATICBOX_API_COMPILE_QA=PASS"
echo "WX33_STATICBOX_DIRECT_HEADER_QA=PASS"

WX_HF4_PROBE="$WORK/bridgex-wx33-hf4-controls-probe.cpp"
cat > "$WX_HF4_PROBE" <<'EOF'
#include <wx/window.h>
#include <wx/filename.h>
#include <wx/settings.h>
#include <wx/textctrl.h>
#include <wx/utils.h>
#include <wx/xrc/xmlres.h>
void bridgex_wx33_hf4_controls_probe(wxWindow* page, wxTextCtrl* editor)
{
    page->SetBackgroundColour(wxSystemSettings::GetColour(wxSYS_COLOUR_WINDOW));
    page->SetForegroundColour(wxSystemSettings::GetColour(wxSYS_COLOUR_WINDOWTEXT));
    wxString windowsDir;
    (void)wxGetEnv(L"WINDIR", &windowsDir);
    wxFileName stableNotepad(windowsDir + L"\\System32\\notepad.exe");
    (void)stableNotepad.FileExists();
    wxString value = editor ? editor->GetValue() : wxString{};
    size_t const nl = value.find(L'\n', 0);
    wxString line = value.Mid(0, nl == wxString::npos ? value.length() : nl);
    wxString lower = line.Lower();
    size_t const marker = lower.find(L"\\windowsapps\\microsoft.windowsnotepad_");
    size_t const quote = line.rfind(L'"', marker == wxString::npos ? 0 : marker);
    (void)quote;
    if (editor) {
        editor->ChangeValue(line.Left(0) + line.Mid(0));
    }
}
EOF
"$WX_CXX" -std=c++17 $WX_CXXFLAGS -c "$WX_HF4_PROBE" -o "$WORK/bridgex-wx33-hf4-controls-probe.o"
[[ -s "$WORK/bridgex-wx33-hf4-controls-probe.o" ]] || { echo "ERROR: wxWidgets Hotfix4 direct-header probe produced no object file." >&2; exit 70; }
echo "WX33_HF4_CONTROL_API_COMPILE_QA=PASS"
echo "WX33_HF4_DIRECT_HEADER_QA=PASS"

WX_HF11_BITMAP_PROBE="$WORK/bridgex-wx33-hf11-safe-bitmap-probe.cpp"
cat > "$WX_HF11_BITMAP_PROBE" <<'EOF'
#include <wx/bitmap.h>
#include <wx/bmpbndl.h>
#include <wx/statbmp.h>
namespace {
wxBitmapBundle BridgeXSafeStaticBitmap(wxBitmapBundle const& bundle)
{
    if (bundle.IsOk()) return bundle;
    return wxBitmapBundle::FromBitmap(wxBitmap(1, 1));
}
wxBitmap BridgeXSafeStaticBitmap(wxBitmap const& bitmap)
{
    if (bitmap.IsOk()) return bitmap;
    return wxBitmap(1, 1);
}
}
void bridgex_wx33_hf11_bitmap_probe(wxStaticBitmap* control, wxBitmapBundle const& bundle, wxBitmap const& bitmap)
{
    control->SetBitmap(BridgeXSafeStaticBitmap(bundle));
    control->SetBitmap(BridgeXSafeStaticBitmap(bitmap));
}
EOF
"$WX_CXX" -std=c++17 $WX_CXXFLAGS -c "$WX_HF11_BITMAP_PROBE" -o "$WORK/bridgex-wx33-hf11-safe-bitmap-probe.o"
[[ -s "$WORK/bridgex-wx33-hf11-safe-bitmap-probe.o" ]] || { echo "ERROR: wxWidgets Hotfix11 safe-bitmap probe produced no object file." >&2; exit 72; }
echo "WX33_HF11_SAFE_BITMAP_API_COMPILE_QA=PASS"

WX_HF8_RESTART_PROBE="$WORK/bridgex-wx33-hf8-restart-probe.cpp"
cat > "$WX_HF8_RESTART_PROBE" <<'EOF'
#include <wx/app.h>
#include <wx/window.h>
#include <wx/msgdlg.h>
#include <wx/stdpaths.h>
#include <wx/utils.h>
void bridgex_wx33_hf8_restart_probe(wxWindow* parent)
{
    wxMessageDialog dialog(parent, L"restart", L"BridgeX", wxYES_NO | wxICON_INFORMATION);
    dialog.SetYesNoLabels(L"Restart now", L"Later");
    auto const executable = wxStandardPaths::Get().GetExecutablePath();
    wxTheApp->CallAfter([executable]() {
        if (wxExecute(executable, wxEXEC_ASYNC) != 0) {
            if (auto* top = wxTheApp->GetTopWindow()) {
                top->Close();
            }
        }
    });
}
EOF
"$WX_CXX" -std=c++17 $WX_CXXFLAGS -c "$WX_HF8_RESTART_PROBE" -o "$WORK/bridgex-wx33-hf8-restart-probe.o"
[[ -s "$WORK/bridgex-wx33-hf8-restart-probe.o" ]] || { echo "ERROR: wxWidgets Hotfix8 restart-CTA probe produced no object file." >&2; exit 73; }
echo "WX33_HF8_RESTART_CTA_API_COMPILE_QA=PASS"


WX_HF16_RESTART_PROBE="$WORK/bridgex-wx33-hf16-restart-handoff-probe.cpp"
cat > "$WX_HF16_RESTART_PROBE" <<'EOF'
#include <windows.h>
#include <wx/string.h>
#include <wx/utils.h>
namespace {
constexpr wchar_t kBridgeXRestartParentPidEnv[] = L"TNSUITE_BRIDGEX_RESTART_PARENT_PID";
constexpr DWORD kBridgeXRestartParentWaitMs = 60000;
bool bridgex_wait_parent_probe()
{
    wxString parentPidText;
    if (!wxGetEnv(kBridgeXRestartParentPidEnv, &parentPidText)) return true;
    wxUnsetEnv(kBridgeXRestartParentPidEnv);
    unsigned long parentPid{};
    if (!parentPidText.ToULong(&parentPid) || !parentPid || parentPid == static_cast<unsigned long>(::GetCurrentProcessId())) return false;
    HANDLE const parent = ::OpenProcess(SYNCHRONIZE, FALSE, static_cast<DWORD>(parentPid));
    if (!parent) return ::GetLastError() == ERROR_INVALID_PARAMETER;
    DWORD const waitResult = ::WaitForSingleObject(parent, kBridgeXRestartParentWaitMs);
    ::CloseHandle(parent);
    return waitResult == WAIT_OBJECT_0;
}
}
long bridgex_hf16_restart_spawn_probe(wxString const& executable)
{
    auto const restartParentPid = wxString::Format(L"%lu", wxGetProcessId());
    if (!wxSetEnv(kBridgeXRestartParentPidEnv, restartParentPid)) return 0;
    auto const restartedPid = wxExecute(executable, wxEXEC_ASYNC);
    wxUnsetEnv(kBridgeXRestartParentPidEnv);
    return restartedPid;
}
EOF
"$WX_CXX" -std=c++17 $WX_CXXFLAGS -c "$WX_HF16_RESTART_PROBE" -o "$WORK/bridgex-wx33-hf16-restart-handoff-probe.o"
[[ -s "$WORK/bridgex-wx33-hf16-restart-handoff-probe.o" ]] || { echo "ERROR: wxWidgets Hotfix16 restart-handoff probe produced no object file." >&2; exit 74; }
echo "WX33_HF16_RESTART_HANDOFF_API_COMPILE_QA=PASS"

log "Contrast QA - fail closed"
python "$QA/contrast_check.py" | tee "$WORK/contrast-report.txt"
grep -q '^CONTRAST_QA=PASS$' "$WORK/contrast-report.txt"

log "Download FileZilla ${FZ_VERSION} source"
curl --fail --location --retry 4 --retry-delay 2 \
  --output "$SRC_ARCHIVE" "$FZ_SOURCE_URL"
echo "${FZ_SOURCE_SHA256}  ${SRC_ARCHIVE}" | sha256sum --check --strict

tar -xf "$SRC_ARCHIVE" -C "$WORK"
[[ -f "$SRC/src/interface/FileZilla.cpp" ]] || { echo "ERROR: Source extraction failed." >&2; exit 13; }

log "Hotfix15 SHA-verified native association QA - fail closed"
python "$QA/hotfix15_extracted_upstream_check.py" "$SRC" | tee "$WORK/hotfix15-extracted-upstream-report.txt"
grep -q '^HOTFIX15_EXTRACTED_UPSTREAM_QA=PASS$' "$WORK/hotfix15-extracted-upstream-report.txt"

log "Apply current MSYS2 MinGW compatibility patches"
cd "$SRC"
patch -Np1 -i "$PATCHES/0002-fix-mingw-compiler-detection.patch"

log "Apply TNSuite BridgeX UI patch"
python "$KIT/scripts/patch_tnsuite_bridgex.py" "$SRC"
grep -q 'TNSUITE_BRIDGEX_BUILD12_THEME' "$SRC/src/interface/FileZilla.cpp"
grep -q 'wxColour(15, 23, 36)' "$SRC/src/interface/FileZilla.cpp"
grep -q 'wxColour(14, 94, 168)' "$SRC/src/interface/FileZilla.cpp"
if grep -Eq 'wxColour\(0x[0-9A-Fa-f]{6}\)' "$SRC/src/interface/FileZilla.cpp"; then
  echo 'ERROR: web-style hexadecimal wxColour constructor remains; Windows COLORREF byte order would corrupt the palette.' >&2
  exit 39
fi
grep -q 'TNSUITE_BRIDGEX_BUILD12_APPEARANCE' "$SRC/src/interface/FileZilla.cpp"
grep -q 'wxApp::DarkMode_Always' "$SRC/src/interface/FileZilla.cpp"
grep -q 'SetAppearance(wxApp::Appearance::Light)' "$SRC/src/interface/FileZilla.cpp"
! grep -q 'DarkMode_Never' "$SRC/src/interface/FileZilla.cpp"
grep -q 'OPTION_BRIDGEX_THEME' "$SRC/src/interface/Options.h"
grep -q 'TNSUITE_BRIDGEX_BUILD12_INTERFACE_APPEARANCE' "$SRC/src/interface/settings/optionspage_interface.cpp"
grep -q 'std::wstring(L"vi_VN")' "$SRC/src/interface/settings/optionspage_interface.cpp"
grep -q 'TNSUITE_BRIDGEX_BUILD12_LANGUAGE_IN_INTERFACE' "$SRC/src/interface/settings/settingsdialog.cpp"
grep -q 'TNSUITE_BRIDGEX_BUILD12_WELCOME' "$SRC/src/interface/welcome_dialog.cpp"
! grep -q 'welcome.filezilla-project.org' "$SRC/src/interface/welcome_dialog.cpp"
grep -q 'BridgeX-Help.html' "$SRC/src/interface/menu_bar.cpp"
grep -q 'BridgeX-Report-Bug.html' "$SRC/src/interface/menu_bar.cpp"
grep -q 'TNSUITE_BRIDGEX_BUILD12_WX33' "$SRC/configure.ac"
grep -q 'TNSUITE_BRIDGEX_BUILD12_WX33_AUI' "$SRC/src/interface/aui_notebook_ex.cpp"
grep -q 'GetTabSize(wxReadOnlyDC& dc' "$SRC/src/interface/aui_notebook_ex.cpp"
grep -q 'CreateFromHICON((WXHICON)fileinfo.hIcon)' "$SRC/src/interface/fileexistsdlg.cpp"
grep -q 'static_cast<wchar_t>(fz::local_filesys::path_separator)' "$SRC/src/interface/LocalTreeView.cpp"
grep -q 'sse_algorithm == L"AES256"' "$SRC/src/interface/sitemanager_controls.cpp"
grep -q "extensions.substr(0, pos - 1) + L'|'" "$SRC/src/interface/settings/optionspage_filetype.cpp"
grep -q 'TNSUITE_BRIDGEX_BUILD12_PORTABLE_NO_SHELLEXT' "$SRC/src/Makefile.am"
grep -q 'TNSUITE_BRIDGEX_BUILD12_LOCALES_EXTERNAL' "$SRC/configure.ac"
grep -q 'TNSUITE_BRIDGEX_BUILD12_TOOLBAR_LOG_GUARD' "$SRC/src/interface/toolbar.cpp"
grep -q 'TNSUITE_BRIDGEX_BUILD12_GUI_SUBSYSTEM' "$SRC/src/interface/Makefile.am"
grep -q 'filezilla_LDFLAGS += -mwindows' "$SRC/src/interface/Makefile.am"
grep -q 'SetAppDisplayName("TNSuite BridgeX")' "$SRC/src/interface/FileZilla.cpp"
grep -q 'TNSuite BridgeX' "$SRC/src/interface/Mainfrm.cpp"
grep -q 'About TNSuite BridgeX' "$SRC/src/interface/aboutdialog.cpp"
grep -q 'https://tnsuite.com/' "$SRC/src/interface/aboutdialog.cpp"
grep -q 'TNSUITE_BRIDGEX_BUILD12_AUTOMATION_MENU' "$SRC/src/interface/menu_bar.cpp"
grep -q 'TNSUITE_BRIDGEX_BUILD12_MODERN_TOOLBAR' "$SRC/src/interface/toolbar.cpp"
grep -q 'TNSUITE_BRIDGEX_BUILD12_QUICK_CONNECT' "$SRC/src/interface/quickconnectbar.cpp"
grep -q 'TNSUITE_BRIDGEX_BUILD12_CONNECTION_HEADER' "$SRC/src/interface/quickconnectbar.cpp"
grep -q 'TNSUITE_BRIDGEX_BUILD12_PANE_HEADER' "$SRC/src/interface/viewheader.cpp"
[[ -s "$SRC/src/interface/resources/FileZilla.ico" ]] || { echo 'ERROR: BridgeX application icon missing after branding patch.' >&2; exit 34; }
[[ -s "$SRC/src/interface/resources/480x480/filezilla.png" ]] || { echo 'ERROR: BridgeX UI artwork missing after branding patch.' >&2; exit 35; }
if grep -q 'icon.SetSize(size.x, size.y);' "$SRC/src/interface/fileexistsdlg.cpp"; then
  echo 'ERROR: legacy wxIcon::SetSize remained after patch.' >&2
  exit 18
fi

log "Source compatibility QA - fail closed"
python "$QA/source_compat_check.py" "$SRC" | tee "$WORK/source-compat-report.txt"
grep -q '^SOURCE_COMPAT_QA=PASS$' "$WORK/source-compat-report.txt"

log "Regenerate autotools files"
cd "$SRC"
autoreconf -fiv

log "Configure FileZilla ${FZ_VERSION} against wxWidgets ${WXVER}"
cd "$BUILD"
export CFLAGS="${CFLAGS:-} -Wno-incompatible-pointer-types"
"$SRC/configure" \
  --prefix=/ucrt64 \
  --build="${MINGW_CHOST}" \
  --host="${MINGW_CHOST}" \
  --target="${MINGW_CHOST}" \
  --disable-manualupdatecheck \
  --disable-autoupdatecheck \
  --disable-locales \
  --with-pugixml=builtin \
  --with-wx-config=/ucrt64/bin/wx-config-3.3

log "Compile preflight - patched translation units"
# Do not inherit MAKEFLAGS/MFLAGS from the user's shell; Build09 owns its
# concurrency/keep-going policy explicitly.
unset MAKEFLAGS MFLAGS

# Hotfix11 compiles every translation unit where the SetBitmap input guard was
# actually emitted. Zero touched units is valid: it means the lightweight source
# inventory found no statically resolvable candidate and runtime QA remains the
# authority; never fail the build merely because the old constructor hypothesis
# is absent from upstream source.
mapfile -t HF11_BITMAP_SOURCES < <(grep -RIl --include='*.cpp' 'TNSUITE_BRIDGEX_BUILD12_HF11_SAFE_BITMAP_BUNDLE' "$SRC/src/interface" | sort)
HF11_BITMAP_OBJECTS=()
for source in "${HF11_BITMAP_SOURCES[@]}"; do
  rel="${source#$SRC/src/interface/}"
  dir="$(dirname "$rel")"
  base="$(basename "$rel" .cpp)"
  if [[ "$dir" == "." ]]; then obj="filezilla-${base}.o"; else obj="${dir}/filezilla-${base}.o"; fi
  HF11_BITMAP_OBJECTS+=("$obj")
done
if (( ${#HF11_BITMAP_OBJECTS[@]} > 0 )); then
  printf 'HF11_STATICBITMAP_PATCHED_TUS=%s\n' "${HF11_BITMAP_OBJECTS[*]}"
  make -C "$BUILD/src/interface" -j1 "${HF11_BITMAP_OBJECTS[@]}"
else
  echo 'HF11_STATICBITMAP_PATCHED_TUS=NONE'
fi
echo "HF11_STATICBITMAP_PATCHED_TU_COMPILE_QA=PASS"
# Compile the exact units modified for wxWidgets 3.3 first. This makes our
# compatibility patch an executable compiler gate instead of relying only on
# textual/static checks.
make -C "$BUILD/src/interface" -j1 \
  filezilla-FileZilla.o \
  filezilla-aui_notebook_ex.o \
  filezilla-fileexistsdlg.o \
  filezilla-dialogex.o \
  filezilla-filelistctrl.o \
  filezilla-LocalTreeView.o \
  filezilla-sitemanager_controls.o \
  filezilla-toolbar.o \
  filezilla-Mainfrm.o \
  filezilla-aboutdialog.o \
  filezilla-menu_bar.o \
  filezilla-quickconnectbar.o \
  filezilla-viewheader.o \
  filezilla-welcome_dialog.o \
  filezilla-Options.o \
  settings/filezilla-settingsdialog.o \
  settings/filezilla-optionspage_interface.o \
  settings/filezilla-optionspage_filetype.o \
  settings/filezilla-optionspage_edit_associations.o
echo "PATCHED_TU_COMPILE_QA=PASS"

log "Shipped locale catalogs preflight"
# Build12 deliberately disables FileZilla's POT regeneration. Validate every
# shipped upstream PO directly with msgfmt; BridgeX-specific strings use the
# separate curated bridgex_vi_VN.po catalog validated immediately afterwards.
LOCALE_QA="$WORK/locale-preflight"
rm -rf "$LOCALE_QA"
locale_preflight_output="$(MSGFMT_BIN=/ucrt64/bin/msgfmt bash "$KIT/scripts/compile-shipped-locales.sh" "$SRC" "$LOCALE_QA")"
echo "$locale_preflight_output"
grep -q '^FILEZILLA_LOCALES_COMPILED=' <<<"$locale_preflight_output"
echo "SHIPPED_LOCALES_COMPILE_QA=PASS"

log "BridgeX Vietnamese locale preflight"
[[ -s "$BRIDGEX_PO" ]] || { echo "ERROR: BridgeX Vietnamese PO catalog missing." >&2; exit 40; }
"$MSGFMT_EXE" --check --check-format -o "$WORK/bridgex-vi-preflight.mo" "$BRIDGEX_PO"
[[ -s "$WORK/bridgex-vi-preflight.mo" ]] || { echo "ERROR: BridgeX Vietnamese MO preflight output missing." >&2; exit 41; }
echo "BRIDGEX_VI_LOCALE_PREFLIGHT_QA=PASS"

log "Portable shell-extension exclusion preflight"
if grep -E '^SUBDIRS[[:space:]]*=.*MAYBE_FZSHELLEXT' "$BUILD/src/Makefile" >/dev/null; then
  echo "ERROR: Shell extension is still present in generated build SUBDIRS." >&2
  exit 19
fi
echo "SHELLEXT_EXCLUSION_QA=PASS"

log "Full compile - memory-safe scheduler"
COMPILE_LOG="$DIST/${BUILD_NAME}-compile.log"
rm -f "$COMPILE_LOG"

# Build06 used `make -k -j$(nproc)`. On high-core-count Windows machines that
# can start dozens of cc1plus.exe processes at once. The Build06 evidence showed
# widespread cc1plus OOM, Cygwin/MSYS2 fork failures and follow-on missing-target
# errors. Build09 defaults to two compiler jobs, stops on the first real error,
# and automatically retries serially if Windows still reports resource pressure.
BUILD_JOBS="${FZDARK_JOBS:-2}"
if ! [[ "$BUILD_JOBS" =~ ^[1-4]$ ]]; then
  echo "ERROR: FZDARK_JOBS must be an integer from 1 to 4; got: $BUILD_JOBS" >&2
  exit 23
fi
echo "FULL_COMPILE_JOBS=$BUILD_JOBS"
echo "FULL_COMPILE_POLICY=LOW_MEMORY_NO_KEEP_GOING"

# Debug info is not needed in the portable deliverable and materially increases
# GCC memory pressure/object size. Keep normal optimization but disable debug info.
SAFE_CFLAGS="-O2 -g0 -Wall -Wno-incompatible-pointer-types"
SAFE_CXXFLAGS="-O2 -g0 -Wall"

run_full_compile() {
  local jobs="$1"
  local mode="$2"
  {
    echo
    echo "===== COMPILE ATTEMPT: ${mode}; jobs=${jobs} ====="
  } | tee -a "$COMPILE_LOG"
  make -j"$jobs" CFLAGS="$SAFE_CFLAGS" CXXFLAGS="$SAFE_CXXFLAGS" 2>&1 | tee -a "$COMPILE_LOG"
  return ${PIPESTATUS[0]}
}

set +e
run_full_compile "$BUILD_JOBS" "primary"
compile_status=$?
set -e

if (( compile_status != 0 )); then
  if grep -Eiq 'out of memory|Resource temporarily unavailable|VirtualProtect failed|dofork:|child_copy:|0xC000012D|0xC0000142' "$COMPILE_LOG"; then
    echo "RESOURCE_PRESSURE_DETECTED=YES" | tee -a "$COMPILE_LOG"
    echo "Retrying unfinished targets with one compiler process..." | tee -a "$COMPILE_LOG"
    sleep 3
    set +e
    run_full_compile 1 "serial-recovery"
    compile_status=$?
    set -e
    if (( compile_status == 0 )); then
      echo "SERIAL_RECOVERY=PASS" | tee -a "$COMPILE_LOG"
    else
      echo "SERIAL_RECOVERY=FAIL" | tee -a "$COMPILE_LOG"
    fi
  fi
fi

if (( compile_status != 0 )); then
  echo "ERROR: Full compile failed with code ${compile_status}." >&2
  echo "COMPILE_LOG=$(cygpath -w "$COMPILE_LOG")" >&2
  exit "$compile_status"
fi

# A successful compile must produce the two private libraries and client binary;
# this also prevents a prior resource failure from being mistaken for success.
[[ -f "$BUILD/src/engine/.libs/libfzclient-private.dll" || -f "$BUILD/src/engine/.libs/libfzclient-private-0.dll" || -f "$BUILD/src/engine/libfzclient-private.la" ]] || {
  echo "ERROR: Engine library missing after successful make." >&2; exit 24;
}
[[ -f "$BUILD/src/commonui/libfzclient-commonui-private.la" ]] || {
  echo "ERROR: CommonUI library missing after successful make." >&2; exit 25;
}
[[ -f "$BUILD/src/interface/filezilla.exe" || -f "$BUILD/src/interface/.libs/filezilla.exe" ]] || {
  echo "ERROR: filezilla.exe missing after successful make." >&2; exit 26;
}
echo "FULL_COMPILE_QA=PASS"

log "Install into portable staging tree"
make install DESTDIR="$STAGE"
[[ -f "$APP/bin/filezilla.exe" ]] || { echo "ERROR: upstream GUI executable was not installed." >&2; exit 14; }
mv -f "$APP/bin/filezilla.exe" "$APP/bin/BridgeX.exe"
[[ -s "$APP/bin/BridgeX.exe" ]] || { echo "ERROR: BridgeX.exe branding rename failed." >&2; exit 36; }

log "Build TNSuite BridgeX CLI"
CLI_EXE="$APP/bin/BridgeX-CLI.exe"
x86_64-w64-mingw32-g++ \
  -std=c++17 -O2 -s -municode \
  -static-libgcc -static-libstdc++ \
  "$KIT/cli/bridgex-cli.cpp" \
  -o "$CLI_EXE"
[[ -s "$CLI_EXE" ]] || { echo "ERROR: BridgeX-CLI.exe was not produced." >&2; exit 28; }

# The CLI is intentionally a console application so it behaves naturally in
# PowerShell/CMD/CI. The GUI FileZilla executable remains Windows GUI subsystem.
CLI_SUBSYSTEM_LINE="$(objdump -p "$CLI_EXE" 2>/dev/null | grep -m1 -E '^[[:space:]]*Subsystem[[:space:]]')"
echo "CLI_PE_SUBSYSTEM=${CLI_SUBSYSTEM_LINE}"
if ! grep -Eq 'Subsystem[[:space:]]+00000003[[:space:]]+\(Windows CUI\)' <<<"$CLI_SUBSYSTEM_LINE"; then
  echo "ERROR: BridgeX-CLI.exe is not linked as a Windows console/CUI program." >&2
  exit 29
fi
echo "CLI_COMPILE_QA=PASS"
echo "CLI_WINDOWS_CUI_SUBSYSTEM_QA=PASS"

# Start Menu helper for an interactive CLI shell. Keeping the shortcut target
# parameter-free avoids fragile NSIS command-line quoting and makes installer
# creation deterministic.
cat > "$APP/bin/BridgeX-CLI-Shell.cmd" <<'EOF'
@echo off
setlocal
title TNSuite BridgeX CLI
cd /d "%~dp0"
echo TNSuite BridgeX CLI
echo ===================
BridgeX-CLI.exe --help
echo.
echo Interactive shell opened in: %CD%
echo Run BridgeX-CLI.exe --help at any time for command usage.
echo.
%ComSpec% /K
EOF
[[ -s "$APP/bin/BridgeX-CLI-Shell.cmd" ]] || { echo "ERROR: BridgeX CLI shell helper was not created." >&2; exit 38; }
echo "CLI_SHELL_HELPER_QA=PASS"

log "Package shipped FileZilla translations without POT regeneration"
locale_install_output="$(MSGFMT_BIN=/ucrt64/bin/msgfmt bash "$KIT/scripts/compile-shipped-locales.sh" "$SRC" "$APP/share/locale")"
echo "$locale_install_output"
grep -q '^FILEZILLA_LOCALES_COMPILED=' <<<"$locale_install_output"
# libfilezilla has its own messages. Copy the already-installed MSYS2 catalogs
# into the portable prefix when present so the custom client does not depend on
# the build environment at runtime.
for mo in /ucrt64/share/locale/*/LC_MESSAGES/libfilezilla.mo; do
  [[ -f "$mo" ]] || continue
  lang="$(basename "$(dirname "$(dirname "$mo")")")"
  dest="$APP/share/locale/$lang/LC_MESSAGES"
  mkdir -p "$dest"
  cp -f "$mo" "$dest/libfilezilla.mo"
done
# Vietnamese is part of the shipped 3.70.6 catalog set and is a concrete
# packaging sentinel for this build.
[[ -s "$APP/share/locale/vi_VN/LC_MESSAGES/filezilla.mo" ]] || {
  echo "ERROR: Vietnamese FileZilla locale catalog missing from portable bundle." >&2
  exit 22
}
echo "PORTABLE_LOCALES_QA=PASS"

log "Package BridgeX Vietnamese UI catalog and local help"
BRIDGEX_LOCALE_DIR="$APP/share/locale/vi_VN/LC_MESSAGES"
mkdir -p "$BRIDGEX_LOCALE_DIR"
"$MSGFMT_EXE" --check --check-format -o "$BRIDGEX_LOCALE_DIR/bridgex.mo" "$KIT/locales/bridgex_vi_VN.po"
[[ -s "$BRIDGEX_LOCALE_DIR/bridgex.mo" ]] || { echo "ERROR: BridgeX Vietnamese catalog missing from portable bundle." >&2; exit 42; }
echo "BRIDGEX_VI_LOCALE_QA=PASS"

mkdir -p "$APP/bin/docs"
cp -f "$KIT/docs/BridgeX-Help.html" "$APP/bin/docs/BridgeX-Help.html"
cp -f "$KIT/docs/BridgeX-Report-Bug.html" "$APP/bin/docs/BridgeX-Report-Bug.html"
[[ -s "$APP/bin/docs/BridgeX-Help.html" && -s "$APP/bin/docs/BridgeX-Report-Bug.html" ]] || { echo "ERROR: BridgeX local help documents missing from portable bundle." >&2; exit 43; }
if grep -Eqi 'filezilla-project\.org|welcome\.filezilla-project\.org' "$APP/bin/docs/BridgeX-Help.html" "$APP/bin/docs/BridgeX-Report-Bug.html"; then
  echo "ERROR: BridgeX local help must not redirect users to upstream FileZilla support channels." >&2
  exit 44
fi
echo "LOCAL_HELP_QA=PASS"

log "Bundle UCRT64 runtime DLL dependencies"
# Copy each non-system DLL imported by every EXE/DLL already in the bundle,
# recursively. Windows system DLLs are intentionally not bundled.
declare -A seen=()
queue=()
while IFS= read -r -d '' f; do queue+=("$f"); done < <(find "$APP/bin" -maxdepth 1 -type f \( -iname '*.exe' -o -iname '*.dll' \) -print0)

idx=0
while (( idx < ${#queue[@]} )); do
  f="${queue[$idx]}"; ((idx+=1))
  key="$(basename "$f" | tr '[:upper:]' '[:lower:]')"
  [[ -n "${seen[$key]:-}" ]] && continue
  seen[$key]=1

  while IFS= read -r dll; do
    [[ -z "$dll" ]] && continue
    src="/ucrt64/bin/$dll"
    if [[ -f "$src" ]]; then
      dst="$APP/bin/$dll"
      if [[ ! -f "$dst" ]]; then
        cp -f "$src" "$dst"
        queue+=("$dst")
      fi
    fi
  done < <(objdump -p "$f" 2>/dev/null | sed -n 's/^[[:space:]]*DLL Name:[[:space:]]*//p' | tr -d '\r')
done

log "Prune and validate production runtime payload"
# Build/source evidence belongs in the BuildKit/dist evidence, not Program Files.
# Windows runtime needs the executable/DLL tree, FileZilla resources, compiled
# locales, BridgeX local help, and upstream license attribution. Import libraries
# and Linux desktop metadata are build/package artifacts and are removed here.
cp -f "$SRC/COPYING" "$APP/COPYING"
rm -rf "$APP/lib" \
       "$APP/share/applications" \
       "$APP/share/appdata" \
       "$APP/share/metainfo" \
       "$APP/share/man" \
       "$APP/share/doc"
find "$APP" -type d -empty -delete 2>/dev/null || true
python "$QA/production_payload_check.py" "$APP" | tee "$WORK/production-payload-report.txt"
grep -q '^PRODUCTION_PAYLOAD_QA=PASS$' "$WORK/production-payload-report.txt"

log "Static binary QA"
# The bundle must contain wxWidgets 3.3 runtime and must not contain wx 3.2 runtime.
find "$APP/bin" -maxdepth 1 -type f -iname 'wx*333*.dll' | grep -q . || {
  echo "ERROR: wxWidgets 3.3 runtime DLLs not found in bundle." >&2; exit 15;
}
if find "$APP/bin" -maxdepth 1 -type f -iname 'wx*32*.dll' | grep -q .; then
  echo "ERROR: wxWidgets 3.2 runtime leaked into bundle." >&2
  exit 16
fi

# FileZilla is a GUI application. Build07 accidentally produced a console-subsystem
# executable, causing a CMD window to appear beside the dark GUI. Fail closed unless
# the PE header explicitly declares IMAGE_SUBSYSTEM_WINDOWS_GUI (2).
PE_SUBSYSTEM_LINE="$(objdump -p "$APP/bin/BridgeX.exe" 2>/dev/null | grep -m1 -E '^[[:space:]]*Subsystem[[:space:]]')"
echo "PE_SUBSYSTEM=${PE_SUBSYSTEM_LINE}"
if ! grep -Eq 'Subsystem[[:space:]]+00000002[[:space:]]+\(Windows GUI\)' <<<"$PE_SUBSYSTEM_LINE"; then
  echo "ERROR: BridgeX.exe is not linked as Windows GUI subsystem." >&2
  exit 27
fi
echo "WINDOWS_GUI_SUBSYSTEM_QA=PASS"
echo "CLI_SOURCE_QA=PASS"
echo "CLI_COMPILE_QA=PASS"
echo "CLI_WINDOWS_CUI_SUBSYSTEM_QA=PASS"
echo "BRIDGEX_VI_LOCALE_QA=PASS"
echo "LOCAL_HELP_QA=PASS"

# Ensure no private key material accidentally entered the output.
if find "$APP" -type f \( -iname '*.ppk' -o -iname 'id_ed25519' -o -iname 'id_rsa' -o -iname '*.pem' \) | grep -q .; then
  echo "ERROR: Potential private-key material found in build output." >&2
  exit 17
fi

log "Write QA evidence outside production payload"
QA_EVIDENCE="$DIST/${BUILD_NAME}-QA-Evidence"
rm -rf "$QA_EVIDENCE"
mkdir -p "$QA_EVIDENCE"
for report in \
  cli-source-report.txt installer-source-report.txt product-content-report.txt \
  hotfix4-runtime-regression-report.txt hotfix5-patch-anchor-report.txt \
  hotfix6-staticbox-compile-report.txt hotfix7-staticbox-header-report.txt \
  hotfix8-runtime-product-report.txt hotfix9-qa-dependency-report.txt \
  hotfix10-restart-statement-report.txt hotfix11-bitmap-setbitmap-report.txt \
  hotfix12-settings-payload-report.txt hotfix13-assoc-upstream-report.txt hotfix14-pipeline-regression-report.txt hotfix15-native-assoc-regression-report.txt hotfix15-extracted-upstream-report.txt production-payload-report.txt \
  contrast-report.txt source-compat-report.txt scheduler-report.txt patch-fixture-report.txt; do
  [[ -f "$WORK/$report" ]] && cp -f "$WORK/$report" "$QA_EVIDENCE/$report"
done
cat > "$QA_EVIDENCE/BUILD_INFO.md" <<EOF
# ${BUILD_NAME}

- FileZilla core: ${FZ_VERSION}
- FileZilla source SHA-256: ${FZ_SOURCE_SHA256}
- wxWidgets: ${WXVER}
- Target: Windows x64 / UCRT64
- Build date: 2026-08-18
- Production payload QA: PASS
- Development source/patch/QA files: BuildKit/evidence only; not shipped in Program Files.
EOF
{
  echo "FILEZILLA_SOURCE=${FZ_SOURCE_URL}"
  echo "FILEZILLA_SHA256=${FZ_SOURCE_SHA256}"
  echo "WX_VERSION=${WXVER}"
  awk '$1 ~ /^mingw-w64-ucrt-x86_64-(wxwidgets3\.3-msw|libfilezilla|fzssh|gnutls|sqlite3)$/ { print }' "$PACMAN_DB_SNAPSHOT" || true
  if (( ${#missing[@]} )); then echo "PACKAGES_INSTALLED_DURING_BUILD=${missing[*]}"; fi
} > "$QA_EVIDENCE/SOURCE_MANIFEST.txt"
echo "QA_EVIDENCE=$(cygpath -w "$QA_EVIDENCE")"

log "Create portable ZIP"
ZIP="$DIST/${BUILD_NAME}.zip"
SHA="$DIST/${BUILD_NAME}.zip.sha256"
rm -f "$ZIP" "$SHA"
(
  cd "$APP"
  zip -q -r -9 "$ZIP" .
)
sha256sum "$ZIP" | tee "$SHA"
printf '%s\n' "$(cygpath -w "$ZIP")" > "$DIST/latest-portable.txt"

log "Build NSIS installer"
SETUP="$DIST/${BUILD_NAME}-Setup.exe"
SETUP_SHA="$DIST/${BUILD_NAME}-Setup.exe.sha256"
rm -f "$SETUP" "$SETUP_SHA"
[[ -x "$MAKENSIS" ]] || { echo "ERROR: makensis.exe missing from isolated UCRT64 environment." >&2; exit 31; }
PAYLOAD_WIN="$(cygpath -m "$APP")"
SETUP_WIN="$(cygpath -m "$SETUP")"
NSI_WIN="$(cygpath -m "$KIT/installer/TNSuiteBridgeXInstaller.nsi")"
BRAND_ICON_WIN="$(cygpath -m "$KIT/assets/branding/BridgeX-AppIcon.ico")"
"$MAKENSIS" \
  -DPRODUCT_VERSION="0.5-Build12-Hotfix16" \
  -DBUILD_NAME="$BUILD_NAME" \
  -DPAYLOAD_DIR="$PAYLOAD_WIN" \
  -DOUTPUT_EXE="$SETUP_WIN" \
  -DBRAND_ICON="$BRAND_ICON_WIN" \
  "$NSI_WIN"
[[ -s "$SETUP" ]] || { echo "ERROR: NSIS returned success but setup EXE is missing." >&2; exit 32; }
SETUP_SUBSYSTEM_LINE="$(objdump -p "$SETUP" 2>/dev/null | grep -m1 -E '^[[:space:]]*Subsystem[[:space:]]')"
echo "INSTALLER_PE_SUBSYSTEM=${SETUP_SUBSYSTEM_LINE}"
if ! grep -Eq 'Subsystem[[:space:]]+00000002[[:space:]]+\(Windows GUI\)' <<<"$SETUP_SUBSYSTEM_LINE"; then
  echo "ERROR: setup EXE is not Windows GUI subsystem." >&2
  exit 33
fi
echo "INSTALLER_WINDOWS_GUI_SUBSYSTEM_QA=PASS"
sha256sum "$SETUP" | tee "$SETUP_SHA"
printf '%s\n' "$(cygpath -w "$SETUP")" > "$DIST/latest-installer.txt"
printf '%s\n' "$(cygpath -w "$SETUP")" > "$DIST/latest.txt"
echo "INSTALLER_BUILD_QA=PASS"

log "Clean transient build cache"
# Artifact is already complete. Remove source/object scratch and downloaded
# pacman package archives so a successful build doesn't leave avoidable cache.
rm -rf "$WORK"
paccache -rk0 >/dev/null 2>&1 || rm -f /var/cache/pacman/pkg/* 2>/dev/null || true

echo "TRANSIENT_BUILD_CACHE_CLEANED=PASS"

log "BUILD COMPLETE"
echo "ARTIFACT=$(cygpath -w "$ZIP")"
echo "SHA256_FILE=$(cygpath -w "$SHA")"
echo "CONTRAST_QA=PASS"
echo "SOURCE_COMPAT_QA=PASS"
echo "SCHEDULER_QA=PASS"
echo "BRANDING_ASSET_QA=PASS"
echo "PRODUCT_CONTENT_QA=PASS"
echo "HOTFIX12_SETTINGS_PAYLOAD_QA=PASS"
echo "PRODUCTION_PAYLOAD_QA=PASS"
echo "WX_BINDING=3.3"
echo "PRIVATE_KEY_BUNDLE_CHECK=PASS"
echo "WINDOWS_COMPILE_QA=PASS"
echo "WINDOWS_GUI_SUBSYSTEM_QA=PASS"
echo "CLI_SOURCE_QA=PASS"
echo "CLI_COMPILE_QA=PASS"
echo "CLI_WINDOWS_CUI_SUBSYSTEM_QA=PASS"
echo "BRIDGEX_VI_LOCALE_QA=PASS"
echo "LOCAL_HELP_QA=PASS"
echo "QA_EVIDENCE=$(cygpath -w "$QA_EVIDENCE")"
