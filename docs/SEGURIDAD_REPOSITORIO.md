# Seguridad del repositorio — CatedralX

Fecha de revisión: 2026-11-11
Repositorio: Chalamandra-Magistral-deco/CatedralX
Rama: main
Commit inspeccionado: 2ec860337285b6054bbd0e2b44678c42a769f136

## Resultado ejecutivo

Estado: revisión parcial; no equivale a certificación de ausencia de secretos.

El árbol de main contiene 213 entradas. No se identificaron nombres de archivos evidentes de entorno local, claves privadas o bases de datos. .gitignore excluye .env, .env.* (salvo .env.example), *.pem y *.key. .dockerignore excluye entornos, directorios secrets/, certificados, claves y bases SQLite/DB del contexto Docker.

Se buscaron en el índice de código estos patrones: BEGIN PRIVATE KEY, BEGIN RSA PRIVATE KEY, ghp_, github_pat_, AKIA, sk-proj-, xoxb-, password =, api_key = y secret_key =. No hubo coincidencias directas para los patrones específicos de claves/tokens. Las coincidencias de términos genéricos correspondieron a documentación o validaciones.

Limitación: el índice de búsqueda devolvió archivos asociados a un commit anterior (6c931525...) en vez del HEAD inspeccionado. Por ello, los resultados negativos no prueban el árbol actual. La conexión GitHub disponible no expone las APIs de alertas de Secret Scanning ni permite descargar y escanear todo el historial Git. No se inspeccionaron valores de variables de despliegue.

## Controles observados

| Control | Evidencia | Resultado |
|---|---|---|
| Exclusión local | .gitignore | Presente para .env, .env.*, *.pem, *.key, logs y artefactos. |
| Ejemplo de entorno | !.env.example | Permitido; debe contener placeholders ficticios. |
| Contexto Docker | .dockerignore | Excluye secretos, certificados, claves, DB, caches, tests y docs/archive/. |
| Secret Scanning nativo | API de alertas no accesible | No verificado. |
| Historial completo | No descargable con esta conexión | No verificado. |
| Variables de despliegue | Valores no inspeccionados | No verificado. |
| Protección de main | branches API reportó protected=false; rulesets no accesibles | Sin protección confirmada. |

## Cierre requerido

1. Consultar alertas de Secret Scanning y Push Protection con permisos de seguridad.
2. Ejecutar Gitleaks u otro escáner de historial sobre todas las ramas y tags, no solo main.
3. Revisar blobs históricos y commits alcanzables sin copiar secretos al informe.
4. Si se confirma exposición, revocar/rotar primero en el proveedor; después evaluar purga histórica e impactos.
5. Activar Secret Scanning y Push Protection si el plan y permisos lo permiten.
6. Proteger main con PR obligatorio, checks requeridos, bloqueo de force-push y borrado, y revisión cuando haya más de una persona disponible.
7. Mantener .env.example con placeholders no funcionales.

## Política
- No guardar secretos en issues, PRs, logs, artefactos o documentación.
- .gitignore no elimina secretos ya versionados.
- No reescribir el historial automáticamente: puede romper clones, firmas, releases y referencias.
- Registrar fecha, commit, herramienta, alcance, conteo y resultado; nunca el valor del secreto.

## Veredicto
La revisión estática encontró controles de exclusión adecuados y no obtuvo coincidencias directas para los patrones específicos buscados. La ausencia de secretos en el historial y el estado de Secret Scanning siguen sin demostrarse. No declarar el repositorio "sin secretos" hasta completar los pasos 1–3.
