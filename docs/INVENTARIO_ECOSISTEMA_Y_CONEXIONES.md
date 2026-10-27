# Inventario del ecosistema y matriz de conexiones — DecoX

**Corte:** 2026-10-26  
**Alcance:** metadatos de 23 repositorios de la organización, README/manifiestos y una selección de puntos de entrada, configuración y CI. Esto es una matriz estática inicial, no una certificación de integración de extremo a extremo.

## Criterios de evidencia

- **Conexión en código:** existe una referencia/import/endpoint/config explícita en los archivos revisados; no implica que el servicio remoto esté activo.
- **Declarada:** README/contrato describe un flujo previsto; falta probar el intercambio real.
- **No evidenciada:** no apareció una referencia en los archivos revisados; no demuestra que no exista en todo el árbol.
- **Pendiente:** contenido o runtime no pudo inspeccionarse suficientemente.
- No se borra nada por nombre, antigüedad, tamaño o parecido conceptual.

## 1. Núcleo canónico

| Repo | Rol | Estado observado / siguiente control |
|---|---|---|
| `CatedralX` | Motor analítico determinista, contratos y CLI. | CI de la revisión actual: **290 pruebas aprobadas** y build/smoke de imagen CLI aprobado. La integración con worker/API sigue sin probarse de extremo a extremo. |
| `chalamandra-agent-engine` | API, TaskBus SQLite, worker, stores de candidatos/aceptación y distribución de webhooks. | Corrección P0 de scopes y consulta de runs fusionada en `aee4e114`; pruebas, Ruff, mypy y build/smoke de imagen pasaron en CI. El helper Ed25519 existe y PyNaCl está declarada, pero `acceptance_store` sigue usando HMAC-SHA256. Runtime de VM aún sin confirmar. |

**Fuentes de verdad propuestas:** CatedralX para reglas/cálculos deterministas; agent-engine para asignación/ejecución; verificador independiente para la aceptación; API para acceso/entrega; VM como sustrato, no como etapa analítica.

## 2. Portal, captación y productos

