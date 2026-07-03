const { app, BrowserWindow, Menu } = require("electron");
const path = require("path");

let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1100,
    height: 800,
    minWidth: 400,
    minHeight: 500,
    icon: path.join(__dirname, "../frontend/icon-512.png"),
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  // Loads the SAME frontend used by the website/mobile app - no duplicate code
  mainWindow.loadFile(path.join(__dirname, "../frontend/index.html"));

  // Remove default Electron menu bar for a cleaner "app" look
  Menu.setApplicationMenu(null);
}

app.whenReady().then(createWindow);

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});
