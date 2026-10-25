# Mapa Maestro Chalamandra Magistral DecoX
**Versión:** 0.3 — despliegues de producción y funnel comercial contrastados en vivo
**Fecha:** 2026-10-24
**Base:** Mapa Maestro v0.1 + consulta de solo lectura a Vercel, GitHub, repositorios locales y comprobaciones HTTP.
**Ubicación:** worktree aislado CatedralX-verify. Esta versión no autoriza ni ejecuta cambios de producción.

## 1. Criterios de evidencia
- **VERIFICADO:** respuesta observada directamente en API, archivo, despliegue o prueba.
- **PARCIAL:** configuración declarada o código presente, pero recorrido funcional no probado.
- **PENDIENTE:** evidencia suficiente aún no disponible.
- **BLOQUEO:** discrepancia que impide declarar el flujo listo.
- Los secretos nunca se copiaron a este documento. Para Vercel solo se registraron nombres de variables y entornos, nunca valores.
- HTTP 200 acredita respuesta HTTP; por sí solo no acredita que la página correcta se renderice, ni que login, pago, persistencia o entrega funcionen.

## 2. Resumen ejecutivo
1. Los siete dominios corporativos/producto probados respondieron HTTP 200: www, Interactive, SystemDecode, Tricentric, Triada, Oráculo y Pirinola.
2. Vercel confirma un proyecto de portal y proyectos específicos para los productos principales.
3. **BLOQUEO PRIORITARIO — Interactive:** el alias público actualmente resuelve al despliegue `dpl_CoET…` (commit `a231b91`), cuyo bundle no contiene la ruta `/sesion-descubrimiento`. Hay un despliegue READY del mismo proyecto en el commit `1a666fa` que sí contiene la ruta, pero el registro de alias consultado sigue apuntando al despliegue anterior. La ficha del despliegue nuevo y la consulta del alias discrepan; la respuesta HTTP 200 por sí sola no demuestra paridad.
4. La copia local de INTERACTIVE-DECOX está en HEAD `990241d`. El alias público observado apunta al commit `a231b91`; el despliegue READY más reciente observado para `interactive-decox` está en `1a666fa`. Ninguno de esos commits está representado por el HEAD local; reconciliar con el repositorio remoto antes de modificar o desplegar.
5. Existen dos proyectos Vercel para el mismo repositorio INTERACTIVE-DECOX. El segundo no tiene dominio personalizado y tiene SSO activado para aliases no personalizados; no eliminarlo sin revisar uso.
6. La configuración declara Stripe y/o Supabase para varios productos, pero los pagos, webhooks, persistencia y acceso premium requieren pruebas funcionales específicas. En Interactive, el webhook omite la notificación downstream si falta `PURCHASE_EVENT_WEBHOOK_URL`; esta variable no aparece en la lista de variables de producción consultada.

## 3. Correlación dominio → proyecto → repositorio → despliegue

