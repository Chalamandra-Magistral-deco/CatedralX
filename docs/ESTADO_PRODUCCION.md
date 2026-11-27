# Estado de Implementación — CatedralX

> Registro del estado técnico, validación, integración, seguridad y operación de CatedralX.
>
> **Actualización documental:** 2026-11-26  
> **Último corte técnico verificado:** 2026-11-11  
> **Fuente canónica del código:** rama main de Chalamandra-Magistral-deco/CatedralX  
> **Commit inspeccionado para el corte técnico:** f757a7cfa4e622a4bd6fc242d00408e1751c7e33

> **Vigencia:** esta edición reorganiza y amplía la documentación disponible. No representa una nueva auditoría del repositorio ni una nueva ejecución de pruebas. Los resultados técnicos que siguen corresponden al commit inspeccionado y no deben atribuirse automáticamente al HEAD actual. Para arquitectura, contratos y estructura, consultar docs/ARQUITECTURA_OBJETIVO.md, docs/contracts/README.md y MAPA_SAGRADO.json. El índice documental mencionado en registros anteriores ya no existe en main y no se considera una referencia vigente.

---

# 1. Resumen ejecutivo

## 1.1 Veredicto vigente

**CatedralX cuenta con código y artefacto CLI validados mediante CI. La configuración Compose es consistente. La integración efectiva con Agents y la operación de extremo a extremo no están verificadas.**

La evidencia disponible permite afirmar:

- El workflow de GitHub Actions correspondiente al commit inspeccionado terminó correctamente.
- La suite reportó 372 pruebas aprobadas.
- Las comprobaciones de dependencias y compilación reportaron resultados correctos.
- La imagen Docker se construyó y superó un smoke test de CLI.
- Los contratos superan comprobaciones sintácticas básicas.
- Existen controles de trazabilidad, evidencia y coherencia de aceptación.
- La aceptación independiente Ed25519 todavía necesita completar su canonicalización e integración.
- No existe evidencia suficiente para declarar un recorrido operativo completo entre API, Agents y CatedralX.
- La protección de main no estaba activada en el momento de la inspección.
- La auditoría histórica de secretos permanece incompleta.

**No declarar CatedralX como producción operativa ni como libre de secretos con la evidencia disponible.**

## 1.2 Matriz de estado

| Área | Estado documentado | Evidencia o limitación |
|---|---|---|
| Código CatedralX | Validado por CI | Commit inspeccionado |
| Suite de pruebas | 372 aprobadas | Workflow #182 |
| Gitleaks | Sin hallazgos no exceptuados | Escaneo de 170 commits y refs alcanzables |
| Dependencias | Correctas | pip check |
| Compilación | Correcta | compileall |
| Contratos | Validación sintáctica | No acredita conformidad semántica ni integración |
| Docker | Construido y probado | Smoke test CLI |
| Compose | Configuración válida | docker compose config --quiet |
| Integración con Agents | No verificada | Sin recorrido end-to-end demostrado |
| API y ejecución real | No verificadas | Sin evidencia de runtime integrado |
| Aceptación Ed25519 | Parcial | Canonicalización y conexión pendientes |
| Distribution | Parcial | La publicación requiere aceptación independiente |
| Protección de main | Desactivada al corte | API de ramas reportó protected=false |
| Runtime desplegado | No verificado | Sin evidencia actual |
| Auditoría histórica de secretos | Incompleta | Alcance limitado de Gitleaks |

---

# 2. Identidad y responsabilidades arquitectónicas

CatedralX, Agents y API son componentes relacionados, pero sus responsabilidades no deben confundirse.

La arquitectura establece **un único motor central de razonamiento: CatedralX**.

## 2.1 CatedralX — Motor central

CatedralX es responsable de:

- Razonamiento formal.
- Interpretación y evaluación de solicitudes.
- Aplicación de restricciones.
- Evaluación de evidencia.
- Producción de resultados estructurados.
- Evaluación de decisiones.
- Control de las condiciones de aceptación.
- Trazabilidad y registro decisional.

La taxonomía arquitectónica de referencia distingue subsistemas funcionales y una capacidad transversal de cómputo:

