# Inventario técnico complementario — DecoX
**Versión:** 0.1  
**Fecha:** 2026-10-24  
**Fuente:** inspección de solo lectura en `chalamandra-vm`; archivos de configuración, README, `git rev-parse` y `git status`.  
**Alcance:** no se modificó código, configuración, hosting, DNS ni datos de producto.

## 1. Corrección de metadatos Git
`CatedralX-verify` **sí es un worktree Git válido**. Su `.git` es un archivo que apunta a `CatedralX/.git/worktrees/CatedralX-verify`, como corresponde a un linked worktree. Está en HEAD separado `ec92163`, con numerosos cambios modificados y no rastreados. No tratarlo como carpeta sin Git ni asumir que sus cambios están validados.

## 2. Mapa técnico observado por repositorio

| Proyecto | Evidencia local | Dependencias / arquitectura declaradas | Riesgo o siguiente verificación |
|---|---|---|---|
| `CHALAMANDRA-MAGISTRAL` | HEAD `0b65114`; cambios locales en CSS, `metodologias.html` y `vercel.json` | Sitio HTML/CSS/JS; build Tailwind; configuración Vercel; README declara Formspree y GTM | El script `test` falla intencionalmente con “no test specified”; no usarlo como suite válida. Ejecutar build aislado y comprobar formulario/eventos sin tocar producción. |
| `INTERACTIVE-DECOX` | HEAD `990241d`; rama `feat/discovery-private-portal-20261019`; árbol limpio según `git status` | React/Vite, Gemini, Supabase, funciones `api/ai.ts`, `api/contact.ts`, `api/verify-payment.ts`, `api/stripe-webhook.ts`; Stripe/Resend descritos en README | Las dependencias en el repositorio no prueban que los secretos estén configurados, que los webhooks funcionen ni que haya pagos correctos. Verificar checkout de prueba, webhook y persistencia en entorno de pruebas. |
| `SYSTEM_DECODE_MAGIS-v12.0-FLUX` | HEAD `a2a9be5`; rama `main`; árbol limpio | React 19/TypeScript/Vite; Supabase Auth/datos/créditos; funciones server-side para Gemini/Veo; Stripe opcional; Vercel | Verificar configuración de entorno, políticas de acceso, créditos y pagos de prueba; no exponer valores secretos. |
| `Tricentric-Integration` | HEAD `322467f`; rama `main`; árbol limpio | README describe Supabase Auth, Edge Function `srap-analysis`, Gemini y PostgreSQL RPC | Revisar políticas/RLS, límites diarios y pruebas de flujo antes de afirmar operación de extremo a extremo. |
| `Chalamandra-Triada` | HEAD `d3d9116`; rama `main`; árbol limpio | React, MSAL/Entra, Gemini, Upstash Redis; Vercel config | Confirmar configuración de identidad, límites, almacenamiento y manejo de errores en runtime. |
| `Or-culo-Chalamandra` | HEAD `e602745`; rama `main`; árbol limpio | README identifica origen AI Studio; app Vite/React y SDK Gemini | Alinear artefacto publicado con repo y verificar proxy/servidor para API. Nunca incluir claves en el bundle del navegador. |
| `Pirinola-` | HEAD `89b1bba`; rama `main`; existen `index.html.bak` y `index.html.broken` no rastreados | React/Vite; configuración Vercel | Preservar ambos archivos; compararlos con el archivo activo antes de decidir si son respaldos o artefactos rotos. |
| `Blueprint-Chalamandra---SRAP-Barrio-Edition` | HEAD `6dbce12`; rama `feat/ads-txt-monetization`; cambios en `ads.txt`, `demo/index.html` y `public/ads.txt` | Demo estática; README declara que `api/checkout.js` responde 501 y no procesa pagos | **No presentarlo como checkout operativo.** Revisar cambios locales y evitar duplicidad de `ads.txt`; primero confirmar que el producto y el flujo de pago funcionan. |
| `CHALAMANDRA-S-BUNKER` | HEAD `dfca957`; rama `main`; árbol limpio | README describe app de AI Studio; Express/WS/React/Gemini en package.json | Confirmar despliegue, backend y configuración real; no inferir que la app de AI Studio se sincroniza automáticamente con Git. |
| `CHMADEX-DIAL` | HEAD `c42e271`; rama `main`; árbol limpio | README describe extensión de Chrome; React/Vite/Gemini | Clasificar como extensión/artefacto local hasta verificar publicación y usuarios; no asumir que es un sitio web publicado. |
| `OMNI-CHALAMANDRA-decox` | HEAD `9efe934`; rama `fix/omni-production-hardening`; `app/index.html` modificado | README describe sistema multiagente gobernado; Vercel reescribe la raíz a `app/index.html` | Cambio local pendiente: preservar; revisar el diff y las pruebas antes de cualquier publicación. |

