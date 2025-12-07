const { app, BrowserWindow } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let backendProcess;

const isDev = !app.isPackaged;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js') // Optional
        },
    });

    if (isDev) {
        // In dev, we might want to load the vite dev server or the built files
        // For simplicity, let's load the built files if they exist, or localhost if running
        // But here we are just wrapping the built frontend.
        mainWindow.loadFile(path.join(__dirname, '../frontend/dist/index.html'));
    } else {
        // In production, the frontend is copied to resources/app/frontend
        mainWindow.loadFile(path.join(__dirname, 'frontend/index.html'));
    }
}

function startBackend() {
    let backendExecutable = 'penplotter-backend';
    if (process.platform === 'win32') {
        backendExecutable += '.exe';
    }

    let backendPath;
    if (isDev) {
        backendPath = path.join(__dirname, '../backend/dist/penplotter-backend', backendExecutable);
    } else {
        // In production, extraResources puts it in resources/backend
        // process.resourcesPath points to the resources folder
        backendPath = path.join(process.resourcesPath, 'backend', backendExecutable);
    }

    console.log('Starting backend from:', backendPath);

    backendProcess = spawn(backendPath, [], {
        stdio: 'inherit' // Pipe output to console
    });

    backendProcess.on('error', (err) => {
        console.error('Failed to start backend:', err);
    });

    backendProcess.on('exit', (code, signal) => {
        console.log(`Backend process exited with code ${code} and signal ${signal}`);
    });
}

app.whenReady().then(() => {
    startBackend();
    // Give backend a moment to start? Or just load window and let it retry connection?
    // The frontend should handle connection retries.
    setTimeout(createWindow, 1000);

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('will-quit', () => {
    if (backendProcess) {
        console.log('Killing backend process...');
        backendProcess.kill();
    }
});