| Activo / dominio | Proyecto Vercel | Repositorio y despliegue de producción observado | Estado y observaciones |
|---|---|---|---|
| Portal — www.chalamandramagistral.com | chalamandra-magistral-hlxd | CHALAMANDRA-MAGISTRAL; main; 0b65114 | Dominio verificado. El apex chalamandramagistral.com redirige a www con HTTP 301. El HEAD local coincide con el commit desplegado; el repositorio local tiene 4 cambios sin confirmar. |
| Interactive — interactive.chalamandramagistral.com | interactive-decox | INTERACTIVE-DECOX; alias actual → commit `a231b91`; nuevo despliegue READY → `1a666fa` | **BLOQUEADO para declarar sincronización.** El lookup explícito del alias y el contenido público apuntan al bundle antiguo; el artefacto `1a666fa` sí contiene `/sesion-descubrimiento`. La ficha de ese despliegue lista el dominio en sus aliases, lo cual contradice el lookup explícito del alias. |
| Proyecto duplicado de Interactive — sin dominio personalizado | interactive-decox-dag1 | INTERACTIVE-DECOX; main; 1a666fa | Segundo proyecto Vercel sobre el mismo repositorio y commit. Sin dominios personalizados; SSO activado para aliases no personalizados. Clasificar como posible entorno duplicado, no eliminar hasta confirmar uso. |
| SystemDecode — systemdecode.chalamandramagistral.com | system-decode-magis-v12-0-flux | SYSTEM_DECODE_MAGIS-v12.0-FLUX; main; a2a9be5 | Dominio verificado; respuesta HTTP 200. El HEAD local coincide. Configuración Vercel declara variables de Groq, Stripe y Supabase y hay rutas API de checkout, feedback, Gemini, live-token y webhook. Funcionalidad de pagos/datos pendiente de prueba. |
| Tricentric / SRAP — tricentric.chalamandramagistral.com | tricentric-integration | Tricentric-Integration; main; 322467f | Dominio verificado; HTTP 200. El HEAD local coincide. Vite/React + cliente Supabase; se declara un enlace de pago Stripe. La configuración local de Supabase especifica verify_jwt=false para la función srap-analysis; revisar controles de autorización, abuso y límites dentro de la función antes de declarar el endpoint seguro. |
| Triada — triada.chalamandramagistral.com | chalamandra-triada | Chalamandra-Triada; main; d3d9116 | Dominio verificado; HTTP 200. El HEAD local coincide. Vite/React, Gemini y dependencias MSAL/Redis declaradas en package.json; revisar qué dependencias realmente usa producción y qué configuración les falta. |
| Oráculo — oraculo.chalamandramagistral.com | or-culo-chalamandra | Or-culo-Chalamandra; main; e602745 | Dominio verificado; HTTP 200. El HEAD local coincide. Vite/React, ruta API de Oráculo y variable GEMINI_API_KEY declaradas. El último mensaje de despliegue anuncia un puente comercial hacia Interactive; validar el clic y la ruta final. |
| Pirinola — pirinola.chalamandramagistral.com | pirinola-neural | Pirinola-; main; 89b1bba | Dominio verificado; HTTP 200. El HEAD local coincide. Permanecen dos archivos locales no rastreados: index.html.bak e index.html.broken. No borrarlos sin revisar su contenido y propósito. |
| SRAP Barrio — srap-barrio.vercel.app | srap-barrio | Blueprint-Chalamandra---SRAP-Barrio-Edition; feat/real-money-flow; cee51dd | Despliegue Vercel READY; SSO en aliases no personalizados y sin subdominio de chalamandramagistral.com observado. La copia local está en feat/ads-txt-monetization, HEAD 6dbce12, con 3 cambios; no coincide con el commit desplegado. Reconciliar antes de modificar pagos. |

Los nombres de commit anteriores son prefijos abreviados de SHA confirmados por Vercel/GitHub. Los dominios personalizados aparecen como verificados en la configuración Vercel consultada; esa verificación no demuestra que el alias esté apuntando al artefacto más reciente.

## 4. Hallazgo crítico de Interactive: despliegue vs. dominio
Evidencia leída:
- El despliegue READY `dpl_2Gy…` de `interactive-decox` indica rama `main`, commit `1a666fa`; su bundle directo contiene `/sesion-descubrimiento`. La consulta de alias actual apunta a `dpl_CoET…`, commit `a231b91`, no al artefacto nuevo.
- GitHub en ese commit contiene src/index.tsx que selecciona DiscoveryLandingPage cuando pathname es /sesion-descubrimiento; DiscoveryLandingPage contiene el título “Sesión de Descubrimiento” y enlaza DiscoverySessionPage.
- El paquete servido desde el URL de despliegue directo incluye el texto/ruta de la página y sus CTA.
- El dominio interactivo público también responde HTTP 200 para /sesion-descubrimiento, pero sirve otro bundle. En ese bundle no aparece la cadena de ruta; el HTTP 200 es compatible con un fallback SPA y no prueba que se represente la página correcta.
- La ficha de `dpl_2Gy…` enumera `interactive.chalamandramagistral.com` en su arreglo de aliases, pero `get_alias` y `list_aliases` resuelven el alias al despliegue `dpl_CoET…` y el bundle público coincide con ese paquete antiguo. Se registra como discrepancia de estado entre metadatos del despliegue y asignación de alias vigente; no se modificó el alias.
- El HEAD de la copia local y su referencia origin/main son 990241d; el commit de producción 1a666fa no existe en el almacén Git local revisado. La comparación GitHub sitúa 1a666fa ocho commits por delante de 990241d.

