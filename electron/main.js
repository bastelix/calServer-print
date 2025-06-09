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

  // Wait until the NiceGUI backend is available on its default port
  waitOn({ resources: ["http://localhost:8080"], timeout: 15000 }, (err) => {
    if (err) {
      console.error("NiceGUI not available:", err);
    } else {
      // Once ready load the actual application UI
      win.loadURL("http://localhost:8080");
    }
  });
}

app.whenReady().then(createWindow);
