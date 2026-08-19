#!/usr/bin/env python3
from pathlib import Path
import re
import sys

if len(sys.argv) != 2:
    raise SystemExit('Usage: source_compat_check.py <patched-filezilla-source-root>')
root = Path(sys.argv[1])
checks=[]

def check(label, ok, detail=''):
    ok=bool(ok); checks.append((label,ok))
    print(('PASS  ' if ok else 'FAIL  ')+label+((' — '+detail) if (detail and not ok) else ''))

def text(path):
    p=root/path
    try: return p.read_text(encoding='utf-8')
    except Exception as e:
        check(f'Read {path}', False, str(e)); return ''

def require(path, needle, label):
    t=text(path); check(label, needle in t, f'missing {needle!r}')

def forbid(path, needle, label):
    t=text(path); check(label, needle not in t, f'forbidden legacy pattern remains: {needle!r}')

# Build12 appearance and the Windows palette byte-order regression.
require(Path('src/interface/FileZilla.cpp'), 'TNSUITE_BRIDGEX_BUILD12_THEME', 'Build12 theme marker')
require(Path('src/interface/FileZilla.cpp'), 'wxColour(15, 23, 36)', 'Dark main surface uses explicit RGB')
require(Path('src/interface/FileZilla.cpp'), 'wxColour(14, 94, 168)', 'Selection uses explicit RGB')
require(Path('src/interface/FileZilla.cpp'), 'MSWEnableDarkMode(wxApp::DarkMode_Always', 'Dark mode path')
require(Path('src/interface/FileZilla.cpp'), 'SetAppearance(wxApp::Appearance::Light)', 'Light mode path uses wxWidgets 3.3.3 SetAppearance API')
forbid(Path('src/interface/FileZilla.cpp'), 'DarkMode_Never', 'Unsupported wxWidgets 3.3.3 DarkMode_Never absent')
ui=text(Path('src/interface/FileZilla.cpp'))
check('No web-style one-argument wxColour constructor', re.search(r'wxColour\(0x[0-9A-Fa-f]{6}\)', ui) is None)
require(Path('src/interface/Options.h'), 'OPTION_BRIDGEX_THEME', 'Persistent BridgeX theme option enum')
require(Path('src/interface/Options.cpp'), '{ "BridgeX Theme", 1, option_flags::numeric_clamp, 0, 1 }', 'Persistent BridgeX theme option registration')
require(Path('src/interface/settings/optionspage_interface.cpp'), 'TNSUITE_BRIDGEX_BUILD12_INTERFACE_APPEARANCE', 'Appearance controls under Interface')
require(Path('src/interface/settings/optionspage_interface.cpp'), 'std::wstring(L"vi_VN")', 'Vietnamese selection persistence')
require(Path('src/interface/settings/optionspage_interface.cpp'), 'std::wstring(L"en_US")', 'English selection persistence')
require(Path('src/interface/settings/settingsdialog.cpp'), 'TNSUITE_BRIDGEX_BUILD12_LANGUAGE_IN_INTERFACE', 'Language moved into Interface')
forbid(Path('src/interface/settings/settingsdialog.cpp'), 'AddPage(_("Language"), new COptionsPageLanguage, 0);', 'Standalone language page removed')
require(Path('src/interface/FileZilla.cpp'), 'AddCatalog(_T("bridgex"))', 'BridgeX translation catalog loaded')

