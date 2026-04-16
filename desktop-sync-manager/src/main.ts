import { app, BrowserWindow, ipcMain, dialog } from 'electron';
import * as path from 'path';
import * as fs from 'fs';
import { FileHandler } from './services/fileHandler';
import { CacheManager } from './services/cacheManager';

const isDev = process.env.NODE_ENV === 'development';

let mainWindow: BrowserWindow | null = null;
const fileHandler = new FileHandler();
const cacheManager = new CacheManager();

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      enableRemoteModule: false,
      nodeIntegration: false,
    },
  });

  const startUrl = isDev
    ? 'http://localhost:5173'
    : `file://${path.join(__dirname, '../renderer/index.html')}`;

  mainWindow.loadURL(startUrl);

  if (isDev) {
    mainWindow.webContents.openDevTools();
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.on('ready', () => {
  createWindow();
  cacheManager.initialize();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});

// IPC Handlers

/**
 * Open file dialog to select Excel file
 */
ipcMain.handle('select-file', async () => {
  if (!mainWindow) return null;

  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openFile'],
    filters: [
      { name: 'Excel Files', extensions: ['xlsx', 'xls'] },
      { name: 'All Files', extensions: ['*'] },
    ],
  });

  if (result.canceled) {
    return null;
  }

  const filePath = result.filePaths[0];
  if (!filePath) return null;

  try {
    const fileContent = fs.readFileSync(filePath);
    const fileName = path.basename(filePath);
    const fileHash = fileHandler.calculateHash(fileContent);

    return {
      path: filePath,
      name: fileName,
      size: fileContent.length,
      hash: fileHash,
    };
  } catch (error) {
    console.error('Error reading file:', error);
    throw error;
  }
});

/**
 * Compress file to ZIP
 */
ipcMain.handle('compress-file', async (_, filePath: string) => {
  try {
    const fileContent = fs.readFileSync(filePath);
    const fileName = path.basename(filePath);
    const compressed = await fileHandler.compressFile(fileContent, fileName);

    return {
      buffer: Array.from(compressed),
      originalSize: fileContent.length,
      compressedSize: compressed.length,
      ratio: (compressed.length / fileContent.length * 100).toFixed(1),
    };
  } catch (error) {
    console.error('Error compressing file:', error);
    throw error;
  }
});

/**
 * Upload file to server
 */
ipcMain.handle('upload-file', async (_, data: {
  clienteId: string;
  areaCode: string;
  areaName: string;
  filePath: string;
  fileHash: string;
  apiEndpoint: string;
  authToken: string;
}) => {
  try {
    const fileContent = fs.readFileSync(data.filePath);
    const fileName = path.basename(data.filePath);

    const result = await fileHandler.uploadFile({
      clienteId: data.clienteId,
      areaCode: data.areaCode,
      areaName: data.areaName,
      fileContent,
      fileName,
      fileHash: data.fileHash,
      apiEndpoint: data.apiEndpoint,
      authToken: data.authToken,
    });

    // Cache the file locally
    await cacheManager.cacheFile(
      data.clienteId,
      data.areaCode,
      data.fileHash,
      fileContent
    );

    return result;
  } catch (error) {
    console.error('Error uploading file:', error);
    throw error;
  }
});

/**
 * Download template from server
 */
ipcMain.handle('download-template', async (_, data: {
  clienteId: string;
  apiEndpoint: string;
  authToken: string;
}) => {
  try {
    const template = await fileHandler.downloadTemplate(
      data.clienteId,
      data.apiEndpoint,
      data.authToken
    );

    // Save to temporary location
    const tempDir = app.getPath('temp');
    const tempFile = path.join(tempDir, `plantilla_${data.clienteId}.xlsx`);
    fs.writeFileSync(tempFile, template);

    return {
      path: tempFile,
      name: `plantilla_${data.clienteId}.xlsx`,
      size: template.length,
    };
  } catch (error) {
    console.error('Error downloading template:', error);
    throw error;
  }
});

/**
 * Save file to disk (after download)
 */
ipcMain.handle('save-file', async (_, data: {
  buffer: number[];
  fileName: string;
}) => {
  try {
    const result = await dialog.showSaveDialog(mainWindow!, {
      defaultPath: data.fileName,
      filters: [
        { name: 'Excel Files', extensions: ['xlsx'] },
        { name: 'All Files', extensions: ['*'] },
      ],
    });

    if (result.canceled || !result.filePath) {
      return null;
    }

    const buffer = Buffer.from(data.buffer);
    fs.writeFileSync(result.filePath, buffer);

    return {
      path: result.filePath,
      size: buffer.length,
    };
  } catch (error) {
    console.error('Error saving file:', error);
    throw error;
  }
});

/**
 * Get cache info
 */
ipcMain.handle('get-cache-info', async (_, clienteId: string) => {
  try {
    return await cacheManager.getCacheInfo(clienteId);
  } catch (error) {
    console.error('Error getting cache info:', error);
    throw error;
  }
});

/**
 * Clear cache
 */
ipcMain.handle('clear-cache', async (_, clienteId?: string) => {
  try {
    await cacheManager.clearCache(clienteId);
    return { success: true };
  } catch (error) {
    console.error('Error clearing cache:', error);
    throw error;
  }
});
