#!/usr/bin/env python3
"""Apply TNSuite BridgeX Build12 UI + wxWidgets 3.3 build-compat patches.

Fails closed if expected upstream source anchors are not found.
No auth, protocol, storage, SFTP, or credential-handling code is changed.
"""
from __future__ import annotations
import pathlib
import re
import sys

MARKER = "TNSUITE_BRIDGEX_BUILD12"

if len(sys.argv) != 2:
    raise SystemExit("Usage: patch_tnsuite_bridgex.py <filezilla-source-root>")

root = pathlib.Path(sys.argv[1]).resolve()
ui_path = root / "src" / "interface" / "FileZilla.cpp"
configure_path = root / "configure.ac"
aui_path = root / "src" / "interface" / "aui_notebook_ex.cpp"
fileexists_path = root / "src" / "interface" / "fileexistsdlg.cpp"
localtree_path = root / "src" / "interface" / "LocalTreeView.cpp"
sitemanager_controls_path = root / "src" / "interface" / "sitemanager_controls.cpp"
options_filetype_path = root / "src" / "interface" / "settings" / "optionspage_filetype.cpp"
options_edit_assoc_path = root / "src" / "interface" / "settings" / "optionspage_edit_associations.cpp"
dialogex_path = root / "src" / "interface" / "dialogex.cpp"
filelistctrl_path = root / "src" / "interface" / "filelistctrl.cpp"
toolbar_path = root / "src" / "interface" / "toolbar.cpp"
quickconnect_path = root / "src" / "interface" / "quickconnectbar.cpp"
viewheader_path = root / "src" / "interface" / "viewheader.cpp"
interface_makefile_am_path = root / "src" / "interface" / "Makefile.am"
src_makefile_am_path = root / "src" / "Makefile.am"
mainfrm_path = root / "src" / "interface" / "Mainfrm.cpp"
aboutdialog_path = root / "src" / "interface" / "aboutdialog.cpp"
menu_bar_path = root / "src" / "interface" / "menu_bar.cpp"
resource_root = root / "src" / "interface" / "resources"
brand_assets = pathlib.Path(__file__).resolve().parents[1] / "assets" / "branding"
version_rc_path = resource_root / "version.rc.in"
options_h_path = root / "src" / "interface" / "Options.h"
options_cpp_path = root / "src" / "interface" / "Options.cpp"
options_interface_path = root / "src" / "interface" / "settings" / "optionspage_interface.cpp"
settingsdialog_path = root / "src" / "interface" / "settings" / "settingsdialog.cpp"
welcome_dialog_path = root / "src" / "interface" / "welcome_dialog.cpp"
if not ui_path.is_file():
    raise SystemExit(f"Missing source file: {ui_path}")
if not configure_path.is_file():
    raise SystemExit(f"Missing configure file: {configure_path}")
if not aui_path.is_file():
    raise SystemExit(f"Missing AUI source file: {aui_path}")
if not fileexists_path.is_file():
    raise SystemExit(f"Missing FileExists source file: {fileexists_path}")
for required in (localtree_path, sitemanager_controls_path, options_filetype_path, options_edit_assoc_path, dialogex_path, filelistctrl_path, toolbar_path, quickconnect_path, viewheader_path, interface_makefile_am_path, src_makefile_am_path, mainfrm_path, aboutdialog_path, menu_bar_path, version_rc_path, options_h_path, options_cpp_path, options_interface_path, settingsdialog_path, welcome_dialog_path):
    if not required.is_file():
        raise SystemExit(f"Missing compatibility source file: {required}")

text = ui_path.read_text(encoding="utf-8")
include_anchor = "#elif defined(__WXMSW__)\n#include <shobjidl.h>\n#endif"
include_replacement = "#elif defined(__WXMSW__)\n#include <windows.h>\n#include <shobjidl.h>\n#include <wx/msw/darkmode.h>\n#include <wx/pen.h>\n#include <wx/utils.h>\n#endif"
if include_anchor not in text:
    raise SystemExit("PATCH_FAIL: Windows include anchor not found; refusing fuzzy patch.")
text = text.replace(include_anchor, include_replacement, 1)

namespace_anchor = "using namespace std::literals;\n"
dark_code = r'''

#ifdef __WXMSW__
namespace {
// TNSUITE_BRIDGEX_BUILD12_HF16_RESTART_HANDOFF
// Restarted BridgeX must not construct COptions while the previous process is
// still alive. The previous process owns the final settings flush during its
// normal shutdown path. Starting the replacement process first caused a
// stale-read race: first restart read old theme/language, then the old process
// flushed the new values for the following launch.
constexpr wchar_t kBridgeXRestartParentPidEnv[] = L"TNSUITE_BRIDGEX_RESTART_PARENT_PID";
constexpr DWORD kBridgeXRestartParentWaitMs = 60000;

bool BridgeXWaitForRestartParentIfRequested()
{
	wxString parentPidText;
	if (!wxGetEnv(kBridgeXRestartParentPidEnv, &parentPidText)) {
		return true;
	}

	// One-shot handoff: do not propagate the marker to descendants.
	wxUnsetEnv(kBridgeXRestartParentPidEnv);

	unsigned long parentPid{};
	if (!parentPidText.ToULong(&parentPid) || !parentPid || parentPid == static_cast<unsigned long>(::GetCurrentProcessId())) {
		return false;
	}

	HANDLE const parent = ::OpenProcess(SYNCHRONIZE, FALSE, static_cast<DWORD>(parentPid));
	if (!parent) {
		// Parent may have completed between child creation and this check.
		// Any other failure stays fail-closed.
		return ::GetLastError() == ERROR_INVALID_PARAMETER;
	}

	DWORD const waitResult = ::WaitForSingleObject(parent, kBridgeXRestartParentWaitMs);
	::CloseHandle(parent);
	return waitResult == WAIT_OBJECT_0;
}

// TNSUITE_BRIDGEX_BUILD12_THEME
// wxColour(unsigned long) is COLORREF/BGR on MSW. Build11 used web-style
// 0xRRGGBB integers and therefore rendered the intended navy palette as brown.
// Build12 uses explicit RGB components for deterministic colours.
class CBridgeXDarkModeSettings final : public wxDarkModeSettings
{
public:
	wxColour GetColour(wxSystemColour index) override
	{
		switch (index) {
		case wxSYS_COLOUR_ACTIVECAPTION:
		case wxSYS_COLOUR_APPWORKSPACE:
		case wxSYS_COLOUR_LISTBOX:
		case wxSYS_COLOUR_WINDOW:
			return wxColour(15, 23, 36);       // #0F1724

		case wxSYS_COLOUR_INFOBK:
		case wxSYS_COLOUR_INACTIVECAPTION:
		case wxSYS_COLOUR_MENU:
		case wxSYS_COLOUR_MENUBAR:
			return wxColour(17, 27, 42);       // #111B2A

		case wxSYS_COLOUR_BTNFACE:
			return wxColour(22, 34, 53);       // #162235

		case wxSYS_COLOUR_BTNTEXT:
		case wxSYS_COLOUR_CAPTIONTEXT:
		case wxSYS_COLOUR_HIGHLIGHTTEXT:
		case wxSYS_COLOUR_INFOTEXT:
		case wxSYS_COLOUR_LISTBOXHIGHLIGHTTEXT:
		case wxSYS_COLOUR_LISTBOXTEXT:
		case wxSYS_COLOUR_MENUTEXT:
		case wxSYS_COLOUR_WINDOWTEXT:
			return wxColour(243, 247, 251);    // #F3F7FB

		case wxSYS_COLOUR_INACTIVECAPTIONTEXT:
		case wxSYS_COLOUR_GRAYTEXT:
			return wxColour(169, 182, 198);    // #A9B6C6

		case wxSYS_COLOUR_HOTLIGHT:
			return wxColour(69, 199, 255);     // #45C7FF

		case wxSYS_COLOUR_HIGHLIGHT:
		case wxSYS_COLOUR_LISTBOXHIGHLIGHT:
			return wxColour(14, 94, 168);      // #0E5EA8

		case wxSYS_COLOUR_GRIDLINES:
			return wxColour(49, 68, 90);       // #31445A

		case wxSYS_COLOUR_SCROLLBAR:
			return wxColour(58, 79, 102);      // #3A4F66

		case wxSYS_COLOUR_BTNSHADOW:
		case wxSYS_COLOUR_BTNHIGHLIGHT:
		case wxSYS_COLOUR_3DDKSHADOW:
		case wxSYS_COLOUR_3DLIGHT:
		case wxSYS_COLOUR_ACTIVEBORDER:
		case wxSYS_COLOUR_INACTIVEBORDER:
		case wxSYS_COLOUR_MENUHILIGHT:
		case wxSYS_COLOUR_WINDOWFRAME:
			return wxColour(91, 111, 134);     // #5B6F86

		default:
			return wxDarkModeSettings::GetColour(index);
		}
	}

	wxColour GetMenuColour(wxMenuColour which) override
	{
		switch (which) {
		case wxMenuColour::StandardFg:
			return wxColour(243, 247, 251);
		case wxMenuColour::StandardBg:
			return wxColour(17, 27, 42);
		case wxMenuColour::DisabledFg:
			return wxColour(169, 182, 198);
		case wxMenuColour::HotBg:
			return wxColour(23, 59, 90);
		}
		return wxDarkModeSettings::GetMenuColour(which);
	}

	wxPen GetBorderPen() override
	{
		return wxPen(wxColour(91, 111, 134));
	}
};
}
#endif
'''
if namespace_anchor not in text:
    raise SystemExit("PATCH_FAIL: namespace anchor not found; refusing fuzzy patch.")
text = text.replace(namespace_anchor, namespace_anchor + dark_code, 1)

oninit_anchor = 'bool CFileZillaApp::OnInit()\n{\n\tAddStartupProfileRecord("CFileZillaApp::OnInit()"sv);\n'
oninit_replacement = r'''bool CFileZillaApp::OnInit()
{
	AddStartupProfileRecord("CFileZillaApp::OnInit()"sv);

#ifdef __WXMSW__
	// TNSUITE_BRIDGEX_BUILD12_HF16_WAIT_PARENT_BEFORE_OPTIONS
	if (!BridgeXWaitForRestartParentIfRequested()) {
		return false;
	}
#endif
'''
if oninit_anchor not in text:
    raise SystemExit("PATCH_FAIL: OnInit anchor not found; refusing fuzzy patch.")
text = text.replace(oninit_anchor, oninit_replacement, 1)

identity_anchor = 'SetAppDisplayName("FileZilla");'
if identity_anchor not in text:
    raise SystemExit("PATCH_FAIL: display-name anchor not found.")
text = text.replace(identity_anchor, 'SetAppDisplayName("TNSuite BridgeX");', 1)

appid_anchor = 'SetCurrentProcessExplicitAppUserModelID(L"FileZilla.Client.AppID");'
if appid_anchor not in text:
    raise SystemExit("PATCH_FAIL: AppUserModelID anchor not found.")
text = text.replace(appid_anchor, 'SetCurrentProcessExplicitAppUserModelID(L"TNSuite.BridgeX.Client");', 1)

