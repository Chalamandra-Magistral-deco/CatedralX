# Mapa Maestro Chalamandra Magistral DecoX
**Versión:** 0.2 — correlación de repositorios, Vercel, dominios y señales de backend
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
3. **BLOQUEO PRIORITARIO — Interactive:** el despliegue más reciente de producción de Vercel incorpora la ruta /sesion-descubrimiento, pero el dominio interactivo público está sirviendo un paquete JavaScript diferente que no contiene esa ruta. El despliegue nuevo y el dominio no están en paridad.
4. La copia local de INTERACTIVE-DECOX está en HEAD 990241d, mientras que Vercel informa producción en 1a666fa; GitHub confirma que ese commit está ocho commits por delante del HEAD local. El worktree local no contiene el commit desplegado.
5. Existen dos proyectos Vercel para el mismo repositorio INTERACTIVE-DECOX. El segundo no tiene dominio personalizado y tiene SSO activado para aliases no personalizados; no eliminarlo sin revisar uso.
6. La configuración declara Stripe y/o Supabase para varios productos, pero los pagos, webhooks, persistencia y acceso premium requieren pruebas funcionales específicas.

## 3. Correlación dominio → proyecto → repositorio → despliegue

| Activo / dominio | Proyecto Vercel | Repositorio y despliegue de producción observado | Estado y observaciones |
|---|---|---|---|
| Portal — www.chalamandramagistral.com | chalamandra-magistral-hlxd | CHALAMANDRA-MAGISTRAL; main; 0b65114 | Dominio verificado. El apex chalamandramagistral.com redirige a www con HTTP 301. El HEAD local coincide con el commit desplegado; el repositorio local tiene 4 cambios sin confirmar. |
| Interactive — interactive.chalamandramagistral.com | interactive-decox | INTERACTIVE-DECOX; main; 1a666fa | Dominio registrado y verificado en el proyecto, pero no aparece en los aliases del despliegue más reciente. El paquete del dominio público no contiene la ruta de descubrimiento que sí aparece en el artefacto del despliegue más reciente. **BLOQUEADO para declarar sincronización.** |
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
- El despliegue de producción de interactive-decox indica rama main, commit 1a666fa y estado READY.
- GitHub en ese commit contiene src/index.tsx que selecciona DiscoveryLandingPage cuando pathname es /sesion-descubrimiento; DiscoveryLandingPage contiene el título “Sesión de Descubrimiento” y enlaza DiscoverySessionPage.
- El paquete servido desde el URL de despliegue directo incluye el texto/ruta de la página y sus CTA.
- El dominio interactivo público también responde HTTP 200 para /sesion-descubrimiento, pero sirve otro bundle. En ese bundle no aparece la cadena de ruta; el HTTP 200 es compatible con un fallback SPA y no prueba que se represente la página correcta.
- Los aliases del despliegue más reciente incluyen alias *.vercel.app, pero no interactive.chalamandramagistral.com.
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
**P0 — Interactive (no cambiar producción hasta decidir la versión pública):**
1. La consulta actual de Vercel confirma que el alias público apunta al deployment READY de SHA `a231b911...`, mientras el proyecto tiene un deployment de producción más reciente con SHA `1a666fa...`. Mantener el alias como está hasta comparar ambos despliegues y definir cuál versión debe ser pública.
2. En navegador, comparar en ambos despliegues la ruta `/sesion-descubrimiento`: título, selector de recorrido, CTA, destino comercial y efectos colaterales. No tratar HTTP 200 por sí solo como prueba funcional.
3. Solo después de la decisión explícita, preparar una reasignación del alias y una verificación posterior; sincronizar la copia local por separado, sin sobrescribir el branch de trabajo ni asumir que fetch/merge es inocuo.

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


## 9. Actualización de evidencia de hosting/backend — 2026-10-24

El inventario complementario se amplió con metadatos actuales de Vercel y Supabase en modo solo lectura. La referencia detallada es `INVENTARIO_TECNICO_COMPLEMENTARIO_v0.1_2026-10-24.md`, secciones 6–7.

### Hechos nuevos de alto impacto

1. **Interactive:** el alias `interactive.chalamandramagistral.com` sigue asignado al deployment READY con SHA `a231b911...`, mientras que el deployment de producción más reciente del proyecto `interactive-decox` tiene SHA `1a666fa...`. No se debe cambiar el alias automáticamente: mantener la asignación actual hasta comparar comportamiento y decidir la versión pública.
2. **Proyecto paralelo de Interactive:** `interactive-decox-dag1` no tiene dominio personalizado y apunta al mismo SHA que la integración reciente del proyecto principal. Investigar procedencia y propósito; no borrar.
3. **Supabase compartido localmente:** los archivos de enlace de `INTERACTIVE-DECOX` y `SYSTEM_DECODE_MAGIS-v12.0-FLUX` apuntan ambos a `magis-commercial-production` (`qusrfuwduxpuidowofgc`). El aislamiento de datos entre productos no debe suponerse; confirmar si el uso compartido es deliberado antes de cambios.
4. **Tricentric backend:** el proyecto remoto `tricentric-production` está ACTIVE_HEALTHY y el ref coincide con el enlace local. Su función `srap-analysis` está activa; plataforma indica `verify_jwt=false`, mientras que el código de función aplica middleware `withSupabase({ auth: "user" })` y exige claims. Revisar y probar el límite de autenticación; la discrepancia de configuración no constituye por sí sola prueba de acceso anónimo.
5. **MAGIS comercial:** `magis-commercial-production` está ACTIVE_HEALTHY; tablas observadas tienen RLS habilitado. Los advisors señalan tres tablas sin políticas y protección de contraseñas filtradas desactivada. Resolver conforme al modelo de acceso, no creando políticas genéricas.
6. **Tricentric:** los advisors señalan cuatro funciones `SECURITY DEFINER` ejecutables por usuarios autenticados y protección de contraseñas filtradas desactivada. Revisión de cuerpos/permisos pendiente.
7. **Bunker remoto:** el proyecto Supabase `Bunker` está INACTIVE y su base no pudo listarse. No se encontró un enlace local equivalente en el repo `CHALAMANDRA-S-BUNKER`; no restaurar por coincidencia de nombre.

### Prioridad actual

- **P0 — Seguridad de datos:** revisar autorización/ownership de las funciones Tricentric señaladas y definir políticas correctas para las tablas MAGIS sin políticas.
- **P0 — Frontera de productos:** confirmar si Interactive y SystemDecode deben compartir una base o requerir separación por dominio y datos transaccionales.
- **P1 — Integración pública:** documentar por qué Interactive usa un alias más antiguo que el último deployment de producción y mantenerlo estable hasta decisión fundada.
- **P1 — Inventario operativo:** aclarar el proyecto `interactive-decox-dag1` y el Supabase Bunker inactivo.
- **P2 — Seguridad de cuentas:** evaluar y habilitar, con la autorización correspondiente, protección frente a contraseñas filtradas.

### Límites

Toda esta actualización fue de metadatos/configuración y documentación. No se leyeron archivos `.env`, no se pidieron variables descifradas, no se ejecutó SQL ni se modificaron RLS, funciones, secretos, DNS, aliases, pagos o despliegues. No implica aprobación de producción.
