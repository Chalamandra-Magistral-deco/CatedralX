# Inventario técnico complementario — DecoX
**Versión:** 0.2
**Fecha:** 2026-10-24
**Fuente:** inspección de solo lectura en chalamandra-vm, API autenticada de Vercel y comprobaciones HTTP GET de producción.
**Alcance:** no se modificó código de producto, configuración de hosting, DNS, variables de entorno, pagos ni formularios. Este documento amplía v0.1; no sustituye el Mapa Maestro.

## 1. Corrección de metadatos Git
CatedralX-verify sí es un worktree Git válido. Su .git es un archivo que apunta a CatedralX/.git/worktrees/CatedralX-verify, como corresponde a un linked worktree. Está en HEAD separado ec92163, con numerosos cambios modificados y no rastreados. No tratarlo como carpeta sin Git ni asumir que sus cambios están validados.

## 2. Mapa técnico observado por repositorio

| Proyecto | Evidencia local | Dependencias / arquitectura declaradas | Riesgo o siguiente verificación |
|---|---|---|---|
| CHALAMANDRA-MAGISTRAL | HEAD 0b65114; cambios locales en CSS, metodologias.html y vercel.json | Sitio HTML/CSS/JS; build Tailwind; configuración Vercel; README declara Formspree y GTM | El script test falla intencionalmente con “no test specified”; no usarlo como suite válida. Ejecutar build aislado y comprobar formulario/eventos sin tocar producción. |
| INTERACTIVE-DECOX | HEAD 990241d; rama feat/discovery-private-portal-20261019; árbol limpio según git status | React/Vite, Gemini, Supabase, funciones api/ai.ts, api/contact.ts, api/verify-payment.ts, api/stripe-webhook.ts; Stripe/Resend descritos en README | Las dependencias no prueban que los secretos estén configurados, que los webhooks funcionen ni que haya pagos correctos. Verificar checkout de prueba, webhook y persistencia en entorno de pruebas. |
| SYSTEM_DECODE_MAGIS-v12.0-FLUX | HEAD a2a9be5; rama main; árbol limpio | React 19/TypeScript/Vite; Supabase Auth/datos/créditos; funciones server-side para Gemini/Veo; Stripe opcional; Vercel | Verificar configuración de entorno, políticas de acceso, créditos y pagos de prueba; no exponer valores secretos. |
| Tricentric-Integration | HEAD 322467f; rama main; árbol limpio | README describe Supabase Auth, Edge Function srap-analysis, Gemini y PostgreSQL RPC | Revisar políticas/RLS, límites diarios y pruebas de flujo antes de afirmar operación de extremo a extremo. |
| Chalamandra-Triada | HEAD d3d9116; rama main; árbol limpio | React, MSAL/Entra, Gemini, Upstash Redis; Vercel config | Confirmar configuración de identidad, límites, almacenamiento y manejo de errores en runtime. |
| Or-culo-Chalamandra | HEAD e602745; rama main; árbol limpio | README identifica origen AI Studio; app Vite/React y SDK Gemini | Alinear artefacto publicado con repo y verificar proxy/servidor para API. Nunca incluir claves en el bundle del navegador. |
| Pirinola- | HEAD 89b1bba; rama main; existen index.html.bak e index.html.broken no rastreados | React/Vite; configuración Vercel | Preservar ambos archivos; compararlos con el archivo activo antes de decidir si son respaldos o artefactos rotos. |
| Blueprint-Chalamandra---SRAP-Barrio-Edition | HEAD 6dbce12; rama feat/ads-txt-monetization; cambios en ads.txt, demo/index.html y public/ads.txt | Demo estática; README declara que api/checkout.js responde 501 y no procesa pagos | No presentarlo como checkout operativo. Revisar cambios locales y evitar duplicidad de ads.txt; primero confirmar que el producto y el flujo de pago funcionan. |
| CHALAMANDRA-S-BUNKER | HEAD dfca957; rama main; árbol limpio | README describe app de AI Studio; Express/WS/React/Gemini en package.json | Confirmar despliegue, backend y configuración real; no inferir que la app de AI Studio se sincroniza automáticamente con Git. |
| CHMADEX-DIAL | HEAD c42e271; rama main; árbol limpio | README describe extensión de Chrome; React/Vite/Gemini | Clasificar como extensión/artefacto local hasta verificar publicación y usuarios; no asumir que es un sitio web publicado. |
| OMNI-CHALAMANDRA-decox | HEAD 9efe934; rama fix/omni-production-hardening; app/index.html modificado | README describe sistema multiagente gobernado; Vercel reescribe la raíz a app/index.html | Cambio local pendiente: preservar; revisar el diff y las pruebas antes de cualquier publicación. |