# Build12 appearance is a first-class setting. Apply it only after COptions has
# loaded, but still before the main frame is created.
options_anchor = '\toptions_ = std::make_unique<COptions>();\n\n\tInitLocale();'
options_replacement = r'''	options_ = std::make_unique<COptions>();

#ifdef __WXMSW__
	// TNSUITE_BRIDGEX_BUILD12_APPEARANCE
	int const bridgeXTheme = options_->get_int(OPTION_BRIDGEX_THEME);
	if (bridgeXTheme == 1) {
		if (!MSWEnableDarkMode(wxApp::DarkMode_Always, new CBridgeXDarkModeSettings())) {
			return false;
		}
	}
	else {
		// wxWidgets 3.3.3 only exposes Auto/Always flags for MSW dark mode.
		// Its supported public API for explicitly requesting light appearance is SetAppearance().
		if (SetAppearance(wxApp::Appearance::Light) != wxApp::AppearanceResult::Ok) {
			return false;
		}
	}
#endif

	InitLocale();'''
if options_anchor not in text:
    raise SystemExit("PATCH_FAIL: options initialization anchor not found for BridgeX appearance.")
text = text.replace(options_anchor, options_replacement, 1)

# Load BridgeX translations after the upstream FileZilla catalog.
catalog_anchor = '\tpLocale->AddCatalog(_T("libfilezilla"));'
if text.count(catalog_anchor) < 2:
    raise SystemExit("PATCH_FAIL: locale catalog anchors not found for BridgeX translations.")
text = text.replace(catalog_anchor, '\tpLocale->AddCatalog(_T("bridgex"));\n' + catalog_anchor)

text = text.replace('Could not find the resource files for FileZilla, closing FileZilla.', 'Could not find the resource files for TNSuite BridgeX, closing TNSuite BridgeX.')
text = text.replace('data directory of FileZilla', 'data directory of TNSuite BridgeX')
text = text.replace('FileZilla Error', 'TNSuite BridgeX Error')

ui_path.write_text(text, encoding="utf-8", newline="\n")

# ---------------------------------------------------------------------------
# Build12 Interface settings: English/Vietnamese + Light/Dark.
# FileZilla already has a persistent Language Code option. BridgeX adds one
# product-specific theme option and surfaces both controls directly on the
# Interface page, avoiding the old separate all-locales Language page.
options_h_text = options_h_path.read_text(encoding="utf-8")
options_h_anchor = "\tOPTION_LANGUAGE,\n\tOPTION_CONCURRENTDOWNLOADLIMIT,"
if options_h_anchor not in options_h_text:
    raise SystemExit("PATCH_FAIL: Options.h language enum anchor not found.")
options_h_text = options_h_text.replace(
    options_h_anchor,
    "\tOPTION_LANGUAGE,\n\tOPTION_BRIDGEX_THEME,\n\tOPTION_CONCURRENTDOWNLOADLIMIT,",
    1,
)
options_h_path.write_text(options_h_text, encoding="utf-8", newline="\n")

options_cpp_text = options_cpp_path.read_text(encoding="utf-8")
options_cpp_anchor = '\t\t{ "Language Code", L"", option_flags::normal, 50 },\n\t\t{ "Concurrent download limit", 0, option_flags::numeric_clamp, 0, 10 },'
if options_cpp_anchor not in options_cpp_text:
    raise SystemExit("PATCH_FAIL: Options.cpp language registration anchor not found.")
options_cpp_text = options_cpp_text.replace(
    options_cpp_anchor,
    '\t\t{ "Language Code", L"", option_flags::normal, 50 },\n'
    '\t\t{ "BridgeX Theme", 1, option_flags::numeric_clamp, 0, 1 },\n'
    '\t\t{ "Concurrent download limit", 0, option_flags::numeric_clamp, 0, 10 },',
    1,
)
options_cpp_path.write_text(options_cpp_text, encoding="utf-8", newline="\n")

iface_text = options_interface_path.read_text(encoding="utf-8")
# Hotfix8 restart CTA uses these wx APIs directly. Preserve upstream first
# include/PCH ordering and add explicit dependencies after the first include.
hf8_iface_headers = (
    '#include <wx/app.h>\n',
    '#include <wx/msgdlg.h>\n',
    '#include <wx/stdpaths.h>\n',
    '#include <wx/utils.h>\n',
)
missing_hf8_iface_headers = [h for h in hf8_iface_headers if h.strip() not in iface_text]
if missing_hf8_iface_headers:
    first_iface_include = re.search(r'(?m)^#include[^\n]*\n', iface_text)
    if first_iface_include:
        iface_include_pos = first_iface_include.end()
        iface_text = iface_text[:iface_include_pos] + ''.join(missing_hf8_iface_headers) + iface_text[iface_include_pos:]
    else:
        # QA fixture fallback. Real FileZilla source has an include block.
        iface_text = ''.join(missing_hf8_iface_headers) + iface_text
iface_impl_anchor = "\twxChoice* messagelog_pos_{};\n\twxCheckBox* swap_{};"
if iface_impl_anchor not in iface_text:
    raise SystemExit("PATCH_FAIL: Interface settings impl anchor not found.")
iface_text = iface_text.replace(
    iface_impl_anchor,
    "\twxChoice* messagelog_pos_{};\n\twxCheckBox* swap_{};\n"
    "\twxChoice* language_{};\n\twxChoice* appearance_{};",
    1,
)

iface_create_anchor = "\tSetSizer(main);\n\n\t{\n\t\tauto [box, inner] = lay.createStatBox(main, _(\"Layout\"), 1);"
iface_create_replacement = "\tSetSizer(main);\n\n\t{\n\t\t// TNSUITE_BRIDGEX_BUILD12_INTERFACE_APPEARANCE\n\t\tauto [box, inner] = lay.createStatBox(main, _(\"Appearance\"), 1);\n\t\tauto rows = lay.createFlex(2);\n\t\tinner->Add(rows);\n\n\t\trows->Add(new wxStaticText(box, nullID, _(\"&Language:\")), lay.valign);\n\t\timpl_->language_ = new wxChoice(box, nullID);\n\t\timpl_->language_->Append(_(\"English\"));\n\t\timpl_->language_->Append(_(\"Vietnamese\"));\n\t\trows->Add(impl_->language_, lay.valign);\n\n\t\trows->Add(new wxStaticText(box, nullID, _(\"&Theme:\")), lay.valign);\n\t\timpl_->appearance_ = new wxChoice(box, nullID);\n\t\timpl_->appearance_->Append(_(\"Light\"));\n\t\timpl_->appearance_->Append(_(\"Dark\"));\n\t\trows->Add(impl_->appearance_, lay.valign);\n\n\t\tinner->Add(new wxStaticText(box, nullID, _(\"Language and theme changes are applied after restarting TNSuite BridgeX.\")));\n\t}\n\n\t{\n\t\tauto [box, inner] = lay.createStatBox(main, _(\"Layout\"), 1);"
if iface_create_anchor not in iface_text:
    raise SystemExit("PATCH_FAIL: Interface CreateControls anchor not found.")
iface_text = iface_text.replace(iface_create_anchor, iface_create_replacement, 1)

iface_load_anchor = "bool COptionsPageInterface::LoadPage()\n{\n\timpl_->filepane_layout_->SetSelection(m_pOptions->get_int(OPTION_FILEPANE_LAYOUT));"
iface_load_replacement = "bool COptionsPageInterface::LoadPage()\n{\n\t// TNSUITE_BRIDGEX_BUILD12_INTERFACE_LOAD\n\tauto const language = m_pOptions->get_string(OPTION_LANGUAGE);\n\timpl_->language_->SetSelection(language.rfind(L\"vi\", 0) == 0 ? 1 : 0);\n\timpl_->appearance_->SetSelection(m_pOptions->get_int(OPTION_BRIDGEX_THEME) == 0 ? 0 : 1);\n\n\timpl_->filepane_layout_->SetSelection(m_pOptions->get_int(OPTION_FILEPANE_LAYOUT));"
if iface_load_anchor not in iface_text:
    raise SystemExit("PATCH_FAIL: Interface LoadPage anchor not found.")
iface_text = iface_text.replace(iface_load_anchor, iface_load_replacement, 1)

iface_save_anchor = "bool COptionsPageInterface::SavePage()\n{\n\tm_pOptions->set(OPTION_FILEPANE_LAYOUT, impl_->filepane_layout_->GetSelection());"
iface_save_replacement = r'''bool COptionsPageInterface::SavePage()
{
	// TNSUITE_BRIDGEX_BUILD12_HF8_RESTART_CTA
	// BridgeX intentionally exposes just two supported UI languages. English is
	// the source language; Vietnamese uses the bundled vi_VN catalog.
	auto const oldLanguage = m_pOptions->get_string(OPTION_LANGUAGE);
	int const oldTheme = m_pOptions->get_int(OPTION_BRIDGEX_THEME);
	auto const newLanguage = impl_->language_->GetSelection() == 1 ? std::wstring(L"vi_VN") : std::wstring(L"en_US");
	int const newTheme = impl_->appearance_->GetSelection() == 0 ? 0 : 1;
	bool const restartRequired = oldLanguage != newLanguage || oldTheme != newTheme;

	m_pOptions->set(OPTION_LANGUAGE, newLanguage);
	m_pOptions->set(OPTION_BRIDGEX_THEME, newTheme);

	if (restartRequired) {
		wxMessageDialog restartDialog(
			this,
			_("Language or theme changes require restarting TNSuite BridgeX."),
			_("Restart TNSuite BridgeX"),
			wxYES_NO | wxICON_INFORMATION
		);
		restartDialog.SetYesNoLabels(_("Restart now"), _("Later"));
		if (restartDialog.ShowModal() == wxID_YES) {
			auto const executable = wxStandardPaths::Get().GetExecutablePath();
			wxTheApp->CallAfter([executable]() {
				// TNSUITE_BRIDGEX_BUILD12_HF16_RESTART_PERSISTENCE_HANDOFF
				// The child inherits this one-shot parent PID. Its OnInit waits for
				// this process to terminate before constructing COptions, so normal
				// upstream shutdown persistence completes before theme/language reload.
				auto const restartParentPid = wxString::Format(L"%lu", wxGetProcessId());
				if (!wxSetEnv(L"TNSUITE_BRIDGEX_RESTART_PARENT_PID", restartParentPid)) {
					return;
				}
				auto const restartedPid = wxExecute(executable, wxEXEC_ASYNC);
				wxUnsetEnv(L"TNSUITE_BRIDGEX_RESTART_PARENT_PID");
				if (restartedPid != 0) {
					if (auto* top = wxTheApp->GetTopWindow()) {
						// Preserve upstream shutdown vetoes. A veto leaves the child
						// waiting; it times out and exits rather than reading stale state.
						top->Close();
					}
				}
			});
		}
	}

	m_pOptions->set(OPTION_FILEPANE_LAYOUT, impl_->filepane_layout_->GetSelection());'''

if iface_save_anchor not in iface_text:
    raise SystemExit("PATCH_FAIL: Interface SavePage anchor not found.")
