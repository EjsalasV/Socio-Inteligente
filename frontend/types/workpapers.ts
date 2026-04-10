export interface WorkpaperTask {
  id: string;
  area_code: string;
  area_name: string;
  title: string;
  nia_ref: string;
  prioridad: string;
  required: boolean;
  done: boolean;
  evidence_note: string;
}

export interface QualityGateItem {
  code: "PLAN" | "EXEC" | "REPORT" | string;
  title: string;
  status: "ok" | "blocked";
  detail: string;
}

export interface WorkpaperPlanData {
  cliente_id: string;
  tasks: WorkpaperTask[];
  gates: QualityGateItem[];
  completion_pct: number;
  tasks_page: number;
  tasks_page_size: number;
  tasks_total: number;
  tasks_total_all: number;
  tasks_has_more: boolean;
  coverage_summary: {
    total_assertions: number;
    covered_assertions: number;
    coverage_pct: number;
    missing_by_area: Record<string, string[]>;
  };
}