**Conclusión:** la página está presente en el código del despliegue más reciente, pero la versión publicada bajo el dominio oficial no coincide con ese artefacto en esta revisión. No hice cambios de alias, dominio ni despliegue. La corrección requiere autorización explícita porque modifica tráfico de producción; debe comprobarse después con navegador y ruta real, no solo con HTTP 200.

## 5. Backend y configuración declarada
| Producto | Evidencia estática / configuración | Qué no está probado |
|---|---|---|
| Portal corporativo | HTML/JavaScript estático; README declara Formspree y Google Tag Manager. Vercel tiene variables GEMINI_API_KEY y GROQ_API_KEY además de PORT. | No se identificó una API de servidor asociada en el inventario de archivos revisado; confirmar si las variables de IA son necesarias antes de considerar su retirada. |
| Interactive | Vite/React; rutas API ai, contact, stripe-webhook y verify-payment; variables de Vercel incluyen Gemini, correo Resend y Stripe. El código del webhook admite PURCHASE_EVENT_WEBHOOK_URL para notificar a un sistema de fulfillment. | En los nombres de variables de producción consultados no apareció PURCHASE_EVENT_WEBHOOK_URL. Confirmar si existe otro canal de fulfillment y probar en modo de test que el evento de pago active el servicio de forma durable. El webhook puede responder received aunque no haya URL downstream configurada. |
| SystemDecode | Rutas API de checkout, feedback, Gemini, live-token, vídeo y Stripe webhook; Vercel declara variables de Groq, Stripe y Supabase. | Comprobar checkout/webhook/entrega, persistencia, políticas de acceso y que los secretos permanezcan exclusivamente del lado del servidor. |
| Tricentric | Cliente Supabase, variable de pago Stripe y función de análisis SRAP; la función está configurada con verify_jwt=false en el archivo local. | Revisar la función y sus controles efectivos de autenticación, autorización, rate limiting y protección de costes. No concluir vulnerabilidad solo por la bandera; verificar controles alternativos. |
| Triada | API Gemini y capa de seguridad requestSecurity; dependencias MSAL/Redis aparecen en package.json. En el inventario de nombres Vercel apareció GEMINI_API_KEY para producción y preview. | Verificar si MSAL/Redis se ejecutan en producción y, si son necesarios, qué configuración falta; las dependencias declaradas no prueban uso activo. |
| Oráculo | API de producto y variable Gemini declarada. | Probar petición, manejo de errores y el CTA que conduce a Interactive. |
| Pirinola | La configuración Vercel muestra PIRINOLA_SITE_URL y VITE_SITE_URL; no se observó una carpeta api de primer nivel en el inventario local. | Confirmar si es frontend estático y verificar sus CTAs; no inferir que exista pago/backend porque la página responda. |
| SRAP Barrio | Proyecto Vercel y documentación local de oferta, pago y checkout; proyecto bajo SSO para aliases. | Validar el flujo de compra solo en sandbox/test y alinear copia local vs. despliegue antes de tocar pagos. |

Esta tabla identifica señales de configuración y rutas de código, no certifica que servicios externos estén correctamente configurados o funcionales. No se leyeron valores de claves ni secretos.

## 6. Estado de copias locales (solo lectura)
| Repositorio | Rama/HEAD local | Cambios locales indicados por git status | Riesgo de sincronización |
|---|---|---:|---|
| CHALAMANDRA-MAGISTRAL | main / 0b65114 | 4 | HEAD coincide con portal publicado, pero la copia contiene cambios sin confirmar. |
| CatedralX | feat/financial-motor-deterministic / 428253d | 14 | No limpiar ni sobrescribir. |
| CatedralX-verify | HEAD ec92163; rama no informada por git branch --show-current | 42 | Worktree aislado; los cambios no están consolidados. No hacer merge/push. |
| agents | fix/tool-call-context-budget / 0d2fe84 | 4 | No limpiar ni sobrescribir. |
| INTERACTIVE-DECOX | feat/discovery-private-portal-20261019 / 990241d | 0 | La copia local está ocho commits detrás del commit de producción reportado por Vercel. |
| SYSTEM_DECODE_MAGIS-v12.0-FLUX | main / a2a9be5 | 0 | Coincide con producción observada. |
| Tricentric-Integration | main / 322467f | 0 | Coincide con producción observada. |
| Chalamandra-Triada | main / d3d9116 | 0 | Coincide con producción observada. |
| Or-culo-Chalamandra | main / e602745 | 0 | Coincide con producción observada. |
| Pirinola- | main / 89b1bba | 2 | No borrar index.html.bak ni index.html.broken. |
| Blueprint-Chalamandra---SRAP-Barrio-Edition | feat/ads-txt-monetization / 6dbce12 | 3 | No coincide con la rama/commit publicado. |
| OMNI-CHALAMANDRA-decox | fix/omni-production-hardening / 9efe934 | 1 | Sin proyecto de Vercel asociado localizado en la lista consultada. |
| CHMADEX-DIAL | main / c42e271 | 0 | Parece extensión de navegador (manifest.json); no se localizó un proyecto Vercel asociado. |
| CHALAMANDRA-S-BUNKER | main / dfca957 | 0 | Código de interfaz/prototipo; no se localizó un proyecto Vercel asociado. |

