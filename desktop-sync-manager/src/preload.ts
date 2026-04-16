import { contextBridge, ipcRenderer } from 'electron';

contextBridge.exposeInMainWorld('electronAPI', {
  // File operations
  selectFile: () => ipcRenderer.invoke('select-file'),
  compressFile: (filePath: string) => ipcRenderer.invoke('compress-file', filePath),
  uploadFile: (data: any) => ipcRenderer.invoke('upload-file', data),
  downloadTemplate: (data: any) => ipcRenderer.invoke('download-template', data),
  saveFile: (data: any) => ipcRenderer.invoke('save-file', data),

  // Cache operations
  getCacheInfo: (clienteId: string) => ipcRenderer.invoke('get-cache-info', clienteId),
  clearCache: (clienteId?: string) => ipcRenderer.invoke('clear-cache', clienteId),
});

declare global {
  interface Window {
    electronAPI: {
      selectFile: () => Promise<any>;
      compressFile: (filePath: string) => Promise<any>;
      uploadFile: (data: any) => Promise<any>;
      downloadTemplate: (data: any) => Promise<any>;
      saveFile: (data: any) => Promise<any>;
      getCacheInfo: (clienteId: string) => Promise<any>;
      clearCache: (clienteId?: string) => Promise<any>;
    };
  }
}

export {};
