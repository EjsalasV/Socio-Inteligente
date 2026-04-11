export type LsItem = {
  codigo: string;
  nombre: string;
};

export const LS_CATALOG: LsItem[] = [
  { codigo: "140", nombre: "Efectivo y equivalentes a efectivo" },
  { codigo: "141", nombre: "Inversiones corrientes" },
  { codigo: "130.1", nombre: "Cuentas por cobrar corrientes" },
  { codigo: "130.2", nombre: "Otras cuentas por cobrar" },
  { codigo: "120", nombre: "Otros activos financieros corrientes" },
  { codigo: "110", nombre: "Inventarios" },
  { codigo: "135", nombre: "Gastos pagados por adelantado" },
  { codigo: "136", nombre: "Activos por impuestos corrientes" },
  { codigo: "35", nombre: "Cuentas por cobrar no corrientes" },
  { codigo: "1", nombre: "Propiedad planta y equipo" },
  { codigo: "10", nombre: "Activos intangibles y fondo de comercio" },
  { codigo: "11", nombre: "Activo por derecho de uso" },
  { codigo: "5", nombre: "Propiedades para inversión" },
  { codigo: "12", nombre: "Activos biológicos" },
  { codigo: "14", nombre: "Inversiones no corrientes" },
  { codigo: "15", nombre: "Activos por impuestos diferidos" },
  { codigo: "16", nombre: "Otros activos financieros no corrientes" },
  { codigo: "425", nombre: "Cuentas por pagar" },
  { codigo: "300.1", nombre: "Préstamos corrientes" },
  { codigo: "300.2", nombre: "Préstamos no corrientes" },
  { codigo: "324", nombre: "Pasivos por impuestos corrientes" },
  { codigo: "410", nombre: "Obligaciones por beneficios a empleados" },
  { codigo: "420", nombre: "Provisiones" },
  { codigo: "200", nombre: "Patrimonio" },
  { codigo: "1500", nombre: "Ingresos operativos" },
  { codigo: "1600", nombre: "Gastos administrativos" },
  { codigo: "1700", nombre: "Gastos de ventas" },
  { codigo: "1601", nombre: "Gastos financieros" },
  { codigo: "1800", nombre: "Otros gastos" },
  { codigo: "1900", nombre: "Impuesto a la renta" },
];

export function normalizeLsCode(raw: string): string {
  const code = raw.trim();
  if (!code) return "";
  return code.includes(".") ? code.split(".")[0] : code;
}

export function getLsName(code: string): string {
  const clean = code.trim();
  if (!clean) return `Area ${code}`;

  const exact = LS_CATALOG.find((x) => x.codigo === clean);
  if (exact) return exact.nombre;

  const normalized = normalizeLsCode(clean);
  const found = LS_CATALOG.find((x) => normalizeLsCode(x.codigo) === normalized);
  return found?.nombre ?? `Area ${normalized || clean}`;
}

export function getLsShortName(code: string): string {
  const raw = getLsName(code);
  const lower = raw.toLowerCase();

  if (lower.includes("efectivo")) return "Efectivo";
  if (lower.includes("cuentas por cobrar")) return "Cuentas por cobrar";
  if (lower.includes("inventarios")) return "Inventarios";
  if (lower.includes("inversiones")) return "Inversiones";
  if (lower.includes("propiedad planta")) return "Propiedad planta y equipo";
  if (lower.includes("intangibles")) return "Intangibles";
  if (lower.includes("cuentas por pagar")) return "Cuentas por pagar";
  if (lower.includes("patrimonio")) return "Patrimonio";
  if (lower.includes("ingresos")) return "Ingresos";
  if (lower.includes("gastos")) return "Gastos";

  return raw;
}

export function getLsOptions(limit?: number): LsItem[] {
  if (typeof limit === "number" && limit > 0) {
    return LS_CATALOG.slice(0, limit);
  }
  return LS_CATALOG;
}
