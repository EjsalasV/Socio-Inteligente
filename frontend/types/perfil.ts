export type PerfilPayload = Record<string, unknown>;

export interface ClienteProfileData {
  cliente_id: string;
  perfil: PerfilPayload;
}

export interface PerfilFormData {
  firma_auditoria: string;
  auditor_encargado: string;
  fiscal_year: string;
  riesgo_global: string;
  socio_responsable: string;
  gerente_responsable: string;
  senior_responsable: string;
  semi_responsable: string;
  junior_responsable: string;
  revisor_tecnico: string;
  especialista_externo: string;
  fecha_inicio_encargo: string;
  fecha_objetivo_entrega: string;
  estado_encargo: string;
  nivel_supervision: string;
  complejidad_encargo: string;
  observaciones_operativas: string;
  materialidad_preliminar: string;
  materialidad_preliminar_proyectada: string;
  materialidad_preliminar_trivial: string;
  materialidad_final_planeacion: string;
  materialidad_final_ejecucion: string;
  umbral_trivialidad_final: string;
  materialidad_base_usada: string;
  materialidad_area_referencia: string;
  materialidad_justificacion_nia: string;
  comentario_materialidad: string;
}
