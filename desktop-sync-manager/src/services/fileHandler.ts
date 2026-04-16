import * as crypto from 'crypto';
import * as zlib from 'zlib';
import { promisify } from 'util';
import axios from 'axios';

const gzip = promisify(zlib.gzip);
const gunzip = promisify(zlib.gunzip);

export class FileHandler {
  /**
   * Calculate SHA256 hash of file content
   */
  calculateHash(content: Buffer): string {
    return crypto.createHash('sha256').update(content).digest('hex');
  }

  /**
   * Compress file content to ZIP (gzip format)
   */
  async compressFile(content: Buffer, fileName: string): Promise<Buffer> {
    try {
      const compressed = await gzip(content);
      return compressed;
    } catch (error) {
      console.error('Error compressing file:', error);
      throw new Error(`Failed to compress file: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Decompress gzip content back to original
   */
  async decompressFile(compressed: Buffer): Promise<Buffer> {
    try {
      const decompressed = await gunzip(compressed);
      return decompressed;
    } catch (error) {
      console.error('Error decompressing file:', error);
      throw new Error(`Failed to decompress file: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Upload file to server
   */
  async uploadFile(data: {
    clienteId: string;
    areaCode: string;
    areaName: string;
    fileContent: Buffer;
    fileName: string;
    fileHash: string;
    apiEndpoint: string;
    authToken: string;
  }): Promise<any> {
    try {
      // Compress the file
      const compressed = await this.compressFile(data.fileContent, data.fileName);

      // Create form data
      const formData = new FormData();
      const blob = new Blob([compressed as BlobPart], { type: 'application/octet-stream' });
      formData.append('file', blob, data.fileName);
      formData.append('area_code', data.areaCode);
      formData.append('area_name', data.areaName);

      // Upload
      const response = await axios.post(
        `${data.apiEndpoint}/api/papeles-trabajo/${data.clienteId}/upload`,
        formData,
        {
          headers: {
            Authorization: `Bearer ${data.authToken}`,
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      return {
        success: true,
        data: response.data.data,
        compression: {
          originalSize: data.fileContent.length,
          compressedSize: compressed.length,
          ratio: (compressed.length / data.fileContent.length * 100).toFixed(1),
        },
      };
    } catch (error) {
      console.error('Error uploading file:', error);
      if (axios.isAxiosError(error)) {
        throw new Error(`Upload failed: ${error.response?.data?.message || error.message}`);
      }
      throw error;
    }
  }

  /**
   * Download template from server
   */
  async downloadTemplate(
    clienteId: string,
    apiEndpoint: string,
    authToken: string
  ): Promise<Buffer> {
    try {
      const response = await axios.get(
        `${apiEndpoint}/api/papeles-trabajo/${clienteId}/plantilla`,
        {
          headers: {
            Authorization: `Bearer ${authToken}`,
          },
          responseType: 'arraybuffer',
        }
      );

      return Buffer.from(response.data);
    } catch (error) {
      console.error('Error downloading template:', error);
      if (axios.isAxiosError(error)) {
        throw new Error(`Download failed: ${error.message}`);
      }
      throw error;
    }
  }

  /**
   * Get file info without reading full content (for large files)
   */
  getFileInfo(filePath: string, fileContent: Buffer): {
    name: string;
    size: number;
    hash: string;
  } {
    const name = filePath.split(/[\\/]/).pop() || 'unknown';
    return {
      name,
      size: fileContent.length,
      hash: this.calculateHash(fileContent),
    };
  }
}
