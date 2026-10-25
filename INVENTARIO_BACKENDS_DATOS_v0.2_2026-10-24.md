# Inventario de backends y almacenamiento de datos — DecoX
**Versión:** 0.1  
**Fecha:** 2026-10-24  
**Fuente:** inspección de archivos rastreados Git (código, README y migraciones SQL).  
**Seguridad:** no se abrieron archivos .env, no se consultaron ni copiaron valores secretos, y no se ejecutaron migraciones ni cambios de base de datos.

## Regla de evidencia

Este documento distingue entre arquitectura declarada en código y servicios realmente conectados. La presencia de un cliente, migración, endpoint o variable de entorno no prueba que el servicio remoto esté configurado o que el flujo funcione en producción. Los nombres de proyecto de Supabase en config.toml son alias locales, no prueba del proyecto remoto vinculado.

## Inventario por activo

| Activo | Backend/identidad declarado en fuente | Datos y persistencia observados en código versionado | Estado y riesgo pendiente |
|---|---|---|---|
| Portal corporativo | Frontend estático en Vercel; formulario Formspree; GTM. Hay una migración SQL que endurece RLS multi-tenant para user_metrics y srap_diagnostics. | Las solicitudes del formulario se envían a Formspree, que puede almacenarlas y notificarlas según la configuración de la cuenta. En la revisión de código de frontend no se identificó un cliente Supabase que conecte esas tablas con el formulario. | PARCIAL: no está probado que la base remota tenga esas tablas ni que el sitio las use. Falta confirmar entrega del aviso Formspree y configuración de GTM/GA4. |
| Interactive DecoX | Frontend React/Vite en Vercel; endpoints serverless de Gemini, contacto/Resend, verificación de sesión Stripe y webhook Stripe. Existe carpeta de Supabase con config.toml y una Edge Function MCP. | El progreso de hacks y entradas del Grimorio se guardan en localStorage del navegador. En el código rastreado no se encontró cliente Supabase usado por src/api ni migraciones de esquema de producto; tampoco se encontraron llamadas supabase.auth o consultas .from() en la app/API. Los pagos se verifican consultando Stripe por sesión. El webhook solo envía el evento validado a un sistema downstream si PURCHASE_EVENT_WEBHOOK_URL está configurada. | PARCIAL. El directorio de Supabase no demuestra persistencia de la aplicación. Importante: si el webhook no tiene URL de fulfillment, el código puede responder received=true sin registrar/provisionar la compra en un almacén propio. No se ha leído la configuración de producción; verificar el contrato de fulfillment antes de afirmar que la compra se entrega. |
| SystemDecode / MAGIS | React/Vite en Vercel; Supabase Auth/Postgres; funciones API server-side; Stripe opcional; proveedores de IA en servidor. | Migraciones versionadas definen plans, profiles, user_plans, credit_accounts, credit_ledger, video_operations, operation_feedback y purchases. Hay RLS, restricciones/grants, funciones de consumo/reembolso de créditos y una función de acreditación de compras idempotente en el esquema. | PARCIAL con modelo de datos detallado en código. Aún se debe confirmar qué proyecto remoto está vinculado, que se aplicaron las migraciones y que políticas, variables y webhooks están configurados en producción. No ejecutar db push/migrations como parte de este inventario. |
| Tricentric / SRAP | React/Vite; Supabase Auth/Postgres; Supabase Edge Function srap-analysis con Gemini; política de cuota diaria. | Migraciones definen user_profiles, evaluations, achievements, user_achievements, tricentric_practices y ai_usage_daily. RLS está declarado; las escrituras críticas usan RPC. El handler usa withSupabase con auth de usuario y valida el user id. La configuración local declara verify_jwt=false para la función, por lo que hay que conservar la autenticación del wrapper en el contrato efectivo. | PARCIAL: código de autenticación y controles de cuota observados, no el runtime remoto. Confirmar el proyecto remoto, migraciones aplicadas, políticas RLS y funcionamiento de la función sin exponer tokens. |
| Triada | React/Vite; Microsoft Entra External ID con MSAL/OIDC; API Vercel para Gemini; Upstash Redis para contadores de limitación. | El token de sesión del navegador se almacena en sessionStorage. El backend mantiene contadores Redis persistentes por sujeto e IP; en esta revisión no se identificó una base de datos de producto para almacenar resultados/historial. | PARCIAL: README advierte que no hay tenant/credenciales para probar login real. Verificar issuer/audience/JWKS/scope y Redis en el entorno de despliegue; no afirmar que hay persistencia de sesiones de análisis. |
| Oráculo | Frontend Vite/React; API Vercel /api/oracle hacia Gemini; el código también incluye un proxy para dev/preview. | El límite de consultas por IP está en un Map en memoria del proceso: puede reiniciarse o no compartirse entre instancias. No se identificó un almacén remoto duradero en la revisión de código rastreado. | PARCIAL: la persistencia de resultados no está demostrada. Revisar límites distribuidos y configuración segura del servidor; no incluir API keys en el bundle. |
| Pirinola | Frontend Vite/React; enlace externo de Stripe configurado mediante VITE_STRIPE_PAYMENT_LINK en el código. No se encontró ruta API rastreada en la inspección. | No se identificó una base de datos, autenticación o almacén remoto de resultados en los archivos rastreados revisados. El enlace de pago por sí solo no prueba fulfillment ni registro de compra. | PARCIAL: validar si la variable pública está configurada y qué sucede después de pagar. No se puede afirmar que el producto entregue o persista una compra. Preservar los archivos locales index.html.bak e index.html.broken. |
| Blueprint SRAP Barrio Edition | Demo web estática; existe api/checkout.js. | La demo persiste estado del juego en localStorage. El README declara que el checkout responde HTTP 501 y no procesa pagos; no se identificó almacenamiento remoto de usuario en la revisión. | BLOQUEADO como checkout de venta: no vender ni considerar un pago operativo hasta implementar y probar el flujo real. |
| CHALAMANDRA-S-BUNKER | Proyecto descrito como app originada en AI Studio; dependencias indican React/Vite y servidor Express/WebSocket. | No se inspeccionó un backend persistente o base de datos remota en esta pasada. | PENDIENTE: mapear servidor, persistencia y hosting antes de integrarlo. |
| CHMADEX-DIAL | Extensión de navegador React/Vite; SDK de Gemini declarado. | No se identificó un almacén remoto ni proyecto Vercel vinculado en la revisión previa. | PENDIENTE: clasificar como extensión y comprobar si almacena preferencias o datos fuera del navegador. |
| OMNI-CHALAMANDRA | Aplicación de interfaz web en Vercel config; README declara sistema multiagente gobernado. | No se estableció un backend persistente remoto en la evidencia revisada. | PENDIENTE: verificar API/almacenamiento reales y mantenerlo separado de otros proyectos hasta conocer su contrato. |

