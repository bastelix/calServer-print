param()

Write-Host "Installing Python packages..."
pip install -r requirements.txt

if (Test-Path "electron\package.json") {
    Write-Host "Installing Node packages..."
    pushd electron
    npm install
    popd
}