iface_text = iface_text.replace(iface_save_anchor, iface_save_replacement, 1)
options_interface_path.write_text(iface_text, encoding="utf-8", newline="\n")

settings_text = settingsdialog_path.read_text(encoding="utf-8")
settings_language_page = '\tAddPage(_("Language"), new COptionsPageLanguage, 0);\n'
if settings_language_page not in settings_text:
    raise SystemExit("PATCH_FAIL: standalone Language settings page anchor not found.")
settings_text = settings_text.replace(
    settings_language_page,
    '\t// TNSUITE_BRIDGEX_BUILD12_LANGUAGE_IN_INTERFACE: language lives under Interface.\n',
    1,
)
settingsdialog_path.write_text(settings_text, encoding="utf-8", newline="\n")


# FileZilla 3.70.6 was written against wxWidgets 3.2 AUI APIs. wxWidgets 3.3
# intentionally changed two APIs used by aui_notebook_ex.cpp. Patch only those
# compatibility points; no transfer/auth/credential code is touched.
aui_text = aui_path.read_text(encoding="utf-8")
gettab_old = "virtual wxSize GetTabSize(wxDC& dc, wxWindow* wnd, const wxString& caption, const wxBitmapBundle& bitmap, bool active, int close_button_state, int* x_extent) override"
gettab_new = "virtual wxSize GetTabSize(wxReadOnlyDC& dc, wxWindow* wnd, const wxString& caption, const wxBitmapBundle& bitmap, bool active, int close_button_state, int* x_extent) override"
if gettab_old not in aui_text:
    raise SystemExit("PATCH_FAIL: wxAuiTabArtEx::GetTabSize wx3.2 signature not found; refusing fuzzy patch.")
aui_text = aui_text.replace(gettab_old, gettab_new, 1)

drag_old = "\twxAuiNotebook::OnTabDragMotion(evt);"
drag_new = "\t// TNSUITE_BRIDGEX_BUILD12_WX33_AUI: wx 3.3 performs the base drag operation\n\t// through wxAuiTabEventSource before delivering this notification event.\n\t// Do not call the removed wx 3.2 event-handler overload.\n\tevt.Skip();"
if drag_old not in aui_text:
    raise SystemExit("PATCH_FAIL: wxAuiNotebook::OnTabDragMotion(wxAuiNotebookEvent&) call not found; refusing fuzzy patch.")
aui_text = aui_text.replace(drag_old, drag_new, 1)
aui_path.write_text(aui_text, encoding="utf-8", newline="\n")

# wxWidgets 3.3 removed wxIcon::SetSize(). FileZilla 3.70.6 used SetHandle()
# followed by SetSize() for the shell icon returned by SHGetFileInfo(). Convert
# the native HICON to wxIcon using the supported API and scale through wxBitmap.
# This also preserves ownership semantics: wxIcon destroys the HICON on scope exit.
fileexists_text = fileexists_path.read_text(encoding="utf-8")
icon_old = """\t\twxIcon icon;\n\t\ticon.SetHandle(fileinfo.hIcon);\n\t\ticon.SetSize(size.x, size.y);\n\n\t\tdc->DrawIcon(icon, 0, 0);"""
icon_new = """\t\twxIcon icon;\n\t\tif (icon.CreateFromHICON((WXHICON)fileinfo.hIcon)) {\n\t\t\twxBitmap iconBitmap(icon);\n\t\t\tif (iconBitmap.IsOk() && iconBitmap.GetSize() != size) {\n\t\t\t\twxImage image = iconBitmap.ConvertToImage();\n\t\t\t\timage.Rescale(size.x, size.y, wxIMAGE_QUALITY_HIGH);\n\t\t\t\ticonBitmap = wxBitmap(image);\n\t\t\t}\n\t\t\tif (iconBitmap.IsOk()) {\n\t\t\t\tdc->DrawBitmap(iconBitmap, 0, 0, true);\n\t\t\t}\n\t\t}"""
if icon_old not in fileexists_text:
    raise SystemExit("PATCH_FAIL: wxIcon SetHandle/SetSize compatibility anchor not found; refusing fuzzy patch.")
fileexists_text = fileexists_text.replace(icon_old, icon_new, 1)
fileexists_path.write_text(fileexists_text, encoding="utf-8", newline="\n")


# Runtime QA from Build12 showed two Windows-only presentation problems:
# 1) the executable was linked as a console application, so Explorer launched a
#    command window next to the GUI; and
# 2) wxWidgets 3.3.3 can emit spurious TB_GETITEMRECT diagnostics while the
#    native toolbar is being realized. wxWidgets itself documents that
#    TB_GETITEMRECT can return false without a real error; its 3.3.3 helper then
#    consults the process last-error value, which can be stale. Suppress logging
#    only around the base toolbar Realize() call and clear last-error first.
#    Any actual Realize() failure is still propagated by the boolean return.
toolbar_text = toolbar_path.read_text(encoding="utf-8")

# Build12 actual GUI rework: retain FileZilla's proven transfer workflow but
# make the primary toolbar read like a modern BridgeX desktop application.
# Text labels improve discoverability while the rebranded icon/palette removes
# the visual identity of the upstream application.
toolbar_style_old = "constexpr int toolbarStyle = wxTB_FLAT | wxTB_HORIZONTAL | wxTB_NODIVIDER;"
toolbar_style_new = "// TNSUITE_BRIDGEX_BUILD12_MODERN_TOOLBAR\n\tconstexpr int toolbarStyle = wxTB_FLAT | wxTB_HORIZONTAL | wxTB_NODIVIDER | wxTB_TEXT;"
if toolbar_style_old not in toolbar_text:
    raise SystemExit("PATCH_FAIL: toolbar style anchor not found for BridgeX GUI rework.")
toolbar_text = toolbar_text.replace(toolbar_style_old, toolbar_style_new, 1)

addtool_old = 'wxToolBar::AddTool(XRCID(id), wxString(), bmp, wxBitmap(), type, tooltip, help);'
addtool_new = '''wxString label;
\tif (!strcmp(id, "ID_TOOLBAR_SITEMANAGER")) label = _("Sites");
\telse if (!strcmp(id, "ID_TOOLBAR_LOGVIEW")) label = _("Log");
\telse if (!strcmp(id, "ID_TOOLBAR_LOCALTREEVIEW")) label = _("Local");
\telse if (!strcmp(id, "ID_TOOLBAR_REMOTETREEVIEW")) label = _("Remote");
\telse if (!strcmp(id, "ID_TOOLBAR_QUEUEVIEW")) label = _("Queue");
\telse if (!strcmp(id, "ID_TOOLBAR_REFRESH")) label = _("Refresh");
\telse if (!strcmp(id, "ID_TOOLBAR_PROCESSQUEUE")) label = _("Start");
\telse if (!strcmp(id, "ID_TOOLBAR_CANCEL")) label = _("Cancel");
\telse if (!strcmp(id, "ID_TOOLBAR_DISCONNECT")) label = _("Disconnect");
\telse if (!strcmp(id, "ID_TOOLBAR_RECONNECT")) label = _("Reconnect");
\telse if (!strcmp(id, "ID_TOOLBAR_FILTER")) label = _("Filter");
\telse if (!strcmp(id, "ID_TOOLBAR_COMPARISON")) label = _("Compare");
\telse if (!strcmp(id, "ID_TOOLBAR_SYNCHRONIZED_BROWSING")) label = _("Sync");
\telse if (!strcmp(id, "ID_TOOLBAR_FIND")) label = _("Search");
\twxToolBar::AddTool(XRCID(id), label, bmp, wxBitmap(), type, tooltip, help);'''
if addtool_old not in toolbar_text:
    raise SystemExit("PATCH_FAIL: toolbar AddTool anchor not found for BridgeX labels.")
toolbar_text = toolbar_text.replace(addtool_old, addtool_new, 1)

# strcmp is used only for stable internal toolbar IDs.
include_toolbar_anchor = '#include "toolbar.h"\n'
if include_toolbar_anchor not in toolbar_text:
    raise SystemExit("PATCH_FAIL: toolbar header include anchor missing.")
toolbar_text = toolbar_text.replace(include_toolbar_anchor, include_toolbar_anchor + '#include <cstring>\n', 1)
include_old = '#include "toolbar.h"\n'
include_new = '#include "toolbar.h"\n\n#ifdef __WXMSW__\n#include <wx/log.h>\n#endif\n'
if include_old not in toolbar_text:
    raise SystemExit("PATCH_FAIL: toolbar include anchor not found.")
toolbar_text = toolbar_text.replace(include_old, include_new, 1)
realize_old = '''#ifdef __WXMSW__
bool CToolBar::Realize()
{
	bool ret = wxToolBar::Realize();
'''
realize_new = '''#ifdef __WXMSW__
bool CToolBar::Realize()
{
	bool ret = false;
	{
		// TNSUITE_BRIDGEX_BUILD12_TOOLBAR_LOG_GUARD
		// wxWidgets 3.3.3 may report stale Win32 last-error values when
		// TB_GETITEMRECT returns false for a non-fatal native toolbar state.
		// Silence logging only for the base Realize() call; preserve its result.
		wxLogNull suppressSpuriousToolbarLog;
		::SetLastError(ERROR_SUCCESS);
		ret = wxToolBar::Realize();
	}
'''
if realize_old not in toolbar_text:
    raise SystemExit("PATCH_FAIL: toolbar Realize anchor not found.")
toolbar_text = toolbar_text.replace(realize_old, realize_new, 1)
toolbar_path.write_text(toolbar_text, encoding="utf-8", newline="\n")

# Link FileZilla as a Windows GUI subsystem executable. This prevents Windows
# from creating a console window when bin/filezilla.exe is launched directly.
imake_text = interface_makefile_am_path.read_text(encoding="utf-8")
link_old = '''if FZ_WINDOWS
filezilla_LDFLAGS += -lnormaliz -lole32 -luuid -lnetapi32 -lmpr -lpowrprof -lws2_32 -lshlwapi
endif
'''
link_new = '''if FZ_WINDOWS
# TNSUITE_BRIDGEX_BUILD12_GUI_SUBSYSTEM
filezilla_LDFLAGS += -mwindows
filezilla_LDFLAGS += -lnormaliz -lole32 -luuid -lnetapi32 -lmpr -lpowrprof -lws2_32 -lshlwapi
endif
'''
if link_old not in imake_text:
    raise SystemExit("PATCH_FAIL: FileZilla Windows linker anchor not found.")
imake_text = imake_text.replace(link_old, link_new, 1)
interface_makefile_am_path.write_text(imake_text, encoding="utf-8", newline="\n")

# Build04 full `make -k` exposed additional incompatibilities from the current
# UCRT64/libfilezilla/GCC toolchain. Apply only exact type-safety fixes observed
# in that compiler log.

# libfilezilla path_separator is narrow in this toolchain while LocalTreeView's
# path is std::wstring. Cast the single separator to wchar_t before concatenation.
localtree_text = localtree_path.read_text(encoding="utf-8")
localtree_old = "path + fz::local_filesys::path_separator + pData->m_known_subdir"
localtree_new = "path + static_cast<wchar_t>(fz::local_filesys::path_separator) + pData->m_known_subdir"
if localtree_old not in localtree_text:
    raise SystemExit("PATCH_FAIL: LocalTreeView path-separator compatibility anchor not found.")
