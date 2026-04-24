export type MayorMovement = {
  fecha: string;
  asiento_ref: string;
  numero_cuenta: string;
  nombre_cuenta: string;
  ls: string;
  descripcion: string;
  referencia: string;
  debe: number;
  haber: number;
  neto: number;
  monto_abs: number;
  row_hash: string;
};

export type MayorSummary = {
  total_movimientos: number;
  total_debe: number;
  total_haber: number;
  total_neto: number;
  cuentas_distintas: number;
  asientos_distintos: number;
  fecha_min: string;
  fecha_max: string;
  monto_promedio: number;
};

export type MayorSourceMeta = {
  cliente_id: string;
  source_file: string;
  source_path: string;
  source_format: string;
  signature: string;
  rows: number;
  cache: string;
};

export type MayorMovimientosParams = {
  fecha_desde?: string;
  fecha_hasta?: string;
  cuenta?: string;
  ls?: string;
  referencia?: string;
  texto?: string;
  monto_min?: number;
  monto_max?: number;
  page?: number;
  page_size?: number;
};

export type MayorMovimientosResponse = {
  items: MayorMovement[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  resumen_filtrado: MayorSummary;
  source: MayorSourceMeta;
};

export type MayorValidationAsientosDescuadrados = {
  count_asientos: number;
  count_movimientos: number;
  items: Array<{
    asiento_key: string;
    movimientos: number;
    total_debe: number;
    total_haber: number;
    total_neto: number;
    descuadre_abs: number;
  }>;
};

export type MayorValidationDuplicados = {
  grupos: number;
  movimientos: number;
  items: Array<{
    row_hash: string;
    repeticiones: number;
    asiento_ref: string;
    referencia: string;
    numero_cuenta: string;
    fecha: string;
    monto_abs: number;
  }>;
};

export type MayorValidationSimple = {
  count: number;
  items: MayorMovement[];
};

export type MayorValidationMontosAltos = {
  threshold: number;
  count: number;
  items: MayorMovement[];
};

export type MayorValidationCercaCierre = {
  fecha_cierre: string;
  dias: number;
  count: number;
  items: MayorMovement[];
};

export type MayorValidaciones = {
  generated_at: string;
  asientos_descuadrados: MayorValidationAsientosDescuadrados;
  duplicados: MayorValidationDuplicados;
  movimientos_sin_referencia: MayorValidationSimple;
  montos_altos: MayorValidationMontosAltos;
  movimientos_cerca_cierre: MayorValidationCercaCierre;
};

export type MayorValidacionesResponse = {
  validaciones: MayorValidaciones;
  source: MayorSourceMeta;
};

export type MayorResumenResponse = {
  resumen: MayorSummary;
  source: MayorSourceMeta;
};

