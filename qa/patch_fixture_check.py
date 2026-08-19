#!/usr/bin/env python3
from pathlib import Path
import re, subprocess, sys, tempfile

kit=Path(__file__).resolve().parents[1]
patcher=kit/'scripts/patch_tnsuite_bridgex.py'
compat=kit/'qa/source_compat_check.py'

with tempfile.TemporaryDirectory(prefix='bridgex-build12-patch-') as td:
    root=Path(td)
    for d in ['src/interface/settings','src/interface/resources/480x480']:
        (root/d).mkdir(parents=True, exist_ok=True)

    (root/'src/interface/FileZilla.cpp').write_text(r'''#include "filezilla.h"
#elif defined(__WXMSW__)
#include <shobjidl.h>
#endif
using namespace std::literals;

bool CFileZillaApp::OnInit()
{
	AddStartupProfileRecord("CFileZillaApp::OnInit()"sv);
	SetAppDisplayName("FileZilla");
	SetCurrentProcessExplicitAppUserModelID(L"FileZilla.Client.AppID");
	options_ = std::make_unique<COptions>();

	InitLocale();
}
bool first() {
	pLocale->AddCatalog(_T("libfilezilla"));
	return true;
}
bool second() {
	pLocale->AddCatalog(_T("libfilezilla"));
	return true;
}
void resource_error() {
  auto a = _("Could not find the resource files for FileZilla, closing FileZilla.\nYou can specify the data directory of FileZilla by setting the FZ_DATADIR environment variable.");
  auto b = _("FileZilla Error");
}
''',encoding='utf-8',newline='\n')

    (root/'src/interface/Options.h').write_text('''enum interfaceOptions : unsigned int\n{\n\tOPTION_NUMTRANSFERS,\n\tOPTION_LANGUAGE,\n\tOPTION_CONCURRENTDOWNLOADLIMIT,\n\tOPTIONS_NUM\n};\n''',encoding='utf-8',newline='\n')
    (root/'src/interface/Options.cpp').write_text('''static int f(){\n\tstatic int const value = register_options({\n\t\t{ "Language Code", L"", option_flags::normal, 50 },\n\t\t{ "Concurrent download limit", 0, option_flags::numeric_clamp, 0, 10 },\n\t});\n}\n''',encoding='utf-8',newline='\n')
    (root/'src/interface/settings/optionspage_interface.cpp').write_text(r'''struct COptionsPageInterface::impl
{
	wxChoice* filepane_layout_{};
	wxChoice* messagelog_pos_{};
	wxCheckBox* swap_{};
};
bool COptionsPageInterface::CreateControls(wxWindow* parent)
{
	auto main = lay.createFlex(1);
	SetSizer(main);

	{
		auto [box, inner] = lay.createStatBox(main, _("Layout"), 1);
	}
}
bool COptionsPageInterface::LoadPage()
{
	impl_->filepane_layout_->SetSelection(m_pOptions->get_int(OPTION_FILEPANE_LAYOUT));
	return true;
}
bool COptionsPageInterface::SavePage()
{
	m_pOptions->set(OPTION_FILEPANE_LAYOUT, impl_->filepane_layout_->GetSelection());
	return true;
}
''',encoding='utf-8',newline='\n')
    (root/'src/interface/settings/settingsdialog.cpp').write_text('''void f(){\n\tAddPage(_("Language"), new COptionsPageLanguage, 0);\n}\n''',encoding='utf-8',newline='\n')

    (root/'src/interface/Mainfrm.cpp').write_text(r'''void f(bool language_changed){
    auto a=_T("FileZilla"); auto b=_T(" - FileZilla");
    if (language_changed)
        wxMsg :: Message(
            _("FileZilla needs to be restarted for the language change to take effect."),
            _("Language changed"),
            wxICON_INFORMATION);
}
''',encoding='utf-8',newline='\n')
    (root/'src/interface/aboutdialog.cpp').write_text(r"""void f() {
	wxDialogEx::Create(parent, nullID, _("About FileZilla"));
	std::wstring version = L"FileZilla " + GetFileZillaVersion();
	topRight->Add(new wxStaticText(this, nullID, version));
	topRight->Add(new wxStaticText(this, nullID, L"Copyright (C) 2004-2026  Tim Kosse"));
	homepage->Add(new wxHyperlinkCtrl(this, nullID, L"https://filezilla-project.org/", L"https://filezilla-project.org/"), lay.valign);
	inner->Add(new wxStaticText(box, nullID, _("Settings directory:")));
	auto legal = L"FileZilla makes use of the following third-party libraries:\n\n";
	wxString text = _T("FileZilla Client\n");
	text += _T("Version:          ") + GetFileZillaVersion();
	if (CBuildInfo::GetBuildType() == _T("nightly")) {
		text += _T("-nightly");
	}
	text += '\n';
}
""",encoding='utf-8',newline='\n')
    (root/'src/interface/welcome_dialog.cpp').write_text(r'''bool CWelcomeDialog::Run(bool force)
{
	auto const ownVersion = GetFileZillaVersion();
	auto const greetingVersion = options_.get_string(OPTION_GREETINGVERSION);
	Create(parent_, -1, _("Welcome to FileZilla"));
	auto heading = new wxStaticText(this, -1, _T("FileZilla ") + GetFileZillaVersion());
	headerLeft->Add(new wxStaticText(this, -1, _("The free open source FTP solution")));
	wxString const url = _T("https://welcome.filezilla-project.org/welcome?type=client&category=%s&version=") + ownVersion;
	auto news = new wxStaticText(this, -1, _("What's new"));
	main->Add(new wxHyperlinkCtrl(this, -1, wxString::Format(_("New features and improvements in %s"), ownVersion), wxString::Format(url, _T("news")) + _T("&oldversion=") + greetingVersion), 0, wxLEFT, lay.indent);
	main->Add(new wxHyperlinkCtrl(this, -1, _("Asking questions in the FileZilla Forums"), wxString::Format(url, _T("support_forum"))), 0, wxLEFT, lay.indent);
	main->Add(new wxHyperlinkCtrl(this, -1, _("Reporting bugs and feature requests"), wxString::Format(url, _T("support_more"))), 0, wxLEFT, lay.indent);
	main->Add(new wxHyperlinkCtrl(this, -1, _("Basic usage instructions"), wxString::Format(url, _T("documentation_basic"))), 0, wxLEFT, lay.indent);
	main->Add(new wxHyperlinkCtrl(this, -1, _("Configuring FileZilla and your network"), wxString::Format(url, _T("documentation_network"))), 0, wxLEFT, lay.indent);
	main->Add(new wxHyperlinkCtrl(this, -1, _("Further documentation"), wxString::Format(url, _T("documentation_more"))), 0, wxLEFT, lay.indent);
}
''',encoding='utf-8',newline='\n')
    (root/'src/interface/menu_bar.cpp').write_text(r'''#include "state.h"
void f() {
  auto a = _("Close FileZilla");
  auto b = _("Open the settings dialog of FileZilla");
	wxMenu* help = new wxMenu;
	Append(help, _("&Help"));
	help->Append(XRCID("ID_MENU_HELP_GETTINGHELP"), _("&Getting help..."));
	help->Append(XRCID("ID_MENU_HELP_BUGREPORT"), _("&Report a bug..."));
}
''',encoding='utf-8',newline='\n')

    (root/'configure.ac').write_text('''    if test "${WX_VERSION_MAJOR}.${WX_VERSION_MINOR}" = "3.3"; then\n      AC_MSG_ERROR([You must use wxWidgets 3.2.x, development versions of wxWidgets are not supported.])\n    fi\n''',encoding='utf-8',newline='\n')
    (root/'src/interface/aui_notebook_ex.cpp').write_text('''virtual wxSize GetTabSize(wxDC& dc, wxWindow* wnd, const wxString& caption, const wxBitmapBundle& bitmap, bool active, int close_button_state, int* x_extent) override\n{\n\twxAuiNotebook::OnTabDragMotion(evt);\n}\n''',encoding='utf-8',newline='\n')
    (root/'src/interface/fileexistsdlg.cpp').write_text('''\t\twxIcon icon;\n\t\ticon.SetHandle(fileinfo.hIcon);\n\t\ticon.SetSize(size.x, size.y);\n\n\t\tdc->DrawIcon(icon, 0, 0);\n''',encoding='utf-8',newline='\n')
    (root/'src/interface/toolbar.cpp').write_text(r'''#include "toolbar.h"
namespace {
	constexpr int toolbarStyle = wxTB_FLAT | wxTB_HORIZONTAL | wxTB_NODIVIDER;
}
void CToolBar::MakeTool(char const* id, const wxBitmap& bmp, const wxString& tooltip, const wxString& help, int type) {
	wxToolBar::AddTool(XRCID(id), wxString(), bmp, wxBitmap(), type, tooltip, help);
}
#ifdef __WXMSW__
bool CToolBar::Realize()
{
	bool ret = wxToolBar::Realize();
}
#endif
''',encoding='utf-8',newline='\n')
    (root/'src/interface/quickconnectbar.cpp').write_text(r'''void f() {
	auto sizer = new wxBoxSizer(wxVERTICAL);
	DialogLayout layout(&parent);
	auto mainSizer = layout.createFlex(0, 1);
	auto connect = new wxButton(this, XRCID("ID_QUICKCONNECT_OK"), _("&Quickconnect"));
}
''',encoding='utf-8',newline='\n')
    (root/'src/interface/viewheader.cpp').write_text(r'''void f() {
	m_pLabel = new wxStaticText(this, wxID_ANY, label, wxDefaultPosition, wxDefaultSize);
	wxSize size = GetSize();
}
void CViewHeader::SetLabel(const wxString& label)
{
	m_pLabel->SetLabel(label);
	int w;
	GetTextExtent(label, &w, &m_labelHeight);
}
''',encoding='utf-8',newline='\n')
    (root/'src/interface/Makefile.am').write_text('''if FZ_WINDOWS\nfilezilla_LDFLAGS += -lnormaliz -lole32 -luuid -lnetapi32 -lmpr -lpowrprof -lws2_32 -lshlwapi\nendif\n''',encoding='utf-8',newline='\n')
    (root/'src/interface/LocalTreeView.cpp').write_text('auto v = path + fz::local_filesys::path_separator + pData->m_known_subdir;\n',encoding='utf-8',newline='\n')
    (root/'src/interface/sitemanager_controls.cpp').write_text('if (sse_algorithm == "AES256") {}\nif (sse_algorithm == "aws:kms") {}\nif (sse_algorithm == "customer") {}\n',encoding='utf-8',newline='\n')
    (root/'src/interface/settings/optionspage_filetype.cpp').write_text("auto v = extensions.substr(0, pos - 1) + '|';\n",encoding='utf-8',newline='\n')
    (root/'src/interface/settings/optionspage_edit_associations.cpp').write_text(r'''#include <filezilla.h>

#include "../Options.h"
#include "settingsdialog.h"
#include "optionspage.h"
#include "optionspage_edit_associations.h"

bool COptionsPageEditAssociations::LoadPage()
{
    assocs_->ChangeValue(m_pOptions->get_string(OPTION_EDIT_CUSTOMASSOCIATIONS));
    return true;
}

bool COptionsPageEditAssociations::SavePage()
{
    m_pOptions->set(OPTION_EDIT_CUSTOMASSOCIATIONS, assocs_->GetValue().ToStdWstring());
    return true;
}

extern bool UnquoteCommand(wxString& command, wxString& arguments, bool is_dde = false);
extern bool ProgramExists(const wxString& editor);

bool COptionsPageEditAssociations::Validate()
{
    wxString associations = GetAssociationsForValidation();
    associations.Replace(_T("\r"), wxString());
    int pos;
    while ((pos = associations.Find('\n')) != -1) {
        wxString assoc = associations.Left(pos);
        associations = associations.Mid(pos + 1);
        if (assoc.empty())
            continue;
        wxString command;
        if (!UnquoteCommand(assoc, command))
            return DisplayError(_T("ID_ASSOCIATIONS"), _("Improperly quoted association."));
        if (!ProgramExists(command)) {
            wxString error = _("Associated program not found:");
            error += '\n';
            error += command;
            return DisplayError(_T("ID_ASSOCIATIONS"), error);
        }
    }
    return true;
}
''',encoding='utf-8',newline='\n')
    (root/'src/interface/dialogex.cpp').write_text(r'''#include "dialogex.h"
#include <wx/settings.h>
std::tuple<wxStaticBox*, wxFlexGridSizer*> DialogLayout::createStatBox(wxSizer* sizer, wxString const& label, int proportion, int cols) const
{
	auto boxSizer = new wxStaticBoxSizer(
		new wxStaticBox(
			parent_,
			nullID,
			label
		),
		wxVERTICAL
	);
	auto inner = new wxFlexGridSizer(cols);
	return {boxSizer->GetStaticBox(), inner};
}
''',encoding='utf-8',newline='\n')
    (root/'src/interface/filelistctrl.cpp').write_text(r'''#include "filezilla.h"
template<class CFileData> CFileListCtrl<CFileData>::CFileListCtrl(wxWindow* pParent, CQueueView* pQueue, COptionsBase & options, bool border)
{
	SetBackgroundStyle(wxBG_STYLE_SYSTEM);
#ifndef __WXMSW__
	GetMainWindow()->SetBackgroundStyle(wxBG_STYLE_SYSTEM);
#endif
#ifdef __WXMSW__
	Bind(wxEVT_SYS_COLOUR_CHANGED, [this](wxSysColourChangedEvent& evt) {
		CallAfter([this](){
			InitColors();
		});
		evt.Skip();
	});
#endif
}
''',encoding='utf-8',newline='\n')
    (root/'src/interface/statusbar.h').write_text(r'''#pragma once
#include <wx/statbmp.h>
#include <wx/bmpbndl.h>
class CStatusBar {
public:
    void UpdateSecurity(wxBitmapBundle const& bundle);
private:
    wxStaticBitmap* m_security{};
};
''',encoding='utf-8',newline='\n')
    (root/'src/interface/statusbar.cpp').write_text(r'''#include "filezilla.h"
#include "statusbar.h"
void CStatusBar::UpdateSecurity(wxBitmapBundle const& bundle)
{
    m_security->SetBitmap(bundle);
}
''',encoding='utf-8',newline='\n')
    (root/'src/Makefile.am').write_text('SUBDIRS = include engine $(MAYBE_PUGIXML) $(MAYBE_DBUS) commonui $(MAYBE_GUI) $(MAYBE_STORJ) $(MAYBE_FZSHELLEXT) .\n',encoding='utf-8',newline='\n')

    (root/'src/interface/resources/FileZilla.ico').write_bytes(b'legacy')
    (root/'src/interface/resources/version.rc.in').write_text('''VALUE "CompanyName", "FileZilla Project"\nVALUE "FileDescription", "FileZilla FTP Client"\nVALUE "InternalName", "FileZilla 3"\nVALUE "OriginalFilename", "filezilla.exe"\nVALUE "ProductName", "FileZilla"\n''',encoding='utf-8',newline='\n')
    (root/'src/interface/resources/480x480/filezilla.png').write_bytes(b'legacy')

    cp=subprocess.run([sys.executable,str(patcher),str(root)],text=True,capture_output=True)
    if cp.returncode:
        raise SystemExit(f'PATCH_FIXTURE_QA=FAIL patch rc={cp.returncode}\nSTDOUT:\n{cp.stdout}\nSTDERR:\n{cp.stderr}')
    emitted_iface=(root/'src/interface/settings/optionspage_interface.cpp').read_text(encoding='utf-8')
    for needle in ('TNSUITE_BRIDGEX_BUILD12_HF8_RESTART_CTA', 'SetYesNoLabels(_("Restart now"), _("Later"))', 'oldLanguage', 'newLanguage', 'oldTheme', 'newTheme'):
        if needle not in emitted_iface:
            raise SystemExit(f'PATCH_FIXTURE_QA=FAIL Hotfix8 restart CTA missing: {needle}')

    emitted_ui=(root/'src/interface/FileZilla.cpp').read_text(encoding='utf-8')
    for needle in ('TNSUITE_BRIDGEX_BUILD12_HF16_RESTART_HANDOFF', 'TNSUITE_BRIDGEX_BUILD12_HF16_WAIT_PARENT_BEFORE_OPTIONS', 'BridgeXWaitForRestartParentIfRequested', '::OpenProcess(SYNCHRONIZE', '::WaitForSingleObject(parent, kBridgeXRestartParentWaitMs)', 'waitResult == WAIT_OBJECT_0'):
        if needle not in emitted_ui:
            raise SystemExit(f'PATCH_FIXTURE_QA=FAIL Hotfix16 restart wait missing: {needle}')
    if emitted_ui.index('TNSUITE_BRIDGEX_BUILD12_HF16_WAIT_PARENT_BEFORE_OPTIONS') > emitted_ui.index('options_ = std::make_unique<COptions>();'):
        raise SystemExit('PATCH_FIXTURE_QA=FAIL Hotfix16 child can construct COptions before parent shutdown completes')
    for needle in ('TNSUITE_BRIDGEX_BUILD12_HF16_RESTART_PERSISTENCE_HANDOFF', 'wxSetEnv(L"TNSUITE_BRIDGEX_RESTART_PARENT_PID"', 'wxExecute(executable, wxEXEC_ASYNC)', 'wxUnsetEnv(L"TNSUITE_BRIDGEX_RESTART_PARENT_PID")'):
        if needle not in emitted_iface:
            raise SystemExit(f'PATCH_FIXTURE_QA=FAIL Hotfix16 parent restart handoff missing: {needle}')
    handoff=emitted_iface.index('TNSUITE_BRIDGEX_BUILD12_HF16_RESTART_PERSISTENCE_HANDOFF')
    setenv=emitted_iface.index('wxSetEnv(L"TNSUITE_BRIDGEX_RESTART_PARENT_PID"', handoff)
    execute=emitted_iface.index('wxExecute(executable, wxEXEC_ASYNC)', handoff)
    unsetenv=emitted_iface.index('wxUnsetEnv(L"TNSUITE_BRIDGEX_RESTART_PARENT_PID")', handoff)
    close=emitted_iface.index('top->Close();', handoff)
    if not (setenv < execute < unsetenv < close):
        raise SystemExit('PATCH_FIXTURE_QA=FAIL Hotfix16 restart handoff ordering is invalid')
    if not (emitted_iface.index('m_pOptions->set(OPTION_LANGUAGE, newLanguage);') < handoff and emitted_iface.index('m_pOptions->set(OPTION_BRIDGEX_THEME, newTheme);') < handoff):
        raise SystemExit('PATCH_FIXTURE_QA=FAIL Hotfix16 restart occurs before language/theme option assignment')
    if 'if (wxExecute(executable, wxEXEC_ASYNC) != 0)' in emitted_iface:
        raise SystemExit('PATCH_FIXTURE_QA=FAIL Hotfix15 immediate child-then-close race remains')

    emitted_main=(root/'src/interface/Mainfrm.cpp').read_text(encoding='utf-8')
    if 'needs to be restarted for the language change to take effect' in emitted_main:
        raise SystemExit('PATCH_FIXTURE_QA=FAIL upstream language-only restart popup remains')
    if 'BridgeX Hotfix10: restart notification handled in Interface Settings' not in emitted_main:
        raise SystemExit('PATCH_FIXTURE_QA=FAIL Hotfix10 Mainfrm restart-owner marker missing')
    if 'wxMsg :: Message(' in emitted_main:
        raise SystemExit('PATCH_FIXTURE_QA=FAIL whitespace-qualified upstream restart helper remains')
    if 'if (language_changed)\n        (void)0;' not in emitted_main:
        raise SystemExit('PATCH_FIXTURE_QA=FAIL unbraced-if statement shape was not preserved')
    emitted_status=(root/'src/interface/statusbar.cpp').read_text(encoding='utf-8')
    if 'TNSUITE_BRIDGEX_BUILD12_HF11_SAFE_BITMAP_BUNDLE' not in emitted_status:
        raise SystemExit('PATCH_FIXTURE_QA=FAIL Hotfix11 safe-bitmap helper missing')
    if 'm_security->SetBitmap(BridgeXSafeStaticBitmap(bundle));' not in emitted_status:
        raise SystemExit('PATCH_FIXTURE_QA=FAIL Hotfix11 SetBitmap argument guard missing')
    if '#include "filezilla.h"\n#include <wx/bitmap.h>\n#include <wx/bmpbndl.h>\n' not in emitted_status:
        raise SystemExit('PATCH_FIXTURE_QA=FAIL Hotfix11 direct bitmap headers are not after first/PCH include')
    if 'wxNullBitmap' in emitted_status:
        raise SystemExit('PATCH_FIXTURE_QA=FAIL disproven wxNullBitmap constructor model returned')
    emitted_assoc=(root/'src/interface/settings/optionspage_edit_associations.cpp').read_text(encoding='utf-8')
    repaired_read='RepairStaleStoreNotepadAssociations(assocs_->GetValue())'
    if 'TNSUITE_BRIDGEX_BUILD12_HF12_STORE_NOTEPAD_VALUE_REPAIR' not in emitted_assoc:
        raise SystemExit('PATCH_FIXTURE_QA=FAIL Hotfix12 Store Notepad helper marker missing')
    if 'TNSUITE_BRIDGEX_BUILD12_HF13_ASSOC_CONTROL_DISCOVERY' not in patcher.read_text(encoding='utf-8'):
        raise SystemExit('PATCH_FIXTURE_QA=FAIL Hotfix13 control discovery marker missing')
    if 'TNSUITE_BRIDGEX_BUILD12_HF15_NATIVE_ASSOC_RECEIVER_DISCOVERY' not in patcher.read_text(encoding='utf-8'):
        raise SystemExit('PATCH_FIXTURE_QA=FAIL Hotfix15 native receiver discovery marker missing')
    if 'TNSUITE_BRIDGEX_BUILD12_HF13_VALIDATE_REPAIRED_ASSOCIATIONS' not in emitted_assoc or 'TNSUITE_BRIDGEX_BUILD12_HF13_PERSIST_REPAIRED_ASSOCIATIONS' not in emitted_assoc:
        raise SystemExit('PATCH_FIXTURE_QA=FAIL Hotfix13 repair is not present in Validate and SavePage paths')
    if repaired_read not in emitted_assoc:
        raise SystemExit('PATCH_FIXTURE_QA=FAIL Hotfix15 native assocs_ load value is not repaired')
    if emitted_assoc.count('RepairStaleStoreNotepadAssociations(') < 4:
        raise SystemExit('PATCH_FIXTURE_QA=FAIL Hotfix15 repair helper is not invoked across native Load/Validate/Save paths')
    if 'm_pOptions->set(OPTION_EDIT_CUSTOMASSOCIATIONS, assocs_->GetValue().ToStdWstring());' not in emitted_assoc:
        raise SystemExit('PATCH_FIXTURE_QA=FAIL upstream native m_pOptions persistence was not retained')
    if 'ID_EDIT_ASSOCIATIONS' in emitted_assoc:
        raise SystemExit('PATCH_FIXTURE_QA=FAIL stale Hotfix12 hard-coded ID_EDIT_ASSOCIATIONS leaked into emitted source')
    if 'auto* editor = wxDynamicCast' in emitted_assoc:
        raise SystemExit('PATCH_FIXTURE_QA=FAIL obsolete FindWindow/text-control repair leaked into emitted source')
    emitted_dialogex=(root/'src/interface/dialogex.cpp').read_text(encoding='utf-8')
    if 'TNSUITE_BRIDGEX_BUILD12_HF5_STATICBOX_STRUCTURAL_MATCH' not in emitted_dialogex:
        raise SystemExit('PATCH_FIXTURE_QA=FAIL Hotfix5 structural static-box marker missing from emitted dialogex.cpp')
    if 'TNSUITE_BRIDGEX_BUILD12_HF6_STATICBOX_TARGET' not in emitted_dialogex:
        raise SystemExit('PATCH_FIXTURE_QA=FAIL Hotfix6 static-box target marker missing from emitted dialogex.cpp')
    if 'TNSUITE_BRIDGEX_BUILD12_HF7_STATICBOX_COMPLETE_TYPE' not in emitted_dialogex:
        raise SystemExit('PATCH_FIXTURE_QA=FAIL Hotfix7 complete-type marker missing from emitted dialogex.cpp')
    if '#include <wx/statbox.h>' not in emitted_dialogex:
        raise SystemExit('PATCH_FIXTURE_QA=FAIL Hotfix7 did not emit explicit wx/statbox.h')
    if '#include "dialogex.h"\n#include <wx/statbox.h>\n' not in emitted_dialogex:
        raise SystemExit('PATCH_FIXTURE_QA=FAIL Hotfix7 statbox header is not a direct top-level dependency')
    emitted_filelist=(root/'src/interface/filelistctrl.cpp').read_text(encoding='utf-8')
    if not emitted_filelist.startswith('#include "filezilla.h"\n#include <wx/settings.h>\n'):
        raise SystemExit('PATCH_FIXTURE_QA=FAIL Hotfix7 filelist direct header broke first-include/PCH ordering')
    good = 'boxSizer->GetStaticBox()->SetForegroundColour(wxSystemSettings::GetColour(wxSYS_COLOUR_WINDOWTEXT));'
    bad = 'boxSizer->SetForegroundColour(wxSystemSettings::GetColour(wxSYS_COLOUR_WINDOWTEXT));'
    if good not in emitted_dialogex:
        raise SystemExit('PATCH_FIXTURE_QA=FAIL emitted dialogex.cpp does not colour the owned wxStaticBox')
    if bad in emitted_dialogex:
        raise SystemExit('PATCH_FIXTURE_QA=FAIL emitted dialogex.cpp still calls SetForegroundColour on wxStaticBoxSizer')
    cp=subprocess.run([sys.executable,str(compat),str(root)],text=True,capture_output=True)
    if cp.returncode or 'SOURCE_COMPAT_QA=PASS' not in cp.stdout:
        raise SystemExit(f'PATCH_FIXTURE_QA=FAIL compat rc={cp.returncode}\nSTDOUT:\n{cp.stdout}\nSTDERR:\n{cp.stderr}')
print('PATCH_FIXTURE_QA=PASS')
