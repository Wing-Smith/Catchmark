; ============================================================
; WN-PBR Benchmark Suite 安装程序 (多语言版)
; 作者: Wing North Studio
; 版本: 2.4.0 (Gen2)
; ============================================================

[Setup]
AppId={{92e539b6-1e61-48ee-b533-981ed9743349}}
AppName=WN-PBR Benchmark Suite
AppVersion=2.4.0
AppVerName=WN-PBR Benchmark Suite 2.4.0
AppPublisher=Wing North Studio
DefaultDirName={autopf}\WN-PBR
DefaultGroupName=WN-PBR Benchmark Suite
UninstallDisplayName=WN-PBR Benchmark Suite
UninstallDisplayIcon={app}\Catchmark.exe
OutputDir=.
OutputBaseFilename=WN-PBR-Setup-2.4.0
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
DisableWelcomePage=no
DisableReadyPage=no
ShowLanguageDialog=yes
SetupIconFile=Assets\SetupIcon.ico
WizardSmallImageFile=Assets\WizardSmallImage.bmp
WizardImageFile=Assets\WizardImageLeft.bmp

[Languages]
Name: "zh"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"; LicenseFile: "license_zh.rtf"
Name: "en"; MessagesFile: "compiler:Default.isl"; LicenseFile: "license_en.rtf"

[CustomMessages]
; 中文
zh.TypeFull=完整安装 (含高级组件)
zh.TypeCompact=最小安装 (仅 Benchmark)
zh.TypeCustom=自定义安装
zh.CompBenchmark=Catchmark Benchmark (基础版)
zh.CompViewer=Catchmark Viewer (高级版 - 需序列号)
zh.CompDecryptor=Catchmark Decryptor (高级版 - 需序列号)
zh.TaskGroup=快捷方式选项:
zh.TaskDesktopIcon=创建桌面快捷方式
zh.TaskStartMenu=创建开始菜单快捷方式
zh.TaskPinTaskbar=尝试固定到任务栏 (部分系统可能不支持)
zh.ViewerKeyTitle=Viewer 序列号验证
zh.ViewerKeyDesc=请输入 Catchmark Viewer 的产品密钥
zh.ViewerKeyFormat=密钥格式: XXXXX-XXXXX-XXXXX-XXXXX-XXXXX
zh.ViewerKeyRequired=此组件需要有效序列号才能安装。
zh.ViewerKeyError=请输入有效的 Catchmark Viewer 序列号。%n密钥必须为 Gen2 且对应 Viewer 或全能授权。
zh.DecryptorKeyTitle=Decryptor 序列号验证
zh.DecryptorKeyDesc=请输入 Catchmark Decryptor 的产品密钥
zh.DecryptorKeyFormat=密钥格式: XXXXX-XXXXX-XXXXX-XXXXX-XXXXX
zh.DecryptorKeyRequired=此组件需要有效序列号才能安装。
zh.DecryptorKeyError=请输入有效的 Catchmark Decryptor 序列号。%n密钥必须为 Gen2 且对应 Decryptor 或全能授权。

; English
en.TypeFull=Full Installation (with advanced components)
en.TypeCompact=Compact Installation (Benchmark only)
en.TypeCustom=Custom Installation
en.CompBenchmark=Catchmark Benchmark (Base Edition)
en.CompViewer=Catchmark Viewer (Advanced - requires serial)
en.CompDecryptor=Catchmark Decryptor (Advanced - requires serial)
en.TaskGroup=Shortcut Options:
en.TaskDesktopIcon=Create desktop shortcuts
en.TaskStartMenu=Create Start Menu shortcuts
en.TaskPinTaskbar=Pin to taskbar (may not work on some systems)
en.ViewerKeyTitle=Viewer Serial Verification
en.ViewerKeyDesc=Please enter the product key for Catchmark Viewer
en.ViewerKeyFormat=Key format: XXXXX-XXXXX-XXXXX-XXXXX-XXXXX
en.ViewerKeyRequired=This component requires a valid serial key to install.
en.ViewerKeyError=Please enter a valid Catchmark Viewer serial key.%nKey must be Gen2 and valid for Viewer or All-in-One license.
en.DecryptorKeyTitle=Decryptor Serial Verification
en.DecryptorKeyDesc=Please enter the product key for Catchmark Decryptor
en.DecryptorKeyFormat=Key format: XXXXX-XXXXX-XXXXX-XXXXX-XXXXX
en.DecryptorKeyRequired=This component requires a valid serial key to install.
en.DecryptorKeyError=Please enter a valid Catchmark Decryptor serial key.%nKey must be Gen2 and valid for Decryptor or All-in-One license.