| Repo | Función/stack observados | Conexión al núcleo y deuda confirmada |
|---|---|---|
| `CHALAMANDRA-MAGISTRAL` | Portal institucional estático, build Tailwind y salida Vercel. | Formulario con Formspree más POST secundario a Cloudflare Worker de leads. El POST secundario ignora errores; el Worker no está versionado en este repo. No se demostró persistencia en agent-engine. `package.json` tiene un test placeholder que falla. Duplicados de `.gitignore` retirados en [PR #26](https://github.com/Chalamandra-Magistral-deco/CHALAMANDRA-MAGISTRAL/pull/26), fusionado; el check Vercel del preview pasó. |
| `INTERACTIVE-DECOX` | Portal comercial, catálogo, API routes de IA/contacto, checkout/verificación y webhook de Stripe. | Es la fuente canónica del catálogo usado por Sesión Descubrimiento. No se encontró conexión directa con la API canónica de agentes en los archivos revisados. Checkout debe probarse con entorno de prueba. |
| `SESION-DESCUBRIMIENTO-DECOX` | Aplicación de diagnóstico en cinco fases e informe PDF/JSON. | Documenta handoff desde INTERACTIVE-DECOX tras validación server-side de Stripe mediante `VITE_DISCOVERY_APP_URL`. Mantiene un espejo `src/data/interactiveCatalog.ts` del catálogo canónico. README dice que la URL pública aún debe configurarse/verificarse; integración es declarada, no probada de punta a punta. |
| `Tricentric-Integration` | React, Supabase Auth/Postgres/RLS y Edge Function `srap-analysis` con Gemini. | Flujo de producto propio; no se encontró referencia a CatedralX/agent API en README/manifiestos revisados. |
| `SYSTEM_DECODE_MAGIS-v12.0-FLUX` | Workspace multimodal con React/Vite, Supabase, funciones serverless Vercel y Gemini/Veo; Stripe opcional. | Arquitectura de backend propia. No se confirmó consumo de la API canónica. El documento histórico menciona como pendiente un consumidor de webhooks del modo retorno. |
| `Pirinola-` | Producto educativo de redes neuronales con React/Vite. | GTM y AdSense compartidos, sin conexión interna con el motor evidenciada. Se eliminó un segundo bootstrap GTM idéntico en [PR #2](https://github.com/Chalamandra-Magistral-deco/Pirinola-/pull/2); CI build/lint y check Vercel pasaron; cambio fusionado. |
| `Chalamandra-Magistral-Decodificadora` | Portfolio/experiencia Mandala Vivo y metodología SRAP. | No se encontró referencia al motor canónico en archivos revisados. README conserva instrucciones de clonación genéricas; actualizar por separado. |
| `Chalamandra-Triada` | React/Vite, análisis tesis–antítesis–síntesis; Entra y Gemini según README. | Producto autónomo; conexión al núcleo no evidenciada. |
| `Challamandra-Analisis-cognitivo` | React/Vite, análisis dialéctico/retórico con Gemini e historial local. | Producto autónomo; conexión al núcleo no evidenciada. |
| `chalamandra-6-sombreros` | Aplicación cognitiva con Seis Sombreros, escalera estratégica y Gemini. | Producto autónomo; no consolidar con otros productos por similitud conceptual. |
| `CHMADEX-DIAL` | Extensión Chrome con Gemini Cloud/Nano y extracción contextual. | Arquitectura de extensión propia; no se encontró endpoint canónico de agentes en README revisado. |
| `Insightify-Chalamandra` | Extensión que declara Gemini Nano local, offscreen y caché por hash. | No se encontró conexión al motor canónico. La afirmación “zero-egress” requiere verificación de tráfico y permisos antes de tratarla como garantía. |
| `Gemini-Flash-1` | Chat con imágenes; React/Vite, Express, PostgreSQL y Replit AI Integration. | Backend propio; no se encontró conexión a CatedralX/agent API. |
| `OMNI-CHALAMANDRA-decox` | Prototipo cognitivo/geometría/debate de agentes con salida visual. | `app/main.js` llama a un orquestador local; no se evidenció una conexión a agent-engine. Las URLs `repository`, `bugs` y `homepage` de `package.json` se corrigieron en [PR #1](https://github.com/Chalamandra-Magistral-deco/OMNI-CHALAMANDRA-decox/pull/1). El script `test` sigue siendo placeholder y el destino del script `start` necesita comprobarse antes de modificarlo. |
| `Or-culo-Chalamandra` | App AI Studio/React/Vite con Gemini. | Producto independiente según README/manifiesto; no se encontró conexión a CatedralX. README es plantilla genérica. |
| `CHALAMANDRA-S-BUNKER` | App AI Studio/React/Vite. | Producto independiente; conexión al núcleo no evidenciada. |
| `Blueprint-Chalamandra---SRAP-Barrio-Edition` | Demo SRAP con checkout provisional. | README confirma que `api/checkout.js` responde 501; no tratar como checkout activo ni afirmar que autoriza pagos Premium. |

## 3. Activos, laboratorios y contenido pendiente

| Repo | Papel preliminar | Decisión |
|---|---|---|
| `Bunker-magistral` | Laboratorio experimental de Qiskit/Docker y conceptos de túnel/red/finanzas en README. | No conectarlo ni limpiarlo destructivamente sin inspeccionar código, secretos, red y servicios. El repo es grande y puede contener artefactos relevantes. |
| `brand.kit` | Identidad y documentación de marca/arquitectura. | Activo documental, no runtime ni fuente de contratos técnicos. |
| `demo-repository` | Demo de GitHub con HTML/CSS y workflows. | No es componente del motor según README; confirmar uso antes de archivar. |
| `Chalamandra-all` | Repo privado presente en metadatos de GitHub. | El API de contenido devolvió NOT_FOUND al leer README y package.json. Auditoría de contenido pendiente; no inferir que esté vacío. |

## 4. Mapa de conexiones

| Origen → destino | Evidencia | Estado |
|---|---|---|
| agent-engine → CatedralX | `api/worker_loop.py` invoca el motor mediante ruta local absoluta del checkout. | En código; runtime no verificado. La ruta fija es deuda de configuración/portabilidad. |
| INTERACTIVE-DECOX → SESION-DESCUBRIMIENTO-DECOX | Handoff después de verificar Stripe, vía `VITE_DISCOVERY_APP_URL`. | Documentado; URL y flujo entero por verificar. |
| INTERACTIVE-DECOX → catálogo de Sesión | Fuente canónica más copia espejo `interactiveCatalog.ts`. | Documentado/en código; automatizar o probar sincronización. |
| Portal → Formspree | Envío primario de formulario. | Configuración visible; entrega real no probada. |
| Portal → Cloudflare leads Worker | POST secundario en JS del formulario; errores ignorados. | Endpoint presente; Worker no versionado en este repo y recibo no comprobado. |
| Tricentric → Supabase/Gemini | Edge Function, Auth y RPC de base de datos. | Arquitectura en código/documentos; no comprobada aquí mediante una petición real. |
| SystemDecode → Supabase/Vercel/Gemini | Configuración y arquitectura del producto. | Conexión de producto propia; consumidor del motor central no demostrado. |
| Resto de productos → CatedralX/agent-engine | Sin enlace claro en los archivos seleccionados. | No evidenciada; buscar endpoint, contrato, scope, trace ID y prueba real antes de afirmar integración. |
| VM → servicios activos | Directorios de proyectos presentes en la VM. | La consulta de procesos/sistema expiró; systemd, HEAD/origin locales, salud HTTP y trazas siguen sin verificar. |

## 5. Limpiezas realizadas

1. **agent-engine:** P0 de autorización fusionado como `aee4e114`; CI de pruebas/Ruff/mypy y smoke de imagen pasó. No equivale a despliegue en VM.
2. **CatedralX:** documentación duplicada y estado de contratos/producción reconciliados; se eliminó el consejo de activar modelos por defecto. PR #6 fusionado; 290 pruebas e imagen CLI aprobadas.
3. **Pirinola:** segundo bootstrap GTM idéntico retirado. PR #2 fusionado, CI/build y check Vercel aprobados.
4. **Portal:** reglas duplicadas en `.gitignore` eliminadas por PR #26; el check Vercel pasó antes de fusionar.
5. **Ed25519, productos y VM:** pendientes; no se copiaron, imprimieron ni editaron secretos reales.

## 6. Orden de cierre

1. Contrastar en cada checkout local branch, HEAD, origin, cambios sucios y si hay archivos `.env*` rastreados, sin leer valores secretos.
2. Inspeccionar systemd, procesos, sockets, salud local y logs de la VM con acceso remoto fiable.
3. Unificar contratos de request/result/candidate/acceptance; integrar Ed25519 sin romper el contrato HMAC hasta ejecutar pruebas de migración.
4. Probar una vertical slice reactiva completa; luego retorno/webhooks; al final modo proactivo con scheduler demostrado.
5. Probar leads, pagos, catálogo y productos como flujos independientes; integrarlos al núcleo solo cuando exista una necesidad y contrato explícito.
6. Antes de cada eliminación: revisar referencias, imports, rutas, scripts, config, dependencias, referencias dinámicas y uso en build/deploy.

**Conclusión:** la deuda más importante no es añadir más agentes; es demostrar con contratos y pruebas cuándo un producto utiliza el motor, quién puede aceptar un resultado y qué evidencia queda persistida.
