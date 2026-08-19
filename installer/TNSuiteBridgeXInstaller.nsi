Unicode true
RequestExecutionLevel admin
SetCompressor /SOLID lzma

!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "nsDialogs.nsh"
!include "WinVer.nsh"

!ifndef PRODUCT_VERSION
  !define PRODUCT_VERSION "0.5-Build12-Hotfix16"
!endif
!ifndef BUILD_NAME
  !define BUILD_NAME "TNSuiteBridgeX_260818_v0.5-Build12-Hotfix16-Full"
!endif
!ifndef PAYLOAD_DIR
  !error "PAYLOAD_DIR is required"
!endif
!ifndef OUTPUT_EXE
  !error "OUTPUT_EXE is required"
!endif
!ifndef BRAND_ICON
  !error "BRAND_ICON is required"
!endif

!define PRODUCT_NAME "TNSuite BridgeX"
!define PRODUCT_PUBLISHER "TNSuite"
!define PRODUCT_DIR_REGKEY "Software\TNSuite\BridgeX"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\TNSuiteBridgeX"
!define BRIDGEX_INSTALL_MARKER ".tnsuite-bridgex-install"

; Hotfix8 branded Modern UI. Keep proven NSIS installer technology while
; replacing the generic FileZilla-era presentation with BridgeX artwork.
!define MUI_ICON "${BRAND_ICON}"
!define MUI_UNICON "${BRAND_ICON}"
!define MUI_WELCOMEFINISHPAGE_BITMAP "${__FILEDIR__}\BridgeX-Setup-Sidebar.bmp"
!define MUI_UNWELCOMEFINISHPAGE_BITMAP "${__FILEDIR__}\BridgeX-Setup-Sidebar.bmp"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "${__FILEDIR__}\BridgeX-Setup-Header.bmp"
!define MUI_HEADERIMAGE_UNBITMAP "${__FILEDIR__}\BridgeX-Setup-Header.bmp"
!define MUI_ABORTWARNING
!define MUI_FINISHPAGE_RUN "$INSTDIR\bin\BridgeX.exe"
!define MUI_FINISHPAGE_RUN_TEXT "Launch TNSuite BridgeX"
!define MUI_WELCOMEPAGE_TITLE "Welcome to TNSuite BridgeX"
!define MUI_WELCOMEPAGE_TEXT "Install the secure transfer and automation client for Windows.$\r$\n$\r$\nSetup keeps your BridgeX user settings and connection profiles outside the program folder."
!define MUI_FINISHPAGE_TITLE "TNSuite BridgeX is ready"
!define MUI_FINISHPAGE_TEXT "Setup has installed TNSuite BridgeX. You can launch it now or from the Start Menu."

Name "${PRODUCT_NAME}"
Caption "${PRODUCT_NAME} ${PRODUCT_VERSION} Setup"
OutFile "${OUTPUT_EXE}"
InstallDir "$PROGRAMFILES64\TNSuite\BridgeX"
InstallDirRegKey HKLM "${PRODUCT_DIR_REGKEY}" "InstallDir"
BrandingText "TNSuite BridgeX  |  Secure Transfer & Automation"
ShowInstDetails hide
ShowUninstDetails hide
Icon "${BRAND_ICON}"

VIProductVersion "0.5.12.16"
VIAddVersionKey /LANG=1033 "ProductName" "${PRODUCT_NAME}"
VIAddVersionKey /LANG=1033 "ProductVersion" "${PRODUCT_VERSION}"
VIAddVersionKey /LANG=1033 "FileDescription" "TNSuite BridgeX Installer"
VIAddVersionKey /LANG=1033 "FileVersion" "0.5.12.16"
VIAddVersionKey /LANG=1033 "CompanyName" "${PRODUCT_PUBLISHER}"
VIAddVersionKey /LANG=1033 "LegalCopyright" "BridgeX modifications (C) 2026 TNSuite; FileZilla core remains under its upstream licenses."