Los conteos son la cantidad de líneas reportadas por git status --short en esta revisión, no la cantidad de archivos ni una evaluación del contenido de cada cambio.

## 7. Acciones recomendadas, por prioridad
**P0 — Interactive (requiere autorización para cambio de producción):**
1. Revisar el alias del dominio interactivo y apuntarlo al despliegue aprobado que contiene la página de descubrimiento.
2. Después, abrir https://interactive.chalamandramagistral.com/sesion-descubrimiento en navegador y confirmar título, selector de recorrido, CTA y destino comercial. Verificar que no se haya alterado el resto de Interactive.
3. Sincronizar la copia local de forma controlada; no sobrescribir el branch de trabajo ni asumir que fetch/merge es inocuo.

**P1 — Integridad comercial:**
4. Probar pago en test mode para Interactive y SystemDecode, incluyendo webhook, evento downstream, confirmación y entrega del producto.
5. Confirmar si Interactive necesita PURCHASE_EVENT_WEBHOOK_URL; no añadir una URL inventada ni enviar eventos reales.
6. Revisar la función srap-analysis de Tricentric y documentar su autorización efectiva.
7. Verificar login, persistencia y permisos de cada producto con cuentas de prueba.

**P2 — Control de cartera:**
8. Investigar el proyecto duplicado interactive-decox-dag1 sin eliminarlo.
9. Reconciliar la copia local SRAP Barrio con el commit desplegado antes de tocar checkout.
10. Completar hosting, base de datos, autenticación, analítica, responsable comercial y oferta por cada repositorio adicional: OMNI, CHMADEX-DIAL y CHALAMANDRA-S-BUNKER.

## 8. Límites respetados
- No se modificaron DNS, dominios, aliases, deployments, secretos ni variables de entorno.
- No se leyeron ni copiaron valores secretos.
- No se hicieron commits, merges, pushes ni limpiezas.
- No se ejecutaron compras ni pagos reales.
- No se habilitó trading real ni se cambió CatedralX o agents.

## 9. Confirmación de producción desde Vercel y prueba del funnel — 2026-10-24

### 9.1 Correlación dominio → proyecto → repositorio → commit de producción

Los vínculos siguientes se obtuvieron de la cuenta Vercel conectada: alias actuales, proyecto asociado y despliegue con estado `READY`, objetivo `production` y metadatos Git. Los hashes se muestran abreviados. La asociación es más fuerte que un HTTP 200, pero todavía no valida todas las funciones de la aplicación.