localtree_text = localtree_text.replace(localtree_old, localtree_new, 1)
localtree_path.write_text(localtree_text, encoding="utf-8", newline="\n")

# GetExtraParameter() is std::wstring with the installed libfilezilla. Use wide
# literals for S3 SSE comparisons.
sm_text = sitemanager_controls_path.read_text(encoding="utf-8")
for old, new in (
    ('sse_algorithm == "AES256"', 'sse_algorithm == L"AES256"'),
    ('sse_algorithm == "aws:kms"', 'sse_algorithm == L"aws:kms"'),
    ('sse_algorithm == "customer"', 'sse_algorithm == L"customer"'),
):
    if old not in sm_text:
        raise SystemExit(f"PATCH_FAIL: S3 wide-string compatibility anchor not found: {old}")
    sm_text = sm_text.replace(old, new, 1)
sitemanager_controls_path.write_text(sm_text, encoding="utf-8", newline="\n")

# OPTION_ASCIIFILES is parsed as std::wstring. Keep the escaped pipe wide too.
opt_text = options_filetype_path.read_text(encoding="utf-8")
opt_old = "extensions.substr(0, pos - 1) + '|'"
opt_new = "extensions.substr(0, pos - 1) + L'|'"
if opt_old not in opt_text:
    raise SystemExit("PATCH_FAIL: optionspage_filetype wide-pipe anchor not found.")
opt_text = opt_text.replace(opt_old, opt_new, 1)
options_filetype_path.write_text(opt_text, encoding="utf-8", newline="\n")

# This is a portable client build. The Explorer shell extension is not needed
# and current MinGW headers already define ICopyHookW, causing a duplicate
# declaration in FileZilla 3.70.6. Exclude the shell extension from SUBDIRS
# rather than patching COM declarations we do not ship.
src_make_text = src_makefile_am_path.read_text(encoding="utf-8")
src_subdirs_old = "SUBDIRS = include engine $(MAYBE_PUGIXML) $(MAYBE_DBUS) commonui $(MAYBE_GUI) $(MAYBE_STORJ) $(MAYBE_FZSHELLEXT) ."
src_subdirs_new = "# TNSUITE_BRIDGEX_BUILD12_PORTABLE_NO_SHELLEXT\nSUBDIRS = include engine $(MAYBE_PUGIXML) $(MAYBE_DBUS) commonui $(MAYBE_GUI) $(MAYBE_STORJ) ."
if src_subdirs_old not in src_make_text:
    raise SystemExit("PATCH_FAIL: src/Makefile.am shell-extension SUBDIRS anchor not found.")
src_make_text = src_make_text.replace(src_subdirs_old, src_subdirs_new, 1)
src_makefile_am_path.write_text(src_make_text, encoding="utf-8", newline="\n")

# TNSuite BridgeX full GUI branding/rework. Keep transfer/authentication code untouched.
main_text = mainfrm_path.read_text(encoding="utf-8")
for old, new in (
    ('_T("FileZilla")', '_T("TNSuite BridgeX")'),
    ('_T(" - FileZilla")', '_T(" - TNSuite BridgeX")'),
):
    if old not in main_text:
        raise SystemExit(f"PATCH_FAIL: Mainfrm branding anchor not found: {old}")
    main_text = main_text.replace(old, new)
# TNSUITE_BRIDGEX_BUILD12_HF8_RESTART_CTA_OWNS_NOTIFICATION
# TNSUITE_BRIDGEX_BUILD12_HF10_RESTART_STRUCTURAL_STATEMENT
# Settings > Interface owns the actionable restart prompt. Upstream may use
# wxMessageBox, wxMessageBoxEx or a qualified message helper. Match by C++
# structure instead of a hard-coded callee name.
def _cpp_code_mask(text: str) -> list[bool]:
    code = [True] * len(text)
    i = 0
    state = "code"
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if state == "code":
            if ch == "/" and nxt == "/":
                code[i] = code[i + 1] = False
                i += 2; state = "line"; continue
            if ch == "/" and nxt == "*":
                code[i] = code[i + 1] = False
                i += 2; state = "block"; continue
            if ch == '"':
                code[i] = False; i += 1; state = "string"; continue
            if ch == "'":
                code[i] = False; i += 1; state = "char"; continue
            i += 1; continue
        code[i] = False
        if state == "line":
            if ch == "\n":
                state = "code"; code[i] = True
            i += 1; continue
        if state == "block":
            if ch == "*" and nxt == "/":
                code[i + 1] = False; i += 2; state = "code"; continue
            i += 1; continue
        if ch == "\\":
            if i + 1 < len(text): code[i + 1] = False
            i += 2; continue
        if (state == "string" and ch == '"') or (state == "char" and ch == "'"):
            state = "code"
        i += 1
    return code

def _matching_close_paren(text: str, mask: list[bool], open_pos: int) -> int:
    depth = 0
    for i in range(open_pos, len(text)):
        if not mask[i]:
            continue
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                return i
    return -1

def _restart_call_statement_bounds(text: str, phrase_pos: int):
    mask = _cpp_code_mask(text)
    stack = []
    for i in range(phrase_pos):
        if not mask[i]:
            continue
        if text[i] == "(":
            stack.append(i)
        elif text[i] == ")" and stack:
            stack.pop()
    for open_pos in reversed(stack):
        close_pos = _matching_close_paren(text, mask, open_pos)
        if close_pos == -1:
            continue
        j = close_pos + 1
        while j < len(text) and text[j].isspace():
            j += 1
        if j >= len(text) or text[j] != ";":
            continue
        # Recover the callable expression immediately before the opening paren.
        # Allow optional whitespace around C++ qualification/member operators so
        # qualified helpers such as `wxMsg :: Message(...)` and pointer-member
        # calls remain structurally matchable without hard-coding a callee name.
        prefix_start = max(0, open_pos - 512)
        prefix = text[prefix_start:open_pos]
        match = re.search(
            r"((?:::)?[A-Za-z_][A-Za-z0-9_]*(?:\s*(?:::|\.|->)\s*[A-Za-z_][A-Za-z0-9_]*)*)\s*$",
            prefix,
        )
        if not match:
            continue
        start_name = prefix_start + match.start(1)
        callee_raw = match.group(1)
        callee = re.sub(r"\s+", "", callee_raw)
        if not re.fullmatch(r"(?:::)?[A-Za-z_][A-Za-z0-9_]*(?:(?:::|\.|->)[A-Za-z_][A-Za-z0-9_]*)*", callee):
            continue
        return start_name, j + 1, callee
    return None

restart_phrase = "needs to be restarted for the language change to take effect"
restart_phrase_pos = main_text.find(restart_phrase)
if restart_phrase_pos != -1:
    bounds = _restart_call_statement_bounds(main_text, restart_phrase_pos)
    if not bounds:
        raise SystemExit("PATCH_FAIL: upstream language restart notification found but containing call statement could not be structurally bounded.")
    call_start, call_end, restart_callee = bounds
    main_text = (main_text[:call_start] +
                 "(void)0; /* BridgeX Hotfix10: restart notification handled in Interface Settings; upstream callee=" + restart_callee + " */" +
                 main_text[call_end:])
mainfrm_path.write_text(main_text, encoding="utf-8", newline="\n")

about_text = aboutdialog_path.read_text(encoding="utf-8")
about_pairs = (
    ('_("About FileZilla")', '_("About TNSuite BridgeX")'),
    ('std::wstring version = L"FileZilla " + GetFileZillaVersion();', 'std::wstring version = L"TNSuite BridgeX 0.5 Build12-Hotfix16";'),
    ('L"Copyright (C) 2004-2026  Tim Kosse"', 'L"BridgeX modifications (C) 2026 TNSuite / Tai Nguyen\\nBased on FileZilla Client " + GetFileZillaVersion() + L" (C) 2004-2026 Tim Kosse"'),
    ('_T("FileZilla Client\\n")', '_T("TNSuite BridgeX\\n")'),
)
for old, new in about_pairs:
    if old not in about_text:
        raise SystemExit(f"PATCH_FAIL: About dialog branding anchor not found: {old}")
    about_text = about_text.replace(old, new, 1)

about_version_anchor = '\ttopRight->Add(new wxStaticText(this, nullID, version));\n'
if about_version_anchor not in about_text:
    raise SystemExit("PATCH_FAIL: About version layout anchor not found.")
about_text = about_text.replace(
    about_version_anchor,
    about_version_anchor + '\ttopRight->Add(new wxStaticText(this, nullID, _("Secure Transfer & Automation")));\n',
    1,
)

about_home_old = 'homepage->Add(new wxHyperlinkCtrl(this, nullID, L"https://filezilla-project.org/", L"https://filezilla-project.org/"), lay.valign);'
about_home_new = 'homepage->Add(new wxHyperlinkCtrl(this, nullID, L"https://tnsuite.com/", L"https://tnsuite.com/"), lay.valign);'
if about_home_old not in about_text:
    raise SystemExit("PATCH_FAIL: About homepage anchor not found.")
about_text = about_text.replace(about_home_old, about_home_new, 1)

# Keep the upstream-compatible settings directory for this release so existing
# FileZilla sites/config are not silently lost, but label it honestly.
about_text = about_text.replace('_("Settings directory:")', '_("Compatibility settings directory:")')

legal_intro_old = 'L"FileZilla makes use of the following third-party libraries:\\n\\n"'
legal_intro_new = 'L"TNSuite BridgeX uses the FileZilla core and the following third-party libraries:\\n\\n"'
if legal_intro_old not in about_text:
    raise SystemExit("PATCH_FAIL: About legal intro anchor not found.")
about_text = about_text.replace(legal_intro_old, legal_intro_new, 1)

copy_version_old = r'''	text += _T("Version:          ") + GetFileZillaVersion();
	if (CBuildInfo::GetBuildType() == _T("nightly")) {
		text += _T("-nightly");
	}
	text += '\n';'''
copy_version_new = r'''	text += _T("Version:          0.5 Build12-Hotfix15\n");
	text += _T("FileZilla core:   ") + GetFileZillaVersion() + _T("\n");'''
if copy_version_old not in about_text:
    raise SystemExit("PATCH_FAIL: About clipboard version anchor not found.")
about_text = about_text.replace(copy_version_old, copy_version_new, 1)
aboutdialog_path.write_text(about_text, encoding="utf-8", newline="\n")