Var CreateDesktopShortcut
Var DesktopCheckbox

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
Page custom DesktopShortcutPage DesktopShortcutLeave
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH
!insertmacro MUI_LANGUAGE "English"

Function DesktopShortcutPage
  nsDialogs::Create 1018
  Pop $0
  ${If} $0 == error
    Abort
  ${EndIf}
  ${NSD_CreateLabel} 0 0 100% 18u "Shortcut options"
  Pop $1
  ${NSD_CreateCheckbox} 0 30u 100% 12u "Create a desktop shortcut"
  Pop $DesktopCheckbox
  ${NSD_Check} $DesktopCheckbox
  nsDialogs::Show
FunctionEnd

Function DesktopShortcutLeave
  ${NSD_GetState} $DesktopCheckbox $CreateDesktopShortcut
FunctionEnd

Section "TNSuite BridgeX" SEC_MAIN
  SectionIn RO
  SetShellVarContext all

  ; Close only a BridgeX process whose executable path belongs to this install.
  ; This avoids killing a portable BridgeX instance elsewhere on the machine.
  IfFileExists "$INSTDIR\bin\BridgeX.exe" 0 install_copy
  SetOutPath "$TEMP"
  File /oname=BridgeX-CloseInstalled.ps1 "${__FILEDIR__}\BridgeX-CloseInstalled.ps1"
  nsExec::ExecToStack '"$SYSDIR\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "$TEMP\BridgeX-CloseInstalled.ps1" "$INSTDIR\bin\BridgeX.exe"'
  Pop $0
  Pop $1
  Delete "$TEMP\BridgeX-CloseInstalled.ps1"

install_copy:
  ; Hotfix14: cleaning the build payload alone does not remove development files
  ; left by an older installed build. Clean only a marker-verified BridgeX tree
  ; before copying the new runtime payload. User settings live outside $INSTDIR.
  IfFileExists "$INSTDIR\*.*" 0 install_copy_clean
  IfFileExists "$INSTDIR\${BRIDGEX_INSTALL_MARKER}" install_clean_verified 0
  MessageBox MB_ICONSTOP|MB_OK "An existing BridgeX program directory was found without the TNSuite install marker. Setup will not delete an unverified directory. Uninstall the old copy manually, then run Setup again."
  Abort

install_clean_verified:
  SetOutPath "$TEMP"
  RMDir /r "$INSTDIR"
  IfFileExists "$INSTDIR\*.*" 0 install_copy_clean
  MessageBox MB_ICONSTOP|MB_OK "Setup could not fully clean the previous BridgeX program directory. Close any process using BridgeX files and run Setup again. No mixed-version install was created."
  Abort