## 3. Estado de CatedralX y agents
- CatedralX: HEAD 428253d, rama feat/financial-motor-deterministic; modificaciones locales y archivos no rastreados. No limpiar ni integrar automáticamente.
- CatedralX-verify: HEAD ec92163, detached HEAD; cambios locales sustanciales y documentos de auditoría nuevos. Es aislado a nivel de checkout, pero comparte el repositorio Git mediante el worktree.
- agents: HEAD 0d2fe84, rama fix/tool-call-context-budget; modificaciones locales en core/decomposer.py, core/executor.py y pruebas.
- El puente catedralx_reasoning está documentado en el código de agents. Su configuración efectiva y el resultado actual de integración no quedan probados solo por la presencia del código.

## 4. Conclusiones técnicas previas
1. Hay varios stacks diferentes: sitios estáticos, SPA React/Vite, funciones serverless, Supabase, Microsoft Entra/Upstash y herramientas/extensiones. No procede imponer una migración uniforme sin inventario de runtime.
2. README y archivos de configuración prueban arquitectura declarada, no credenciales configuradas, despliegue actual, seguridad efectiva ni pagos exitosos.
3. Los cambios locales deben permanecer intactos; toda validación de build/tests que requiera dependencias se hará en entorno aislado y sin despliegue.
4. Una respuesta HTTP 200 no identifica por sí sola qué commit publica un dominio. Para esa relación se requiere evidencia del proveedor de hosting.
5. La prioridad comercial es validar un solo flujo de captación del portal y medir contacto cualificado. El checkout del Blueprint está explícitamente incompleto y no debe ser el primer flujo de venta hasta implementarse y probarse.

## 5. Evidencia de Vercel: dominio → proyecto → repositorio → despliegue de producción
Consulta de solo lectura el 2026-10-24. Los SHA se muestran abreviados aquí; el proveedor devolvió el SHA completo y el estado READY.

| Dominio o URL de proyecto | Proyecto de Vercel | Repositorio Git vinculado | Despliegue de producción observado |
|---|---|---|---|
| chalamandramagistral.com; www.chalamandramagistral.com | chalamandra-magistral-hlxd | Chalamandra-Magistral-deco/CHALAMANDRA-MAGISTRAL | READY; main; 0b6511417c99; 2026-10-24 07:31 UTC. El dominio raíz redirige a www con 301. |
| interactive.chalamandramagistral.com | interactive-decox | Chalamandra-Magistral-deco/INTERACTIVE-DECOX | El alias del dominio está asignado al deployment READY de SHA a231b911390a (ID dpl_CoETjgfuU5bdG1YjEwbNLK8SUUFV). El proyecto también tiene un despliegue production más reciente, SHA 1a666fa23862, pero su lista de aliases no incluye el dominio personalizado. |
| tricentric.chalamandramagistral.com | tricentric-integration | Chalamandra-Magistral-deco/Tricentric-Integration | READY; main; 322467fae6b3; 2026-10-17 14:06 UTC. |
| triada.chalamandramagistral.com | chalamandra-triada | Chalamandra-Magistral-deco/Chalamandra-Triada | READY; main; d3d9116eb681; 2026-10-17 01:47 UTC. |
| systemdecode.chalamandramagistral.com | system-decode-magis-v12-0-flux | Chalamandra-Magistral-deco/SYSTEM_DECODE_MAGIS-v12.0-FLUX | READY; main; a2a9be56d77d; 2026-10-16 20:15 UTC. |
| oraculo.chalamandramagistral.com | or-culo-chalamandra | Chalamandra-Magistral-deco/Or-culo-Chalamandra | READY; main; e6027459d1d6; 2026-10-17 03:29 UTC. |
| pirinola.chalamandramagistral.com | pirinola-neural | Chalamandra-Magistral-deco/Pirinola- | READY; main; 89b1bba44d33; 2026-10-17 01:13 UTC. |
| srap-barrio.vercel.app | srap-barrio | Chalamandra-Magistral-deco/Blueprint-Chalamandra---SRAP-Barrio-Edition | READY; feat/real-money-flow; cee51dd26749; 2026-10-06 10:32 UTC. No se observó dominio propio vinculado al proyecto. |
| Proyecto Vercel histórico sin repositorio identificado | — | No se obtuvo repositorio asociado; la consulta no devolvió deployments. Sin dominio propio. |