# Replace the upstream welcome content and all upstream support/documentation
# links with BridgeX-owned product copy. This prevents the fork from presenting
# FileZilla Project help pages as its own support channel.
welcome_text = welcome_dialog_path.read_text(encoding="utf-8")
welcome_replacements = (
    ('Create(parent_, -1, _("Welcome to FileZilla"));', 'Create(parent_, -1, _("Welcome to TNSuite BridgeX"));'),
    ('auto heading = new wxStaticText(this, -1, _T("FileZilla ") + GetFileZillaVersion());', 'auto heading = new wxStaticText(this, -1, _T("TNSuite BridgeX 0.5 Build12-Hotfix16"));'),
    ('headerLeft->Add(new wxStaticText(this, -1, _("The free open source FTP solution")));', 'headerLeft->Add(new wxStaticText(this, -1, _("Secure Transfer & Automation")));'),
    ('auto news = new wxStaticText(this, -1, _("What\'s new"));', 'auto news = new wxStaticText(this, -1, _("What\'s new in BridgeX"));'),
    ('main->Add(new wxHyperlinkCtrl(this, -1, wxString::Format(_("New features and improvements in %s"), ownVersion), wxString::Format(url, _T("news")) + _T("&oldversion=") + greetingVersion), 0, wxLEFT, lay.indent);', 'main->Add(new wxStaticText(this, -1, _("BridgeX Build12 adds a redesigned connection header, Light/Dark themes, and English/Vietnamese UI.")), 0, wxLEFT, lay.indent);'),
    ('main->Add(new wxHyperlinkCtrl(this, -1, _("Asking questions in the FileZilla Forums"), wxString::Format(url, _T("support_forum"))), 0, wxLEFT, lay.indent);', 'main->Add(new wxStaticText(this, -1, _("Open Help > Getting help for the local BridgeX guide.")), 0, wxLEFT, lay.indent);'),
    ('main->Add(new wxHyperlinkCtrl(this, -1, _("Reporting bugs and feature requests"), wxString::Format(url, _T("support_more"))), 0, wxLEFT, lay.indent);', 'main->Add(new wxStaticText(this, -1, _("Use Help > Report a bug for the BridgeX diagnostic checklist.")), 0, wxLEFT, lay.indent);'),
    ('main->Add(new wxHyperlinkCtrl(this, -1, _("Basic usage instructions"), wxString::Format(url, _T("documentation_basic"))), 0, wxLEFT, lay.indent);', 'main->Add(new wxStaticText(this, -1, _("Sites stores reusable connections; Quick Connect is for one-off sessions.")), 0, wxLEFT, lay.indent);'),
    ('main->Add(new wxHyperlinkCtrl(this, -1, _("Configuring FileZilla and your network"), wxString::Format(url, _T("documentation_network"))), 0, wxLEFT, lay.indent);', 'main->Add(new wxStaticText(this, -1, _("Automation opens the BridgeX CLI for scripted SFTP operations.")), 0, wxLEFT, lay.indent);'),
    ('main->Add(new wxHyperlinkCtrl(this, -1, _("Further documentation"), wxString::Format(url, _T("documentation_more"))), 0, wxLEFT, lay.indent);', 'main->Add(new wxStaticText(this, -1, _("Appearance and language are configured in Settings > Interface.")), 0, wxLEFT, lay.indent);'),
)
for old, new in welcome_replacements:
    if old not in welcome_text:
        raise SystemExit(f"PATCH_FAIL: Welcome dialog anchor not found: {old[:80]}")
    welcome_text = welcome_text.replace(old, new, 1)

welcome_url = '\twxString const url = _T("https://welcome.filezilla-project.org/welcome?type=client&category=%s&version=") + ownVersion;\n'
if welcome_url not in welcome_text:
    raise SystemExit("PATCH_FAIL: upstream Welcome URL anchor not found.")
welcome_text = welcome_text.replace(welcome_url, '\t// TNSUITE_BRIDGEX_BUILD12_WELCOME: no upstream product/support URLs.\n', 1)
welcome_dialog_path.write_text(welcome_text, encoding="utf-8", newline="\n")

menu_text = menu_bar_path.read_text(encoding="utf-8")
menu_text = menu_text.replace('_("Close FileZilla")', '_("Close TNSuite BridgeX")')
menu_text = menu_text.replace('_("Open the settings dialog of FileZilla")', '_("Open TNSuite BridgeX settings")')
menu_text = menu_text.replace('_("Open the directory access permissions dialog to configure the local directories FileZilla has access to.")', '_("Open directory access permissions for TNSuite BridgeX.")')
include_anchor = '#include "state.h"\n'
include_replacement = '#include "state.h"\n\n#ifdef __WXMSW__\n#include <wx/filename.h>\n#include <wx/stdpaths.h>\n#include <wx/utils.h>\n#endif\n'
if include_anchor not in menu_text:
    raise SystemExit("PATCH_FAIL: menu include anchor not found")
menu_text = menu_text.replace(include_anchor, include_replacement, 1)
automation_anchor = '\twxMenu* help = new wxMenu;\n\tAppend(help, _("&Help"));\n'
automation_block = '''\t// TNSUITE_BRIDGEX_BUILD12_AUTOMATION_MENU
\twxMenu* automation = new wxMenu;
\tAppend(automation, _("&Automation"));
\tconst int cliHelpId = wxWindow::NewControlId();
\tconst int cliDoctorId = wxWindow::NewControlId();
\tautomation->Append(cliHelpId, _("Open BridgeX &CLI"), _("Open the BridgeX automation CLI in PowerShell"));
\tautomation->Append(cliDoctorId, _("Run CLI &Doctor"), _("Validate Windows OpenSSH and BridgeX CLI runtime"));
\tmainFrame_.Bind(wxEVT_MENU, [](wxCommandEvent&) {
\t\twxFileName exe(wxStandardPaths::Get().GetExecutablePath());
\t\texe.SetFullName(L"BridgeX-CLI.exe");
\t\twxString command = L"powershell.exe -NoExit -NoLogo -Command \\\"& '" + exe.GetFullPath() + L"' --help\\\"";
\t\twxExecute(command);
\t}, cliHelpId);
\tmainFrame_.Bind(wxEVT_MENU, [](wxCommandEvent&) {
\t\twxFileName exe(wxStandardPaths::Get().GetExecutablePath());
\t\texe.SetFullName(L"BridgeX-CLI.exe");
\t\twxString command = L"powershell.exe -NoExit -NoLogo -Command \\\"& '" + exe.GetFullPath() + L"' doctor --json\\\"";
\t\twxExecute(command);
\t}, cliDoctorId);

\twxMenu* help = new wxMenu;
\tAppend(help, _("&Help"));
'''
if automation_anchor not in menu_text:
    raise SystemExit("PATCH_FAIL: menu Help anchor not found for Automation menu")
menu_text = menu_text.replace(automation_anchor, automation_block, 1)

# Replace FileZilla official help/bug links with local BridgeX documents.
help_items_old = '\thelp->Append(XRCID("ID_MENU_HELP_GETTINGHELP"), _("&Getting help..."));\n\thelp->Append(XRCID("ID_MENU_HELP_BUGREPORT"), _("&Report a bug..."));'
help_items_new = '''\tconst int bridgeXHelpId = wxWindow::NewControlId();
\tconst int bridgeXBugId = wxWindow::NewControlId();
\thelp->Append(bridgeXHelpId, _("&Getting help..."));
\thelp->Append(bridgeXBugId, _("&Report a bug..."));
\tmainFrame_.Bind(wxEVT_MENU, [](wxCommandEvent&) {
\t\twxFileName exe(wxStandardPaths::Get().GetExecutablePath());
\t\twxFileName doc(exe.GetPathWithSep() + L"docs\\\\BridgeX-Help.html");
\t\twxLaunchDefaultApplication(doc.GetFullPath());
\t}, bridgeXHelpId);
\tmainFrame_.Bind(wxEVT_MENU, [](wxCommandEvent&) {
\t\twxFileName exe(wxStandardPaths::Get().GetExecutablePath());
\t\twxFileName doc(exe.GetPathWithSep() + L"docs\\\\BridgeX-Report-Bug.html");
\t\twxLaunchDefaultApplication(doc.GetFullPath());
\t}, bridgeXBugId);'''
if help_items_old not in menu_text:
    raise SystemExit("PATCH_FAIL: upstream Help/Bug menu anchors not found.")
menu_text = menu_text.replace(help_items_old, help_items_new, 1)
menu_bar_path.write_text(menu_text, encoding="utf-8", newline="\n")

# BridgeX connection header: this is a real structural UI change, not just a
# recolour. It adds a branded context row above the connection controls while
# preserving FileZilla protocol parsing and authentication behaviour.
quick_text = quickconnect_path.read_text(encoding="utf-8")
quick_old = 'auto connect = new wxButton(this, XRCID("ID_QUICKCONNECT_OK"), _("&Quickconnect"));'
quick_new = 'auto connect = new wxButton(this, XRCID("ID_QUICKCONNECT_OK"), _("&Connect")); // TNSUITE_BRIDGEX_BUILD12_QUICK_CONNECT'
if quick_old not in quick_text:
    raise SystemExit("PATCH_FAIL: Quickconnect button anchor not found.")
quick_text = quick_text.replace(quick_old, quick_new, 1)

quick_layout_anchor = "\tDialogLayout layout(&parent);\n\tauto mainSizer = layout.createFlex(0, 1);"
quick_layout_replacement = "\tDialogLayout layout(&parent);\n\n\t// TNSUITE_BRIDGEX_BUILD12_CONNECTION_HEADER\n\tauto brandRow = new wxBoxSizer(wxHORIZONTAL);\n\tsizer->Add(brandRow, wxSizerFlags().Expand().Border(wxLEFT | wxRIGHT | wxTOP, layout.dlgUnits(4)));\n\tauto brand = new wxStaticText(this, nullID, _(\"TNSuite BridgeX\"));\n\twxFont brandFont = brand->GetFont();\n\tbrandFont.SetWeight(wxFONTWEIGHT_BOLD);\n\tbrandFont.SetPointSize(brandFont.GetPointSize() + 1);\n\tbrand->SetFont(brandFont);\n\tbrand->SetForegroundColour(wxSystemSettings::GetColour(wxSYS_COLOUR_HOTLIGHT));\n\tbrandRow->Add(brand, 0, wxALIGN_CENTER_VERTICAL);\n\tbrandRow->AddSpacer(layout.dlgUnits(6));\n\tauto productLine = new wxStaticText(this, nullID, _(\"Secure Transfer & Automation\"));\n\tproductLine->SetForegroundColour(wxSystemSettings::GetColour(wxSYS_COLOUR_GRAYTEXT));\n\tbrandRow->Add(productLine, 0, wxALIGN_CENTER_VERTICAL);\n\tbrandRow->AddStretchSpacer();\n\tauto protocols = new wxStaticText(this, nullID, _(\"SFTP  /  FTP  /  FTPS\"));\n\tprotocols->SetForegroundColour(wxSystemSettings::GetColour(wxSYS_COLOUR_GRAYTEXT));\n\tbrandRow->Add(protocols, 0, wxALIGN_CENTER_VERTICAL);\n\n#ifdef __WXMSW__\n\tSetBackgroundColour(wxSystemSettings::GetColour(wxSYS_COLOUR_BTNFACE));\n#endif\n\n\tauto mainSizer = layout.createFlex(0, 1);"
if quick_layout_anchor not in quick_text:
    raise SystemExit("PATCH_FAIL: Quickconnect layout anchor not found for BridgeX header.")