install_copy_clean:
  SetOutPath "$INSTDIR"
  File /r "${PAYLOAD_DIR}\*"

  ; Marker makes recursive uninstall deletion fail closed instead of trusting an
  ; arbitrary InstallDir value from the registry.
  FileOpen $0 "$INSTDIR\${BRIDGEX_INSTALL_MARKER}" w
  FileWrite $0 "TNSuite BridgeX ${PRODUCT_VERSION}$\r$\n"
  FileClose $0

  WriteRegStr HKLM "${PRODUCT_DIR_REGKEY}" "InstallDir" "$INSTDIR"
  WriteUninstaller "$INSTDIR\Uninstall.exe"

  CreateDirectory "$SMPROGRAMS\TNSuite BridgeX"
  CreateShortCut "$SMPROGRAMS\TNSuite BridgeX\TNSuite BridgeX.lnk" "$INSTDIR\bin\BridgeX.exe" "" "$INSTDIR\bin\BridgeX.exe" 0
  CreateShortCut "$SMPROGRAMS\TNSuite BridgeX\BridgeX CLI.lnk" "$INSTDIR\bin\BridgeX-CLI-Shell.cmd" "" "$INSTDIR\bin\BridgeX.exe" 0
  CreateShortCut "$SMPROGRAMS\TNSuite BridgeX\Uninstall TNSuite BridgeX.lnk" "$INSTDIR\Uninstall.exe"

  ${If} $CreateDesktopShortcut == ${BST_CHECKED}
    CreateShortCut "$DESKTOP\TNSuite BridgeX.lnk" "$INSTDIR\bin\BridgeX.exe" "" "$INSTDIR\bin\BridgeX.exe" 0
  ${EndIf}

  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "DisplayName" "${PRODUCT_NAME}"
  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "InstallLocation" "$INSTDIR"
  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\bin\BridgeX.exe"
  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "UninstallString" '"$INSTDIR\Uninstall.exe"'
  WriteRegStr HKLM "${PRODUCT_UNINST_KEY}" "QuietUninstallString" '"$INSTDIR\Uninstall.exe" /S'
  WriteRegDWORD HKLM "${PRODUCT_UNINST_KEY}" "NoModify" 1
  WriteRegDWORD HKLM "${PRODUCT_UNINST_KEY}" "NoRepair" 1

  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\App Paths\BridgeX.exe" "" "$INSTDIR\bin\BridgeX.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\App Paths\BridgeX.exe" "Path" "$INSTDIR\bin"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\App Paths\BridgeX-CLI.exe" "" "$INSTDIR\bin\BridgeX-CLI.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\App Paths\BridgeX-CLI.exe" "Path" "$INSTDIR\bin"
SectionEnd

Section "Uninstall"
  SetShellVarContext all

  ; Fail closed: recursive removal is allowed only for a directory created by
  ; this BridgeX installer generation.
  IfFileExists "$INSTDIR\${BRIDGEX_INSTALL_MARKER}" uninstall_marker_ok
  MessageBox MB_ICONSTOP|MB_OK "BridgeX install marker is missing. Program files were not removed to avoid deleting an unverified directory."
  Abort

uninstall_marker_ok:
  ; Close only the installed BridgeX instance. The helper is embedded into the
  ; uninstaller and extracted to %TEMP% on demand; it is not kept in Program Files.
  ; If Windows still holds a DLL, /REBOOTOK below schedules the remainder.
  SetOutPath "$TEMP"
  File /oname=BridgeX-CloseInstalled.ps1 "${__FILEDIR__}\BridgeX-CloseInstalled.ps1"
  nsExec::ExecToStack '"$SYSDIR\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "$TEMP\BridgeX-CloseInstalled.ps1" "$INSTDIR\bin\BridgeX.exe"'
  Pop $0
  Pop $1
  Delete "$TEMP\BridgeX-CloseInstalled.ps1"

uninstall_shortcuts:
  Delete "$SMPROGRAMS\TNSuite BridgeX\TNSuite BridgeX.lnk"
  Delete "$SMPROGRAMS\TNSuite BridgeX\BridgeX CLI.lnk"
  Delete "$SMPROGRAMS\TNSuite BridgeX\Uninstall TNSuite BridgeX.lnk"
  RMDir "$SMPROGRAMS\TNSuite BridgeX"
  Delete "$DESKTOP\TNSuite BridgeX.lnk"

  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\App Paths\BridgeX.exe"
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\App Paths\BridgeX-CLI.exe"
  DeleteRegKey HKLM "${PRODUCT_UNINST_KEY}"
  DeleteRegKey HKLM "${PRODUCT_DIR_REGKEY}"

  ; Preserve user settings/site profiles under %APPDATA%. Move OUTDIR out of
  ; the installation tree before recursive deletion, then remove locked files
  ; now or schedule them with /REBOOTOK.
  SetOutPath "$TEMP"
  RMDir /r /REBOOTOK "$INSTDIR"
  ; Remove TNSuite parent only when it became empty; other products are safe.
  RMDir "$PROGRAMFILES64\TNSuite"
SectionEnd
