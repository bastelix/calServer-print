const { app, BrowserWindow } = require("electron");
const { spawn } = require("child_process");
const path = require("path");
const isDev = require("electron-is-dev");
const waitOn = require("wait-on");

function createWindow() {
  const win = new BrowserWindow({
    width: 1024,
    height: 768,
    webPreferences: {
      contextIsolation: true
    }
  });

  const exePath = isDev
    ? path.join(__dirname, "..", "dist", "labeltool.exe")
    : path.join(process.resourcesPath, "labeltool.exe");

  const child = spawn(exePath, [], {
    detached: true,
    stdio: "ignore",
    windowsHide: true
  });

  child.unref();

  waitOn({ resources: ["http://localhost:8501"], timeout: 15000 }, (err) => {
    if (err) {
      console.error("Streamlit not available:", err);
    } else {
      win.loadURL("http://localhost:8501");
    }
  });
}

app.whenReady().then(createWindow);
