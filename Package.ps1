# ==========================================
# WN-PBR Auto Build Script (PowerShell)
# Description: Clean cache before each build, single window sequential build
# Priority: Python3.14 > Python3.13, auto check nuitka
# jobs14
# Encoding: UTF-8 with BOM
# ==========================================
$ErrorActionPreference = "Continue"
$baseDir = "D:\Python Files\Catchmark"
Set-Location $baseDir

# 优先顺序：3.14 → 3.13，并且校验该Python环境已安装nuitka
$pythonPath = $null
$candidates = @(
    { & py -3.14 -c "import sys; print(sys.executable)" 2>$null },
    { & python314 -c "import sys; print(sys.executable)" 2>$null },
    { & py -3.13 -c "import sys; print(sys.executable)" 2>$null },
    { & python313 -c "import sys; print(sys.executable)" 2>$null }
)

foreach ($getter in $candidates) {
    $p = & $getter
    if (-not [string]::IsNullOrWhiteSpace($p)) {
        $p = $p.Trim()
        try {
            & $p -c "import nuitka" 2>$null
            $pythonPath = $p
            break
        } catch {}
    }
}

if (-not $pythonPath) {
    Write-Host "[ERROR] Python3.14 / Python3.13 not found, or target Python has no nuitka installed.`nRun: py -3.14 -m pip install nuitka" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Resolved Python path: $pythonPath" -ForegroundColor DarkGray

function Build-InCurrentProcess {
    param(
        [string]$Name,
        [string]$Icon,
        [string]$Output,
        [string]$Source,
        [string]$ExtraArgs = ""
    )

    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "  Building $Name" -ForegroundColor Cyan
    Write-Host "==========================================" -ForegroundColor Cyan

    $srcBase = [System.IO.Path]::GetFileNameWithoutExtension($Source)

    # Clean Nuitka cache directories
    $dirs = @('build','onefilebuild','dist',"$srcBase.build","$srcBase.onefile-build")
    foreach ($d in $dirs) {
        if (Test-Path $d) {
            Remove-Item -Recurse -Force $d -ErrorAction SilentlyContinue
            Write-Host "  Cleaned: $d" -ForegroundColor DarkGray
        }
    }
    if (Test-Path $Output) {
        Remove-Item -Force $Output -ErrorAction SilentlyContinue
        Write-Host "  Cleaned old file: $Output" -ForegroundColor DarkGray
    }

    $nuitkaCmd = @(
        "-m", "nuitka",
        "--standalone", "--onefile",
        "--jobs=14",
        "--onefile-tempdir-spec={TEMP}\Catchmark",
        "--company-name=Catchmark",
        "--product-version=2.4.0.0",
        "--windows-icon-from-ico=$Icon",
        "--remove-output",
        "-o", $Output
    )
    if ($ExtraArgs -ne "") {
        $splitArgs = $ExtraArgs.Split(" ", [System.StringSplitOptions]::RemoveEmptyEntries)
        $nuitkaCmd += $splitArgs
    }
    $nuitkaCmd += $Source

    Write-Host "  Running: $pythonPath $($nuitkaCmd -join ' ')" -ForegroundColor DarkGray
    & $pythonPath @nuitkaCmd
    $exitCode = $LASTEXITCODE

    if ($exitCode -eq 0) {
        Write-Host "  [OK] $Name" -ForegroundColor Green
        return $true
    } else {
        Write-Host "  [FAIL] Exit code: $exitCode" -ForegroundColor Red
        return $false
    }
}

# Ensure Release directory exists
if (-not (Test-Path "Release")) {
    New-Item -ItemType Directory -Path "Release" | Out-Null
}

# 1. Catchmark Viewer (GUI, tkinter)
$ok1 = Build-InCurrentProcess `
    -Name "Catchmark Viewer" `
    -Icon "Image\Catchmark_Viewer.ico" `
    -Output "Release\Catchmark Viewer.exe" `
    -Source "Program\TTESGG.py" `
    -ExtraArgs "--windows-console-mode=disable --enable-plugin=tk-inter --include-data-files=Image\Catchmark_Viewer.png=Catchmark_Viewer.png"

# 2. Catchmark Decryptor (GUI, tkinter)
$ok2 = Build-InCurrentProcess `
    -Name "Catchmark Decryptor" `
    -Icon "Image\Catchmark_Decryptor.ico" `
    -Output "Release\Catchmark Decryptor.exe" `
    -Source "Program\DDSGG.py" `
    -ExtraArgs "--windows-console-mode=disable --enable-plugin=tk-inter --include-data-files=Image\Catchmark_Decryptor.png=Catchmark_Decryptor.png"

# 3. Catchmark Benchmark (Console application)
$ok3 = Build-InCurrentProcess `
    -Name "Catchmark Benchmark" `
    -Icon "Image\Catchmark.ico" `
    -Output "Release\Catchmark.exe" `
    -Source "Program\SSNGG.py" `
    -ExtraArgs "--include-data-files=Image\Catchmark.ico=Catchmark.ico --include-data-files=Image\Catchmark.png=Catchmark.png"

# Refresh Windows icon cache
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Refreshing icon cache..." -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
ie4uinit.exe -show
Write-Host "  [OK] Icon cache refreshed" -ForegroundColor Green

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  All builds completed!" -ForegroundColor Cyan
Write-Host "=========================================="
Write-Host "  Viewer: $($ok1 ? '✅ Success' : '❌ Failed')"
Write-Host "  Decryptor: $($ok2 ? '✅ Success' : '❌ Failed')"
Write-Host "  Benchmark: $($ok3 ? '✅ Success' : '❌ Failed')"
Write-Host "  Output: $baseDir\Release" -ForegroundColor White

# 自动打开Release文件夹
Start-Process $baseDir\Release

Write-Host ""
Read-Host "Press Enter to exit"
