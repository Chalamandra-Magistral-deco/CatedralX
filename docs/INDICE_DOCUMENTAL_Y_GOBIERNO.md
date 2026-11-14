# Índice documental y política de conservación — CatedralX

Actualizado: 2026-11-11. Fuente de código: main.

## Reglas
- Este índice y docs/ESTADO_PRODUCCION.md son las entradas de navegación y estado vigente.
- Los documentos fechados describen solo el corte indicado.
- No reescribir evidencia histórica para hacerla coincidir con el presente.
- No eliminar documentos por antigüedad o duplicación aparente sin consolidar primero su contenido y comprobar referencias. Las duplicaciones confirmadas pueden eliminarse después de actualizar el índice y preservar la información necesaria.
- Separar diseño previsto, código presente, CI probado, integración probada y runtime verificado.
- No publicar secretos, tokens, claves privadas, credenciales ni datos personales.

## Documentos de referencia
- README.md: entrada, alcance del motor, pruebas y límites.
- docs/ESTADO_PRODUCCION.md: estado verificable de main y límites operativos.
- MAPA_SAGRADO.json: mapa estructural reconciliado con el árbol actual; no prueba de despliegue.
- docs/ARQUITECTURA_OBJETIVO.md: diseño lógico; no prueba de despliegue.
- docs/ARQUITECTURA_MECANICA_RETROALIMENTACION.md: diagnóstico, criterios de conservación y diseño del feedback.
- docs/INTEGRACION_CATEDRALX_AGENTS.md: contrato previsto con Agents; requiere verificación cruzada.
- docs/INVENTARIO_ECOSISTEMA_Y_CONEXIONES.md: snapshot del 2026-10-26, no inventario actual certificado.
- docs/contracts/README.md y docs/contracts/*.yaml: especificaciones Request, Distribution y Orchestration.
- DOCUMENTACION/IDENTIDAD-CANONICA.md: registro histórico de identidad canónica.
- docs/SEGURIDAD_REPOSITORIO.md: alcance y límites de la revisión de secretos.

## Otros documentos de soporte

- docs/BLUEPRINT_COMPOSE.md y docs/BLUEPRINT_COMPOSE_FULL.yaml: propuestas/blueprints de infraestructura; no prueban despliegue y deben tratarse como diseño.
- docs/CHALAMANDRA_CORE_MASTER_SPEC.md: especificación maestra.
- docs/FLUJOS_SISTEMA.md: jerarquía de componentes y flujos reactivo, retorno y proactivo (referencia única de flujos).
- docs/MCX_OPTIMIZE_MAP.md: mapa de optimización.
- docs/AUDIT_LOG_PHASE_A.md: registro de auditoría.
- docs/runbooks/loopback-status.md: runbook de observación histórica; no ejecutar contra un host actual sin adaptación y autorización.

## Archivo histórico preservado

### docs/archive/
Se conservan seis versiones fechadas 2026-10-24:
- MAPA_MAESTRO_DECOX_v0.2_2026-10-24.md
- MAPA_MAESTRO_DECOX_v0.3_2026-10-24.md
- MAPA_MAESTRO_DECOX_v0.4_2026-10-24.md
- MAPA_MAESTRO_DECOX_v0.5_2026-10-24.md
- MAPA_MAESTRO_DECOX_v0.6_2026-10-24.md
- MAPA_MAESTRO_DECOX_v0.7_2026-10-24.md

Tratamiento: conservar como secuencia evolutiva y evidencia. No usar estados de proyectos, variables, dominios o despliegues como actuales. La versión más alta no se considera vigente sin reconciliación con fuentes actuales.

### docs/audit/
Se conservan informes de auditoría y evidencia:
- AUDITORIA_CONSOLIDACION_PERGAMINO.md
- CATEDRAL_COGNITIVE_STATE_V4_2.md
- CATEDRAL_RECONSTRUCCION.md
- COMPARACION_CLON_REPO_PRINCIPAL_2026-10-24.md
- ESTADO_SINCRONIZACION_AI_STUDIO_v0.1_2026-10-24.md
- EVIDENCIA_HOSTING_VERCEL_v0.1_2026-10-24.md
- INVENTARIO_BACKENDS_DATOS_v0.1_2026-10-24.md
- INVENTARIO_BACKENDS_DATOS_v0.2_2026-10-24.md
- INVENTARIO_TECNICO_COMPLEMENTARIO_v0.1_2026-10-24.md
- INVENTARIO_TECNICO_COMPLEMENTARIO_v0.2_2026-10-24.md
- MAPA_MAESTRO_CANONICO.md
- MATRIZ_ACEPTACION_PERGAMINO.md
- MATRIZ_CONFLICTOS_PRINCIPAL_CLON_2026-10-24.md
- PROMPT_CATEDRALX.md
- RESEARCH_EVALUATION_2026-10-24.md
- VALIDACION_PUENTE_AGENTS_CATEDRALX_v0.1_2026-10-24.md

Tratamiento: conservar como evidencia. Los informes fechados 24 de octubre son snapshots y sus afirmaciones operativas no se presumen vigentes. MAPA_MAESTRO_CANONICO.md es material de auditoría, no reemplaza este índice.

### docs/legacy/
Se conservan cuatro archivos de implementaciones anteriores:
- MCX-OPTIMIZE-optimize.py
- MCX-optimize.py
- OPTIMIZE-optimize.py
- motor.py

Tratamiento: referencia histórica, no módulos de ejecución canónicos. No importarlos ni reactivarlos sin decisión técnica y pruebas.

### docs/superpowers/plans/
- 2026-10-24-governance-to-order-contract.md: plan histórico, no estado de implementación.

## Mantenimiento
- Toda auditoría nueva registra fecha, commit, alcance, método, evidencia, limitaciones y conclusión.
- Actualizar documentos canónicos en su ubicación; no crear copias final/final2/latest.
- Si un informe deja de ser vigente, conservarlo y añadir nota de supersesión con enlace al actual.
- Cambiar contratos YAML junto con pruebas/implementación o decisión explícita.
- No mover ni borrar evidencia histórica por limpieza cosmética.

## Orden de lectura
1. README.md
2. docs/ESTADO_PRODUCCION.md
3. docs/ARQUITECTURA_OBJETIVO.md
4. docs/FLUJOS_SISTEMA.md
5. docs/INTEGRACION_CATEDRALX_AGENTS.md
6. docs/contracts/README.md
7. docs/SEGURIDAD_REPOSITORIO.md
8. docs/audit/ y docs/archive/ cuando se requiera evidencia histórica.
