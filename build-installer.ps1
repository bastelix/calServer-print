# Build and sign Windows executable and ZIP installer

$cert = "cert\selfsign.pfx"
$password = "testpass"
$exe = "dist\labeltool.exe"
$timestamp = "http://timestamp.digicert.com"

# ensure pyinstaller is available and build the executable
if (-not (Get-Command pyinstaller -ErrorAction SilentlyContinue)) {
  python -m pip install pyinstaller | Out-Null
}
pyinstaller --noconfirm --onefile --name labeltool --add-data "app;app" launcher.py

# sign executable with self-signed certificate
if (Test-Path $cert -and Test-Path $exe) {
  & "C:\Program Files (x86)\Windows Kits\10\bin\x64\signtool.exe" sign `
    /f $cert /p $password /tr $timestamp /td sha256 /fd sha256 `
    $exe
}

# create portable ZIP package
if (Test-Path $exe) {
  Compress-Archive -Path $exe -DestinationPath dist\labeltool.zip -Force
}
