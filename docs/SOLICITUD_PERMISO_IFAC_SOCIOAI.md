# Borrador de solicitud IFAC OPRI: SocioAI

## Tipo de solicitud

Permiso previo para uso limitado de materiales IFAC/IAASB en una herramienta de IA de apoyo profesional.

## Solicitante

- Organizacion o persona juridica: `[[CONFIRMAR]]`
- Responsable: `[[CONFIRMAR]]`
- Cargo profesional: `[[CONFIRMAR]]`
- Pais: Ecuador
- Correo: `[[CONFIRMAR]]`
- Sitio o dominio del producto: `[[CONFIRMAR]]`

## Descripcion del producto

SocioAI es un mentor de auditoria con trazabilidad para apoyar el aprendizaje y la ejecucion de auditorias de calidad. No sustituye el juicio profesional, no firma conclusiones y no es un gestor de papeles de trabajo tipo Caseware. El piloto cubre exclusivamente Ingresos y Cuentas por Cobrar.

El sistema propone preguntas, factores a considerar, evidencia faltante y candidatos de procedimientos. El auditor responsable conserva la decision y aprobacion final. Toda atribucion normativa debe mostrar fuente y localizador; si no existe soporte verificado, la cita se bloquea.

## Material solicitado

- NIA 240, incluida la NIA 240 Revisada 2025.
- NIA 315 Revisada 2019.
- NIA 330 vigente.
- NIA 500 vigente.
- Version oficial en espanol latinoamericano cuando este disponible y autorizado.

## Alcance minimo solicitado

Se solicita autorizacion para:

1. Almacenar en un repositorio privado extractos limitados y localizadores de las normas indicadas.
2. Crear un indice privado de recuperacion para responder consultas de usuarios autorizados.
3. Enviar al modelo unicamente los fragmentos necesarios para una consulta concreta.
4. Generar explicaciones educativas y orientacion profesional con citas al parrafo correspondiente.
5. Mostrar extractos breves al usuario junto con atribucion, version y enlace oficial.

No se solicita autorizacion para publicar o distribuir las normas completas, entrenar modelos propios con el contenido, permitir descargas masivas ni presentar el producto como aprobado o respaldado por IFAC/IAASB.

## Controles implementados

- Fuentes restringidas operan en `metadata_only` hasta obtener permiso.
- No se indexa actualmente el cuerpo de las NIA.
- Las citas requieren autoridad, version, vigencia, jurisdiccion, aplicacion local, localizador, permiso y revision humana documentada.
- El sistema bloquea decisiones profesionales automaticas.
- Los cambios de version requieren nueva revision y dejan trazabilidad.
- Acceso por cliente y usuario autenticado: `[[CONFIRMAR IMPLEMENTACION Y DETALLE]]`.
- Cifrado en transito y reposo: `[[CONFIRMAR]]`.
- Retencion y eliminacion de fragmentos: `[[CONFIRMAR PLAZO]]`.
- Proveedor del modelo y politica de no entrenamiento: `[[CONFIRMAR PROVEEDOR, REGION Y TERMINOS]]`.

## Usuarios y comercializacion

- Usuarios previstos durante el piloto: `[[CONFIRMAR CANTIDAD]]`.
- Tipo de usuarios: asistentes, semis, seniors, gerentes y socios de auditoria.
- Territorio inicial: Ecuador.
- Modalidad: `[[CONFIRMAR PILOTO GRATUITO, INTERNO O COMERCIAL]]`.
- Fecha estimada de lanzamiento: `[[CONFIRMAR]]`.

## Preguntas para IFAC

1. Que modalidad de permiso corresponde al alcance descrito?
2. Se permiten embeddings privados y recuperacion de extractos si el proveedor contractual no usa los datos para entrenamiento?
3. Que limites de extension y visualizacion aplican a los extractos?
4. El permiso puede cubrir la traduccion oficial existente en espanol latinoamericano?
5. Que avisos de copyright, marcas, atribucion y descargo deben mostrarse?
6. Que registros de uso, seguridad y eliminacion exige IFAC?

## Canal

Presentar mediante https://apps.ifac.org/opri/ o solicitar aclaracion a `Permissions@ifac.org`.