[Types]
Name: "full"; Description: "{cm:TypeFull}"
Name: "compact"; Description: "{cm:TypeCompact}"
Name: "custom"; Description: "{cm:TypeCustom}"; Flags: iscustom

[Components]
Name: "benchmark"; Description: "{cm:CompBenchmark}"; Types: full compact custom; Flags: checkablealone
Name: "viewer"; Description: "{cm:CompViewer}"; Types: full custom; Flags: checkablealone
Name: "decryptor"; Description: "{cm:CompDecryptor}"; Types: full custom; Flags: checkablealone

[Tasks]
Name: "desktopicon"; Description: "{cm:TaskDesktopIcon}"; GroupDescription: "{cm:TaskGroup}"
Name: "startmenu"; Description: "{cm:TaskStartMenu}"; GroupDescription: "{cm:TaskGroup}"
Name: "pintotaskbar"; Description: "{cm:TaskPinTaskbar}"; GroupDescription: "{cm:TaskGroup}"

[Files]
Source: "Release\Catchmark.exe"; DestDir: "{app}"; Components: benchmark
Source: "Image\Catchmark.ico"; DestDir: "{app}"; Components: benchmark
Source: "Image\Catchmark.png"; DestDir: "{app}"; Components: benchmark

Source: "Release\Catchmark Viewer.exe"; DestDir: "{app}"; Components: viewer
Source: "Image\Catchmark_Viewer.ico"; DestDir: "{app}"; Components: viewer
Source: "Image\Catchmark_Viewer.png"; DestDir: "{app}"; Components: viewer

Source: "Release\Catchmark Decryptor.exe"; DestDir: "{app}"; Components: decryptor
Source: "Image\Catchmark_Decryptor.ico"; DestDir: "{app}"; Components: decryptor
Source: "Image\Catchmark_Decryptor.png"; DestDir: "{app}"; Components: decryptor

[Icons]
Name: "{group}\Catchmark Benchmark"; Filename: "{app}\Catchmark.exe"; Components: benchmark; Tasks: startmenu
Name: "{group}\Catchmark Viewer"; Filename: "{app}\Catchmark Viewer.exe"; Components: viewer; Tasks: startmenu
Name: "{group}\Catchmark Decryptor"; Filename: "{app}\Catchmark Decryptor.exe"; Components: decryptor; Tasks: startmenu

Name: "{autodesktop}\Catchmark Benchmark"; Filename: "{app}\Catchmark.exe"; Components: benchmark; Tasks: desktopicon
Name: "{autodesktop}\Catchmark Viewer"; Filename: "{app}\Catchmark Viewer.exe"; Components: viewer; Tasks: desktopicon
Name: "{autodesktop}\Catchmark Decryptor"; Filename: "{app}\Catchmark Decryptor.exe"; Components: decryptor; Tasks: desktopicon

[Code]
const
  REG_PATH = 'Software\WN-PBR\Licenses';
  GEN_ID = '3';
  CHARSET = '23456789ABCDEFGHJKLMNPQRSTUVWXYZ';

function SetFocus(hWnd: HWND): HWND; external 'SetFocus@user32.dll stdcall';

