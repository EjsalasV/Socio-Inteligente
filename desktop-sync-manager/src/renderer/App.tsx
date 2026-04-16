import React, { useState } from 'react';
import { DownloadIcon, UploadIcon, FileIcon, CheckCircleIcon, AlertCircleIcon, TrashIcon } from 'lucide-react';
import './App.css';

interface FileInfo {
  path: string;
  name: string;
  size: number;
  hash?: string;
}

interface UploadResult {
  fileId: number;
  version: number;
  parsedRows: number;
  summary: any;
}

export default function App() {
  const [step, setStep] = useState<'login' | 'dashboard' | 'download' | 'upload'>('login');
  const [clienteId, setClienteId] = useState('');
  const [apiEndpoint, setApiEndpoint] = useState('http://localhost:8000');
  const [authToken, setAuthToken] = useState('');
  const [areaCode, setAreaCode] = useState('');
  const [areaName, setAreaName] = useState('');

  const [selectedFile, setSelectedFile] = useState<FileInfo | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [cacheInfo, setCacheInfo] = useState<any>(null);

  const [uploadProgress, setUploadProgress] = useState<{
    originalSize: number;
    compressedSize: number;
    ratio: string;
  } | null>(null);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!clienteId || !authToken) {
      setMessage({ type: 'error', text: 'Completa todos los campos requeridos' });
      return;
    }
    setStep('dashboard');
    await loadCacheInfo();
  };

  const loadCacheInfo = async () => {
    try {
      const info = await window.electronAPI.getCacheInfo(clienteId);
      setCacheInfo(info);
    } catch (error) {
      console.error('Error loading cache:', error);
    }
  };

  const handleDownloadTemplate = async () => {
    try {
      setIsLoading(true);
      setMessage(null);

      const result = await window.electronAPI.downloadTemplate({
        clienteId,
        apiEndpoint,
        authToken,
      });

      // Save file
      const saved = await window.electronAPI.saveFile({
        buffer: Array.from(await readFileAsBuffer(result.path)),
        fileName: `plantilla_${clienteId}.xlsx`,
      });

      if (saved) {
        setMessage({
          type: 'success',
          text: `Plantilla descargada: ${saved.path}`,
        });
      }
    } catch (error) {
      setMessage({
        type: 'error',
        text: `Error descargando plantilla: ${error instanceof Error ? error.message : 'Error desconocido'}`,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectFile = async () => {
    try {
      setIsLoading(true);
      setSelectedFile(null);
      setUploadProgress(null);

      const file = await window.electronAPI.selectFile();
      if (file) {
        setSelectedFile(file);
        setMessage({ type: 'success', text: 'Archivo seleccionado correctamente' });
      }
    } catch (error) {
      setMessage({
        type: 'error',
        text: `Error seleccionando archivo: ${error instanceof Error ? error.message : 'Error desconocido'}`,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleUploadFile = async () => {
    if (!selectedFile || !areaCode || !areaName) {
      setMessage({
        type: 'error',
        text: 'Selecciona archivo, código y nombre del área',
      });
      return;
    }

    try {
      setIsLoading(true);

      const result = await window.electronAPI.uploadFile({
        clienteId,
        areaCode,
        areaName,
        filePath: selectedFile.path,
        fileHash: selectedFile.hash,
        apiEndpoint,
        authToken,
      });

      if (result.success) {
        setUploadProgress(result.compression);
        setMessage({
          type: 'success',
          text: `Archivo subido (v${result.data.version}) - Compresión: ${result.compression.ratio}%`,
        });
        setSelectedFile(null);
        setAreaCode('');
        setAreaName('');
        await loadCacheInfo();
      }
    } catch (error) {
      setMessage({
        type: 'error',
        text: `Error subiendo archivo: ${error instanceof Error ? error.message : 'Error desconocido'}`,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearCache = async () => {
    if (!window.confirm(`¿Limpiar caché de ${clienteId}?`)) {
      return;
    }

    try {
      setIsLoading(true);
      await window.electronAPI.clearCache(clienteId);
      setMessage({ type: 'success', text: 'Caché limpiado' });
      await loadCacheInfo();
    } catch (error) {
      setMessage({
        type: 'error',
        text: `Error limpiando caché: ${error instanceof Error ? error.message : 'Error desconocido'}`,
      });
    } finally {
      setIsLoading(false);
    }
  };

  async function readFileAsBuffer(filePath: string): Promise<Buffer> {
    return new Promise((resolve, reject) => {
      const fs = require('fs');
      fs.readFile(filePath, (err: any, data: any) => {
        if (err) reject(err);
        else resolve(data);
      });
    });
  }

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-content">
          <h1>Socio AI Sync Manager</h1>
          <p>Descarga plantillas, carga papeles de trabajo y gestiona versiones</p>
        </div>
      </header>

      <main className="container">
        {step === 'login' && (
          <div className="card login-card">
            <h2>Conectar a Socio AI</h2>
            <form onSubmit={handleLogin}>
              <div className="form-group">
                <label htmlFor="apiEndpoint">URL del Servidor</label>
                <input
                  id="apiEndpoint"
                  type="text"
                  value={apiEndpoint}
                  onChange={(e) => setApiEndpoint(e.target.value)}
                  placeholder="http://localhost:8000"
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="clienteId">ID del Cliente</label>
                <input
                  id="clienteId"
                  type="text"
                  value={clienteId}
                  onChange={(e) => setClienteId(e.target.value)}
                  placeholder="cliente-123"
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="authToken">Token de Autorización</label>
                <input
                  id="authToken"
                  type="password"
                  value={authToken}
                  onChange={(e) => setAuthToken(e.target.value)}
                  placeholder="Tu JWT token"
                  required
                />
              </div>

              <button type="submit" className="btn btn-primary" disabled={isLoading}>
                Conectar
              </button>
            </form>
          </div>
        )}

        {step === 'dashboard' && (
          <div className="dashboard">
            {/* Connection Info */}
            <div className="info-bar">
              <span>Conectado como: <strong>{clienteId}</strong></span>
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => {
                  setStep('login');
                  setClienteId('');
                  setAuthToken('');
                }}
              >
                Cambiar cliente
              </button>
            </div>

            {/* Messages */}
            {message && (
              <div className={`message message-${message.type}`}>
                {message.type === 'success' ? (
                  <CheckCircleIcon size={20} />
                ) : (
                  <AlertCircleIcon size={20} />
                )}
                <p>{message.text}</p>
              </div>
            )}

            {/* Quick Actions */}
            <div className="grid grid-2">
              <div className="card">
                <div className="card-icon download">
                  <DownloadIcon size={32} />
                </div>
                <h3>Descargar Plantilla</h3>
                <p>Obtén la plantilla Excel vacía para completar offline</p>
                <button
                  className="btn btn-primary"
                  onClick={handleDownloadTemplate}
                  disabled={isLoading}
                >
                  Descargar
                </button>
              </div>

              <div className="card">
                <div className="card-icon upload">
                  <UploadIcon size={32} />
                </div>
                <h3>Subir Archivo</h3>
                <p>Sube tu Excel completado con versionamiento automático</p>
                <button
                  className="btn btn-primary"
                  onClick={() => setStep('upload')}
                  disabled={isLoading}
                >
                  Seleccionar archivo
                </button>
              </div>
            </div>

            {/* Cache Info */}
            {cacheInfo && (
              <div className="card">
                <h3>Información de Caché Local</h3>
                <div className="cache-info">
                  <div className="stat">
                    <span className="label">Archivos en caché:</span>
                    <span className="value">{cacheInfo.fileCount}</span>
                  </div>
                  <div className="stat">
                    <span className="label">Tamaño total:</span>
                    <span className="value">{formatBytes(cacheInfo.totalSize)}</span>
                  </div>
                </div>
                {cacheInfo.areas && Object.keys(cacheInfo.areas).length > 0 && (
                  <div className="cache-areas">
                    <h4>Por área:</h4>
                    {Object.entries(cacheInfo.areas).map(([area, info]: [string, any]) => (
                      <div key={area} className="area-cache">
                        <span>{area}</span>
                        <span>{info.fileCount} archivo(s) • {formatBytes(info.size)}</span>
                      </div>
                    ))}
                  </div>
                )}
                <button
                  className="btn btn-danger btn-sm"
                  onClick={handleClearCache}
                  disabled={isLoading}
                >
                  <TrashIcon size={14} />
                  Limpiar caché
                </button>
              </div>
            )}
          </div>
        )}

        {step === 'upload' && (
          <div className="upload-view">
            <button
              className="btn btn-secondary"
              onClick={() => setStep('dashboard')}
              disabled={isLoading}
            >
              ← Volver
            </button>

            <div className="card upload-card">
              <h2>Subir Archivo Excel</h2>

              {message && (
                <div className={`message message-${message.type}`}>
                  {message.type === 'success' ? (
                    <CheckCircleIcon size={20} />
                  ) : (
                    <AlertCircleIcon size={20} />
                  )}
                  <p>{message.text}</p>
                </div>
              )}

              <div className="form-group">
                <label htmlFor="areaCode">Código del Área</label>
                <input
                  id="areaCode"
                  type="text"
                  value={areaCode}
                  onChange={(e) => setAreaCode(e.target.value)}
                  placeholder="ej. SFI-001"
                  disabled={!!selectedFile}
                />
              </div>

              <div className="form-group">
                <label htmlFor="areaName">Nombre del Área</label>
                <input
                  id="areaName"
                  type="text"
                  value={areaName}
                  onChange={(e) => setAreaName(e.target.value)}
                  placeholder="ej. Sistemas Financieros"
                  disabled={!!selectedFile}
                />
              </div>

              {!selectedFile ? (
                <div
                  className="file-selector"
                  onClick={handleSelectFile}
                  onDrop={(e) => {
                    e.preventDefault();
                    // Handle drop
                  }}
                >
                  <FileIcon size={48} />
                  <p>Haz clic para seleccionar un archivo Excel</p>
                  <span className="text-small">o arrastra y suelta aquí</span>
                </div>
              ) : (
                <div className="file-preview">
                  <div className="file-info">
                    <FileIcon size={32} />
                    <div>
                      <p className="file-name">{selectedFile.name}</p>
                      <p className="file-size">
                        {formatBytes(selectedFile.size)} • Hash: {selectedFile.hash?.substring(0, 8)}...
                      </p>
                    </div>
                  </div>
                  <button
                    className="btn btn-secondary"
                    onClick={() => setSelectedFile(null)}
                    disabled={isLoading}
                  >
                    Cambiar
                  </button>
                </div>
              )}

              {uploadProgress && (
                <div className="compression-info">
                  <h4>Compresión lograda</h4>
                  <div className="compression-stats">
                    <div className="stat">
                      <span className="label">Tamaño original:</span>
                      <span className="value">{formatBytes(uploadProgress.originalSize)}</span>
                    </div>
                    <div className="stat">
                      <span className="label">Comprimido:</span>
                      <span className="value">{formatBytes(uploadProgress.compressedSize)}</span>
                    </div>
                    <div className="stat">
                      <span className="label">Ratio:</span>
                      <span className="value">{uploadProgress.ratio}%</span>
                    </div>
                  </div>
                </div>
              )}

              <button
                className="btn btn-primary"
                onClick={handleUploadFile}
                disabled={!selectedFile || !areaCode || !areaName || isLoading}
              >
                {isLoading ? 'Subiendo...' : 'Subir archivo'}
              </button>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="footer">
        <p>Socio AI v1.0.0 • Sync Manager para Papeles de Trabajo</p>
      </footer>
    </div>
  );
}