# wxWidgets 3.3 and Build08 runtime compatibility.
require(Path('src/interface/aui_notebook_ex.cpp'), 'GetTabSize(wxReadOnlyDC& dc', 'wx3.3 AUI read-only DC signature')
forbid(Path('src/interface/aui_notebook_ex.cpp'), 'wxAuiNotebook::OnTabDragMotion(evt);', 'Removed wx3.2 AUI drag overload absent')
forbid(Path('src/interface/fileexistsdlg.cpp'), 'icon.SetSize(size.x, size.y);', 'Removed wxIcon::SetSize absent')
require(Path('src/interface/fileexistsdlg.cpp'), 'icon.CreateFromHICON((WXHICON)fileinfo.hIcon)', 'wx3.3 HICON import API')
require(Path('src/interface/fileexistsdlg.cpp'), 'image.Rescale(size.x, size.y, wxIMAGE_QUALITY_HIGH);', 'Shell icon resize preserved')
require(Path('configure.ac'), 'TNSUITE_BRIDGEX_BUILD12_WX33', 'wx3.3 configure override marker')
require(Path('src/interface/toolbar.cpp'), 'TNSUITE_BRIDGEX_BUILD12_TOOLBAR_LOG_GUARD', 'Toolbar spurious-log guard marker')
require(Path('src/interface/toolbar.cpp'), 'wxLogNull suppressSpuriousToolbarLog;', 'Toolbar base-Realize logging suppression is scoped')
require(Path('src/interface/toolbar.cpp'), '::SetLastError(ERROR_SUCCESS);', 'Toolbar clears stale Win32 last-error before base Realize')
require(Path('src/interface/Makefile.am'), 'TNSUITE_BRIDGEX_BUILD12_GUI_SUBSYSTEM', 'Windows GUI-subsystem linker marker')
require(Path('src/interface/Makefile.am'), 'filezilla_LDFLAGS += -mwindows', 'GUI links as Windows subsystem')

# Current UCRT64 compiler compatibility.
require(Path('src/interface/LocalTreeView.cpp'), 'static_cast<wchar_t>(fz::local_filesys::path_separator)', 'LocalTreeView wide path separator')
forbid(Path('src/interface/LocalTreeView.cpp'), 'path + fz::local_filesys::path_separator + pData->m_known_subdir', 'Legacy LocalTreeView narrow separator absent')
for literal in ('AES256','aws:kms','customer'):
    require(Path('src/interface/sitemanager_controls.cpp'), f'sse_algorithm == L"{literal}"', f'S3 SSE wide literal {literal}')
    forbid(Path('src/interface/sitemanager_controls.cpp'), f'sse_algorithm == "{literal}"', f'Legacy S3 narrow literal {literal} absent')
require(Path('src/interface/settings/optionspage_filetype.cpp'), "extensions.substr(0, pos - 1) + L'|'", 'Wide escaped pipe literal')
forbid(Path('src/interface/settings/optionspage_filetype.cpp'), "extensions.substr(0, pos - 1) + '|'", 'Legacy narrow escaped pipe absent')
require(Path('src/Makefile.am'), 'TNSUITE_BRIDGEX_BUILD12_PORTABLE_NO_SHELLEXT', 'Portable shell-extension exclusion marker')
forbid(Path('src/Makefile.am'), '$(MAYBE_STORJ) $(MAYBE_FZSHELLEXT) .', 'Shell extension removed from build SUBDIRS')
require(Path('configure.ac'), 'TNSUITE_BRIDGEX_BUILD12_LOCALES_EXTERNAL', 'External shipped-locale packaging marker')