Todos los dominios personalizados listados en la tabla de productos aparecieron como verificados en la configuración del proyecto. Esto acredita la asociación en Vercel, no toda la resolución DNS externa ni el funcionamiento del backend.

### Hallazgo importante: dos proyectos de Interactive
Vercel tiene dos proyectos que apuntan al mismo repositorio y al mismo commit reciente de main:
- interactive-decox: tiene el dominio personalizado interactive.chalamandramagistral.com.
- interactive-decox-dag1: no tiene dominio personalizado listado; aun así tiene despliegue READY de producción en su URL vercel.app, con el mismo SHA 1a666fa23862.

Esto es un candidato a duplicidad de infraestructura, no autorización para eliminarlo. Antes de decidir, revisar uso, variables/configuración no secreta y logs de ambos proyectos. No se tocó ninguno.

### Diferencia entre main publicado y cambios locales

**Verificación directa de aliases (Vercel, 2026-10-24):** la consulta del dominio interactive.chalamandramagistral.com resuelve en Vercel al deployment dpl_CoETjgfuU5bdG1YjEwbNLK8SUUFV (main, SHA a231b911390a418c145538ed2d6a6c28c768ecff, READY). La consulta de aliases para el deployment reciente dpl_2GyDWbn1s8sJ5tKbZSrSZhvT1Qek (SHA 1a666fa...) devuelve solo aliases *.vercel.app, sin el dominio personalizado. Por tanto, “deployment más reciente del proyecto” y “deployment al que está asignado el dominio” no son lo mismo en Interactive.
- Portal: el despliegue actual apunta a 0b65114, con mensaje “revert: restore site to state before quality audit changes”. Los cambios locales mencionados para CSS, metodologias.html y vercel.json no deben asumirse publicados.
- Interactive tiene tres estados distintos: el checkout local está en HEAD 990241d; el alias público está asignado al deployment de main SHA a231b911390a (ID dpl_CoETjgfuU5bdG1YjEwbNLK8SUUFV); el proyecto tiene además un despliegue production más reciente en SHA 1a666fa23862 sin el dominio personalizado. No sincronizar ni desplegar hasta comparar las tres versiones.
- Blueprint SRAP: el checkout local estaba en HEAD 6dbce12 y con cambios locales; producción publica otro SHA, cee51dd26749, en feat/real-money-flow. El README local declara que api/checkout.js responde 501; el estado del checkout desplegado requiere inspección de código/endpoint antes de ofrecerlo como pago real.
- Tricentric, Triada, SystemDecode, Oráculo y Pirinola tienen despliegues READY de producción vinculados a SHA identificables. Esto no prueba autenticación, APIs, créditos o flujos internos operativos.

## 6. Prueba de accesibilidad del flujo comercial del portal
Comprobaciones HTTP GET hechas desde la VM el 2026-10-24:
- https://chalamandramagistral.com/ → 200; URL final canónica: https://www.chalamandramagistral.com/
- https://chalamandramagistral.com/ofertas.html → 200
- https://chalamandramagistral.com/contact.html?interes=mapa-srap → 200
- https://chalamandramagistral.com/thanks.html → 200
- https://interactive.chalamandramagistral.com/ → 200
- https://tricentric.chalamandramagistral.com/ → 200
- https://systemdecode.chalamandramagistral.com/ → 200

### Oferta → contacto
La página de ofertas contiene enlaces a contact.html con estos intereses:
- mapa-srap
- consultoria
- taller-srap
- arquitectura-sistemas

La página de contacto usa un formulario que envía por POST a Formspree. El script desplegado assets/form-decox.js obtuvo HTTP 200 y su SHA-256 coincide exactamente con el archivo local: bdd7c6261e8e252b875e8097bd63b85843380542f67691b4ee463053490b59fd. El script añade atribución (lead_source, lead_offer, origen y UTM), intenta emitir el evento de analítica generate_lead después de recibir respuesta exitosa y redirige a /thanks.html. El código implementa este comportamiento.

**No se envió un lead real ni un POST de prueba.** Por tanto, no está demostrado que Formspree acepte el formulario, llegue el correo, la analítica registre el evento o el seguimiento comercial ocurra. No usar HTTP 200 de la página de gracias como prueba de conversión: la ruta estática puede abrirse sin enviar formulario.