| Dominio público | Proyecto Vercel asociado al alias | Repositorio de origen reportado por el despliegue que sirve el alias | Commit del target actual del alias | Estado / observación |
|---|---|---|---|---|
| `chalamandramagistral.com` → `www.chalamandramagistral.com` | `chalamandra-magistral-hlxd` | `CHALAMANDRA-MAGISTRAL` | `0b65114` | READY; redirección 301 de apex a www. El HEAD local también es `0b65114`, pero hay 4 entradas modificadas sin confirmar: esos cambios locales no están incluidos por el solo hecho de existir. |
| `interactive.chalamandramagistral.com` | `interactive-decox` | `INTERACTIVE-DECOX` | `a231b91` | READY, pero el alias lookup apunta al bundle antiguo. El HEAD local es `990241d`; el mismo proyecto tiene un despliegue READY más nuevo en `1a666fa` con ruta de descubrimiento, aún no demostrado como target vigente del alias. |
| `systemdecode.chalamandramagistral.com` | `system-decode-magis-v12-0-flux` | `SYSTEM_DECODE_MAGIS-v12.0-FLUX` | `a2a9be5` | READY; HEAD local coincide con el commit publicado. |
| `tricentric.chalamandramagistral.com` | `tricentric-integration` | `Tricentric-Integration` | `322467f` | READY; HEAD local coincide con el commit publicado. No se observó `.vercel/project.json` local en este checkout; el alias de la cuenta Vercel sí está verificado. |
| `triada.chalamandramagistral.com` | `chalamandra-triada` | `Chalamandra-Triada` | `d3d9116` | READY; HEAD local coincide con el commit publicado. |
| `oraculo.chalamandramagistral.com` | `or-culo-chalamandra` | `Or-culo-Chalamandra` | `e602745` | READY; HEAD local coincide con el commit publicado. No se observó `.vercel/project.json` local. |
| `pirinola.chalamandramagistral.com` | `pirinola-neural` | `Pirinola-` | `89b1bba` | READY; HEAD local coincide con el commit publicado. Hay dos archivos locales no rastreados (`index.html.bak`, `index.html.broken`); no se eliminaron. No se observó `.vercel/project.json` local. |

Vercel reporta dos despliegues READY del commit `1a666fa` desde `INTERACTIVE-DECOX`: uno bajo `interactive-decox` (`dpl_2Gy…`) y otro bajo el proyecto separado `interactive-decox-dag1` (`dpl_9U1…`). La consulta de dominios de producción no encontró dominio personalizado para `interactive-decox-dag1`, y su URL directa está protegida por SSO. El hallazgo operativo más importante es la discrepancia entre la ficha del despliegue `dpl_2Gy…` (que enumera el dominio) y la consulta explícita `get_alias`/`list_aliases` (que apunta a `dpl_CoET…`, commit `a231b91`); el bundle público observado también coincide con el artefacto antiguo.

- El subdominio `interactive.chalamandramagistral.com` está vinculado al proyecto `interactive-decox`, pero durante esta comprobación sirve el bundle anterior en vez de la versión que contiene `/sesion-descubrimiento`.
- `interactive-decox-dag1` es otro proyecto Vercel del mismo repositorio, con el mismo commit `1a666fa`, sin dominio personalizado observado y con acceso SSO a la URL directa.
- El bundle público incluye el texto de la oferta “Sesión de Descubrimiento”, pero no contiene la ruta `/sesion-descubrimiento`; el HTTP 200 de esa ruta corresponde a fallback SPA, no demuestra que se muestre la página correcta.
- **No cambiar alias ni hacer despliegues para resolverlo todavía.** Comparar rutas, componentes, checkout, webhook, modelos de datos y accesos entre ambos artefactos; documentar el target canónico y solicitar autorización explícita antes de tocar producción.

### 9.2 Prueba técnica del formulario público

| Comprobación | Evidencia observada | Conclusión |
|---|---|---|
| `contact.html` público | HTTP 200 | La página responde |
| `assets/form-decox.js` público | HTTP 200 | El manejador JavaScript se sirve |
| `thanks.html` público | HTTP 200 | La página de confirmación responde |
| `ofertas.html` público | HTTP 200 | La página de oferta responde |
| Formulario | Campos obligatorios y destino Formspree presentes en el HTML público | Configuración del formulario visible |
| Envío sintético de QA a Formspree | HTTP 200, respuesta JSON con `ok=true` | **El proveedor aceptó un envío de prueba**; no se contactó a ningún cliente ni se registró una solicitud comercial real |
| Código de atribución | Manejador público agrega `lead_source`, `lead_offer`, `lead_origin` y UTMs; tras respuesta exitosa emite `dataLayer` con evento `generate_lead` | Instrumentación definida en código |
| Confirmación | El manejador redirige a `/thanks.html` tras respuesta exitosa | Redirección definida en código |