## Hallazgos que afectan decisiones

1. **Interactive no tiene persistencia de producto demostrada por el código rastreado.** El progreso observado está en localStorage. La carpeta de Supabase y su Edge Function MCP no demuestran que el producto de usuario use una base de datos Supabase.
2. **Interactive requiere confirmar fulfillment de Stripe.** El webhook valida la firma; para eventos de checkout, envía los datos a un endpoint downstream solo si PURCHASE_EVENT_WEBHOOK_URL tiene valor. Si falta, el código devuelve recepción correcta y no muestra una persistencia/entrega propia en este handler. La variable no se leyó ni se verificó en producción.
3. **MAGIS posee el esquema comercial más explícito en los repositorios revisados:** planes, cuenta y ledger de créditos, compras y feedback/operaciones, junto con RLS y funciones server-side. Esto no equivale a confirmar migraciones aplicadas ni un pago real.
4. **Tricentric también presenta un esquema persistente claro** para perfiles, evaluaciones, logros, prácticas y cuota diaria, además de la función autenticada. El runtime remoto sigue sin validación de extremo a extremo.
5. Triada presenta autenticación OIDC y contadores de cuota Redis, pero no una base de datos de historial observada. Oráculo utiliza un contador en memoria para rate limiting y no muestra un almacén duradero en la revisión.
6. Pirinola y Blueprint no deben tratarse como sistemas de pago completos solo porque muestran un enlace o endpoint. Blueprint declara checkout 501.
7. La configuración real de producción (variables presentes, project refs, migraciones remotas y entrega de correos/eventos) sigue pendiente. No se consultaron secretos para esta auditoría.

## Siguiente secuencia segura

1. Revisar solamente nombres/estado de variables en Vercel y el proyecto Supabase vinculado, sin mostrar valores, y correlacionar los project refs con los repositorios.
2. Verificar en Supabase Dashboard el estado de migraciones y RLS, sin ejecutarlas ni cambiarlas.
3. Confirmar en Stripe Test Mode que Interactive tiene un destino downstream de fulfillment, o documentar quién registra y entrega la compra.
4. Probar el checkout de MAGIS únicamente en modo test después de confirmar sus variables y el webhook.
5. Mantener las apps de AI Studio fuera de producción hasta que una copia del código esté versionada en una rama aislada y sus pruebas pasen.

## Límite de alcance

Esto es una lectura de código rastreado y migraciones declaradas. No es una auditoría de bases de datos remotas ni certifica pagos, autenticación, datos reales, seguridad operativa o ingresos.


## 2. Verificación de nombres de variables Vercel — 2026-10-24

La lista de nombres y objetivos de entorno, consultada sin descifrar valores, se encuentra en VERIFICACION_NOMBRES_ENV_VERCEL_v0.1_2026-10-24.md. Los puntos más relevantes para la arquitectura de datos son:

- Interactive: aparecen variables de Discovery, Stripe y Resend de producción; no aparece PURCHASE_EVENT_WEBHOOK_URL ni el mapeo de precio Magistral. Verificar fulfillment en modo test.
- interactive-decox-dag1: no se encontraron variables de entorno registradas ni dominio personalizado. No apuntar el dominio público a ese proyecto.
- Triada: el proyecto Vercel solo mostró GEMINI_API_KEY; no aparecieron los nombres OIDC_* ni UPSTASH_REDIS_REST_* que el servidor requiere. Mantener la API como PENDIENTE de verificación operativa.
- Pirinola: la variable VITE_STRIPE_PAYMENT_LINK utilizada en el CTA no aparece en el listado de Vercel; el estado del CTA publicado no se deduce solo del inventario de variables.
- MAGIS y Tricentric muestran nombres de variables de Supabase/Stripe en Vercel, pero esto no demuestra validez de valores, migraciones remotas aplicadas ni ejecución de pagos.
- Los valores secretos no se leyeron ni se almacenaron. Las variables requeridas por funciones Supabase deben verificarse en la configuración de Supabase por separado.

Esta evidencia actualiza la recomendación operativa; no se cambió configuración ni se ejecutaron pruebas de pagos.
