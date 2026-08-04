import assert from "node:assert/strict";
import test from "node:test";

import { summarizeUiError } from "../../lib/ui-errors.ts";

test("detecta sesion expirada", () => {
  const summary = summarizeUiError("Sesion expirada", "Reintenta la accion");

  assert.equal(summary.status, 401);
  assert.equal(summary.title, "Sesi\u00f3n expirada");
  assert.equal(summary.detail, "Tu sesi\u00f3n expir\u00f3. Vuelve a iniciar sesi\u00f3n para continuar.");
});

test("traduce errores HTTP frecuentes sin filtrar detalles de un error 500", () => {
  const notFound = summarizeUiError("API error 404: Conversacion no encontrada", "Revisa la referencia", "la conversaci\u00f3n");
  const conflict = summarizeUiError("API error 409: Estado en uso", "Revisa la referencia");
  const validation = summarizeUiError("API error 422: Datos invalidos", "Revisa la referencia");
  const server = summarizeUiError("API error 500: secreto-tecnico", "Revisa la referencia");

  assert.deepEqual(notFound, {
    status: 404,
    title: "Recurso no encontrado",
    detail: "No encontramos la conversaci\u00f3n.",
  });
  assert.equal(conflict.status, 409);
  assert.equal(validation.status, 422);
  assert.deepEqual(server, {
    status: 500,
    title: "Error interno del servidor",
    detail: "El servidor tuvo un problema interno. Int\u00e9ntalo de nuevo en unos minutos.",
  });
  assert.equal(server.detail.includes("secreto-tecnico"), false);
});

test("usa el mensaje del API para un codigo HTTP desconocido", () => {
  assert.deepEqual(summarizeUiError("API error 418 (Teapot): No disponible", "Reintenta la accion"), {
    status: 418,
    title: "Error 418",
    detail: "No disponible",
  });
});

test("acepta Error estandar y string sin status HTTP", () => {
  assert.deepEqual(summarizeUiError(new Error("Conexion interrumpida"), "Reintenta la accion"), {
    title: "No se pudo completar la acci\u00f3n",
    detail: "Conexion interrumpida",
  });
  assert.deepEqual(summarizeUiError("Servicio temporalmente ocupado", "Reintenta la accion"), {
    title: "No se pudo completar la acci\u00f3n",
    detail: "Servicio temporalmente ocupado",
  });
});

test("usa el fallback para valores desconocidos o errores vacios", () => {
  for (const error of [{ message: "detalle no confiable" }, 42, null, new Error("")]) {
    assert.deepEqual(summarizeUiError(error, "Reintenta la accion"), {
      title: "No se pudo completar la acci\u00f3n",
      detail: "Reintenta la accion",
    });
  }
});