| Subsistema | Dominio | Responsabilidad |
|---|---|---|
| RSX / PERCEIVE | Percepción | Ingesta, normalización y validación de información |
| SCX / REASON | Razonamiento | Interpretación, análisis y evaluación de alternativas |
| MCX / OPTIMIZE | Optimización | Evaluación y mejora bajo restricciones |
| DSX / DEFENSE | Defensa | Políticas, límites, vetos y controles de seguridad |
| AEX / DECISION | Decisión | Construcción del resultado decisional estructurado |
| FEX / FEEDBACK + GOVERNANCE | Retroalimentación y gobierno | Registro de resultados, aprendizaje, reglas y control |
| MSX / PROVENANCE | Procedencia | Trazabilidad, evidencia, integridad y registro inmutable |
| ENERGY | Créditos virtuales de cómputo | Presupuesto y control del consumo computacional |

Esta tabla expresa la taxonomía objetivo; no acredita que todos los subsistemas estén implementados, activos, conectados o desplegados. La correspondencia debe demostrarse con rutas reales, código y pruebas.

Frontera de autoridad: DecisionResult es el único resultado formal de CatedralX que Agents puede consumir como puente decisional. No es una orden ni una autorización de ejecución. El borde externo permanece en Agents; Agents invoca CatedralX internamente y conserva la coordinación, verificación independiente y ejecución delegada.

## 2.2 Agents — Coordinación y ejecución

Agents es un proyecto y repositorio independiente.

Su responsabilidad arquitectónica comprende:

- Coordinación de agentes.
- Adaptadores de modelos y proveedores.
- Gestión de tareas.
- Workers.
- Colas y transporte de trabajos.
- Recuperación de resultados candidatos.
- Integración operativa con las capacidades de CatedralX.

Agents puede ejecutar tareas delegadas, pero no debe apropiarse de la autoridad central de razonamiento ni declarar por sí solo que un resultado cumple las condiciones de aceptación independiente.

## 2.3 API — Acceso y comunicación

API es la capa de comunicación entre productos, usuarios, servicios, Agents y CatedralX.

Sus responsabilidades conceptuales comprenden:

- Recepción de solicitudes.
- Autenticación y autorización.
- Validación de entradas.
- Aplicación de scopes y permisos.
- Transporte de contratos.
- Propagación de identificadores de trazabilidad.
- Entrega de respuestas.

La capa API no debe convertirse en un motor de razonamiento paralelo.

**Situación documental:** en la implementación descrita por los registros técnicos de Agents, la capa API forma parte del repositorio Agents mediante su directorio api/ y su servicio agents-api. No existe evidencia en este corte que justifique declarar un tercer repositorio API independiente.

La separación de responsabilidades no implica necesariamente separación física en tres repositorios.

## 2.4 Regla de autoridad

| Componente | Autoridad |
|---|---|
| Propietaria del proyecto | Gobierno y autorización de cambios |
| CatedralX | Razonamiento, evaluación y aceptación conforme a sus contratos |
| API | Acceso, comunicación y controles de transporte |
| Agents | Coordinación y ejecución delegada |
| Proveedores externos | Prestación de capacidades y resultados candidatos |
| Distribution | Entrega de resultados que cumplan las condiciones de autorización |

Los componentes externos no adquieren autoridad decisional por el mero hecho de participar en el procesamiento.

---

# 3. Modelo de interacción entre API, Agents y CatedralX

La arquitectura contempla tres flujos principales.

## 3.1 REQUEST — Solicitud

Flujo conceptual:

**Usuario / Producto → API → Agents → CatedralX**

Responsabilidad:

1. Recibir la solicitud.
2. Validar identidad, permisos y formato.
3. Registrar la trazabilidad.
4. Entregar la solicitud al procesamiento correspondiente.
5. Permitir que CatedralX evalúe el problema y determine si necesita delegar tareas.

No todas las solicitudes requieren una llamada a un proveedor externo.

## 3.2 DISTRIBUTION — Distribución

Flujo conceptual:

**Resultado → Evaluación → Aceptación independiente → Distribución autorizada**

Responsabilidad:

- Entregar únicamente resultados que cumplan las condiciones contractuales.
- Verificar la firma y el digest requeridos.
- Conservar la trazabilidad hasta el destino.
- No convertir resultados pendientes, rechazados o inciertos en resultados aceptados.

