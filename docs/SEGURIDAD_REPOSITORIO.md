# Seguridad del repositorio — CatedralX

Fecha de revisión: 2026-11-11  
Repositorio: Chalamandra-Magistral-deco/CatedralX  
Rama: main  
Commit inspeccionado: dddf89b89fc452bbeee93d2a11c07824b844f2d7

## Resultado ejecutivo

**Estado: escaneo histórico Gitleaks aprobado; controles nativos de GitHub y valores de despliegue aún no verificados.**

El árbol de main contiene 216 entradas. `.gitignore` excluye `.env`, `.env.*` (salvo `.env.example`), `*.pem` y `*.key`. `.dockerignore` excluye entornos, directorios secrets/, certificados, claves, bases SQLite/DB, cachés, tests y documentación archivada del contexto Docker.

## Escaneo de historial

- Herramienta: Gitleaks **8.30.1**, versión fijada y checksum SHA-256 verificado en CI.
- Ejecución: [workflow #141](https://github.com/Chalamandra-Magistral-deco/CatedralX/actions/runs/42993684978), job "Scan all Git history with Gitleaks".
- Alcance: checkout con `fetch-depth: 0`, refs y tags alcanzables; **129 commits escaneados**, aproximadamente 1.82 MB.
- Resultado final: **no leaks found**.
- Revisión de falsos positivos: dos alertas históricas de regla `generic-api-key` correspondían a valores sintéticos de prueba en `tests/test_sustainability_governance.py`, línea 159, commits `a83d8e127b2ea51ba1e27b790e5347c7989c346a` y `91c219a2c7682c4ea791be094a8dc03726f46231`. Se comprobó que eran material ficticio para probar solapamiento de claves HMAC; el test actual usa bytes repetidos de baja entropía. `.gitleaksignore` excluye únicamente esas dos huellas históricas exactas.
- El escaneo cubre los commits alcanzables desde refs disponibles en el momento de la ejecución; no cubre objetos inalcanzables, refs borradas, copias externas ni secretos de proveedores.

## Controles observados

| Control | Evidencia | Resultado |
|---|---|---|
| Exclusión local | `.gitignore` | Presente para `.env`, `.env.*`, `*.pem`, `*.key`, logs y artefactos. |
| Contexto Docker | `.dockerignore` | Excluye secretos, certificados, claves, DB, cachés, tests y `docs/archive/`. |
| Gitleaks histórico | CI #141, 129 commits | Aprobado; sin hallazgos no exceptuados. |
| Falsos positivos históricos | `.gitleaksignore` | Dos huellas exactas revisadas; no hay exclusiones amplias por archivo o regla. |
| Secret Scanning / Push Protection nativo | API de alertas no accesible por la conexión | No verificado. |
| Variables de despliegue | Valores no inspeccionados | No verificado. |
| Protección de main | API de ramas reporta `protected=false` | Sin protección activa confirmada. |
| Branch protection API | Respuesta 403: recurso no accesible a la integración | No se pudo consultar/configurar desde esta conexión. |
| Repository rulesets | Respuesta 403: GitHub indica requisito de plan superior o repositorio público | No disponible con la configuración actual del repositorio privado. |

## Cierre requerido

1. Consultar Secret Scanning y Push Protection desde una sesión con permisos de seguridad y plan compatible.
2. Proteger `main` con PR obligatorio, checks requeridos, bloqueo de force-push y revisión cuando haya más de una persona disponible.
3. Revisar valores de secretos en los proveedores externos sin imprimirlos ni copiarlos al repositorio.
4. Mantener el escaneo Gitleaks de historial en CI y revisar cualquier nuevo hallazgo antes de exceptuarlo.
5. Activar el borrado automático de ramas tras fusionar PR, si la configuración del repositorio lo permite; las refs históricas #11, #12 y #13 siguen presentes porque esta conexión no ofrece borrado de ramas.

## Política

- No guardar secretos en issues, PRs, logs, artefactos o documentación.
- `.gitignore` no elimina secretos ya versionados.
- No reescribir el historial automáticamente: puede romper clones, firmas, releases y referencias.
- Registrar fecha, commit, alcance, herramienta, conteo y resultado; nunca el valor del secreto.

## Veredicto

El escaneo de historial alcanzable con Gitleaks pasó sin hallazgos no exceptuados. Las dos excepciones son huellas exactas de fixtures sintéticos revisados. **No declarar el repositorio absolutamente libre de secretos** hasta comprobar Secret Scanning nativo, valores de proveedores y refs/objetos fuera del alcance del escaneo.
