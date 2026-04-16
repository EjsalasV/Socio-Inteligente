'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { useRouter } from 'next/navigation';
import { useAuditContext } from '@/lib/hooks/useAuditContext';

interface SearchResult {
  type: 'hallazgo' | 'area' | 'reporte' | 'norma' | 'procedimiento';
  title: string;
  id: string;
  excerpt: string;
  href: string;
  metadata: Record<string, any>;
}

function SearchPageContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { clienteId } = useAuditContext();

  const query = searchParams.get('q') || '';
  const page = parseInt(searchParams.get('page') || '1', 10);
  const tipo = searchParams.get('tipo') || '';

  const [results, setResults] = useState<SearchResult[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedType, setSelectedType] = useState<string>(tipo);

  useEffect(() => {
    if (query) {
      performSearch();
    }
  }, [query, page, selectedType]);

  async function performSearch() {
    if (!query) return;

    try {
      setIsLoading(true);
      const params = new URLSearchParams({ q: query, limit: '20' });

      if (clienteId) {
        params.append('cliente_id', clienteId);
      }

      if (selectedType) {
        params.append('filters', JSON.stringify({ tipo: selectedType }));
      }

      const res = await fetch(`/api/search?${params}`);
      const data = await res.json();

      setResults(data.data?.results || []);
      setTotal(data.data?.total || 0);
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setIsLoading(false);
    }
  }

  function handleTypeFilter(type: string) {
    setSelectedType(selectedType === type ? '' : type);
    const params = new URLSearchParams({ q: query });
    if (clienteId) {
      params.append('cliente_id', clienteId);
    }
    if (selectedType !== type && type) {
      params.append('tipo', type);
    }
    router.push(`/search?${params}`);
  }

  function navigateTo(href: string) {
    router.push(href);
  }

  const typeIcons: Record<string, string> = {
    norma: '📋',
    hallazgo: '⚠️',
    area: '📁',
    reporte: '📊',
    procedimiento: '✓',
  };

  const typeCounts = {
    norma: results.filter(r => r.type === 'norma').length,
    hallazgo: results.filter(r => r.type === 'hallazgo').length,
    area: results.filter(r => r.type === 'area').length,
    reporte: results.filter(r => r.type === 'reporte').length,
    procedimiento: results.filter(r => r.type === 'procedimiento').length,
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto p-6">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Búsqueda Global</h1>
          {query && (
            <p className="text-gray-600">
              Resultados para: <span className="font-semibold">"{query}"</span>
              {total > 0 && <span className="ml-2">({total} resultados)</span>}
            </p>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Filters Sidebar */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow p-6 sticky top-20">
              <h2 className="text-lg font-semibold mb-4 text-gray-900">Filtros</h2>

              <div className="space-y-2">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={selectedType === ''}
                    onChange={() => handleTypeFilter('')}
                    className="rounded"
                  />
                  <span className="text-sm">Todos ({total})</span>
                </label>

                {Object.entries(typeCounts).map(([type, count]) => (
                  <label key={type} className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={selectedType === type}
                      onChange={() => handleTypeFilter(type)}
                      className="rounded"
                    />
                    <span className="text-sm">
                      {typeIcons[type]} {type.charAt(0).toUpperCase() + type.slice(1)} ({count})
                    </span>
                  </label>
                ))}
              </div>
            </div>
          </div>

          {/* Results */}
          <div className="lg:col-span-3">
            {isLoading && (
              <div className="flex justify-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
              </div>
            )}

            {!isLoading && results.length === 0 && query && (
              <div className="bg-white rounded-lg shadow p-12 text-center">
                <p className="text-gray-600 mb-2">No se encontraron resultados para "{query}"</p>
                <p className="text-sm text-gray-500">Intenta con otros términos de búsqueda</p>
              </div>
            )}

            {!isLoading && results.length > 0 && (
              <div className="space-y-4">
                {results.map((result, idx) => (
                  <div
                    key={`${result.type}-${result.id}-${idx}`}
                    className="bg-white rounded-lg shadow hover:shadow-md transition-shadow cursor-pointer p-6"
                    onClick={() => navigateTo(result.href)}
                  >
                    <div className="flex items-start gap-4">
                      <div className="text-3xl">{typeIcons[result.type]}</div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-2">
                          <h3 className="text-lg font-semibold text-gray-900 truncate">
                            {result.title}
                          </h3>
                          <span className="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
                            {result.type}
                          </span>
                        </div>
                        <p className="text-gray-600 text-sm mb-3 line-clamp-2">
                          {result.excerpt}
                        </p>
                        {Object.keys(result.metadata).length > 0 && (
                          <div className="flex gap-4 text-xs text-gray-500">
                            {Object.entries(result.metadata).map(([key, value]) => (
                              <span key={key}>
                                <span className="font-medium">{key}:</span> {String(value)}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={<div className="flex justify-center py-12"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div></div>}>
      <SearchPageContent />
    </Suspense>
  );
}