quick_text = quick_text.replace(quick_layout_anchor, quick_layout_replacement, 1)
quickconnect_path.write_text(quick_text, encoding="utf-8", newline="\n")

# Modern local/remote pane headers: stronger hierarchy and BridgeX cyan accent.
# This changes presentation only; path/navigation behavior remains upstream.
view_text = viewheader_path.read_text(encoding="utf-8")
view_anchor = '''\tm_pLabel = new wxStaticText(this, wxID_ANY, label, wxDefaultPosition, wxDefaultSize);
\twxSize size = GetSize();'''
view_replacement = '''\tm_pLabel = new wxStaticText(this, wxID_ANY, label.Upper(), wxDefaultPosition, wxDefaultSize);
#ifdef __WXMSW__
\t// TNSUITE_BRIDGEX_BUILD12_PANE_HEADER
\tm_pLabel->SetForegroundColour(wxSystemSettings::GetColour(wxSYS_COLOUR_HOTLIGHT));
\twxFont bridgeXHeaderFont = m_pLabel->GetFont();
\tbridgeXHeaderFont.SetWeight(wxFONTWEIGHT_BOLD);
\tm_pLabel->SetFont(bridgeXHeaderFont);
#endif
\twxSize size = GetSize();'''
if view_anchor not in view_text:
    raise SystemExit("PATCH_FAIL: view header label anchor not found.")
view_text = view_text.replace(view_anchor, view_replacement, 1)
setlabel_old = '''\tm_pLabel->SetLabel(label);
\tint w;
\tGetTextExtent(label, &w, &m_labelHeight);'''
setlabel_new = '''\twxString bridgeXLabel = label.Upper();
\tm_pLabel->SetLabel(bridgeXLabel);
\tint w;
\tGetTextExtent(bridgeXLabel, &w, &m_labelHeight);'''
if setlabel_old not in view_text:
    raise SystemExit("PATCH_FAIL: view header SetLabel anchor not found.")
view_text = view_text.replace(setlabel_old, setlabel_new, 1)
viewheader_path.write_text(view_text, encoding="utf-8", newline="\n")

# Rebrand Windows VERSIONINFO metadata while keeping upstream version numbers.
version_text = version_rc_path.read_text(encoding="utf-8")
for old, new in (
    ('VALUE "CompanyName", "FileZilla Project"', 'VALUE "CompanyName", "TNSuite"'),
    ('VALUE "FileDescription", "FileZilla FTP Client"', 'VALUE "FileDescription", "TNSuite BridgeX Secure Transfer Client"'),
    ('VALUE "InternalName", "FileZilla 3"', 'VALUE "InternalName", "TNSuite BridgeX"'),
    ('VALUE "OriginalFilename", "filezilla.exe"', 'VALUE "OriginalFilename", "BridgeX.exe"'),
    ('VALUE "ProductName", "FileZilla"', 'VALUE "ProductName", "TNSuite BridgeX"'),
):
    if old not in version_text:
        raise SystemExit(f"PATCH_FAIL: VERSIONINFO branding anchor not found: {old}")
    version_text = version_text.replace(old, new, 1)
version_rc_path.write_text(version_text, encoding="utf-8", newline="\n")

# ---------------------------------------------------------------------------
# Build12-Hotfix4 runtime fixes from Windows GUI acceptance.
#
# 1) wxStaticBox captions can stay on the native light-theme text colour even
#    when the rest of a dialog follows BridgeX dark mode. Patch the shared
#    DialogLayout factory so every group caption (Settings, host-key details,
#    and other dialogs) follows wxSYS_COLOUR_WINDOWTEXT in both appearances.
dialogex_text = dialogex_path.read_text(encoding="utf-8")
if "TNSUITE_BRIDGEX_BUILD12_HF4_STATICBOX_TEXT" in dialogex_text:
    raise SystemExit("PATCH_FAIL: Hotfix4 static-box patch unexpectedly already present.")
factory_pos = dialogex_text.find('DialogLayout::createStatBox')
if factory_pos < 0:
    raise SystemExit("PATCH_FAIL: DialogLayout::createStatBox function not found.")
factory_end = dialogex_text.find('\n}', factory_pos)
if factory_end < 0:
    raise SystemExit("PATCH_FAIL: DialogLayout::createStatBox end anchor not found.")
factory_block = dialogex_text[factory_pos:factory_end + 2]

# Build12-Hotfix8: Hotfix5 correctly reached the real 3.70.6 factory but its
# structural token search used the prefix `new wxStaticBox`, which also matches
# `new wxStaticBoxSizer`. It therefore recovered the wxStaticBoxSizer variable
# (`boxSizer`) and incorrectly called SetForegroundColour on the sizer itself.
# Target the actual wxStaticBoxSizer construction deliberately, recover that
# assigned sizer variable, and colour the owned wxStaticBox through GetStaticBox().
# This mirrors the real upstream ownership model and remains fail-closed.
sizer_match = re.search(r'\bnew\s+wxStaticBoxSizer\s*\(', factory_block)
if not sizer_match:
    raise SystemExit("PATCH_FAIL: DialogLayout wxStaticBoxSizer construction token not found.")
staticbox_sizer_new = sizer_match.start()
statement_start = factory_block.rfind('\n', 0, staticbox_sizer_new) + 1
statement_end = factory_block.find(';', staticbox_sizer_new)
if statement_end < 0:
    raise SystemExit("PATCH_FAIL: DialogLayout wxStaticBoxSizer construction terminator not found.")
statement = factory_block[statement_start:statement_end + 1]
lhs = factory_block[statement_start:staticbox_sizer_new]
var_match = re.search(r'([A-Za-z_][A-Za-z0-9_]*)\s*=\s*$', lhs, re.S)
if not var_match:
    raise SystemExit("PATCH_FAIL: DialogLayout wxStaticBoxSizer assigned variable not found.")
staticbox_sizer_var = var_match.group(1)
indent_match = re.match(r'[ \t]*', statement)
indent = indent_match.group(0) if indent_match else '\t'
staticbox_inject = statement + (
    "\n#ifdef __WXMSW__\n"
    f"{indent}// TNSUITE_BRIDGEX_BUILD12_HF4_STATICBOX_TEXT\n"
    f"{indent}// TNSUITE_BRIDGEX_BUILD12_HF5_STATICBOX_STRUCTURAL_MATCH\n"
    f"{indent}// TNSUITE_BRIDGEX_BUILD12_HF6_STATICBOX_TARGET\n"
    f"{indent}// TNSUITE_BRIDGEX_BUILD12_HF7_STATICBOX_COMPLETE_TYPE\n"
    f"{indent}{staticbox_sizer_var}->GetStaticBox()->SetForegroundColour(wxSystemSettings::GetColour(wxSYS_COLOUR_WINDOWTEXT));\n"
    "#endif"
)
absolute_start = factory_pos + statement_start
absolute_end = factory_pos + statement_end + 1
dialogex_text = dialogex_text[:absolute_start] + staticbox_inject + dialogex_text[absolute_end:]

# Hotfix7: wx/sizer.h only forward-declares wxStaticBox. Calling a member on
# GetStaticBox() therefore requires the complete wxStaticBox definition from
# wx/statbox.h in this translation unit. Keep both dependencies explicit and do
# not rely on umbrella/transitive wx headers.
include_anchor = '#include "dialogex.h"\n'
if include_anchor not in dialogex_text:
    raise SystemExit("PATCH_FAIL: dialogex include anchor not found for Hotfix7 wx headers.")
required_dialogex_includes = []
if '#include <wx/statbox.h>' not in dialogex_text:
    required_dialogex_includes.append('#include <wx/statbox.h>\n')
if '#include <wx/settings.h>' not in dialogex_text:
    required_dialogex_includes.append('#include <wx/settings.h>\n')
if required_dialogex_includes:
    dialogex_text = dialogex_text.replace(include_anchor, include_anchor + ''.join(required_dialogex_includes), 1)
# TNSUITE_BRIDGEX_BUILD12_HF7_STATICBOX_COMPLETE_TYPE

dialogex_path.write_text(dialogex_text, encoding="utf-8", newline="\n")

# 2) A version-specific Microsoft Store Notepad path becomes stale whenever the
#    Store package is updated. FileZilla validates every custom association when
#    saving Settings, so one stale txt association can block unrelated Language
#    or Theme changes.
#
# Hotfix15 correction: the SHA-verified FileZilla 3.70.6 source does not bind
# OPTION_EDIT_CUSTOMASSOCIATIONS through XRC SetTextFromOption/SetOptionFromText.
# It loads and saves the native association editor directly. Discover that
# receiver from the authoritative option data path, require Load/Validate/Save
# to resolve consistently, and normalize the value without replacing upstream
# validation or persistence logic.
assoc_text = options_edit_assoc_path.read_text(encoding="utf-8")

# TNSUITE_BRIDGEX_BUILD12_HF13_ASSOC_CONTROL_DISCOVERY
# TNSUITE_BRIDGEX_BUILD12_HF15_NATIVE_ASSOC_RECEIVER_DISCOVERY
native_load_pattern = re.compile(
    r'(?P<receiver>[A-Za-z_][A-Za-z0-9_]*)\s*->\s*ChangeValue\s*\(\s*'
    r'm_pOptions\s*->\s*get_string\s*\(\s*OPTION_EDIT_CUSTOMASSOCIATIONS\s*\)\s*\)\s*;',
    re.S,
)
native_save_pattern = re.compile(
    r'm_pOptions\s*->\s*set\s*\(\s*OPTION_EDIT_CUSTOMASSOCIATIONS\s*,\s*'
    r'(?P<receiver>[A-Za-z_][A-Za-z0-9_]*)\s*->\s*GetValue\s*\(\s*\)\s*\.\s*ToStdWstring\s*\(\s*\)\s*\)\s*;',
    re.S,
)
load_receivers = [m.group('receiver') for m in native_load_pattern.finditer(assoc_text)]
save_receivers = [m.group('receiver') for m in native_save_pattern.finditer(assoc_text)]
if len(load_receivers) != 1 or len(save_receivers) != 1 or load_receivers[0] != save_receivers[0]:
    inventory = [
        f"{line_no}:{line.strip()}"
        for line_no, line in enumerate(assoc_text.splitlines(), 1)
        if 'OPTION_EDIT_CUSTOMASSOCIATIONS' in line or 'ChangeValue' in line or 'GetValue' in line
    ]
    raise SystemExit(
        "PATCH_FAIL: expected one consistent native OPTION_EDIT_CUSTOMASSOCIATIONS receiver; "
        f"load={load_receivers!r} save={save_receivers!r}. Relevant source lines: {inventory!r}"
    )
association_receiver = load_receivers[0]
if association_receiver == 'ID_EDIT_ASSOCIATIONS':
    raise SystemExit("PATCH_FAIL: obsolete Hotfix12 association ID assumption resolved as receiver.")


