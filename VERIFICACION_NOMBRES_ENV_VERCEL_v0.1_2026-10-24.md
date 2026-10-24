# Verificación de nombres de variables en Vercel — DecoX
**Fecha:** 2026-10-24  
**Versión:** 0.1  
**Método:** listado de nombres y entornos configurados en proyectos Vercel; consulta realizada con descifrado deshabilitado.  
**Seguridad:** no se solicitaron ni mostraron valores, tokens, claves ni secretos. No se cambiaron variables.

## Resultados por proyecto

| Proyecto Vercel | Nombres observados en configuración | Nombres que faltan o requieren atención según el código | Lectura correcta |
|---|---|---|---|
| chalamandra-magistral-hlxd | GEMINI_API_KEY, GROQ_API_KEY, PORT en production y preview | Revisar si GEMINI_API_KEY/GROQ_API_KEY tienen rutas consumidoras activas; no se identificó un endpoint cliente en esta pasada que pruebe su necesidad. | La presencia de un nombre no prueba valor válido o que la variable se use. |
| interactive-decox | En production: RESEND_API_KEY, GEMINI_MODEL, STRIPE_WEBHOOK_SECRET, STRIPE_SECRET_KEY, STRIPE_DISCOVERY_PRICE_ID, CONTACT_FROM_EMAIL, CONTACT_TO_EMAIL, GEMINI_API_KEY y VITE_STRIPE_DISCOVERY_URL. VITE_STRIPE_DISCOVERY_URL también aparece para development. | No se encontró PURCHASE_EVENT_WEBHOOK_URL, STRIPE_MAGISTRAL_PRICE_ID ni VITE_STRIPE_MAGISTRAL_URL en el listado actual del proyecto. El código de verify-payment mapea solo discovery. | El esquema de compra configurado por nombre se concentra en Discovery. El webhook de Stripe puede responder recepción sin fulfillment downstream cuando falta PURCHASE_EVENT_WEBHOOK_URL. El destino de producción y el pago Magistral necesitan verificación antes de afirmarse operativos. |
| interactive-decox-dag1 | No se devolvieron variables de entorno para el proyecto. | El código de la aplicación necesita su configuración de servidor si usa Gemini/Stripe/Resend. | No tiene dominio personalizado en la consulta de Vercel ni variables registradas; no es candidato apto para recibir el dominio público sin sincronización y configuración deliberadas. |
| system-decode-magis-v12-0-flux | En production: GROQ_API_KEY, SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY, SUPABASE_SECRET_KEY, MAGIS_APP_URL, STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, STRIPE_PRICE_STARTER, STRIPE_PRICE_PRO y VITE_SUPABASE_URL/VITE_SUPABASE_PUBLISHABLE_KEY. STRIPE_WEBHOOK_SECRET también aparece en preview. | No se encontró GEMINI_API_KEY en la lista; el código y documentación recientes mencionan migración de algunos módulos hacia Groq. | Hay nombres de configuración de Supabase/Stripe presentes; no se verificaron valores, conexión remota, planes o webhooks. |
| tricentric-integration | En production: VITE_SUPABASE_URL, VITE_SUPABASE_PUBLISHABLE_KEY, VITE_STRIPE_PAYMENT_LINK, VITE_SITE_URL y VITE_ENABLE_LOCAL_AI; las dos variables de Supabase y otras públicas también tienen preview/development según listado. | Las variables y secretos propios de Supabase Edge Functions deben comprobarse en Supabase, no inferirse desde el listado de variables de Vercel. | Existe configuración de cliente por nombre; no prueba que el proyecto Supabase remoto tenga las migraciones actuales. |
| chalamandra-triada | GEMINI_API_KEY en production y preview. | El código exige OIDC_ISSUER, OIDC_AUDIENCE, OIDC_JWKS_URL, OIDC_REQUIRED_SCOPE, UPSTASH_REDIS_REST_URL y UPSTASH_REDIS_REST_TOKEN; esos nombres no aparecen en el listado actual del proyecto Vercel. | **BLOQUEO probable de API en Vercel:** el README/código indica que la ausencia de OIDC o Redis provoca rechazo de solicitudes. Confirmar configuración con un test de runtime autorizado antes de marcar Triada como operativa. |
| or-culo-chalamandra | GEMINI_API_KEY en production y preview. | No se observó otra variable obligatoria en el código revisado del endpoint Oráculo. | La presencia del nombre no prueba que la clave sea válida o que el proveedor responda. |
| pirinola-neural | PIRINOLA_SITE_URL y VITE_SITE_URL en production. | El código de OfferCard consulta VITE_STRIPE_PAYMENT_LINK; ese nombre no aparece en la lista actual de variables de Vercel. | **Pago no verificado:** un build nuevo sin esa variable puede mostrar el aviso de checkout no configurado. El bundle ya publicado puede conservar configuración antigua; no se concluye el estado visual de producción sin probar la página. |

## Hallazgos priorizados

### P0 — Interactive: fulfillment de compra
- El código valida la firma de Stripe y, para eventos compatibles, intenta enviar event_id, event_type, session_id y payment_status a PURCHASE_EVENT_WEBHOOK_URL si está configurada.
- En el listado actual del proyecto Vercel no aparece esa variable. Si la ausencia se confirma en el entorno de producción, el handler puede devolver received=true sin que este código registre la compra ni entregue el servicio.
- No se debe enviar un pago real para probarlo. Próximo control: comprobar el destino de fulfillment autorizado y hacer un test controlado en Stripe Test Mode.

### P1 — Triada: autenticación y cuotas
- El código servidor requiere OIDC issuer/audience/JWKS/scope y Upstash Redis. Los nombres no figuran en el listado de variables Vercel consultado.
- Hasta verificar un ambiente seguro con esos valores configurados no considerar probado el acceso autenticado ni la limitación de tasa en producción.

### P1 — Pirinola: CTA de pago
- El componente usa VITE_STRIPE_PAYMENT_LINK para mostrar el enlace de pago, pero la variable no aparece en la configuración actual de Vercel consultada.
- Verificar el CTA público y su destino antes de anunciar venta; no cambiar configuración ni desplegar en esta fase.

### P1 — AI Studio / interactive-decox-dag1
- El proyecto no presenta variables de entorno en el listado consultado y no tiene dominio personalizado asignado.
- Mantenerlo separado. La app ejecutable de Google AI Studio sigue siendo la fuente original que debe sincronizarse, no asumir que el proyecto dag1 contiene una copia idéntica.

## Límites

- La consulta cubrió nombres, tipos y objetivos de entorno sin descifrar valores.
- La ausencia de un nombre en Vercel no excluye que exista configuración externa en otro servicio; en el caso de las funciones de Supabase, su configuración debe revisarse en Supabase por separado.
- No se probaron transacciones, no se contactó a clientes, no se llamó a Gemini y no se cambiaron variables, DNS, aliases o deployments.