# Build12-Hotfix4 runtime acceptance fixes.
require(Path('src/interface/dialogex.cpp'), 'TNSUITE_BRIDGEX_BUILD12_HF4_STATICBOX_TEXT', 'Hotfix4 shared static-box text marker')
require(Path('src/interface/dialogex.cpp'), 'TNSUITE_BRIDGEX_BUILD12_HF5_STATICBOX_STRUCTURAL_MATCH', 'Hotfix5 structural static-box anchor marker')
require(Path('src/interface/dialogex.cpp'), 'TNSUITE_BRIDGEX_BUILD12_HF6_STATICBOX_TARGET', 'Hotfix6 static-box target marker')
require(Path('src/interface/dialogex.cpp'), 'TNSUITE_BRIDGEX_BUILD12_HF7_STATICBOX_COMPLETE_TYPE', 'Hotfix7 complete-type marker')
require(Path('src/interface/dialogex.cpp'), '#include <wx/statbox.h>', 'Hotfix7 explicit wxStaticBox complete-type header')
require(Path('src/interface/dialogex.cpp'), '#include <wx/settings.h>', 'Static-box explicit wx system-colour header')
require(Path('src/interface/filelistctrl.cpp'), '#include <wx/settings.h>', 'File-list explicit wx system-colour header')
require(Path('src/interface/dialogex.cpp'), 'GetStaticBox()->SetForegroundColour(wxSystemSettings::GetColour(wxSYS_COLOUR_WINDOWTEXT))', 'Static-box caption colours the owned wxStaticBox')
forbid(Path('src/interface/dialogex.cpp'), 'boxSizer->SetForegroundColour(wxSystemSettings::GetColour(wxSYS_COLOUR_WINDOWTEXT))', 'No colour call on wxStaticBoxSizer')
require(Path('src/interface/dialogex.cpp'), 'wxSYS_COLOUR_WINDOWTEXT', 'Static-box captions follow active appearance text colour')
require(Path('src/interface/settings/optionspage_edit_associations.cpp'), 'TNSUITE_BRIDGEX_BUILD12_HF12_STORE_NOTEPAD_VALUE_REPAIR', 'Hotfix12 stale Store Notepad value-repair marker')
require(Path('src/interface/settings/optionspage_edit_associations.cpp'), 'TNSUITE_BRIDGEX_BUILD12_HF13_VALIDATE_REPAIRED_ASSOCIATIONS', 'Hotfix13 validates repaired association value')
require(Path('src/interface/settings/optionspage_edit_associations.cpp'), 'TNSUITE_BRIDGEX_BUILD12_HF13_PERSIST_REPAIRED_ASSOCIATIONS', 'Hotfix13 persists repaired association value')
require(Path('src/interface/settings/optionspage_edit_associations.cpp'), 'TNSUITE_BRIDGEX_BUILD12_HF15_NATIVE_LOAD_REPAIR', 'Hotfix15 repairs association immediately after native load')
require(Path('src/interface/settings/optionspage_edit_associations.cpp'), 'TNSUITE_BRIDGEX_BUILD12_HF15_NATIVE_VALIDATE_REPAIR', 'Hotfix15 repairs native association before validation')
require(Path('src/interface/settings/optionspage_edit_associations.cpp'), 'TNSUITE_BRIDGEX_BUILD12_HF15_NATIVE_PERSIST_REPAIR', 'Hotfix15 repairs native association before persistence')
require(Path('src/interface/settings/optionspage_edit_associations.cpp'), 'RepairStaleStoreNotepadAssociations(assocs_->GetValue())', 'Hotfix15 repairs discovered native association receiver')
require(Path('src/interface/settings/optionspage_edit_associations.cpp'), 'm_pOptions->set(OPTION_EDIT_CUSTOMASSOCIATIONS, assocs_->GetValue().ToStdWstring());', 'Hotfix15 retains upstream native association persistence')
forbid(Path('src/interface/settings/optionspage_edit_associations.cpp'), 'ID_EDIT_ASSOCIATIONS', 'Stale Hotfix12 hard-coded association ID absent')
require(Path('src/interface/settings/optionspage_edit_associations.cpp'), 'microsoft.windowsnotepad_', 'Store Notepad repair is narrowly scoped')
require(Path('src/interface/settings/optionspage_edit_associations.cpp'), r'System32\\notepad.exe', 'Store Notepad repair targets stable system Notepad')
require(Path('src/interface/settings/optionspage_edit_associations.cpp'), 'Associated program not found:', 'Missing-program validation remains present for other associations')
require(Path('src/interface/filelistctrl.cpp'), 'TNSUITE_BRIDGEX_BUILD12_HF4_LIST_SURFACE', 'Hotfix4 file-list surface marker')
require(Path('src/interface/filelistctrl.cpp'), 'SetBackgroundColour(wxSystemSettings::GetColour(wxSYS_COLOUR_WINDOW))', 'File lists follow active WINDOW background')
require(Path('src/interface/filelistctrl.cpp'), 'SetForegroundColour(wxSystemSettings::GetColour(wxSYS_COLOUR_WINDOWTEXT))', 'File lists follow active WINDOWTEXT foreground')

# Build12-Hotfix8 runtime/product fixes.
iface_path=Path('src/interface/settings/optionspage_interface.cpp')
require(iface_path, 'TNSUITE_BRIDGEX_BUILD12_HF8_RESTART_CTA', 'Hotfix8 restart CTA marker')
for header in ('#include <wx/app.h>', '#include <wx/msgdlg.h>', '#include <wx/stdpaths.h>', '#include <wx/utils.h>'):
    require(iface_path, header, f'Hotfix8 restart CTA direct header {header}')