def find_method_span(source, method_name):
    signature = re.search(
        rf'bool\s+COptionsPageEditAssociations::{re.escape(method_name)}\s*\(\s*\)\s*\{{',
        source,
    )
    if not signature:
        return None
    open_brace = source.find('{', signature.start())
    depth = 0
    i = open_brace
    state = 'code'
    while i < len(source):
        c = source[i]
        n = source[i + 1] if i + 1 < len(source) else ''
        if state == 'code':
            if c == '/' and n == '/':
                state = 'line_comment'; i += 2; continue
            if c == '/' and n == '*':
                state = 'block_comment'; i += 2; continue
            if c == '"':
                state = 'string'; i += 1; continue
            if c == "'":
                state = 'char'; i += 1; continue
            if c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    return (signature.start(), open_brace, i + 1)
        elif state == 'line_comment':
            if c == '\n': state = 'code'
        elif state == 'block_comment':
            if c == '*' and n == '/': state = 'code'; i += 2; continue
        elif state in ('string', 'char'):
            quote = '"' if state == 'string' else "'"
            if c == '\\': i += 2; continue
            if c == quote: state = 'code'
        i += 1
    return None

load_span = find_method_span(assoc_text, 'LoadPage')
validate_span = find_method_span(assoc_text, 'Validate')
save_span = find_method_span(assoc_text, 'SavePage')
if not load_span or not validate_span or not save_span:
    raise SystemExit(
        f"PATCH_FAIL: association method span missing Load={bool(load_span)} Validate={bool(validate_span)} Save={bool(save_span)}"
    )
load_binding = native_load_pattern.search(assoc_text)
save_binding = native_save_pattern.search(assoc_text)
if not (load_span[0] <= load_binding.start() < load_span[2]):
    raise SystemExit("PATCH_FAIL: native association load binding is outside LoadPage().")
if not (save_span[0] <= save_binding.start() < save_span[2]):
    raise SystemExit("PATCH_FAIL: native association save binding is outside SavePage().")
# Validate() only needs to be structurally resolvable. Hotfix15 intentionally
# does not assume how upstream validation reads the editor: changing the native
# receiver before the existing body is sufficient and avoids another source-shape guess.

include_match = re.search(r'(?m)^[ \t]*#include[ \t]+[<"]optionspage_edit_associations\.h[>"][ \t]*\n', assoc_text)
if not include_match:
    raise SystemExit("PATCH_FAIL: edit-associations header include not found.")
include_insert = '''
#ifdef __WXMSW__
#include <wx/filename.h>
#include <wx/utils.h>
#endif
'''
assoc_text = assoc_text[:include_match.end()] + include_insert + assoc_text[include_match.end():]
helper = r'''
#ifdef __WXMSW__
namespace {
// TNSUITE_BRIDGEX_BUILD12_HF12_STORE_NOTEPAD_VALUE_REPAIR
// TNSUITE_BRIDGEX_BUILD12_HF13_ASSOC_VALUE_REPAIR
// TNSUITE_BRIDGEX_BUILD12_HF15_NATIVE_ASSOC_VALUE_REPAIR
wxString RepairStaleStoreNotepadAssociations(wxString value)
{
    wxString windowsDir;
    if (!wxGetEnv(L"WINDIR", &windowsDir) || windowsDir.empty()) {
        return value;
    }
    wxFileName stableNotepad(windowsDir + L"\\System32\\notepad.exe");
    if (!stableNotepad.FileExists()) {
        return value;
    }
    wxString const replacement = stableNotepad.GetFullPath();

    wxString repaired;
    size_t start = 0;
    while (start <= value.length()) {
        size_t nl = value.find(L'\n', start);
        if (nl == wxString::npos) {
            nl = value.length();
        }
        wxString line = value.Mid(start, nl - start);
        wxString lower = line.Lower();
        wxString const storeMarker = L"\\windowsapps\\microsoft.windowsnotepad_";
        wxString const exeSuffix = L"\\notepad\\notepad.exe";
        size_t marker = lower.find(storeMarker);
        size_t suffix = lower.find(exeSuffix, marker == wxString::npos ? 0 : marker);
        if (marker != wxString::npos && suffix != wxString::npos) {
            size_t pathStart = 0;
            size_t quote = line.rfind(L'"', marker);
            if (quote != wxString::npos) {
                pathStart = quote + 1;
            }
            else {
                size_t space = line.rfind(L' ', marker);
                size_t tab = line.rfind(L'\t', marker);
                size_t const afterSpace = space == wxString::npos ? 0 : space + 1;
                size_t const afterTab = tab == wxString::npos ? 0 : tab + 1;
                pathStart = afterSpace > afterTab ? afterSpace : afterTab;
            }
            size_t pathEnd = suffix + exeSuffix.length();
            line = line.Left(pathStart) + replacement + line.Mid(pathEnd);
        }
        repaired += line;
        if (nl < value.length()) {
            repaired += L'\n';
            start = nl + 1;
        }
        else {
            break;
        }
    }
    return repaired;
}
}
#endif
'''
last_include = list(re.finditer(r'(?m)^#include[^\n]*\n', assoc_text))
if not last_include:
    raise SystemExit("PATCH_FAIL: no include block in edit-associations source.")
pos = last_include[-1].end()
assoc_text = assoc_text[:pos] + helper + assoc_text[pos:]

# Re-resolve native source locations after includes/helper insertion.
load_binding = native_load_pattern.search(assoc_text)
save_binding = native_save_pattern.search(assoc_text)
load_span = find_method_span(assoc_text, 'LoadPage')
validate_span = find_method_span(assoc_text, 'Validate')
save_span = find_method_span(assoc_text, 'SavePage')

# Normalize immediately after the authoritative load so the Settings UI shows
# the stable path, but leave FileZilla's original option load untouched.
load_indent_match = re.search(r'(?m)^(?P<indent>[ \t]*)' + re.escape(load_binding.group(0)), assoc_text)
if not load_indent_match:
    raise SystemExit("PATCH_FAIL: native LoadPage binding indentation not resolved.")
load_indent = load_indent_match.group('indent')
load_injection = f'''\n{load_indent}#ifdef __WXMSW__
{load_indent}// TNSUITE_BRIDGEX_BUILD12_HF15_NATIVE_LOAD_REPAIR
{load_indent}{association_receiver}->ChangeValue(RepairStaleStoreNotepadAssociations({association_receiver}->GetValue()));
{load_indent}#endif'''
assoc_text = assoc_text[:load_binding.end()] + load_injection + assoc_text[load_binding.end():]

# Re-resolve spans after load injection, then normalize the same native control
# at the beginning of Validate(). The upstream validation body remains intact.
validate_span = find_method_span(assoc_text, 'Validate')
validate_indent_match = re.match(r'[ \t]*', assoc_text[validate_span[1] + 1:])
validate_indent = validate_indent_match.group(0) + '\t'
validate_injection = f'''\n{validate_indent}#ifdef __WXMSW__
{validate_indent}// TNSUITE_BRIDGEX_BUILD12_HF13_VALIDATE_REPAIRED_ASSOCIATIONS
{validate_indent}// TNSUITE_BRIDGEX_BUILD12_HF15_NATIVE_VALIDATE_REPAIR
{validate_indent}{{
{validate_indent}\twxString const bridgeXBefore = {association_receiver}->GetValue();
{validate_indent}\twxString const bridgeXAfter = RepairStaleStoreNotepadAssociations(bridgeXBefore);
{validate_indent}\tif (bridgeXAfter != bridgeXBefore) {{
{validate_indent}\t\t{association_receiver}->ChangeValue(bridgeXAfter);
{validate_indent}\t}}
{validate_indent}}}
{validate_indent}#endif'''
assoc_text = assoc_text[:validate_span[1] + 1] + validate_injection + assoc_text[validate_span[1] + 1:]

# Normalize again at SavePage entry so persistence is protected even if the
# control changed after validation. Keep m_pOptions->set(...) byte-for-byte.
save_span = find_method_span(assoc_text, 'SavePage')
save_indent_match = re.match(r'[ \t]*', assoc_text[save_span[1] + 1:])
save_indent = save_indent_match.group(0) + '\t'
save_injection = f'''\n{save_indent}#ifdef __WXMSW__
{save_indent}// TNSUITE_BRIDGEX_BUILD12_HF13_PERSIST_REPAIRED_ASSOCIATIONS
{save_indent}// TNSUITE_BRIDGEX_BUILD12_HF15_NATIVE_PERSIST_REPAIR
{save_indent}{{
{save_indent}\twxString const bridgeXBefore = {association_receiver}->GetValue();
{save_indent}\twxString const bridgeXAfter = RepairStaleStoreNotepadAssociations(bridgeXBefore);
{save_indent}\tif (bridgeXAfter != bridgeXBefore) {{
{save_indent}\t\t{association_receiver}->ChangeValue(bridgeXAfter);
{save_indent}\t}}
{save_indent}}}
{save_indent}#endif'''
assoc_text = assoc_text[:save_span[1] + 1] + save_injection + assoc_text[save_span[1] + 1:]

if not native_save_pattern.search(assoc_text):
    raise SystemExit("PATCH_FAIL: upstream native association persistence was not preserved.")
if 'Associated program not found:' not in assoc_text:
    raise SystemExit("PATCH_FAIL: upstream missing-program validation was not preserved.")
for marker in (
    'TNSUITE_BRIDGEX_BUILD12_HF15_NATIVE_LOAD_REPAIR',
    'TNSUITE_BRIDGEX_BUILD12_HF13_VALIDATE_REPAIRED_ASSOCIATIONS',
    'TNSUITE_BRIDGEX_BUILD12_HF15_NATIVE_VALIDATE_REPAIR',
    'TNSUITE_BRIDGEX_BUILD12_HF13_PERSIST_REPAIRED_ASSOCIATIONS',
    'TNSUITE_BRIDGEX_BUILD12_HF15_NATIVE_PERSIST_REPAIR',
):
    if marker not in assoc_text:
        raise SystemExit(f"PATCH_FAIL: required association marker missing: {marker}")
if 'ID_EDIT_ASSOCIATIONS' in assoc_text:
    raise SystemExit("PATCH_FAIL: stale hard-coded ID_EDIT_ASSOCIATIONS assumption remains in patched source.")

options_edit_assoc_path.write_text(assoc_text, encoding="utf-8", newline="\n")
print(f"EDIT_ASSOC_HF15_RECEIVER={association_receiver}")
print("EDIT_ASSOC_HF15_NATIVE_DATA_PATH=PASS")

# 3) Native report/list controls were still rendering near-black while BridgeX
#    workspace/tree surfaces used the intended navy. CFileListCtrl is the
#    shared local/remote file-list base; explicitly bind it to the current
#    system WINDOW/WINDOWTEXT colours and reapply on a theme change.
filelist_text = filelistctrl_path.read_text(encoding="utf-8")
# Hotfix7: make wxSystemSettings a direct translation-unit dependency too.
# Preserve FileZilla's first-include/PCH ordering by inserting after the first
# include directive, without depending on a specific upstream header name.
if '#include <wx/settings.h>' not in filelist_text:
    first_include = re.search(r'(?m)^#include[^\n]*\n', filelist_text)
    if not first_include:
        raise SystemExit("PATCH_FAIL: filelistctrl first include not found for wx/settings.h.")
    include_pos = first_include.end()
    filelist_text = filelist_text[:include_pos] + '#include <wx/settings.h>\n' + filelist_text[include_pos:]