**Límite de la prueba:** no se verificó la llegada de la notificación al buzón receptor ni se abrió el panel de Formspree; tampoco se ejecutó un navegador automatizado que observara el recorrido visual completo. La respuesta `ok=true` confirma la aceptación del proveedor, no la entrega de correo ni que GTM/GA4 tenga una conversión configurada y recibiendo eventos. El envío de prueba lleva una identificación inequívoca de QA y no constituye un lead de venta.

### 9.3 Ruta comercial observada

El HTML público ofrece una ruta real de página a contacto:

1. Inicio (`index.html`) enlaza a `ofertas.html` y a `contact.html`; existe un CTA hacia Mapa SRAP con parámetros de atribución.
2. `ofertas.html` dirige los CTA de Mapa SRAP, consultoría, taller SRAP y arquitectura de sistemas a `contact.html` con parámetros `interes` y/o `origen`.
3. `assets/form-decox.js` interpreta esos parámetros y preselecciona tipo de consulta/mensaje; añade `lead_source` y UTMs al envío.
4. Una respuesta de éxito de Formspree hace que el código emita `generate_lead` en `dataLayer` y redirija a la página de confirmación.

**Estado del recorrido:** rutas, manejador público y aceptación de un envío sintético verificados. Notificación al buzón, almacenamiento/CRM, etiqueta que consume `generate_lead`, configuración de conversión de GA4/Google Ads y seguimiento humano permanecen pendientes. No afirmar ingresos/ventas a partir de esta prueba.

### 9.4 Decisiones inmediatas basadas en evidencia

1. **No desplegar el portal desde el worktree actual sin revisar su diff.** El HEAD local coincide con la versión de producción, pero sus cuatro archivos modificados todavía no están confirmados.
2. **Resolver el estado canónico de Interactive.** Comparar el dominio actual (`interactive-decox`, commit `a231b91`) con el proyecto separado `interactive-decox-dag1` (commit `1a666fa`) y documentar el resultado antes de mover dominios o desplegar.
3. **Confirmar recepción del formulario** en el panel/buzón autorizado y revisar las reglas GTM/GA4; la prueba de proveedor no reemplaza esta comprobación.
4. Completar los tres vínculos locales de Vercel que faltan (`Tricentric-Integration`, `Or-culo-Chalamandra`, `Pirinola-`) solo después de verificar el nombre de proyecto correcto; no ejecutar `vercel link` ni reconfigurar proyectos de forma automática.
5. A continuación, probar checkout/webhook únicamente en modo de prueba de cada aplicación. No ejecutar compras reales ni migraciones.

### 9.5 Límites respetados durante esta revisión

- Solo se consultó Vercel y se hicieron peticiones HTTP de lectura, excepto un único envío sintético autorizado al formulario propio, claramente marcado como QA.
- No se leyeron valores de `.env`, variables de entorno, claves API ni secretos.
- No se modificaron los repositorios principales, alias, DNS, bases de datos, hosting ni despliegues.
- Los cambios Git preexistentes se conservaron. La única nueva documentación que se crea en esta etapa es esta versión del Mapa Maestro en el worktree aislado.

## 10. Variables de entorno por nombre y flujo — consulta de solo lectura

Se consultaron nombres/targets de variables en Vercel con `decrypt=false`. No se recuperaron ni imprimieron valores. La presencia de una variable en la lista no demuestra que su valor sea válido; su ausencia en una lista no demuestra por sí sola que no exista otro mecanismo de integración fuera de Vercel.

