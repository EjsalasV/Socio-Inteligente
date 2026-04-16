'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuditContext } from '@/lib/hooks/useAuditContext';

interface Suggestion {
  text: string;
  type: 'hallazgo' | 'area' | 'reporte' | 'norma' | 'procedimiento';
  id: string;
}

export default function GlobalSearch() {
  const router = useRouter();
  const { clienteId } = useAuditContext();
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Fetch suggestions
  useEffect(() => {
    if (!query || query.length < 2) {
      setSuggestions([]);
      setShowDropdown(false);
      return;
    }

    const timer = setTimeout(() => {
      fetchSuggestions(query);
    }, 300);

    return () => clearTimeout(timer);
  }, [query]);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowDropdown(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  async function fetchSuggestions(q: string) {
    try {
      setIsLoading(true);
      const params = new URLSearchParams({
        q,
        limit: '10',
      });
      if (clienteId) {
        params.append('cliente_id', clienteId);
      }

      const res = await fetch(`/api/search/suggestions?${params}`);
      const data = await res.json();
      setSuggestions(data.data?.suggestions || []);
      setShowDropdown(true);
    } catch (error) {
      console.error('Error fetching suggestions:', error);
    } finally {
      setIsLoading(false);
    }
  }

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (query.trim()) {
      const params = new URLSearchParams({ q: query });
      if (clienteId) {
        params.append('cliente_id', clienteId);
      }
      router.push(`/search?${params}`);
      setShowDropdown(false);
    }
  }

  function handleSelectSuggestion(suggestion: Suggestion) {
    setQuery(suggestion.text);
    setShowDropdown(false);

    // Navigate based on type
    const urls: Record<string, string> = {
      norma: `/biblioteca?search=${suggestion.id}`,
      hallazgo: `/dashboard/${clienteId}`,
      area: `/areas/${clienteId}/${suggestion.id}`,
      reporte: `/reportes/${clienteId}`,
      procedimiento: `/procedimientos`,
    };

    const url = urls[suggestion.type];
    if (url) {
      router.push(url);
    }
  }

  const typeIcons: Record<string, string> = {
    norma: '📋',
    hallazgo: '⚠️',
    area: '📁',
    reporte: '📊',
    procedimiento: '✓',
  };

  return (
    <div className="relative w-full max-w-md" ref={dropdownRef}>
      <form onSubmit={handleSearch} className="relative">
        <div className="relative">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Buscar normas, hallazgos, áreas..."
            className="w-full px-4 py-2 pr-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
          />
          <button
            type="submit"
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
          >
            🔍
          </button>
        </div>
      </form>

      {showDropdown && suggestions.length > 0 && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-50">
          {suggestions.map((suggestion, idx) => (
            <button
              key={`${suggestion.type}-${suggestion.id}-${idx}`}
              onClick={() => handleSelectSuggestion(suggestion)}
              className="w-full text-left px-4 py-2 hover:bg-gray-100 border-b border-gray-100 last:border-b-0 flex items-center gap-2"
            >
              <span className="text-lg">{typeIcons[suggestion.type]}</span>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-gray-900 truncate">
                  {suggestion.text}
                </div>
                <div className="text-xs text-gray-500">{suggestion.type}</div>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
