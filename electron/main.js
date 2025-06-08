const { app, BrowserWindow } = require("electron");
const { spawn } = require("child_process");
const path = require("path");
const isDev = require("electron-is-dev");

function createWindow() {
  const win = new BrowserWindow({
    width: 1024,
    height: 768,
    webPreferences: {
      contextIsolation: true
    }
  });

  win.loadURL("http://localhost:8501");

  const exePath = isDev
    ? path.join(__dirname, "..", "dist", "labeltool.exe")
    : path.join(process.resourcesPath, "labeltool.exe");

  const child = spawn(exePath, [], {
    detached: true,
    stdio: "ignore",
    windowsHide: true
  });

  child.unref();
}

app.whenReady().then(createWindow);
