# Seguridad del repositorio — CatedralX

Fecha de revisión: 2026-11-11  
Repositorio: Chalamandra-Magistral-deco/CatedralX  
Rama: main  
Commit inspeccionado: dd863ae9835fb1cdba2f454fb6479766a84ded41

## Resultado ejecutivo

**Estado: revisión parcial; no equivale a certificación de ausencia de secretos.**

El árbol de main contiene 216 entradas. `.gitignore` excluye `.env`, `.env.*` (salvo `.env.example`), `*.pem` y `*.key`. `.dockerignore` excluye entornos, directorios secrets/, certificados, claves, bases SQLite/DB, cachés, tests y documentación archivada del contexto Docker.

Se buscaron en el índice de código estos patrones: `BEGIN PRIVATE KEY`, `BEGIN RSA PRIVATE KEY`, `ghp_`, `github_pat_`, `AKIA`, `sk-proj-`, `xoxb-`, `password =`, `api_key =` y `secret_key =`. No hubo coincidencias directas para los patrones específicos de claves/tokens. El índice de búsqueda puede estar desfasado respecto de HEAD; los resultados negativos no prueban el árbol actual ni el historial.

## Controles observados

| Control | Evidencia | Resultado |
|---|---|---|
| Exclusión local | `.gitignore` | Presente para `.env`, `.env.*`, `*.pem`, `*.key`, logs y artefactos. |
| Ejemplo de entorno | `!.env.example` | Permitido; debe contener placeholders ficticios. |
| Contexto Docker | `.dockerignore` | Excluye secretos, certificados, claves, DB, cachés, tests y `docs/archive/`. |
| Secret Scanning nativo | API de alertas no accesible por la conexión | No verificado. |
| Historial completo | No descargable/escaneable con esta conexión | No verificado. |
| Variables de despliegue | Valores no inspeccionados | No verificado. |
| Protección de main | API de ramas reporta `protected=false` | Sin protección activa confirmada. |
| Branch protection API | Respuesta 403: recurso no accesible a la integración | No se pudo consultar/configurar desde esta conexión. |
| Repository rulesets | Respuesta 403: GitHub indica requisito de plan superior o repositorio público | No disponible con la configuración actual del repositorio privado. |

## Cierre requerido

1. Consultar alertas de Secret Scanning y Push Protection desde una sesión con permisos de seguridad.
2. Ejecutar Gitleaks u otro escáner de historial sobre todas las ramas y tags, no solo main.
3. Revisar blobs históricos y commits alcanzables sin copiar secretos al informe.
4. Si se confirma exposición, revocar/rotar primero en el proveedor; después evaluar purga histórica e impactos.
5. Activar Secret Scanning y Push Protection si el plan y permisos lo permiten.
6. Proteger main con PR obligatorio, checks requeridos, bloqueo de force-push y revisión cuando haya más de una persona disponible.
7. Mantener `.env.example` con placeholders no funcionales.
8. Activar el borrado automático de ramas tras fusionar PR, si la configuración del repositorio lo permite; las refs históricas #11, #12 y #13 siguen presentes porque esta conexión no ofrece borrado de ramas.

## Política

- No guardar secretos en issues, PRs, logs, artefactos o documentación.
- `.gitignore` no elimina secretos ya versionados.
- No reescribir el historial automáticamente: puede romper clones, firmas, releases y referencias.
- Registrar fecha, commit, herramienta, alcance, conteo y resultado; nunca el valor del secreto.

## Veredicto

La revisión estática encontró controles de exclusión adecuados y no obtuvo coincidencias directas para los patrones específicos buscados. La ausencia de secretos en el historial y el estado de Secret Scanning siguen sin demostrarse. No declarar el repositorio "sin secretos" hasta completar los pasos 1–3.