## 7. Prioridad operativa siguiente
1. Validar el formulario en una prueba autorizada y controlada, sin inventar datos de cliente y sin convertirlo en un contacto comercial falso. Confirmar recepción de correo, atribución y evento con consentimiento aplicable.
2. Registrar un procedimiento de seguimiento: responsable, respuesta inicial, estado de oportunidad y resultado. No se observó evidencia de CRM/registro centralizado en esta consulta.
3. Mantener como primer flujo monetizable una oferta de servicio con contacto/propuesta comercial, mientras el checkout de SRAP no esté demostrado como funcional.
4. Resolver la duplicidad potencial de interactive-decox-dag1 solo tras verificar si tiene uso; no borrar ni cambiar dominios.
5. Después, elegir un producto y probar pago en modo test, con webhook y entrega verificable, antes de activar cobros reales.

## 8. Límites de esta auditoría
- Vercel fue consultado en modo de lectura; no se crearon proyectos ni despliegues, no se modificaron dominios ni DNS y no se leyeron valores de variables de entorno.
- Las solicitudes HTTP realizadas fueron GET. No se enviaron formularios, no se generaron leads falsos y no se iniciaron pagos.
- Los estados READY, la configuración de dominios y los hashes documentan evidencia concreta, pero no reemplazan pruebas funcionales de APIs, autenticación, pagos o entrega de producto.
- Los cambios no rastreados y modificaciones locales de CatedralX, agents, Blueprint, OMNI y otros repositorios deben preservarse hasta revisión explícita.


## 9. Confirmación directa de alias por deployment

Consulta de solo lectura a Vercel realizada el 2026-10-24. Se consultó cada deployment READY de producción y su lista de aliases, no solo la lista de dominios del proyecto.

| Alias observado | Deployment al que está asignado | Rama / SHA | Resultado |
|---|---|---|---|
| www.chalamandramagistral.com | dpl_91bVYm73c5NH7LFByL11yAdbuqHC | main / 0b6511417c99 | Alias presente; apex chalamandramagistral.com redirige a www. |
| interactive.chalamandramagistral.com | dpl_CoETjgfuU5bdG1YjEwbNLK8SUUFV | main / a231b911390a | Alias presente en este deployment READY. |
| tricentric.chalamandramagistral.com | dpl_ohUZ1DXQaq2X6MYALMtRAqS2QbR2 | main / 322467fae6b3 | Alias presente. El alias tricentric-integration-lyart.vercel.app redirige al dominio personalizado. |
| triada.chalamandramagistral.com | dpl_41LbXifeZHtc8xwMgjNyqFoPcCj4 | main / d3d9116eb681 | Alias presente. |
| systemdecode.chalamandramagistral.com | dpl_9k4SS7S5a2KW1ubCegnVAwjWiK8K | main / a2a9be56d77d | Alias presente. El alias system-decode-magis-v12-0-flux-six.vercel.app redirige al dominio personalizado. |
| oraculo.chalamandramagistral.com | dpl_HUjw8qRjgEVxqqBguJQX5fBaJgRA | main / e6027459d1d6 | Alias presente. |
| pirinola.chalamandramagistral.com | dpl_C8oH8hNMcb1ZtyxEc3KmmcpSEbLh | main / 89b1bba44d33 | Alias presente. |
| srap-barrio.vercel.app | dpl_7YGcjDgihGjoewzvVNofpkSd2vBW | feat/real-money-flow / cee51dd26749 | Alias presente; no apareció un dominio personalizado chalamandramagistral.com para este producto. |

### Resolución específica de Interactive

La consulta directa de interactive.chalamandramagistral.com devolvió el deployment dpl_CoETjgfuU5bdG1YjEwbNLK8SUUFV, commit a231b911390a418c145538ed2d6a6c28c768ecff, estado READY. La lista de aliases del deployment más reciente de interactive-decox, dpl_2GyDWbn1s8sJ5tKbZSrSZhvT1Qek (commit 1a666fa238623d308b220ff0a63255b3cf167f52), incluye solamente los aliases vercel.app; no incluye interactive.chalamandramagistral.com.

Por tanto hay tres referencias diferentes que no deben mezclarse:
1. Checkout local: INTERACTIVE-DECOX, HEAD 990241d, rama de feature.
2. Deployment al que está asignado el dominio oficial: main, SHA a231b911, READY.
3. Deployment más reciente de producción del proyecto interactive-decox y deployment del proyecto separado interactive-decox-dag1: main, SHA 1a666fa, READY, sin el dominio oficial en su lista de aliases.

**Decisión:** no se movió el alias. El ajuste cambia qué versión ven los usuarios y requiere autorización explícita y prueba de ruta previa a cualquier cambio.