La existencia de un resultado o de un gate central ACCEPTED no autoriza por sí sola su publicación.

## 3.3 ORCHESTRATION — Orquestación

Flujo conceptual:

**CatedralX → Tarea autorizada → Agents → Ejecución → Resultado candidato → Evaluación**

Responsabilidad:

- Permitir que CatedralX solicite trabajo especializado.
- Delegar la ejecución operativa a Agents.
- Recuperar resultados y evidencia.
- Volver a evaluar los resultados en el motor central.

La orquestación autónoma no elimina las políticas de seguridad ni los requisitos de autorización y aceptación.

## 3.4 Principio de separación

**CatedralX decide qué necesita hacerse; Agents coordina cómo realizar las tareas delegadas; API permite la comunicación controlada.**

Esta distribución evita duplicidad de responsabilidades y mantiene la unicidad del motor central.

---

# 4. Estado técnico verificado — corte 2026-11-11

## 4.1 CI y pruebas

- GitHub Actions del commit inspeccionado: workflow run [#182](https://github.com/Chalamandra-Magistral-deco/CatedralX/actions/runs/42997292139), completado correctamente.
- Suite: **372 pruebas aprobadas**.
- pip check: correcto.
- compileall: correcto.
- Los tres contratos YAML OpenAPI superan el análisis sintáctico YAML en CI.
- Los dos JSON Schema superan el análisis sintáctico JSON.

Estas comprobaciones no sustituyen:

- Validación semántica de OpenAPI.
- Validación completa de JSON Schema contra casos de negocio.
- Conformidad de los contratos con el runtime de Agents.
- Integración entre los servicios.
- Verificación de operación real.

## 4.2 Dependencias

La organización documentada de dependencias es:

| Archivo | Función |
|---|---|
| requirements.txt | Rangos de dependencias de runtime |
| requirements.lock | Entorno completo fijado para CI y pruebas |
| requirements-runtime.lock | Conjunto mínimo fijado para la imagen de runtime |

Se documentaron los siguientes cambios:

- Se retiró requirements-test.txt porque no tenía consumidores internos y duplicaba declaraciones de dependencias.
- Docker instala exclusivamente el lockfile de runtime.
- La construcción falla de forma cerrada si el lockfile no está disponible.
- Se retiró el fallback no reproducible.
- Se retiró curl, que no tenía uso en la imagen.

## 4.3 Docker y Compose

- La configuración Compose supera docker compose config --quiet.
- La imagen Docker se construyó correctamente.
- El smoke test CLI fue satisfactorio.
- Compose representa una ejecución CLI puntual.
- Compose no configura el proceso CLI como daemon.
- No publica el puerto 5050.
- El endpoint opcional que escucha en loopback es una herramienta separada.

La validación de la configuración no demuestra que exista un servicio desplegado ni que haya un proceso operativo escuchando.

## 4.4 CI y ramas

- Los eventos push están limitados a main.
- Los eventos pull_request están limitados a main.
- El ajuste busca evitar ejecuciones duplicadas entre pushes de ramas de trabajo y apertura de PR.
- El árbol Git inspeccionado contiene 216 entradas: 184 archivos y 121 archivos Python.
- Las ramas visibles en el corte eran main y tres refs de trabajo asociadas a los PR #11, #12 y #13, ya fusionados.
- No se detectó trabajo pendiente en esos PR.
- Las refs antiguas permanecían porque la conexión disponible no exponía una operación de eliminación de ramas.

## 4.5 Protección de la rama principal

En la inspección, la API de ramas reportó:

**protected=false**

Por tanto:

**La protección de main no estaba activada en el corte técnico.**

No se debe describir la rama como protegida hasta comprobar una configuración efectiva de reglas o rulesets.

## 4.6 Entorno de ejecución anterior

La VM anterior quedó fuera del plan operativo.

No debe utilizarse como fuente de estado actual ni como destino de despliegue.

Su información histórica debe tratarse exclusivamente como referencia documental.

---

# 5. Estado de contratos, decisión y aceptación

## 5.1 Request

El contrato Request exige:

- Precio actual.
- Timestamp con zona horaria.
- Fuente identificable.

Los timestamps sin zona horaria son rechazados por el constructor central.

## 5.2 DecisionResult

El constructor central:

- Conserva trazas válidas.
- Rechaza trazas explícitas inválidas.
- Acepta únicamente decisiones dentro de BUY, SELL y HOLD.
- No infiere automáticamente la viabilidad a partir de la decisión.
- Degrada una aceptación cuando la evidencia o la procedencia no pueden verificarse.

La viabilidad, representada mediante viability_bp, debe proporcionarse explícitamente en CENTRAL_DIMENSIONS_BP.

reinvestment_surplus mantiene una única fuente de procedencia: DYNAMIC_CONSTRAINTS. No debe duplicarse en las dimensiones BP.

## 5.3 Coherencia del almacenamiento

El store exige:

- Coherencia entre status=ACCEPTED y evaluation_gate=ACCEPTED.
- Evidencia con digest.
- Enlace con identificadores de procedencia.

Estas comprobaciones refuerzan la integridad del resultado almacenado, pero no sustituyen la aceptación independiente.

## 5.4 Acceptance y firma Ed25519

Se debe distinguir entre dos estados:

**Gate central ACCEPTED**

Significa que el resultado superó las condiciones de evaluación internas correspondientes.

**Aceptación independiente Ed25519**

Requiere comprobar la firma y el digest conforme al contrato de aceptación.

El gate central ACCEPTED no equivale a aceptación independiente ni a autorización de publicación.

La canonicalización de los datos firmados todavía requiere un acuerdo técnico explícito y pruebas de conformidad con Agents.

El flujo público solo podrá exponer accepted después de verificar la firma independiente y el digest exigidos.

---

# 6. Seguridad y límites de confianza

## 6.1 Gitleaks

Gitleaks 8.30.1 reportó:

- Escaneo de 170 commits y refs alcanzables.
- Ningún hallazgo no exceptuado.
- Dos falsos positivos históricos de fixtures sintéticos.
- Excepciones en .gitleaksignore asociadas a huellas exactas.

Este resultado no certifica la ausencia total de secretos en todos los objetos históricos, repositorios, proveedores, entornos o sistemas conectados.

## 6.2 Límites de autoridad

Se mantienen los siguientes principios:

- API, worker y generador de candidatos no pueden usar la autoridad del verificador independiente.
- La clave privada Ed25519 debe residir exclusivamente en el proceso autorizado de firma.
- La API receptora debe validar mediante la clave pública correspondiente.
- El endpoint de resultados del worker exige token de servicio y scope explícito, aunque el listener opere en loopback.
- Los resultados pendientes, bloqueados, rechazados o inciertos no deben publicarse como aceptados.
- No se deben copiar, imprimir ni almacenar secretos reales en Git.
- CHALAMANDRA_API_ENABLE_MODEL_CALLS=false debe conservarse por defecto; no debe activarse para aparentar una integración completa.

## 6.3 Alcance de la revisión de seguridad

La revisión estática es parcial.

Debe consultarse:

**docs/SEGURIDAD_REPOSITORIO.md**

No se certifica:

- Ausencia de secretos en todo el historial.
- Estado de Secret Scanning.
- Ausencia de credenciales expuestas en proveedores.
- Estado de variables de entorno en runtime.
- Configuración de secretos de servicios desplegados.
- Seguridad completa de API, workers y redes operativas.

---

# 7. Integración efectiva y operación

## 7.1 Estado de integración

**No hay evidencia de runtime nuevo ni integración end-to-end activa en el corte inspeccionado.**

La validación de CatedralX mediante CI acredita el comportamiento cubierto por sus pruebas y la construcción de la imagen.

No acredita:

- Conexión activa con Agents.
- Funcionamiento coordinado de API, workers y CatedralX.
- Ejecución de tareas en un entorno real.
- Propagación completa de trazabilidad.
- Verificación de aceptación independiente en operación.
- Publicación correcta mediante Distribution.
- Despliegue real en producción.

## 7.2 Estado de operación

No existe evidencia suficiente en este corte para certificar:

- Procesos activos.
- Servicios systemd.
- Endpoints disponibles.
- DNS y red.
- Túneles.
- Puertos activos.
- Variables de entorno efectivas.
- Recepción y procesamiento real de solicitudes.
- Distribución externa de resultados aceptados.

No se debe utilizar un registro histórico de una VM para certificar la situación actual.

## 7.3 Veredicto operativo

| Condición | Resultado |
|---|---|
| Código versionado | Validado en el commit inspeccionado |
| Suite de CI | Aprobada |
| Imagen CLI | Construida y smoke test satisfactorio |
| Configuración Compose | Consistente |
| Contratos sintácticos | Validados |
| Conformidad semántica entre repositorios | Pendiente |
| Integración API–Agents–CatedralX | No verificada |
| Aceptación independiente | Pendiente |
| Distribution autorizada en runtime | No verificada |
| Producción operativa | No acreditada |

---

# 8. Inventario y correspondencia arquitectónica pendiente

La arquitectura objetivo debe contrastarse con los repositorios reales sin asumir que la estructura conceptual ya está implementada.

| Elemento | Responsabilidad objetivo | Evidencia que debe verificarse |
|---|---|---|
| CatedralX | Motor central de razonamiento | Código, contratos, pruebas y punto de invocación |
| Agents | Coordinación y ejecución | Workers, adaptadores, task bus y consumidores |
| API | Acceso y comunicación | Rutas, scopes, autenticación, contratos y trazabilidad |
| RSX / PERCEIVE | Percepción e ingesta | Rutas reales, validadores, contratos y pruebas |
| SCX / REASON | Razonamiento | Rutas reales, evaluadores y pruebas |
| MCX / OPTIMIZE | Optimización | Rutas reales, restricciones y pruebas |
| DSX / DEFENSE | Protección transversal | Gates, vetos, políticas y auditoría |
| AEX / DECISION | Resultado decisional | Constructor y contrato de DecisionResult |
| FEX / FEEDBACK + GOVERNANCE | Retroalimentación y gobierno | Registros, persistencia y controles de gobierno |
| MSX / PROVENANCE | Procedencia | Trazas, evidencia, integridad y registro |
| ENERGY | Créditos virtuales de cómputo | Presupuesto y medición del consumo |
| Acceptance | Aceptación independiente | Firma Ed25519, digest y verificador |
| Distribution | Entrega de resultados aceptados | Dispatcher, suscripciones y comprobaciones |

La correspondencia debe realizarse archivo por archivo.

No se deben renombrar, mover, eliminar o duplicar módulos basándose únicamente en el árbol conceptual.

---

# 9. Secuencia de remediación y cierre

Las acciones siguientes representan trabajo pendiente. No constituyen autorización para modificar los repositorios, desplegar servicios o borrar ramas.

## Etapa 0 — Actualizar la evidencia

- Consultar el HEAD real de main.
- Identificar el commit exacto vigente.
- Repetir las verificaciones necesarias en ese commit.
- Registrar las fechas y fuentes de evidencia.
- Determinar si el estado del 11 de noviembre sigue siendo aplicable.

No declarar vigencia operativa a partir de un snapshot anterior sin reconciliación.

## Etapa 1 — Protección y gobierno del código

- Confirmar reglas de protección de main.
- Documentar los checks obligatorios.
- Definir condiciones para fusionar cambios.
- Verificar la autoridad de las cuentas y permisos relevantes.

## Etapa 2 — Contrato de aceptación independiente

- Acordar la canonicalización del contenido firmado.
- Definir el digest y la representación inequívoca de los datos.
- Integrar Ed25519 en el flujo correspondiente.
- Mantener separada la custodia de la clave privada.
- Validar mediante la clave pública.
- Crear pruebas positivas, negativas y de manipulación del contenido.

## Etapa 3 — Contratos y trazabilidad

- Verificar la conformidad semántica de los contratos Request, DecisionResult, Evidence, Acceptance, Distribution y Orchestration.
- Reconciliar las definiciones de CatedralX con los consumidores de Agents.
- Propagar trace_id y catedralx_trace_id.
- Corregir y conectar el parser W3C.
- Validar los identificadores, encabezados y flags en pruebas.

## Etapa 4 — Integración API–Agents–CatedralX

Comprobar con evidencia:

1. API recibe una solicitud autorizada.
2. La solicitud llega a Agents conforme al contrato.
3. Agents invoca la capacidad correspondiente de CatedralX.
4. CatedralX produce un resultado trazable.
5. Agents devuelve un resultado candidato y su evidencia.
6. CatedralX evalúa el resultado.
7. La aceptación independiente verifica firma y digest.
8. Distribution permite únicamente la entrega autorizada.

Debe probarse primero una sola vertical slice completa.

## Etapa 5 — Distribución y límites externos

- Completar los contratos de suscripciones.
- Validar el endpoint de alta.
- Reconciliar scopes.
- Endurecer las comprobaciones SSRF frente a redirecciones y resolución DNS.
- Impedir que resultados pendientes o rechazados alcancen destinos públicos.

## Etapa 6 — Revisión integral

En el commit exacto:

- Ejecutar la suite completa.
- Ejecutar Ruff y mypy cuando correspondan.
- Ejecutar comprobaciones de contratos.
- Construir la imagen.
- Ejecutar smoke tests.
- Validar integración.
- Registrar artefactos, resultados y evidencias.

## Etapa 7 — Inspección operativa autorizada

Una vez identificado el entorno operativo correcto y obtenida autorización:

- Inspeccionar systemd.
- Revisar procesos.
- Comprobar sockets.
- Revisar configuración sin revelar secretos.
- Examinar logs.
- Verificar conectividad.
- Probar recepción de una solicitud controlada.
- Comprobar el recorrido hasta el resultado y su aceptación.

La inspección no implica reiniciar servicios, activar modelos, desplegar nuevas imágenes ni publicar resultados.

---

# 10. Criterios de estado: no confundir etapas

Para mantener un gobierno técnico preciso, se utilizarán estas definiciones:

| Estado | Significado |
|---|---|
| EXISTE | El archivo, módulo o servicio está presente |
| IMPLEMENTADO | El comportamiento está desarrollado en código |
| PROBADO | Existen pruebas que ejercitan el comportamiento |
| VALIDADO | Las comprobaciones especificadas han pasado |
| INTEGRADO | Los componentes se comunican mediante contratos funcionales |
| SINCRONIZADO | Las versiones y estados relevantes están alineados |
| ACEPTADO | Un verificador autorizado confirmó el resultado |
| DESPLEGADO | El artefacto está instalado en el entorno correspondiente |
| OPERATIVO | Existe evidencia de funcionamiento real |
| PRODUCCIÓN VERIFICADA | Se comprobó el recorrido operativo y sus controles en el entorno productivo |

Ningún estado superior debe inferirse automáticamente a partir de uno inferior.

En particular:

- Código existente no significa integración.
- CI aprobado no significa producción.
- Gate central ACCEPTED no significa aceptación independiente.
- Imagen construida no significa servicio desplegado.
- Servicio desplegado no significa operación correcta.
- Un resultado generado no significa que esté autorizado para distribuirse.

---

# 11. Registro histórico preservado — corte 2026-10-26

Este registro conserva observaciones de una auditoría anterior.

Sus afirmaciones sobre VM, servicios, integración, dependencias, aceptación y pruebas no representan el estado vigente del 11 de noviembre ni deben utilizarse como evidencia operativa actual.

## 11.1 Veredicto histórico

No declarar el sistema integrado operativo de extremo a extremo.

La regresión P0 de autorización fue corregida y fusionada en:

**aee4e114ecdc86d9ff8abade69e02799b500d90e**

En aquella revisión pasaron pruebas, Ruff, mypy y smoke test de imagen.

La aceptación Ed25519 todavía no estaba conectada y el recorrido real en VM seguía sin verificarse.

La unidad systemd versionada para la API escuchaba en loopback y configuraba:

**CHALAMANDRA_API_ENABLE_MODEL_CALLS=false**

Esto describía el archivo versionado, no demostraba que el servicio estuviera activo en la VM.

## 11.2 Estado histórico de componentes

| Componente | Estado observado | Evidencia o limitación |
|---|---|---|
| CatedralX determinista | Código presente | BIN/catedral, elite/ y tests/ existían; no se ejecutó la suite completa en esa revisión |
| API de Agents | Código presente | api/server.py utilizaba JWT y scopes en varias rutas |
| TaskBus SQLite | Código presente | api/task_bus.py implementaba reserva e idempotencia |
| Rutas internas | P0 corregido | GET de runs comprobaba orchestration:read y utilizaba task_bus.get_run_tasks(); POST de resultados comprobaba tasks:complete |
| Worker | Parcial | api/worker_loop.py invocaba CatedralX mediante una ruta fija |
| Aceptación | Parcial | Existían HMAC-SHA256 y comprobación de digest; el helper Ed25519 no estaba integrado al gate |
| Distribución | Parcial | Store y dispatcher existían; faltaba completar el ciclo de suscripciones y eventos |
| Trazabilidad W3C | Parcial | Existía api/trace_parser.py, pero el servidor no llamaba al helper |
| CI | Sin veredicto final en aquella revisión | No se disponía de una ejecución completa reciente consultable |
| VM y red | No verificados | La lectura del repositorio no confirmaba servicios, red, puertos ni entrega real |

## 11.3 Límites de confianza históricos

- Mantener CHALAMANDRA_API_ENABLE_MODEL_CALLS=false por defecto.
- API, worker y generador de candidatos no podían utilizar la autoridad del verificador independiente.
- La clave privada Ed25519 debía permanecer en el proceso autorizado de firma.
- La API receptora debía validar con la clave pública.
- El endpoint de resultados del worker requería token de servicio y scope explícito.
- Los resultados pendientes, bloqueados, rechazados o inciertos no podían publicarse como aceptados.
- No se debían copiar secretos reales a Git.

## 11.4 Snapshot operativo anterior

Un documento fechado 2026-10-25 afirmaba que API, worker, túnel Cloudflare y dominio estaban activos.

Esas afirmaciones no se revalidaron en las revisiones posteriores.

No deben utilizarse para confirmar operación actual.

---

# 12. Documentos de referencia

| Documento | Responsabilidad |
|---|---|
| DOCUMENTACION/IDENTIDAD-CANONICA.md | Identidad y pertenencia oficial de CatedralX |
| docs/ARQUITECTURA_OBJETIVO.md | Arquitectura y responsabilidades objetivo |
| docs/contracts/README.md | Índice de contratos |
| MAPA_SAGRADO.json | Snapshot del inventario estructural |
| docs/SEGURIDAD_REPOSITORIO.md | Revisión y controles de seguridad |
| docs/ESTADO_PRODUCCION.md | Estado técnico, validación e integración |

MAPA_SAGRADO.json está anclado a su commit de origen. No debe interpretarse como representación automática del HEAD, de una instalación local o de un despliegue operativo.

Los registros en docs/archive/ y docs/legacy/ conservan documentación histórica. No se debe inferir que todo el material histórico esté clasificado o preservado sin una inspección documental específica.

---

# 13. Declaración final de estado

Al corte técnico verificado del 11 de noviembre de 2026:

**CatedralX cuenta con código, pruebas y artefacto CLI validados por CI. La configuración Compose es consistente. La integración efectiva con Agents, la aceptación independiente completa y la operación de extremo a extremo no están verificadas. La protección de main y la auditoría histórica integral de secretos permanecen pendientes.**

La arquitectura establece responsabilidades diferenciadas:

- **API comunica.**
- **Agents coordina y ejecuta tareas delegadas.**
- **CatedralX razona, evalúa y decide.**
- **RSX / PERCEIVE ingiere y valida información.**
- **SCX / REASON analiza y razona.**
- **MCX / OPTIMIZE evalúa alternativas bajo restricciones.**
- **DSX / DEFENSE aplica límites y vetos.**
- **AEX / DECISION estructura el resultado decisional.**
- **FEX / FEEDBACK + GOVERNANCE registra resultados y controles de gobierno.**
- **MSX / PROVENANCE conserva trazabilidad y procedencia.**
- **ENERGY representa créditos virtuales de cómputo.**
- **Distribution entrega únicamente resultados autorizados.**

CatedralX permanece como el único motor central de razonamiento.

La prioridad no es declarar el sistema terminado, sino cerrar las conexiones contractuales, probar una vertical slice completa y demostrar cada estado con evidencia verificable.

**Regla de gobierno:** primero observar, después interpretar, luego proponer. Ningún cambio de código, estructura, configuración, despliegue o repositorio se ejecuta sin autorización explícita de la propietaria.