| Proyecto Vercel | Nombres relevantes observados | Evaluación / próximo control |
|---|---|---|
| `interactive-decox` | `RESEND_API_KEY`, `CONTACT_TO_EMAIL`, `CONTACT_FROM_EMAIL`, `GEMINI_API_KEY`, `GEMINI_MODEL`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_DISCOVERY_PRICE_ID`, `VITE_STRIPE_DISCOVERY_URL` | Los nombres se alinean con API de IA, correo de contacto y Stripe. La variable de checkout `VITE_STRIPE_DISCOVERY_URL` está configurada para producción; al ser `VITE_*`, su valor se incorpora al código cliente y debe tratarse como URL pública, nunca como clave secreta. |
| `interactive-decox` — ausencia importante | `PURCHASE_EVENT_WEBHOOK_URL` no apareció en los nombres consultados para producción. Sí está documentada en `.env.example` y se lee en `api/stripe-webhook.ts`. | **BLOQUEO para afirmar fulfillment automático.** Si falta la URL, el webhook acepta el evento Stripe verificado y devuelve `{ received: true }` sin enviar el evento al sistema downstream. Configurar y probar un destino idempotente o documentar fulfillment manual antes de prometer entrega automática. No añadir ni cambiar variables sin aprobación. |
| `interactive-decox-dag1` | La consulta de variables no devolvió nombres | No tratar este proyecto protegido como destino de producción hasta confirmar configuración, acceso y destino del checkout. No copiar variables de otro proyecto automáticamente. |
| `system-decode-magis-v12-0-flux` | `GROQ_API_KEY`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PRICE_PRO`, `STRIPE_PRICE_STARTER`, `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, `SUPABASE_SECRET_KEY`, `VITE_SUPABASE_URL`, `VITE_SUPABASE_PUBLISHABLE_KEY`, `MAGIS_APP_URL` | Nombres coherentes con IA, cobro y datos. Validar separadamente checkout, webhook y políticas RLS; no se leyeron valores ni se hizo transacción. Las variables `VITE_*` son públicas por diseño y no deben contener secretos. |
| `tricentric-integration` | `VITE_STRIPE_PAYMENT_LINK`, `VITE_SUPABASE_URL`, `VITE_SUPABASE_PUBLISHABLE_KEY`, `VITE_SITE_URL`, `VITE_ENABLE_LOCAL_AI` | Frontend configurado con URL de pago y Supabase. La URL de pago y la clave publicable son datos del cliente; los controles de autorización y las claves privilegiadas deben residir en backend/DB con políticas adecuadas. No se probó una compra. |
| `chalamandra-magistral-hlxd` (portal) | `GEMINI_API_KEY`, `GROQ_API_KEY`, `PORT` en producción/preview | La búsqueda estática del checkout local no encontró referencias a las dos claves de IA fuera de archivos de entorno/configuración. El portal se construye como salida estática; verificar su uso en el proyecto desplegado antes de decidir si son variables obsoletas. No eliminarlas en esta auditoría. |

### 10.1 Criterios de aceptación para pagos/entrega de Interactive

Antes de declarar el producto listo para cobrar y entregar automáticamente, debe haber evidencia reproducible de:

1. Checkout de prueba crea la sesión correcta para el producto/importe esperados y no expone claves privadas al cliente.
2. Webhook verifica firma y deduplica eventos por `event.id`.
3. El evento pagado se transmite a un sistema downstream configurado, o queda durablemente registrado para fulfillment manual; no basta responder `received`.
4. Una repetición del webhook no duplica acceso, entrega, saldo ni notificación.
5. La UI de postpago y el sistema que entrega el servicio coinciden en el estado real del pago.
6. El camino se prueba con datos sintéticos en modo test, sin cargos reales y sin publicar cambios durante la auditoría.

**Estado actual:** la configuración declarada de Stripe existe, pero no se probó un pago. El destino downstream de Interactive no aparece entre las variables de producción consultadas y el código permite reconocer el evento sin notificar fulfillment. La entrega automatizada queda **PENDIENTE / BLOQUEADA hasta resolver o documentar explícitamente el mecanismo alternativo**.

### 10.2 Funnel de la empresa: estado verificable

| Etapa | Estado actual | Evidencia / brecha |
|---|---|---|
| Búsqueda y llegada web | PARCIAL | Dominios responden; esto no mide tráfico cualificado. |
| Interés en oferta | PARCIAL | `ofertas.html` presenta rutas a Mapa SRAP, consultoría, taller y arquitectura. No se demostró intención real de clientes. |
| Clic al contacto | VERIFICADO en HTML | CTA pasan `interes`/`origen` y, en algunos enlaces, UTM. |
| Contacto técnico | PROBADO a nivel proveedor | Formspree aceptó un envío sintético con HTTP 200 y `ok=true`; recepción en el buzón aún no verificada. |
| Analítica de lead | PARCIAL | El JavaScript emite `generate_lead` a `dataLayer`; faltan prueba en navegador/Tag Assistant y confirmación de etiqueta/conversión en GA4/Ads. |
| Oferta → pago | PENDIENTE | No se creó checkout ni se cobró; validar modo test en cada producto. |
| Pago → entrega | BLOQUEADO para automatización de Interactive | Falta evidencia de un destino downstream configurado y de una entrega idempotente. |
| Recompra y seguimiento | PENDIENTE | No se encontró evidencia verificada de CRM/seguimiento comercial integrado a este funnel. |

La primera mejora comercial debe cerrar la cadena **contacto aceptado → notificación recibida → lead registrado → seguimiento humano**, y medir el resultado antes de comprar tráfico. La prueba sintética no se registra como venta ni lead real.


## 11. Inventario de Supabase y controles de Edge Functions — 2026-10-24

### 11.1 Proyectos de datos identificados por API

| Proyecto Supabase | Ref | Región | Estado reportado | Relación con producto |
|---|---|---|---|---|
| tricentric-production | xgupisrhrihiymmwdlqg | us-east-1 | ACTIVE_HEALTHY | Candidato fuerte para Tricentric porque la función remota coincide con el slug srap-analysis del repositorio; la URL de proyecto usada en producción aún no se vinculó por evidencia de configuración no sensible. |
| magis-commercial-production | qusrfuwduxpuidowofgc | us-east-1 | ACTIVE_HEALTHY | Candidato por nombre para SystemDecode/MAGIS; el vínculo exacto entre el deployment de Vercel y este ref sigue pendiente. |
| Bunker | ymajkowdxhfasquhmxtj | us-west-2 | INACTIVE | Posible relación por nombre con CHALAMANDRA-S-BUNKER, no confirmada. |

La búsqueda de estos refs exactos fuera de archivos de entorno no encontró coincidencias en los repositorios Tricentric, SystemDecode, Interactive o Bunker revisados. No se inspeccionaron valores de variables de entorno ni credenciales.

La consulta de catálogo de tablas devolvió el error “Database is possibly not accessible at the moment”. No se obtuvo el esquema remoto en esta pasada y no se leyeron filas de usuario, pedidos ni transacciones.

### 11.2 Funciones Edge remotas y autenticación observada en código

| Proyecto / función | Estado remoto | Configuración gateway | Evidencia de control en el código desplegado | Pendiente |
|---|---|---|---|---|
| tricentric-production / srap-analysis | ACTIVE, versión 42 | verify_jwt=false | La función usa middleware withSupabase y comprueba userId; también aplica comprobación de origen y validación de entrada. | No se encontró rate limiting explícito en la inspección estática; revisar cuotas, límites de uso, abuso y coste del modelo. |
| magis-commercial-production / mcp | ACTIVE, versión 1 | verify_jwt=false | La función encadena withOAuthProtectedResource y withSupabase y pasa las claims verificadas al handler; la fuente del middleware describe validación del token y cliente con alcance RLS. | No se encontró rate limiting explícito en la inspección estática; probar el acceso con y sin token en ambiente controlado y revisar cuotas/concurrencia. |

Interpretación de seguridad: verify_jwt=false indica que Supabase no aplica la verificación JWT del gateway para esas funciones. Por sí sola no prueba que la función acepte peticiones sin autenticar. La inspección observó middleware de autenticación a nivel de aplicación; aún se deben probar sus límites, permisos, cuotas, validación y resistencia al abuso. No cambiar verify_jwt ni los permisos sin una revisión compatible con el flujo OAuth/MCP y aprobación explícita.

Se creó el seguimiento Jira CHAL-12: “Verificar límites de abuso y autorización de Edge Functions Supabase”. Está vinculado al épico CHAL-2 y pendiente de ejecución.

### 11.3 Siguiente acción técnica

1. Conservar la matriz Vercel como fuente del vínculo dominio → proyecto → alias → deployment/commit.
2. Confirmar app → ref Supabase sin exponer valores secretos y sin leer datos de negocio.
3. Inspeccionar RLS y handlers de las dos funciones, definir una prueba negativa segura y documentar cuotas/coste máximo.
4. Resolver por decisión explícita el destino canónico de Interactive; no mover aliases ni desplegar durante esta revisión.
5. Si el catálogo de tablas sigue sin estar disponible, registrar el bloqueo y continuar con fuentes de esquema versionadas, sin intentar acceder a datos de producción.

No se modificaron funciones, configuración de autenticación, tablas, migraciones, variables de entorno, aliases, DNS o despliegues.
