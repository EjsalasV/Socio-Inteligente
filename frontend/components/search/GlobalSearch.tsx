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
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  // Reset selected index when suggestions change
  useEffect(() => {
    setSelectedIndex(-1);
  }, [suggestions]);

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

  // Handle keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!showDropdown || suggestions.length === 0) {
      if (e.key === 'Escape') {
        setShowDropdown(false);
      }
      return;
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex((prev) =>
          prev < suggestions.length - 1 ? prev + 1 : prev
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex((prev) => (prev > 0 ? prev - 1 : -1));
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0) {
          handleSelectSuggestion(suggestions[selectedIndex]);
        }
        break;
      case 'Escape':
        e.preventDefault();
        setShowDropdown(false);
        break;
      default:
        break;
    }
  };

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
      <form onSubmit={handleSearch} className="relative" role="search">
        <label htmlFor="global-search" className="sr-only">
          Buscar normas, hallazgos, áreas
        </label>
        <div className="relative">
          <input
            id="global-search"
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Buscar normas, hallazgos, áreas..."
            aria-label="Buscar normas, hallazgos, áreas"
            aria-autocomplete="list"
            aria-expanded={showDropdown && suggestions.length > 0}
            aria-controls={showDropdown && suggestions.length > 0 ? 'search-results' : undefined}
            className="w-full px-4 py-2 pr-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white min-h-[44px]"
          />
          <button
            type="submit"
            aria-label="Ejecutar búsqueda"
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700 p-1"
          >
            🔍
          </button>
        </div>
      </form>

      {showDropdown && suggestions.length > 0 && (
        <div
          id="search-results"
          ref={listRef}
          className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-50"
          role="listbox"
        >
          {suggestions.map((suggestion, idx) => (
            <button
              key={`${suggestion.type}-${suggestion.id}-${idx}`}
              onClick={() => handleSelectSuggestion(suggestion)}
              onMouseEnter={() => setSelectedIndex(idx)}
              role="option"
              aria-selected={selectedIndex === idx}
              className={`w-full text-left px-4 py-2 border-b border-gray-100 last:border-b-0 flex items-center gap-2 min-h-[44px] transition-colors ${
                selectedIndex === idx
                  ? 'bg-blue-50 text-blue-900'
                  : 'hover:bg-gray-100 text-gray-900'
              }`}
            >
              <span className="text-lg" aria-hidden="true">
                {typeIcons[suggestion.type]}
              </span>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium truncate">
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
