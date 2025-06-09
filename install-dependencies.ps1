param()

Write-Host "Installing Python packages..."
pip install -r requirements.txt

if (Test-Path "electron\package.json") {
    if (Get-Command npm -ErrorAction SilentlyContinue) {
        Write-Host "Installing Node packages..."
        pushd electron
        npm install
        popd
    }
    else {
        Write-Warning "npm not found. Skipping Node package installation."
        Write-Host "Install Node.js (https://nodejs.org/) or run `winget install OpenJS.NodeJS.LTS` and re-run this script."
    }
}