require(iface_path, 'SetYesNoLabels(_("Restart now"), _("Later"))', 'Hotfix8 restart CTA labels')
for needle in ('oldLanguage', 'newLanguage', 'oldTheme', 'newTheme', 'restartRequired'):
    require(iface_path, needle, f'Hotfix8 restart change detection {needle}')

# Build12-Hotfix16 first-restart persistence lifecycle. The replacement process
# may exist before the parent exits, but it must not construct COptions until the
# parent process is terminated and upstream shutdown persistence has completed.
require(Path('src/interface/FileZilla.cpp'), 'TNSUITE_BRIDGEX_BUILD12_HF16_RESTART_HANDOFF', 'Hotfix16 parent/child restart handoff helper')
require(Path('src/interface/FileZilla.cpp'), 'TNSUITE_BRIDGEX_BUILD12_HF16_WAIT_PARENT_BEFORE_OPTIONS', 'Hotfix16 startup wait marker')
require(Path('src/interface/FileZilla.cpp'), '::OpenProcess(SYNCHRONIZE', 'Hotfix16 waits on exact parent process')
require(Path('src/interface/FileZilla.cpp'), '::WaitForSingleObject(parent, kBridgeXRestartParentWaitMs)', 'Hotfix16 bounded parent termination wait')
require(Path('src/interface/FileZilla.cpp'), 'waitResult == WAIT_OBJECT_0', 'Hotfix16 wait timeout/error fails closed')
require(iface_path, 'TNSUITE_BRIDGEX_BUILD12_HF16_RESTART_PERSISTENCE_HANDOFF', 'Hotfix16 settings restart persistence handoff marker')
require(iface_path, 'wxSetEnv(L"TNSUITE_BRIDGEX_RESTART_PARENT_PID"', 'Hotfix16 restart parent PID is inherited by child')
require(iface_path, 'wxUnsetEnv(L"TNSUITE_BRIDGEX_RESTART_PARENT_PID")', 'Hotfix16 parent restart environment is restored')
ui_hf16 = text(Path('src/interface/FileZilla.cpp'))
iface_hf16 = text(iface_path)
check('Hotfix16 child waits before COptions construction',
      ui_hf16.find('TNSUITE_BRIDGEX_BUILD12_HF16_WAIT_PARENT_BEFORE_OPTIONS') < ui_hf16.find('options_ = std::make_unique<COptions>();'))
handoff = iface_hf16.find('TNSUITE_BRIDGEX_BUILD12_HF16_RESTART_PERSISTENCE_HANDOFF')
check('Hotfix16 language/theme assignment precedes restart handoff',
      0 <= iface_hf16.find('m_pOptions->set(OPTION_LANGUAGE, newLanguage);') < handoff and
      0 <= iface_hf16.find('m_pOptions->set(OPTION_BRIDGEX_THEME, newTheme);') < handoff)
setenv = iface_hf16.find('wxSetEnv(L"TNSUITE_BRIDGEX_RESTART_PARENT_PID"', handoff)
execute = iface_hf16.find('wxExecute(executable, wxEXEC_ASYNC)', handoff)
unsetenv = iface_hf16.find('wxUnsetEnv(L"TNSUITE_BRIDGEX_RESTART_PARENT_PID")', handoff)
close = iface_hf16.find('top->Close();', handoff)
check('Hotfix16 restart ordering is setenv -> spawn -> unsetenv -> close', 0 <= setenv < execute < unsetenv < close)
check('Hotfix15 immediate spawn/close race removed', 'if (wxExecute(executable, wxEXEC_ASYNC) != 0)' not in iface_hf16)

forbid(Path('src/interface/Mainfrm.cpp'), 'needs to be restarted for the language change to take effect', 'Upstream duplicate restart popup removed')
static_bitmap_files=[]
for candidate in (root/'src/interface').rglob('*.cpp'):
    candidate_text=candidate.read_text(encoding='utf-8')
    if 'TNSUITE_BRIDGEX_BUILD12_HF11_SAFE_BITMAP_BUNDLE' in candidate_text:
        static_bitmap_files.append(candidate)
        rel=candidate.relative_to(root)
        check(f'Hotfix11 direct wx/bitmap.h in {rel}', '#include <wx/bitmap.h>' in candidate_text)
        check(f'Hotfix11 direct wx/bmpbndl.h in {rel}', '#include <wx/bmpbndl.h>' in candidate_text)
        check(f'Hotfix11 bundle validity guard in {rel}', 'bundle.IsOk()' in candidate_text)
        check(f'Hotfix11 guarded SetBitmap in {rel}', 'SetBitmap(BridgeXSafeStaticBitmap(' in candidate_text)