## 10. Comparación HTTP de la ruta de descubrimiento de Interactive

Solicitudes GET realizadas desde la VM el 2026-10-24; no se enviaron formularios ni se modificó el alias.

| URL consultada | HTTP / tamaño de HTML | Bundle cargado |
|---|---|---|
| https://interactive.chalamandramagistral.com/sesion-descubrimiento | 200 / 7,393 bytes | /assets/index-B1YFHBQm.js |
| https://interactive-decox-avfky1r8b-chalamandra-magistral-s-projects.vercel.app/sesion-descubrimiento | 200 / 7,393 bytes | /assets/index-B1YFHBQm.js |
| https://interactive-decox-raw8sen15-chalamandra-magistral-s-projects.vercel.app/sesion-descubrimiento | 200 / 11,277 bytes | /assets/index-Cq089rGF.js |

### Verificación de bundle
- Bundle servido por el dominio oficial: 50,465 bytes; SHA-256 ca227bb608042ada842407cf2b6a4dd8e677d18afbc8ce585b7cd83d0c935a96.
- Bundle del deployment más reciente: 63,758 bytes; SHA-256 c8267899d8de3d674de5b284a9a65ab91975ecb046ce75d907b9853ef02a440b.
- La cadena literal sesion-descubrimiento no aparece en el bundle público ni en el deployment anterior; sí aparece en el bundle del deployment más reciente.
- La cadena visible “Sesión de Descubrimiento” aparece en ambos bundles. Por tanto, buscar solo el título no basta para comprobar que la ruta nueva está integrada en el router.

### Conclusión de la prueba
El hecho de que las tres URLs devuelvan HTTP 200 no demuestra que la página independiente se esté renderizando. La evidencia combinada de alias de Vercel, SHA de Git y bundle servido indica que el dominio oficial sigue sirviendo la versión anterior, mientras que el deployment más reciente contiene el enrutamiento nuevo. La diferencia es material para usuarios y navegación comercial.

**Siguiente paso seguro:** antes de cambiar el alias, ejecutar pruebas de aceptación del deployment nuevo (ruta raíz, /sesion-descubrimiento, navegación hacia el formulario corporativo, consola/red y pruebas automatizadas disponibles). La decisión de mover el dominio a ese deployment requiere autorización explícita. No se cambió el alias durante esta auditoría.


## 11. Contraste remoto de Supabase y permisos — actualización 2026-10-24

Esta sección amplía la comprobación anterior, que no había podido recuperar el catálogo remoto. En esta pasada las llamadas de metadatos y las consultas SELECT de catálogos PostgreSQL sí respondieron. **Las conclusiones antiguas de “esquema remoto no disponible” quedan supersedidas por los hallazgos concretos de esta sección.** No se consultaron filas de negocio ni se ejecutaron escrituras.

### 11.1 Proyectos remotos y vínculo local observado

| Proyecto | Ref | Estado remoto | Evidencia local de vínculo |
|---|---|---|---|
| `tricentric-production` | `xgupisrhrihiymmwdlqg` | `ACTIVE_HEALTHY`, PostgreSQL 17 | `Tricentric-Integration/supabase/.temp/project-ref` y `linked-project.json` contienen este ref. |
| `magis-commercial-production` | `qusrfuwduxpuidowofgc` | `ACTIVE_HEALTHY`, PostgreSQL 17 | `SYSTEM_DECODE_MAGIS-v12.0-FLUX/supabase/.temp/project-ref` y `linked-project.json` contienen este ref. También `INTERACTIVE-DECOX/supabase/.temp/linked-project.json` contiene exactamente el mismo ref. |
| `Bunker` | `ymajkowdxhfasquhmxtj` | `INACTIVE`, PostgreSQL 17 | No se encontró un archivo de vínculo equivalente bajo `CHALAMANDRA-S-BUNKER`; no asumir que sea el mismo sistema por su nombre. El catálogo remoto no fue accesible en la consulta realizada. |

**Bloqueo de arquitectura:** los archivos locales de Interactive y SystemDecode apuntan al mismo proyecto Supabase comercial. Esto demuestra el vínculo de los checkouts locales, no que todos los entornos de despliegue estén usando esas mismas credenciales. Confirmar si comparten intencionalmente identidad, tablas y transacciones antes de separar o migrar algo. No se modificó la configuración local.

### 11.2 Edge Functions remotas

