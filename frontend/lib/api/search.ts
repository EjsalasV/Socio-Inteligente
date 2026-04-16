/**
 * Search API client
 */

export interface SearchResult {
  type: 'hallazgo' | 'area' | 'reporte' | 'norma' | 'procedimiento';
  title: string;
  id: string;
  excerpt: string;
  href: string;
  metadata: Record<string, any>;
}

export interface SearchResponse {
  results: SearchResult[];
  total: number;
}

export interface SearchSuggestion {
  text: string;
  type: 'hallazgo' | 'area' | 'reporte' | 'norma' | 'procedimiento';
  id: string;
}

export interface SearchSuggestionsResponse {
  suggestions: SearchSuggestion[];
}

export async function search(
  query: string,
  clienteId?: string,
  filters?: Record<string, any>
): Promise<SearchResponse> {
  const params = new URLSearchParams({ q: query });

  if (clienteId) {
    params.append('cliente_id', clienteId);
  }

  if (filters) {
    params.append('filters', JSON.stringify(filters));
  }

  const res = await fetch(`/api/search?${params}`);
  if (!res.ok) {
    throw new Error(`Search failed: ${res.status}`);
  }

  const data = await res.json();
  return data.data || { results: [], total: 0 };
}

export async function getSearchSuggestions(
  query: string,
  clienteId?: string,
  limit: number = 5
): Promise<SearchSuggestionsResponse> {
  const params = new URLSearchParams({
    q: query,
    limit: String(limit),
  });

  if (clienteId) {
    params.append('cliente_id', clienteId);
  }

  const res = await fetch(`/api/search/suggestions?${params}`);
  if (!res.ok) {
    throw new Error(`Search suggestions failed: ${res.status}`);
  }

  const data = await res.json();
  return data.data || { suggestions: [] };
}
