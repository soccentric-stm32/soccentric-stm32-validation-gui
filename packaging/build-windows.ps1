$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
$env:HWVAL_STUDIO_GIT_COMMIT = (git rev-parse --short HEAD 2>$null)
$env:HWVAL_STUDIO_BUILD_DATE = (Get-Date -Format "yyyy-MM-dd")
python scripts/make_icons.py
pyinstaller packaging/hwval-studio.spec --noconfirm --clean
$version = python -c "import hwval_studio; print(hwval_studio.__version__)"
if (Get-Command wix -ErrorAction SilentlyContinue) {
    wix build packaging/windows/Product.wxs -d Version=$version -o "dist/HWVAL_Studio-$version.msi"
    Write-Host "MSI written to dist/HWVAL_Studio-$version.msi"
} else {
    Write-Host "WiX not found; the one-folder build is in dist/hwval-studio"
}