var
  ViewerKeyPage, DecryptorKeyPage: TWizardPage;
  ViewerKeyEdits: array[0..4] of TEdit;
  DecryptorKeyEdits: array[0..4] of TEdit;
  ViewerKeyLabel, DecryptorKeyLabel: TLabel;
  ViewerKeyMasked, DecryptorKeyMasked: String;
  IsViewerLicensed, IsDecryptorLicensed: Boolean;
  InKeyEditChange: Boolean;

function CharToVal(c: Char): Integer;
begin
  case c of
    '2': Result := 0;  '3': Result := 1;  '4': Result := 2;  '5': Result := 3;
    '6': Result := 4;  '7': Result := 5;  '8': Result := 6;  '9': Result := 7;
    'A': Result := 8;  'B': Result := 9;  'C': Result := 10; 'D': Result := 11;
    'E': Result := 12; 'F': Result := 13; 'G': Result := 14; 'H': Result := 15;
    'J': Result := 16; 'K': Result := 17; 'L': Result := 18; 'M': Result := 19;
    'N': Result := 20; 'P': Result := 21; 'Q': Result := 22; 'R': Result := 23;
    'S': Result := 24; 'T': Result := 25; 'U': Result := 26; 'V': Result := 27;
    'W': Result := 28; 'X': Result := 29; 'Y': Result := 30; 'Z': Result := 31;
  else
    Result := -1;
  end;
end;

function ValToChar(v: Integer): Char;
begin
  case (v and $1F) of
    0:  Result := '2';  1:  Result := '3';  2:  Result := '4';  3:  Result := '5';
    4:  Result := '6';  5:  Result := '7';  6:  Result := '8';  7:  Result := '9';
    8:  Result := 'A';  9:  Result := 'B';  10: Result := 'C';  11: Result := 'D';
    12: Result := 'E';  13: Result := 'F';  14: Result := 'G';  15: Result := 'H';
    16: Result := 'J';  17: Result := 'K';  18: Result := 'L';  19: Result := 'M';
    20: Result := 'N';  21: Result := 'P';  22: Result := 'Q';  23: Result := 'R';
    24: Result := 'S';  25: Result := 'T';  26: Result := 'U';  27: Result := 'V';
    28: Result := 'W';  29: Result := 'X';  30: Result := 'Y';  31: Result := 'Z';
  end;
end;

function ComputeChecksum(const KeyPart: String): String;
var
  h: Cardinal;
  v, i: Integer;
begin
  h := $12345678;
  for i := 1 to Length(KeyPart) do
  begin
    v := CharToVal(KeyPart[i]);
    if v < 0 then
    begin
      Result := 'XXXXX';
      Exit;
    end;
    h := h xor (Cardinal(v) shl ((i-1) mod 27));
    h := ((h shl 3) or (h shr 29));
    h := h + Cardinal(v) * 2654435761;
    h := h xor Cardinal(v shr ((i-1) mod 3 + 1));
  end;

  Result := '';
  for i := 0 to 4 do
  begin
    Result := Result + ValToChar(Integer((h shr (i * 5)) and $1F));
  end;
end;

function ValidateKey(const Key, ExpectedType: String; var MaskedKey: String): Boolean;
var
  stripped, checksum, expectedChecksum: String;
  i: Integer;
  gen, keyType: Char;
begin
  Result := False;

  stripped := '';
  for i := 1 to Length(Key) do
  begin
    if (Key[i] <> '-') and (Key[i] <> ' ') then
      stripped := stripped + Uppercase(Key[i]);
  end;

  if Length(stripped) <> 25 then Exit;

  for i := 1 to 25 do
  begin
    if CharToVal(stripped[i]) < 0 then Exit;
  end;

  gen := stripped[1];
  keyType := stripped[2];

  if gen <> GEN_ID then Exit;

  if (keyType <> 'V') and (keyType <> 'D') and (keyType <> 'A') then Exit;

  if (ExpectedType = 'V') and (keyType <> 'V') and (keyType <> 'A') then Exit;
  if (ExpectedType = 'D') and (keyType <> 'D') and (keyType <> 'A') then Exit;

  checksum := Copy(stripped, 21, 5);
  expectedChecksum := ComputeChecksum(Copy(stripped, 1, 20));
  if checksum <> expectedChecksum then Exit;

  MaskedKey := '';
  for i := 1 to 5 do
  begin
    if i > 1 then MaskedKey := MaskedKey + '-';
    MaskedKey := MaskedKey + Copy(stripped, (i-1)*5 + 1, 1) + '****';
  end;

  Result := True;