| Proyecto / función | Estado / versión | `verify_jwt` en plataforma | Control observado en fuente desplegada |
|---|---|---|---|
| `tricentric-production / srap-analysis` | ACTIVE / v42 | false | Usa `withSupabase({ auth: "user" })`, exige `ctx.userClaims.id`, aplica origen permitido, valida payload y consume cuota antes de invocar Gemini. No declarar que la bandera por sí sola demuestra acceso anónimo. |
| `magis-commercial-production / mcp` | ACTIVE / v1 | false | Encadena `withOAuthProtectedResource` y `withSupabase({ auth: "user" })`; registra actualmente una herramienta `whoami` que devuelve las claims verificadas del usuario de la sesión. |

La comprobación anterior de código estático que indicaba “no se encontró rate limiting explícito” permanece como pendiente: Tricentric limita por cuota diaria del lado servidor; el alcance y el riesgo de abuso deben comprobarse con pruebas controladas. No se envió una petición sin token ni se realizó una prueba de abuso en producción.

### 11.3 RLS y privilegios visibles — Tricentric

Las seis tablas públicas observadas tienen RLS habilitado. Las políticas visibles son:
- `user_profiles`, `evaluations`, `tricentric_practices` y `user_achievements`: SELECT para `authenticated` limitado por `auth.uid()) al registro del usuario.
- `achievements`: SELECT para usuarios autenticados.
- `ai_usage_daily`: política de denegación para operaciones directas de `anon` y `authenticated`, consistente con administración del lado servidor.

El advisor marcó cuatro firmas `SECURITY DEFINER`: `complete_evaluation`, dos sobrecargas de `complete_tricentric_practice` y `ensure_user_profile`. La inspección adicional de definiciones y ACL mostró:
- EXECUTE para `authenticated` y `service_role`, no para `anon`.
- `search_path` vacío en esas definiciones.
- Las firmas inspeccionadas comprueban `auth.uid()` y limitan las escrituras a ese usuario; la sobrecarga simple delega en la firma completa.
- Esto reduce el riesgo aparente de ejecución anónima, pero no reemplaza pruebas negativas con dos cuentas de prueba ni la revisión de funciones auxiliares llamadas por estas RPC.

Permanece el aviso de Supabase Auth: protección frente a contraseñas filtradas desactivada.

### 11.4 RLS y privilegios visibles — MAGIS comercial

Las ocho tablas públicas observadas tienen RLS habilitado. En las tablas `profiles`, `user_plans`, `credit_accounts` y `credit_ledger`, el SELECT concedido a `authenticated` tiene una política que filtra por el usuario actual; `plans` permite a usuarios autenticados leer planes activos.

Para las tablas `operation_feedback`, `purchases` y `video_operations`:
- RLS está habilitado y no se observaron políticas.
- Las comprobaciones de privilegios mostraron que ni `anon` ni `authenticated` tienen privilegio SELECT; `service_role` sí lo tiene.
- Por tanto, el acceso directo de lectura de clientes está fail-closed en las tablas observadas. Aún debe revisarse cada endpoint server-side para asegurar que valida identidad/propiedad y que el uso de service-role tiene un alcance limitado.

No se deben crear políticas genéricas solo para quitar el aviso del advisor. Primero establecer qué rutas deben escribir/leer esas tablas y si la operación es exclusivamente server-side. También permanece desactivada la protección contra contraseñas filtradas en Supabase Auth.

Referencias del advisor:
- [Funciones SECURITY DEFINER ejecutables por usuarios autenticados](https://supabase.com/docs/guides/database/database-linter?lint=0029_authenticated_security_definer_function_executable)
- [RLS habilitado sin políticas](https://supabase.com/docs/guides/database/database-linter?lint=0008_rls_enabled_no_policy)
- [Protección contra contraseñas filtradas](https://supabase.com/docs/guides/auth/password-security#password-strength-and-leaked-password-protection)

### 11.5 Límites y decisiones siguientes

- Consultas hechas: metadatos de proyectos/funciones, `pg_policies`, catálogo de funciones y ACLs/privilegios. No se consultaron datos de usuarios, compras, créditos o evaluaciones.
- No se modificó SQL, RLS, permisos, funciones, migraciones, secretos ni settings; tampoco se probó una sesión real ni una compra.
- Próxima prioridad: revisar el contrato de aislamiento Interactive/SystemDecode y hacer pruebas negativas con identidades sintéticas; después revisar los RPC/handlers señalados y el acceso de servidor a las tablas sin políticas. No ejecutar cambios en producción sin plan y autorización.
