import assert from "node:assert/strict";
import test from "node:test";

import { answerStillNeedsConfirmation } from "../../lib/entity-profile-follow-up.ts";

test("detecta respuestas que todavía declaran una confirmación pendiente", () => {
  assert.equal(
    answerStillNeedsConfirmation("Me falta confirmar si aprueba la Contadora o la Gerente Financiera."),
    true,
  );
});

test("acepta una respuesta que identifica concretamente al responsable", () => {
  assert.equal(
    answerStillNeedsConfirmation("La Gerente Financiera revisa y realiza la aprobación final."),
    false,
  );
});