## 3. Estado de CatedralX y agents
- `CatedralX`: HEAD `428253d`, rama `feat/financial-motor-deterministic`; modificaciones locales y archivos no rastreados. No limpiar ni integrar automáticamente.
- `CatedralX-verify`: HEAD `ec92163`, detached HEAD; cambios locales sustanciales y documentos de auditoría nuevos. Es aislado a nivel de checkout, pero comparte el repositorio Git mediante el worktree.
- `agents`: HEAD `0d2fe84`, rama `fix/tool-call-context-budget`; modificaciones locales en `core/decomposer.py`, `core/executor.py` y pruebas.
- El puente `catedralx_reasoning` está documentado en el código de agents. Su configuración efectiva y el resultado actual de integración no quedan probados solo por la presencia del código.

## 4. Conclusiones verificables
1. Hay varios stacks diferentes: sitios estáticos, SPA React/Vite, funciones serverless, Supabase, Microsoft Entra/Upstash y herramientas/extensiones. No procede imponer una migración uniforme sin inventario de runtime.
2. README y archivos de configuración prueban arquitectura declarada, no credenciales configuradas, despliegue actual, seguridad efectiva ni pagos exitosos.
3. Los cambios locales deben permanecer intactos; toda validación de build/tests que requiera dependencias se hará en entorno aislado y sin despliegue.
4. La respuesta HTTP 200 de un dominio no identifica qué commit lo publica. El vínculo dominio → proyecto → despliegue → commit sigue pendiente de evidencia del proveedor de hosting.
5. La prioridad comercial es validar un solo flujo de captación del portal y medir contacto cualificado. El checkout del Blueprint está explícitamente incompleto y no debe ser el primer flujo de venta hasta implementarse y probarse.

## 5. Siguiente secuencia de solo lectura
1. Recuperar metadatos de Vercel/Firebase para mapear cada dominio a proyecto y deployment SHA.
2. Inspeccionar diffs de los worktrees/repositorios con cambios locales, sin aplicar ni descartar ninguno.
3. Validar builds/tests en clones temporales o worktrees adicionales, aislados del estado de trabajo actual.
4. Probar los recorridos de contacto/checkout en modo test y documentar evidencia por paso.
5. Actualizar el Mapa Maestro solo con relaciones que tengan fuente, fecha y prueba explícitas.


## 6. Backend remoto — comprobación Supabase (solo lectura, 2026-10-24)

Se consultaron los metadatos de proyectos, tablas, Edge Functions y avisos de seguridad mediante la conexión autorizada de Supabase. No se ejecutó SQL, no se modificaron políticas, no se cambiaron secretos y no se consultaron filas de usuarios.

| Proyecto remoto | Estado observado | Enlace desde archivos locales | Evidencia de backend | Riesgos / siguiente control |
|---|---|---|---|---|
| `tricentric-production` (`xgupisrhrihiymmwdlqg`) | ACTIVE_HEALTHY; PostgreSQL 17 | `Tricentric-Integration/supabase/.temp/project-ref` y `linked-project.json` coinciden con el ref remoto | 6 tablas públicas listadas con RLS habilitado; Edge Function `srap-analysis` activa v42 | La configuración de plataforma informa `verify_jwt=false`, pero el código desplegado usa `withSupabase({ auth: "user" })` y exige claims del usuario. Revisar explícitamente el límite de autenticación, además de los avisos de SECURITY DEFINER y protección de contraseñas filtradas. |
| `magis-commercial-production` (`qusrfuwduxpuidowofgc`) | ACTIVE_HEALTHY; PostgreSQL 17 | Tanto `SYSTEM_DECODE_MAGIS-v12.0-FLUX/supabase/.temp/project-ref` como `INTERACTIVE-DECOX/supabase/.temp/linked-project.json` apuntan al mismo ref | 8 tablas públicas listadas con RLS habilitado; Edge Function `mcp` activa v1 | **Dos repositorios locales están vinculados al mismo proyecto remoto de Supabase.** Confirmar si compartir base de datos es deliberado antes de considerar aislamiento de datos entre Interactive y SystemDecode. No se hizo ninguna migración. |
| `Bunker` (`ymajkowdxhfasquhmxtj`) | INACTIVE; PostgreSQL 17 | No se encontró un enlace local equivalente en el repo `CHALAMANDRA-S-BUNKER` durante esta revisión | No se listaron Edge Functions; el inventario de tablas falló por inaccesibilidad de la base | No activar ni restaurar automáticamente. Confirmar propietario, finalidad y si el proyecto es legado antes de intervenir. |

