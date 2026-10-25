# Mapa Maestro Chalamandra Magistral DecoX
**Versión:** 0.5 — consolidación del mapa, despliegues, funnel y contraste remoto de backend
**Fecha:** 2026-10-24
**Base:** revisiones previas del Mapa Maestro + consultas de solo lectura a Vercel, GitHub, Supabase y repositorios locales.
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
6. La configuración declara Stripe y/o Supabase para varios productos, pero los pagos, webhooks, persistencia y acceso premium requieren pruebas funcionales específicas.

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
**P0 — Interactive (estado posterior a la reversión solicitada):**
1. El alias interactive.chalamandramagistral.com fue reasignado al despliegue anterior dpl_CoETjgfuU5bdG1YjEwbNLK8SUUFV, SHA a231b911390a418c145538ed2d6a6c28c768ecff, para restaurar la página previa solicitada.
2. No volver a cambiar el alias ni desplegar hasta reconciliar las fuentes. La ruta /sesion-descubrimiento respondió HTTP 200 con el fallback SPA, pero su presentación visual no quedó verificada en navegador.
3. Mantener interactive-decox-dag1 separado. Primero comparar su fuente con el código ejecutable existente en Google AI Studio y preparar una integración aislada que no modifique el dominio público.

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
- No se modificó DNS, registro de dominio, secretos ni variables de entorno. La revisión inicial era de solo lectura; después, por la instrucción explícita de restaurar la página previa, se reasignó únicamente el alias de Interactive al despliegue anterior. No se cambió código ni se creó un deployment nuevo.
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
- El dominio público está restaurado en interactive-decox (SHA a231b91).
- interactive-decox-dag1 permanece como proyecto separado con SHA 1a666fa y sin dominio personalizado en la consulta. No se ha demostrado que su contenido sea idéntico a la app ejecutable de Google AI Studio.
- No volver a mover el alias. Comparar las fuentes y sincronizar la aplicación de AI Studio en una rama aislada.

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

- La auditoría inicial consultó Vercel y endpoints HTTP; también hubo un único envío sintético autorizado al formulario propio, marcado como QA. Posteriormente se reasignó el alias de Interactive para restaurar la versión anterior, según la instrucción de la usuaria.
- No se leyeron valores de `.env`, variables de entorno, claves API ni secretos.
- No se modificaron los repositorios principales, DNS, bases de datos, configuración de hosting ni código. Excepción registrada: el alias público de Interactive fue reasignado al deployment previo solicitado; no se creó un deployment nuevo.
- Los cambios Git preexistentes se conservaron. La única nueva documentación que se crea en esta etapa es esta versión del Mapa Maestro en el worktree aislado.

## 10. Validación del puente agents → CatedralX — 2026-10-24

- Suite offline de registro/contrato: **21 pruebas aprobadas** (test_catedralx_tool.py, test_master.py, test_tool_registry.py).
- Prueba de humo mediante Master.execute_agent_tool_call con el motor real del worktree CatedralX-verify: status=ok; señal consistente; trading_eligible=false; orders_created=false; orders_executed=false.
- Se usó una serie local sintética de 60 valores solo para verificar el contrato. No se consultó mercado, APIs externas ni modelos. El estado se redirigió a /tmp y se eliminó.
- Los estados Git antes/después coincidieron: las modificaciones preexistentes de agents y CatedralX-verify se conservaron.
- **Alcance limitado:** valida el código actual en un entorno aislado; no certifica runtime productivo, copia principal de CatedralX, datos de mercado en vivo, rentabilidad o aptitud para trading.
- Evidencia detallada: VALIDACION_PUENTE_AGENTS_CATEDRALX_v0.1_2026-10-24.md.

## 11. Inventario de backend y persistencia — 2026-10-24

- El análisis de código rastreado indica que Interactive persiste progreso observado en localStorage. No se encontró cliente Supabase usado por la app/API ni migraciones de esquema de producto en el árbol rastreado, aunque existe una carpeta Supabase con función MCP.
- En Interactive, el webhook Stripe solo reenvía eventos verificados a un destino de fulfillment cuando PURCHASE_EVENT_WEBHOOK_URL está configurada. Si falta, el handler puede responder received=true sin registrar/provisionar una compra propia. La configuración real no se inspeccionó; es un bloqueo de verificación comercial.
- MAGIS tiene migraciones que definen planes, perfiles, planes de usuario, cuentas/libro de créditos, compras, operaciones de vídeo y feedback, con RLS y rutinas server-side declaradas.
- Tricentric tiene migraciones para perfiles, evaluaciones, logros, prácticas y cuota diaria de IA; la Edge Function usa autenticación de usuario en su wrapper y debe validarse contra el proyecto remoto.
- Triada usa Entra/OIDC para identidad y Upstash Redis para límites; no se identificó base de datos de historial en el código revisado. Oráculo usa rate limiting en memoria y no se identificó almacenamiento duradero. Pirinola usa un enlace externo de Stripe sin backend de fulfillment demostrado. Blueprint SRAP mantiene estado local y su README declara checkout 501.
- Inventario detallado, con límites por activo y próximos pasos: INVENTARIO_BACKENDS_DATOS_v0.1_2026-10-24.md.
- La información proviene de código rastreado; no se consultaron valores de archivos .env ni se verificaron tablas/migraciones remotas. No se ejecutaron cambios de base de datos.


## 12. Contraste remoto de Supabase — actualización posterior, 2026-10-24

Esta sección supersede cualquier afirmación previa de que no se había podido contrastar el esquema remoto. En esta pasada respondieron los metadatos, catálogos de políticas y privilegios; las consultas fueron de solo lectura y no tocaron filas de negocio.

