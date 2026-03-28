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
  materialidad_preliminar: number;
  comentario_materialidad: string;
}