### 6.1 Avisos de seguridad observados

**Tricentric**
- El advisor marcó cuatro funciones `SECURITY DEFINER` ejecutables por `authenticated`: `complete_evaluation`, dos sobrecargas de `complete_tricentric_practice` y `ensure_user_profile`. Es un hallazgo que requiere revisar cuerpos, controles de pertenencia y grants; la alerta por sí sola no prueba explotación.
- Supabase Auth tiene desactivada la protección contra contraseñas conocidas como filtradas.

**MAGIS comercial**
- El advisor informó RLS habilitado sin políticas para `operation_feedback`, `purchases` y `video_operations`. Esto normalmente bloquea el acceso directo mediante roles expuestos, pero podría también impedir funciones legítimas. Revisar los caminos previstos de acceso y permisos antes de crear políticas.
- Supabase Auth tiene desactivada la protección contra contraseñas filtradas.

Referencias oficiales de remediación del advisor:
- [SECURITY DEFINER ejecutable por usuarios autenticados](https://supabase.com/docs/guides/database/database-linter?lint=0029_authenticated_security_definer_function_executable)
- [RLS habilitado sin políticas](https://supabase.com/docs/guides/database/database-linter?lint=0008_rls_enabled_no_policy)
- [Protección contra contraseñas filtradas](https://supabase.com/docs/guides/auth/password-security#password-strength-and-leaked-password-protection)

### 6.2 Límites de la comprobación

- Los nombres de tablas, estado RLS y avisos vienen de metadatos/advisors; no se probaron formularios, políticas mediante sesiones reales ni flujos de compra.
- La configuración de plataforma `verify_jwt=false` no basta para concluir que el código carezca de autenticación; se debe evaluar la capa de middleware y los claims. Tampoco sustituye pruebas de acceso por rol.
- No se leyeron valores de archivos `.env`, no se solicitaron variables descifradas desde Vercel y no se imprimieron credenciales.
- No se realizaron cambios de producción, SQL, políticas, dominios ni despliegues.

## 7. Dominio → proyecto → deployment: contraste de Vercel (solo lectura, 2026-10-24)

Se contrastaron los aliases y metadatos actuales de Vercel con el inventario previo.

| Dominio / activo | Proyecto | Deployment asignado al alias | Commit y nota |
|---|---|---|---|
| `chalamandramagistral.com` → 301 a `www`; `www.chalamandramagistral.com` | `chalamandra-magistral-hlxd` | `dpl_91bVYm73c5NH7LFByL11yAdbuqHC` — READY | `CHALAMANDRA-MAGISTRAL`, `main`, `0b6511417c99166a4997e4d9c974a3e7bde947e2` |
| `interactive.chalamandramagistral.com` | `interactive-decox` | `dpl_CoETjgfuU5bdG1YjEwbNLK8SUUFV` — READY | `INTERACTIVE-DECOX`, `main`, `a231b911390a418c145538ed2d6a6c28c768ecff`. El deployment más reciente de producción que lista el proyecto es distinto (`1a666fa238623d308b220ff0a63255b3cf167f52`). El alias continúa asignado explícitamente a la versión anterior; no se reasignó. |
| `tricentric.chalamandramagistral.com` | `tricentric-integration` | `dpl_ohUZ1DXQaq2X6MYALMtRAqS2QbR2` — READY | `Tricentric-Integration`, `main`, `322467fae6b3771f4fb47e209a8a8f63b25883a6` |
| `triada.chalamandramagistral.com` | `chalamandra-triada` | `dpl_41LbXifeZHtc8xwMgjNyqFoPcCj4` — READY | `Chalamandra-Triada`, `main`, `d3d9116eb68162823d75c44383c869368c5e0e23` |
| `systemdecode.chalamandramagistral.com` | `system-decode-magis-v12-0-flux` | `dpl_9k4SS7S5a2KW1ubCegnVAwjWiK8K` — READY | `SYSTEM_DECODE_MAGIS-v12.0-FLUX`, `main`, `a2a9be56d77d3b3fe8ed4304cb6ff9a827cb321d` |
| `oraculo.chalamandramagistral.com` | `or-culo-chalamandra` | `dpl_HUjw8qRjgEVxqqBguJQX5fBaJgRA` — READY | `Or-culo-Chalamandra`, `main`, `e6027459d1d65ab5f4ef16983682e0b568b3a2e4` |
| `pirinola.chalamandramagistral.com` | `pirinola-neural` | `dpl_C8oH8hNMcb1ZtyxEc3KmmcpSEbLh` — READY | `Pirinola-`, `main`, `89b1bba44d33e7bebda98a67b63e7cfc0609144c` |

### 7.1 Proyectos que requieren decisión, no eliminación

- `interactive-decox-dag1` no tiene dominio personalizado en la lista consultada y su deployment READY utiliza el mismo SHA de integración que el deployment más reciente de `interactive-decox`. Esto amerita rastrear su origen y propósito; no demuestra que sea duplicado descartable.
- `srap-barrio` apunta a `Blueprint-Chalamandra---SRAP-Barrio-Edition`, rama `feat/real-money-flow`, SHA `cee51dd26749fc3694eb61f2429bd23fa938e746`. El repo declara que `api/checkout.js` responde 501 y no procesa pagos; tratarlo como demo, no como checkout operativo.
- El alias de Interactive se mantuvo sin cambios durante esta consulta. La diferencia entre deployment asignado al alias y latest production debe quedar documentada hasta que se decida expresamente cuál versión debe estar pública.

**Resultado:** se amplió la evidencia de backend y hosting sin alterar datos ni configuración de producción. Próximo paso de control: revisar las funciones y políticas señaladas con sus owners antes de cualquier cambio, y confirmar por negocio si Interactive y SystemDecode deben compartir el proyecto Supabase o quedar aislados.


### 6.3 Revisión SQL adicional de permisos y límites (solo SELECT a catálogos del sistema)

Se consultaron únicamente catálogos PostgreSQL (`pg_proc`, `pg_policies`, privilegios de funciones y privilegios de tablas); no se consultaron filas de usuarios ni tablas de negocio.

**Tricentric — funciones SECURITY DEFINER**
- Las cuatro firmas señaladas por el advisor no permiten ejecución a `anon`; `authenticated` y `service_role` sí tienen EXECUTE.
- Las definiciones inspeccionadas establecen `search_path` vacío, comprueban `auth.uid()` no nulo y enlazan escrituras a ese usuario. La sobrecarga simple de `complete_tricentric_practice` delega en la firma completa, que vuelve a comprobar autenticación y aplica el guardado por `auth.uid()`.
- Esto reduce el riesgo aparente de ejecución anónima y muestra controles explícitos de pertenencia en las definiciones revisadas, pero **no cierra la alerta automáticamente**: revisar también funciones auxiliares llamadas, las políticas que condicionan las lecturas, y probar con dos cuentas sintéticas que no se pueda consultar ni mutar el estado de la otra.
- Las políticas visibles en `public` restringen SELECT de perfiles, evaluaciones, prácticas y logros del usuario a `auth.uid()`; `achievements` se puede leer para usuarios autenticados y `ai_usage_daily` tiene una política que deniega operaciones directas a `anon` y `authenticated`.

**MAGIS comercial — tablas con RLS sin políticas**
- Los catálogos confirman que `operation_feedback`, `purchases` y `video_operations` tienen RLS activo, no tienen políticas y no dan privilegio SELECT directo a `anon` ni a `authenticated`; `service_role` sí puede leerlas.
- Esto es **fail-closed para lectura directa de los roles de cliente** en las tablas observadas. No demuestra que las rutas server-side estén correctamente autorizadas; se debe comprobar que cada endpoint valida el usuario/propiedad, no confía en IDs enviados por el cliente y reserva service-role para operaciones justificadas.
- No crear políticas genéricas para eliminar el warning: primero determinar el modelo de acceso requerido para compras, operaciones y comentarios. La ausencia de políticas puede ser intencional para tablas operadas solo por backend o puede estar bloqueando una función legítima.

Estas comprobaciones ajustan la severidad inicial: los advisories son señales para revisión, no evidencia suficiente por sí sola de explotación. No hubo cambios a privilegios, funciones o políticas.