### 12.1 Proyectos y frontera de datos

- `tricentric-production` (`xgupisrhrihiymmwdlqg`) está `ACTIVE_HEALTHY`. Los archivos locales `Tricentric-Integration/supabase/.temp/project-ref` y `linked-project.json` coinciden con ese ref.
- `magis-commercial-production` (`qusrfuwduxpuidowofgc`) está `ACTIVE_HEALTHY`. Los archivos de enlace de `SYSTEM_DECODE_MAGIS-v12.0-FLUX` y `INTERACTIVE-DECOX` apuntan al mismo ref.
- `Bunker` (`ymajkowdxhfasquhmxtj`) está `INACTIVE`; el catálogo de tablas no fue accesible en la consulta. No asumir que corresponde al repo `CHALAMANDRA-S-BUNKER` por el nombre.

**BLOQUEO DE ARQUITECTURA:** Interactive y SystemDecode están enlazados localmente al mismo proyecto Supabase comercial. Falta confirmar si compartir autenticación, datos y operaciones de crédito es deliberado; el vínculo local no prueba por sí solo qué credenciales usa cada despliegue. No separar ni migrar hasta definir la frontera del producto.

### 12.2 Funciones remotas y autenticación

- Tricentric: `srap-analysis` está ACTIVE v42 con `verify_jwt=false` en metadatos de plataforma. El código desplegado aplica `withSupabase({ auth: "user" })`, requiere claims de usuario, valida origen y payload y consume cuota antes de invocar Gemini.
- MAGIS comercial: `mcp` está ACTIVE v1 con `verify_jwt=false` en metadatos de plataforma. El código encadena `withOAuthProtectedResource` y `withSupabase({ auth: "user" })`; actualmente registra una herramienta `whoami` que devuelve claims verificadas.

La bandera `verify_jwt=false` describe el gateway, no basta por sí sola para afirmar que existe acceso anónimo. Falta prueba negativa controlada con y sin identidad, además de límites de uso/coste. No se cambió esta configuración.

### 12.3 RLS y permisos observados

**Tricentric**
- Las seis tablas públicas consultadas tienen RLS activo.
- Las políticas de SELECT para perfiles, evaluaciones, prácticas y logros de usuario limitan el resultado a `auth.uid()`; `achievements` es legible por usuarios autenticados; `ai_usage_daily` deniega acceso directo a `anon` y `authenticated`.
- El advisor marcó cuatro firmas `SECURITY DEFINER`. La revisión de definiciones/ACL confirmó `EXECUTE` para `authenticated` y `service_role`, no para `anon`; las funciones inspeccionadas usan `search_path` vacío y comprueban `auth.uid()`. Esto reduce el riesgo aparente de invocación anónima, pero siguen pendientes pruebas entre dos cuentas sintéticas y revisión de auxiliares.
- Supabase Auth tiene desactivada la protección frente a contraseñas filtradas.

**MAGIS comercial**
- Las ocho tablas públicas consultadas tienen RLS activo.
- `profiles`, `user_plans`, `credit_accounts` y `credit_ledger` tienen políticas de lectura por usuario; `plans` permite leer planes activos a usuarios autenticados.
- `operation_feedback`, `purchases` y `video_operations` no tienen políticas y no conceden SELECT directo a `anon` ni `authenticated`; `service_role` sí tiene ese privilegio. El acceso directo de lectura de clientes aparece fail-closed en las comprobaciones realizadas, pero todavía hay que revisar la autorización de los endpoints server-side que utilizan service-role.
- Supabase Auth tiene desactivada la protección frente a contraseñas filtradas.

Referencias oficiales relacionadas con los avisos:
- [Advisor: SECURITY DEFINER ejecutable por usuarios autenticados](https://supabase.com/docs/guides/database/database-linter?lint=0029_authenticated_security_definer_function_executable)
- [Advisor: RLS habilitado sin políticas](https://supabase.com/docs/guides/database/database-linter?lint=0008_rls_enabled_no_policy)
- [Supabase Auth: protección contra contraseñas filtradas](https://supabase.com/docs/guides/auth/password-security#password-strength-and-leaked-password-protection)

### 12.4 Prioridad consolidada

1. **P0 — Frontera Interactive/SystemDecode:** confirmar si el backend compartido es intencional y si cuentas, créditos, compras y perfiles deben estar aislados.
2. **P0 — MAGIS server-side:** verificar los endpoints que escriben/leen `purchases`, `video_operations` y `operation_feedback`; no añadir políticas genéricas para quitar warnings.
3. **P1 — Tricentric RPC:** probar denegación cruzada entre cuentas y revisar funciones auxiliares llamadas por RPC.
4. **P1 — Funciones Edge:** probar ausencia/presencia de token y documentar límites de cuota/coste con datos sintéticos, sin someter producción a pruebas de abuso.
5. **P2 — Seguridad de Auth:** revisar configuración de protección contra contraseñas filtradas en ambos proyectos.

### 12.5 Límites de la evidencia

Se consultaron metadatos, políticas y catálogos de funciones/privilegios; no se consultaron filas de usuarios, compras, evaluaciones o créditos. No se leyeron archivos `.env`, no se solicitaron valores descifrados desde Vercel, no se modificaron SQL/RLS/funciones/secretos/DNS/aliases/despliegues y no se ejecutaron pagos. Estas observaciones no son certificación de seguridad ni aprobación para producción.

Referencia ampliada: `INVENTARIO_TECNICO_COMPLEMENTARIO_v0.2_2026-10-24.md`, sección 11.
