export type KnowledgeEntity = {
  id: number;
  cliente_id: string;
  entity_type: string;
  title: string;
  content: string;
  status: string;
  source_module: string;
  source_id: string;
  source_ref: string;
  metadata: Record<string, unknown>;
  tags: string[];
  confidence: number | null;
  created_at: string;
  updated_at: string;
};

export type KnowledgeRelation = {
  id: number;
  cliente_id: string;
  relation_type: string;
  from_entity_id: number;
  to_entity_id: number;
  weight: number;
  metadata: Record<string, unknown>;
  source_module: string;
  source_id: string;
  created_at: string;
  updated_at: string;
};

export type KnowledgeEvent = {
  id: number;
  cliente_id: string;
  event_type: string;
  entity_id: number | null;
  relation_id: number | null;
  chunk_id: number | null;
  source_module: string;
  source_id: string;
  payload: Record<string, unknown>;
  created_by: string;
  created_at: string;
};

export type KnowledgeChunkMatch = {
  chunk_id: number;
  entity_id: number | null;
  text: string;
  source_module: string;
  source_id: string;
  score: number;
};

export type KnowledgeAskSource = {
  entity_id: number | null;
  entity_type: string;
  title: string;
  source_module: string;
  source_id: string;
  score: number;
  excerpt: string;
};

export type KnowledgeAskResponse = {
  query: string;
  answer: string;
  sources: KnowledgeAskSource[];
  matched_chunks: KnowledgeChunkMatch[];
};

export type KnowledgeEntitiesResponse = {
  items: KnowledgeEntity[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

export type KnowledgeGraphResponse = {
  cliente_id: string;
  nodes: Array<{
    id: number;
    entity_type: string;
    title: string;
    status: string;
    source_module: string;
    source_id: string;
    updated_at: string;
  }>;
  edges: Array<{
    id: number;
    relation_type: string;
    from_entity_id: number;
    to_entity_id: number;
    weight: number;
    source_module: string;
    source_id: string;
    updated_at: string;
  }>;
  meta: {
    total_nodes: number;
    total_edges: number;
  };
};

export type KnowledgeTimelineResponse = {
  items: KnowledgeEvent[];
  total: number;
};