end;

function GetFullKey(isViewer: Boolean): String;
var
  i: Integer;
begin
  Result := '';
  for i := 0 to 4 do
  begin
    if isViewer then
      Result := Result + ViewerKeyEdits[i].Text
    else
      Result := Result + DecryptorKeyEdits[i].Text;
    if i < 4 then
      Result := Result + '-';
  end;
end;

procedure KeyEditChange(Sender: TObject);
var
  Edit: TEdit;
  i, idx: Integer;
  text, stripped: String;
  isViewer: Boolean;
begin
  if InKeyEditChange then Exit;
  InKeyEditChange := True;
  try
    Edit := TEdit(Sender);

    idx := -1;
    isViewer := False;
    for i := 0 to 4 do
    begin
      if Edit = ViewerKeyEdits[i] then
      begin
        idx := i;
        isViewer := True;
        Break;
      end;
      if Edit = DecryptorKeyEdits[i] then
      begin
        idx := i;
        isViewer := False;
        Break;
      end;
    end;

    if idx = -1 then Exit;

    text := Edit.Text;
    if text <> Uppercase(text) then
    begin
      Edit.Text := Uppercase(text);
      Edit.SelStart := Length(Edit.Text);
    end;

    if (Pos('-', text) > 0) or (Length(text) > 5) then
    begin
      stripped := '';
      for i := 1 to Length(text) do
      begin
        if (text[i] <> '-') and (text[i] <> ' ') then
          stripped := stripped + text[i];
      end;

      for i := 0 to 4 do
      begin
        if isViewer then
        begin
          if i * 5 < Length(stripped) then
            ViewerKeyEdits[i].Text := Copy(stripped, i*5 + 1, 5)
          else
            ViewerKeyEdits[i].Text := '';
        end
        else
        begin
          if i * 5 < Length(stripped) then
            DecryptorKeyEdits[i].Text := Copy(stripped, i*5 + 1, 5)
          else
            DecryptorKeyEdits[i].Text := '';
        end;
      end;

      for i := 0 to 4 do
      begin
        if isViewer then
        begin
          if Length(ViewerKeyEdits[i].Text) < 5 then
          begin
            SetFocus(ViewerKeyEdits[i].Handle);
            Break;
          end
          else if i = 4 then
            SetFocus(ViewerKeyEdits[4].Handle);
        end
        else
        begin
          if Length(DecryptorKeyEdits[i].Text) < 5 then
          begin
            SetFocus(DecryptorKeyEdits[i].Handle);
            Break;
          end
          else if i = 4 then
            SetFocus(DecryptorKeyEdits[4].Handle);
        end;
      end;
    end
    else if (Length(text) = 5) and (idx < 4) then
    begin
      if isViewer then
        SetFocus(ViewerKeyEdits[idx + 1].Handle)
      else
        SetFocus(DecryptorKeyEdits[idx + 1].Handle);
    end;
  finally
    InKeyEditChange := False;
  end;
end;

procedure LoadLicenseStatus;
var
  viewerKey, decryptorKey: String;
begin
  IsViewerLicensed := RegQueryStringValue(HKLM, REG_PATH, 'Viewer', viewerKey);
  IsDecryptorLicensed := RegQueryStringValue(HKLM, REG_PATH, 'Decryptor', decryptorKey);
end;

procedure InitializeWizard;
var
  i: Integer;
  dash: TLabel;
