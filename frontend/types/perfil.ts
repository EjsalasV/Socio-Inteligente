export type PerfilPayload = Record<string, unknown>;

export interface ClienteProfileData {
  cliente_id: string;
  perfil: PerfilPayload;
}

export interface PerfilFormData {
  firma_auditoria: string;
  auditor_encargado: string;
  fiscal_year: string;
  sector: string;
  nombre_legal: string;
  pais_operacion: string;
  marco_contable: string;
  norma_auditoria: string;
  riesgo_global: string;
  materialidad_preliminar: string;
  materialidad_preliminar_proyectada: string;
  materialidad_preliminar_trivial: string;
  materialidad_final_planeacion: string;
  materialidad_final_ejecucion: string;
  umbral_trivialidad_final: string;
  comentario_materialidad: string;
}