filelist_anchor = '\tSetBackgroundStyle(wxBG_STYLE_SYSTEM);\n'
if filelist_anchor not in filelist_text:
    raise SystemExit("PATCH_FAIL: CFileListCtrl background-style anchor not found.")
filelist_replacement = '''	SetBackgroundStyle(wxBG_STYLE_SYSTEM);
#ifdef __WXMSW__
	// TNSUITE_BRIDGEX_BUILD12_HF4_LIST_SURFACE
	SetBackgroundColour(wxSystemSettings::GetColour(wxSYS_COLOUR_WINDOW));
	SetForegroundColour(wxSystemSettings::GetColour(wxSYS_COLOUR_WINDOWTEXT));
#endif
'''
filelist_text = filelist_text.replace(filelist_anchor, filelist_replacement, 1)
# Existing MSW sys-colour handler is a stable, precise place to reapply after a
# Light/Dark restart or Windows colour notification.
handler_anchor = '''		CallAfter([this](){
			InitColors();
		});'''
if handler_anchor not in filelist_text:
    raise SystemExit("PATCH_FAIL: CFileListCtrl sys-colour handler anchor not found.")
handler_replacement = '''		CallAfter([this](){
			SetBackgroundColour(wxSystemSettings::GetColour(wxSYS_COLOUR_WINDOW));
			SetForegroundColour(wxSystemSettings::GetColour(wxSYS_COLOUR_WINDOWTEXT));
			InitColors();
		});'''
filelist_text = filelist_text.replace(handler_anchor, handler_replacement, 1)
filelistctrl_path.write_text(filelist_text, encoding="utf-8", newline="\n")

# Hotfix11 runtime correction: the Hotfix8 constructor hypothesis was disproved by
# the exact FileZilla 3.70.6 source used by the Windows build: it contains no
# wxStaticBitmap(... wxNullBitmap ...) constructor matching that assumption.
# Runtime evidence instead reaches wxStaticBitmap::SetBitmap(wxBitmapBundle const&).
# Inventory actual wxStaticBitmap receivers and guard SetBitmap inputs narrowly.
# Zero candidates is an inventory result, not a build blocker; GUI runtime remains
# authoritative. Never disable or filter wxWidgets assertions globally.
interface_cpp_root = root / "src" / "interface"

hf11_staticbitmap_names = set()
hf11_decl_patterns = (
    re.compile(r"\bwxStaticBitmap\s*\*+\s*(?:const\s+)?([A-Za-z_][A-Za-z0-9_]*)"),
    re.compile(r"\bwxStaticBitmap\s+([A-Za-z_][A-Za-z0-9_]*)\b"),
    re.compile(r"(?:unique_ptr|shared_ptr)\s*<\s*wxStaticBitmap\s*>\s*([A-Za-z_][A-Za-z0-9_]*)"),
)
for decl_file in sorted(interface_cpp_root.rglob("*")):
    if decl_file.suffix.lower() not in {".h", ".hpp", ".cpp"}:
        continue
    decl_text = decl_file.read_text(encoding="utf-8")
    for decl_pattern in hf11_decl_patterns:
        hf11_staticbitmap_names.update(decl_pattern.findall(decl_text))


def _hf11_has_top_level_comma(text: str, mask: list[bool], open_pos: int, close_pos: int) -> bool:
    depth = 0
    for i in range(open_pos + 1, close_pos):
        if not mask[i]:
            continue
        ch = text[i]
        if ch in "([{":
            depth += 1
        elif ch in ")]}" and depth:
            depth -= 1
        elif ch == "," and depth == 0:
            return True
    return False


def _hf11_inject_bitmap_guard(text: str, candidate) -> str:
    first_include = re.search(r"(?m)^#include[^\n]*\n", text)
    if not first_include:
        raise SystemExit(f"PATCH_FAIL: {candidate} has guarded SetBitmap but no include anchor.")
    insert_at = first_include.end()
    headers = ""
    if "#include <wx/bitmap.h>" not in text:
        headers += "#include <wx/bitmap.h>\n"
    if "#include <wx/bmpbndl.h>" not in text:
        headers += "#include <wx/bmpbndl.h>\n"
    if headers:
        text = text[:insert_at] + headers + text[insert_at:]
    include_block = re.match(r"(?:#include[^\n]*\n|[ \t]*\n)+", text)
    if not include_block:
        raise SystemExit(f"PATCH_FAIL: {candidate} include block could not be bounded.")
    helper = r'''// TNSUITE_BRIDGEX_BUILD12_HF11_SAFE_BITMAP_BUNDLE
namespace {
wxBitmapBundle BridgeXSafeStaticBitmap(wxBitmapBundle const& bundle)
{
    if (bundle.IsOk()) {
        return bundle;
    }
    return wxBitmapBundle::FromBitmap(wxBitmap(1, 1));
}

wxBitmap BridgeXSafeStaticBitmap(wxBitmap const& bitmap)
{
    if (bitmap.IsOk()) {
        return bitmap;
    }
    return wxBitmap(1, 1);
}
}

'''
    return text[:include_block.end()] + helper + text[include_block.end():]


hf11_setbitmap_patched = []
hf11_setbitmap_call_count = 0
hf11_call_pattern = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*(->|\.)\s*SetBitmap\s*\(")
for candidate in sorted(interface_cpp_root.rglob("*.cpp")):
    candidate_text = candidate.read_text(encoding="utf-8")
    mask = _cpp_code_mask(candidate_text)
    edits = []
    for call in hf11_call_pattern.finditer(candidate_text):
        if not mask[call.start()]:
            continue
        receiver = call.group(1)
        # Runtime evidence points at status-bar state icons. Known wxStaticBitmap
        # declarations are eligible; statusbar.cpp is a narrow fallback if the
        # receiver declaration is hidden behind a typedef/base declaration.
        if receiver not in hf11_staticbitmap_names and candidate.name.lower() != "statusbar.cpp":
            continue
        open_pos = call.end() - 1
        close_pos = _matching_close_paren(candidate_text, mask, open_pos)
        if close_pos == -1:
            raise SystemExit(f"PATCH_FAIL: {candidate} SetBitmap call could not be bounded.")
        if _hf11_has_top_level_comma(candidate_text, mask, open_pos, close_pos):
            continue
        argument = candidate_text[open_pos + 1:close_pos].strip()
        if not argument or argument.startswith("BridgeXSafeStaticBitmap("):
            continue
        edits.append((open_pos + 1, close_pos, f"BridgeXSafeStaticBitmap({argument})"))
    hf11_setbitmap_call_count += len(edits)
    if not edits:
        continue
    patched_text = candidate_text
    for edit_start, edit_end, replacement in reversed(edits):
        patched_text = patched_text[:edit_start] + replacement + patched_text[edit_end:]
    patched_text = _hf11_inject_bitmap_guard(patched_text, candidate)
    candidate.write_text(patched_text, encoding="utf-8", newline="\n")
    hf11_setbitmap_patched.append((candidate, len(edits)))

print(f"HF11_UPSTREAM_STATICBITMAP_DECLS={len(hf11_staticbitmap_names)}")
print(f"HF11_UPSTREAM_SETBITMAP_CALLS={hf11_setbitmap_call_count}")
print("HF11_UPSTREAM_BITMAP_INVENTORY_QA=PASS")
if not hf11_setbitmap_patched:
    print("STATUSBITMAP_HF11_PATCH_APPLIED=NONE")

# Replace upstream FileZilla application artwork with BridgeX brand assets.
icon_source = brand_assets / "BridgeX-AppIcon.ico"
if not icon_source.is_file():
    raise SystemExit(f"PATCH_FAIL: missing brand asset {icon_source}")
(resource_root / "FileZilla.ico").write_bytes(icon_source.read_bytes())
for png in resource_root.glob("*x*/filezilla.png"):
    replacement = brand_assets / f"BridgeX-{png.parent.name}.png"
    if replacement.is_file():
        png.write_bytes(replacement.read_bytes())
if not (resource_root / "480x480" / "filezilla.png").is_file():
    raise SystemExit("PATCH_FAIL: 480x480 BridgeX application artwork missing")

# FileZilla 3.70.6 intentionally rejects wxWidgets 3.3 because it was treated as
# a development branch when this release line was authored. Build12 needs wx 3.3
# for native per-app Windows dark mode, so replace only that configure-time guard.
# The build script separately pins/verifies wxWidgets 3.3.x and fails closed.
configure_text = configure_path.read_text(encoding="utf-8")
wx33_guard = """    if test "${WX_VERSION_MAJOR}.${WX_VERSION_MINOR}" = "3.3"; then
      AC_MSG_ERROR([You must use wxWidgets 3.2.x, development versions of wxWidgets are not supported.])
    fi
"""
wx33_replacement = """    # TNSUITE_BRIDGEX_BUILD12_WX33
    # TNSUITE_BRIDGEX_BUILD12_LOCALES_EXTERNAL: configure is invoked with --disable-locales;
    # shipped .po catalogs are validated and packaged directly by the Build12 runner.
    if test "${WX_VERSION_MAJOR}.${WX_VERSION_MINOR}" = "3.3"; then
      AC_MSG_NOTICE([TNSuite BridgeX Build12: wxWidgets 3.3 compatibility override enabled])
    fi
"""
if wx33_guard not in configure_text:
    raise SystemExit("PATCH_FAIL: wxWidgets 3.3 configure guard not found; refusing fuzzy patch.")
configure_text = configure_text.replace(wx33_guard, wx33_replacement, 1)
configure_path.write_text(configure_text, encoding="utf-8", newline="\n")

print(f"PATCH_APPLIED={ui_path}")
print(f"CONFIGURE_PATCH_APPLIED={configure_path}")
print(f"AUI_WX33_PATCH_APPLIED={aui_path}")
print(f"ICON_WX33_PATCH_APPLIED={fileexists_path}")
print(f"LOCALTREE_TOOLCHAIN_PATCH_APPLIED={localtree_path}")
print(f"SITEMANAGER_TOOLCHAIN_PATCH_APPLIED={sitemanager_controls_path}")
print(f"OPTIONS_TOOLCHAIN_PATCH_APPLIED={options_filetype_path}")
print(f"EDIT_ASSOC_HF4_PATCH_APPLIED={options_edit_assoc_path}")
print(f"STATICBOX_HF4_PATCH_APPLIED={dialogex_path}")
print(f"FILELIST_HF4_PATCH_APPLIED={filelistctrl_path}")
for patched_file, patched_count in hf11_setbitmap_patched:
    print(f"STATUSBITMAP_HF11_PATCH_APPLIED={patched_file}:{patched_count}")
print(f"PORTABLE_NO_SHELLEXT_PATCH_APPLIED={src_makefile_am_path}")
print("PATCH_SCOPE=TNSUITE_BRIDGEX_BUILD12_GUI_APPEARANCE_LANGUAGE_HELP_BRAND_WX33_UCRT64_COMPAT_HF10_RUNTIME_PRODUCT")
