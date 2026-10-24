# Evidencia de hosting y despliegues — DecoX
**Versión:** 0.1  
**Fecha:** 2026-10-24  
**Método:** lectura de proyectos, dominios, aliases y despliegues de Vercel; contraste con inventario local y README.  
**Alcance:** solo lectura de metadatos salvo la reasignación autorizada del alias de Interactive para restaurar el despliegue previo. No se cambió DNS ni código.

## 1. Mapeo confirmado: dominio → proyecto → despliegue asignado

| Dominio | Proyecto Vercel | Repositorio / rama y SHA del despliegue asignado | Evidencia y límites |
|---|---|---|---|
| chalamandramagistral.com → redirige 301 a www | chalamandra-magistral-hlxd | CHALAMANDRA-MAGISTRAL / main / 0b6511417c99166a4997e4d9c974a3e7bde947e2 | Alias y despliegue READY; sitio estático HTML/CSS/JS según README. |
| www.chalamandramagistral.com | chalamandra-magistral-hlxd | Mismo proyecto y despliegue del portal | Dominio verificado; README declara Formspree y GTM, pero no prueba envío de formularios ni conversión real. |
| interactive.chalamandramagistral.com | interactive-decox | INTERACTIVE-DECOX / main / a231b911390a418c145538ed2d6a6c28c768ecff | Alias reasignado y verificado tras rollback solicitado. Despliegue dpl_CoETjgfuU5bdG1YjEwbNLK8SUUFV, estado READY. La versión de integración 1a666fa ya no recibe este alias. |
| tricentric.chalamandramagistral.com | tricentric-integration | Tricentric-Integration / main / 322467fae6b3771f4fb47e209a8a8f63b25883a6 | Alias confirmado; app Vite. README declara Supabase Auth, Edge Function srap-analysis, Gemini y PostgreSQL RPC; runtime y RLS pendientes. |
| triada.chalamandramagistral.com | chalamandra-triada | Chalamandra-Triada / main / d3d9116eb68162823d75c44383c869368c5e0e23 | Alias confirmado; app Vite. README declara React, MSAL/Entra, Gemini y Upstash Redis; runtime/permisos pendientes. |
| systemdecode.chalamandramagistral.com | system-decode-magis-v12-0-flux | SYSTEM_DECODE_MAGIS-v12.0-FLUX / main / a2a9be56d77d3b3fe8ed4304cb6ff9a827cb321d | Alias confirmado; app Vite. README declara Supabase Auth/datos/créditos, funciones server-side para modelos y Stripe opcional; pagos y controles de acceso no probados. |
| oraculo.chalamandramagistral.com | or-culo-chalamandra | Or-culo-Chalamandra / main / e6027459d1d65ab5f4ef16983682e0b568b3a2e4 | Alias confirmado; app Vite/React con origen declarado en AI Studio. API/proxy y secretos del runtime pendientes de comprobar. |
| pirinola.chalamandramagistral.com | pirinola-neural | Pirinola- / main / 89b1bba44d33e7bebda98a67b63e7cfc0609144c | Alias confirmado; app Vite. Protección SSO para despliegues no asociados a dominios personalizados. Preservar index.html.bak y index.html.broken; no borrarlos. |

## 2. Otros proyectos de Vercel observados

| Proyecto | Evidencia | Estado de clasificación |
|---|---|---|
| interactive-decox-dag1 | Existe en el equipo; la consulta de dominios devolvió una lista vacía. | PENDIENTE: investigar origen y necesidad; no borrar ni cambiar. |
| srap-barrio | Despliegue consultado apunta a Blueprint-Chalamandra---SRAP-Barrio-Edition, rama feat/real-money-flow, SHA cee51dd26749fc3694eb61f2429bd23fa938e746. | El README del Blueprint declara que api/checkout.js responde 501 y no procesa pagos. No presentarlo como checkout operativo. |
| interactive-decox — despliegue de integración | dpl_2GyDWbn1s8sJ5tKbZSrSZhvT1Qek, SHA 1a666fa238623d308b220ff0a63255b3cf167f52. | Permanece en historial, pero el dominio público fue reasignado al despliegue anterior. No eliminar el despliegue ni reescribir más historia. |

## 3. Arquitecturas backend declaradas en repositorios

Estas son declaraciones de README/configuración, no comprobaciones de disponibilidad o seguridad del servicio:

- Portal corporativo: HTML/CSS/JS; build Tailwind; Formspree y Google Tag Manager declarados.
- Interactive DecoX: React/Vite; endpoints api/ai.ts, api/contact.ts, api/verify-payment.ts y api/stripe-webhook.ts; Supabase, Gemini, Stripe y Resend aparecen en código/documentación. Requiere pruebas seguras de autenticación, persistencia, webhook y checkout antes de declarar el flujo operativo.
- SystemDecode/MAGIS: React/Vite; Supabase Auth/datos/créditos; endpoints server-side de modelos; Stripe opcional.
- Tricentric: Supabase Auth, Edge Function srap-analysis, Gemini y RPC de PostgreSQL.
- Triada: React/Vite; Microsoft Entra/MSAL, Gemini y Upstash Redis.
- Oráculo: React/Vite y SDK Gemini; revisar proxy/server y confirmar que las claves no están en el bundle público.
- Pirinola: React/Vite; configuración Vercel; verificar runtime y archivos locales sin rastrear.
- CatedralX ↔ agents: el puente catedralx_reasoning está presente en código; rutas/configuración efectiva e integración en ejecución siguen pendientes. CatedralX continúa bloqueado para trading real.

## 4. Hallazgos y decisiones

1. Se confirmó con metadatos de Vercel la relación entre los siete dominios principales y sus proyectos/despliegues asignados.
2. El dominio raíz del portal redirige a www con HTTP 301.
3. Interactive: el primer intento de rollback solo restableció main; la comprobación posterior encontró el alias público todavía en el despliegue nuevo. Se reasignó interactive.chalamandramagistral.com al despliegue READY del SHA a231b911… y se consultó de nuevo el alias, que ahora devuelve ese despliegue. El HTML público respondió HTTP 200. La ruta /sesion-descubrimiento entrega el fallback SPA de la versión previa; HTTP 200 no implica que exista una página independiente en esa ruta.
4. La existencia de un endpoint o una variable en código no prueba que el secreto esté configurado ni que el flujo funcione. No se leyeron ni guardaron valores de variables de entorno.
5. No se cambió Cloudflare/DNS, bases de datos ni código de producto; no se ejecutaron pagos ni se hicieron despliegues nuevos.

## 5. Próxima secuencia de verificación

1. Contrastar runtime/backends y políticas de acceso por producto, sin mostrar valores secretos.
2. Probar formulario y eventos del portal en un entorno seguro; registrar el resultado de contacto cualificado.
3. Verificar en modo test el checkout/webhook de Interactive y persistencia Supabase, sin cobros reales.
4. Aislar interactive-decox-dag1 como posible duplicado hasta entender su procedencia.
5. Verificar el puente agents → CatedralX en aislado y documentar salida/errores sin activar órdenes.
6. Vincular cada producto con oferta, CTA, contacto, pago y seguimiento comercial para priorizar un flujo medible.
