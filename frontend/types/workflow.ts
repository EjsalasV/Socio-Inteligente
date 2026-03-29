import type { QualityGateItem } from "./workpapers";

export type WorkflowPhase = "planificacion" | "ejecucion" | "informe";

export interface WorkflowState {
  cliente_id: string;
  previous_phase: WorkflowPhase;
  current_phase: WorkflowPhase;
  changed: boolean;
  gates: QualityGateItem[];
}
