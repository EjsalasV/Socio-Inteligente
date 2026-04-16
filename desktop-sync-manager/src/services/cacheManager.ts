import * as fs from 'fs';
import * as path from 'path';
import { app } from 'electron';

export class CacheManager {
  private cacheDir: string;

  constructor() {
    this.cacheDir = path.join(app.getPath('userData'), 'cache', 'papeles-trabajo');
  }

  /**
   * Initialize cache directory
   */
  initialize(): void {
    if (!fs.existsSync(this.cacheDir)) {
      fs.mkdirSync(this.cacheDir, { recursive: true });
    }
  }

  /**
   * Get cache file path for a specific client and file
   */
  private getCacheFilePath(clienteId: string, areaCode: string, fileHash: string): string {
    const clientCacheDir = path.join(this.cacheDir, clienteId, areaCode);
    if (!fs.existsSync(clientCacheDir)) {
      fs.mkdirSync(clientCacheDir, { recursive: true });
    }
    return path.join(clientCacheDir, `${fileHash.substring(0, 8)}.xlsx`);
  }

  /**
   * Cache a file locally
   */
  async cacheFile(
    clienteId: string,
    areaCode: string,
    fileHash: string,
    fileContent: Buffer
  ): Promise<void> {
    try {
      const filePath = this.getCacheFilePath(clienteId, areaCode, fileHash);
      fs.writeFileSync(filePath, fileContent);
    } catch (error) {
      console.error('Error caching file:', error);
      // Don't throw - caching is optional
    }
  }

  /**
   * Get cached file
   */
  async getCachedFile(
    clienteId: string,
    areaCode: string,
    fileHash: string
  ): Promise<Buffer | null> {
    try {
      const filePath = this.getCacheFilePath(clienteId, areaCode, fileHash);
      if (fs.existsSync(filePath)) {
        return fs.readFileSync(filePath);
      }
      return null;
    } catch (error) {
      console.error('Error retrieving cached file:', error);
      return null;
    }
  }

  /**
   * Get cache info for a client
   */
  async getCacheInfo(clienteId: string): Promise<{
    totalSize: number;
    fileCount: number;
    areas: { [key: string]: { fileCount: number; size: number } };
  }> {
    try {
      const clientCacheDir = path.join(this.cacheDir, clienteId);
      if (!fs.existsSync(clientCacheDir)) {
        return {
          totalSize: 0,
          fileCount: 0,
          areas: {},
        };
      }

      const areas: { [key: string]: { fileCount: number; size: number } } = {};
      let totalSize = 0;
      let totalFiles = 0;

      const areaDirs = fs.readdirSync(clientCacheDir);
      for (const areaCode of areaDirs) {
        const areaPath = path.join(clientCacheDir, areaCode);
        if (!fs.statSync(areaPath).isDirectory()) continue;

        const files = fs.readdirSync(areaPath);
        let areaSize = 0;

        for (const file of files) {
          const filePath = path.join(areaPath, file);
          const stat = fs.statSync(filePath);
          areaSize += stat.size;
          totalSize += stat.size;
        }

        areas[areaCode] = {
          fileCount: files.length,
          size: areaSize,
        };

        totalFiles += files.length;
      }

      return {
        totalSize,
        fileCount: totalFiles,
        areas,
      };
    } catch (error) {
      console.error('Error getting cache info:', error);
      return {
        totalSize: 0,
        fileCount: 0,
        areas: {},
      };
    }
  }

  /**
   * Clear cache for a specific client or all cache
   */
  async clearCache(clienteId?: string): Promise<void> {
    try {
      if (clienteId) {
        const clientCacheDir = path.join(this.cacheDir, clienteId);
        if (fs.existsSync(clientCacheDir)) {
          fs.rmSync(clientCacheDir, { recursive: true, force: true });
        }
      } else {
        if (fs.existsSync(this.cacheDir)) {
          fs.rmSync(this.cacheDir, { recursive: true, force: true });
        }
        this.initialize();
      }
    } catch (error) {
      console.error('Error clearing cache:', error);
      throw error;
    }
  }

  /**
   * Get list of cached versions for an area
   */
  async getCachedVersions(clienteId: string, areaCode: string): Promise<string[]> {
    try {
      const areaPath = path.join(this.cacheDir, clienteId, areaCode);
      if (!fs.existsSync(areaPath)) {
        return [];
      }

      return fs.readdirSync(areaPath).filter(f => f.endsWith('.xlsx'));
    } catch (error) {
      console.error('Error getting cached versions:', error);
      return [];
    }
  }
}