begin
  LoadLicenseStatus;
  InKeyEditChange := False;

  ViewerKeyPage := CreateCustomPage(wpSelectComponents,
    ExpandConstant('{cm:ViewerKeyTitle}'),
    ExpandConstant('{cm:ViewerKeyDesc}'));

  ViewerKeyLabel := TLabel.Create(ViewerKeyPage);
  ViewerKeyLabel.Parent := ViewerKeyPage.Surface;
  ViewerKeyLabel.Caption := ExpandConstant('{cm:ViewerKeyFormat}') + #13#10 +
                            ExpandConstant('{cm:ViewerKeyRequired}');
  ViewerKeyLabel.Left := 0;
  ViewerKeyLabel.Top := 0;
  ViewerKeyLabel.Width := ViewerKeyPage.SurfaceWidth;
  ViewerKeyLabel.Height := 65;

  for i := 0 to 4 do
  begin
    ViewerKeyEdits[i] := TEdit.Create(ViewerKeyPage);
    ViewerKeyEdits[i].Parent := ViewerKeyPage.Surface;
    ViewerKeyEdits[i].Left := i * 95;
    ViewerKeyEdits[i].Top := 75;
    ViewerKeyEdits[i].Width := 80;
    ViewerKeyEdits[i].Height := 28;
    ViewerKeyEdits[i].OnChange := @KeyEditChange;

    if i < 4 then
    begin
      dash := TLabel.Create(ViewerKeyPage);
      dash.Parent := ViewerKeyPage.Surface;
      dash.Caption := '-';
      dash.Left := i * 95 + 82;
      dash.Top := 79;
      dash.Width := 12;
    end;
  end;

  DecryptorKeyPage := CreateCustomPage(wpSelectComponents,
    ExpandConstant('{cm:DecryptorKeyTitle}'),
    ExpandConstant('{cm:DecryptorKeyDesc}'));

  DecryptorKeyLabel := TLabel.Create(DecryptorKeyPage);
  DecryptorKeyLabel.Parent := DecryptorKeyPage.Surface;
  DecryptorKeyLabel.Caption := ExpandConstant('{cm:DecryptorKeyFormat}') + #13#10 +
                               ExpandConstant('{cm:DecryptorKeyRequired}');
  DecryptorKeyLabel.Left := 0;
  DecryptorKeyLabel.Top := 0;
  DecryptorKeyLabel.Width := DecryptorKeyPage.SurfaceWidth;
  DecryptorKeyLabel.Height := 65;

  for i := 0 to 4 do
  begin
    DecryptorKeyEdits[i] := TEdit.Create(DecryptorKeyPage);
    DecryptorKeyEdits[i].Parent := DecryptorKeyPage.Surface;
    DecryptorKeyEdits[i].Left := i * 95;
    DecryptorKeyEdits[i].Top := 75;
    DecryptorKeyEdits[i].Width := 80;
    DecryptorKeyEdits[i].Height := 28;
    DecryptorKeyEdits[i].OnChange := @KeyEditChange;

    if i < 4 then
    begin
      dash := TLabel.Create(DecryptorKeyPage);
      dash.Parent := DecryptorKeyPage.Surface;
      dash.Caption := '-';
      dash.Left := i * 95 + 82;
      dash.Top := 79;
      dash.Width := 12;
    end;
  end;
end;

function ShouldSkipPage(PageID: Integer): Boolean;
begin
  Result := False;

  if PageID = ViewerKeyPage.ID then
  begin
    if not WizardIsComponentSelected('viewer') then
      Result := True
    else if IsViewerLicensed then
      Result := True;
  end;

  if PageID = DecryptorKeyPage.ID then
  begin
    if not WizardIsComponentSelected('decryptor') then
      Result := True
    else if IsDecryptorLicensed then
      Result := True;
  end;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
  key: String;