check('Hotfix11 bitmap inventory permits zero statically-resolved candidates', True)
all_interface='\n'.join(c.read_text(encoding='utf-8') for c in (root/'src/interface').rglob('*.cpp'))
check('Hotfix11 does not suppress wx assertions globally', not any(x in all_interface for x in ('wxDisableAsserts', 'SetAssertHandler', 'wxSetAssertHandler')))

# BridgeX product UI and content.
require(Path('src/interface/FileZilla.cpp'), 'SetAppDisplayName("TNSuite BridgeX")', 'BridgeX application display name')
require(Path('src/interface/Mainfrm.cpp'), 'TNSuite BridgeX', 'BridgeX main window title')
require(Path('src/interface/aboutdialog.cpp'), 'About TNSuite BridgeX', 'BridgeX About dialog')
require(Path('src/interface/aboutdialog.cpp'), 'https://tnsuite.com/', 'BridgeX About homepage')
require(Path('src/interface/aboutdialog.cpp'), 'Based on FileZilla Client', 'Upstream attribution retained in About')
require(Path('src/interface/welcome_dialog.cpp'), 'Welcome to TNSuite BridgeX', 'BridgeX Welcome dialog')
require(Path('src/interface/welcome_dialog.cpp'), 'TNSUITE_BRIDGEX_BUILD12_WELCOME', 'BridgeX-owned Welcome marker')
forbid(Path('src/interface/welcome_dialog.cpp'), 'welcome.filezilla-project.org', 'Upstream welcome service removed')
forbid(Path('src/interface/welcome_dialog.cpp'), 'Asking questions in the FileZilla Forums', 'Upstream forum CTA removed')
require(Path('src/interface/menu_bar.cpp'), 'TNSUITE_BRIDGEX_BUILD12_AUTOMATION_MENU', 'BridgeX Automation menu')
menu_text = text(Path('src/interface/menu_bar.cpp'))
check('Menu emitter has no literal escaped-tab indentation', not re.search(r'(?m)^\\t', menu_text), 'literal \\t leaked into generated C++')
require(Path('src/interface/menu_bar.cpp'), 'BridgeX-Help.html', 'BridgeX local Help action')
require(Path('src/interface/menu_bar.cpp'), 'BridgeX-Report-Bug.html', 'BridgeX local Report-a-bug action')
require(Path('src/interface/toolbar.cpp'), 'TNSUITE_BRIDGEX_BUILD12_MODERN_TOOLBAR', 'BridgeX modern text toolbar')
require(Path('src/interface/toolbar.cpp'), 'wxTB_TEXT', 'BridgeX toolbar labels enabled')
require(Path('src/interface/toolbar.cpp'), 'label = _("Sites")', 'BridgeX toolbar product labels')
require(Path('src/interface/quickconnectbar.cpp'), 'TNSUITE_BRIDGEX_BUILD12_CONNECTION_HEADER', 'BridgeX connection header structural UI')
require(Path('src/interface/quickconnectbar.cpp'), 'TNSUITE_BRIDGEX_BUILD12_QUICK_CONNECT', 'BridgeX Connect action')
require(Path('src/interface/viewheader.cpp'), 'TNSUITE_BRIDGEX_BUILD12_PANE_HEADER', 'BridgeX pane-header styling')
require(Path('src/interface/viewheader.cpp'), 'wxSYS_COLOUR_HOTLIGHT', 'Pane-header accent follows active appearance')
require(Path('src/interface/resources/version.rc.in'), 'VALUE "ProductName", "TNSuite BridgeX"', 'BridgeX Windows version metadata')
icon=root/'src/interface/resources/FileZilla.ico'
check('BridgeX Windows ICO', icon.is_file() and icon.stat().st_size>1000)

if not all(ok for _,ok in checks):
    print('SOURCE_COMPAT_QA=FAIL'); raise SystemExit(1)
print('SOURCE_COMPAT_QA=PASS')