begin
  Result := True;

  if CurPageID = ViewerKeyPage.ID then
  begin
    key := GetFullKey(True);
    if not ValidateKey(key, 'V', ViewerKeyMasked) then
    begin
      MsgBox(ExpandConstant('{cm:ViewerKeyError}'), mbError, MB_OK);
      Result := False;
    end;
  end;

  if CurPageID = DecryptorKeyPage.ID then
  begin
    key := GetFullKey(False);
    if not ValidateKey(key, 'D', DecryptorKeyMasked) then
    begin
      MsgBox(ExpandConstant('{cm:DecryptorKeyError}'), mbError, MB_OK);
      Result := False;
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
  PsCmd: String;
begin
  if CurStep = ssPostInstall then
  begin
    if WizardIsComponentSelected('viewer') and (not IsViewerLicensed) then
    begin
      RegWriteStringValue(HKLM, REG_PATH, 'Viewer', GetFullKey(True));
    end;

    if WizardIsComponentSelected('decryptor') and (not IsDecryptorLicensed) then
    begin
      RegWriteStringValue(HKLM, REG_PATH, 'Decryptor', GetFullKey(False));
    end;

    if WizardIsTaskSelected('pintotaskbar') then
    begin
      PsCmd := '-WindowStyle Hidden -Command "$shell=New-Object -ComObject Shell.Application; $folder=$shell.Namespace(''' + ExpandConstant('{app}') + '''); $item=$folder.ParseName(''Catchmark.exe''); $verb=$item.Verbs()|Where-Object{$_.Name-match''Pin to taskbar''}; if($verb){$verb.DoIt()}"';
      ShellExec('open', 'powershell.exe', PsCmd, '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    end;

    if WizardIsComponentSelected('viewer') then
    begin
      RegWriteStringValue(HKLM, 'Software\Classes\.catchmark', '', 'Catchmark.Viewer');
      RegWriteStringValue(HKLM, 'Software\Classes\Catchmark.Viewer', '', 'Catchmark Benchmark Result');
      RegWriteStringValue(HKLM, 'Software\Classes\Catchmark.Viewer\DefaultIcon', '', ExpandConstant('"{app}\Catchmark_Viewer.ico"'));
      RegWriteStringValue(HKLM, 'Software\Classes\Catchmark.Viewer\shell\open\command', '', ExpandConstant('"{app}\Catchmark Viewer.exe" "%1"'));
    end
    else if WizardIsComponentSelected('decryptor') then
    begin
      RegWriteStringValue(HKLM, 'Software\Classes\.catchmark', '', 'Catchmark.Decryptor');
      RegWriteStringValue(HKLM, 'Software\Classes\Catchmark.Decryptor', '', 'Catchmark Encrypted Result');
      RegWriteStringValue(HKLM, 'Software\Classes\Catchmark.Decryptor\DefaultIcon', '', ExpandConstant('"{app}\Catchmark_Decryptor.ico"'));
      RegWriteStringValue(HKLM, 'Software\Classes\Catchmark.Decryptor\shell\open\command', '', ExpandConstant('"{app}\Catchmark Decryptor.exe" "%1"'));
    end
    else
    begin
      RegDeleteKeyIncludingSubkeys(HKLM, 'Software\Classes\.catchmark');
      RegDeleteKeyIncludingSubkeys(HKLM, 'Software\Classes\Catchmark.Viewer');
      RegDeleteKeyIncludingSubkeys(HKLM, 'Software\Classes\Catchmark.Decryptor');
    end;
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
  begin
    RegDeleteKeyIncludingSubkeys(HKLM, 'Software\WN-PBR');
    RegDeleteKeyIncludingSubkeys(HKLM, 'Software\Classes\.catchmark');
    RegDeleteKeyIncludingSubkeys(HKLM, 'Software\Classes\Catchmark.Viewer');
    RegDeleteKeyIncludingSubkeys(HKLM, 'Software\Classes\Catchmark.Decryptor');
  end;
end;

function InitializeSetup: Boolean;
begin
  Result := True;
end;
