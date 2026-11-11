# Arquitectura mecánica, depuración y retroalimentación

**Estado:** diseño documentado; feedback directo implementado en el código versionado.  
**Fecha del diseño:** 2026-10-28. **Reconciliación documental:** 2026-11-11.  
**Alcance:** repositorio CatedralX. La integración de formularios/API externos requiere una implementación separada en Agents/producto.  
**Vigencia de pruebas:** el conteo de 337 pruebas mencionado en registros de octubre es histórico. La CI de main validó 354 pruebas, pip check, compileall, Compose config, Docker build y CLI smoke test en el commit 3bc0e234d4b4c651b77a3c84a9b2ecbdb51b13d5 (run #145), incluyendo Gitleaks sobre 133 commits sin hallazgos no exceptuados.

## Resumen ejecutivo de intervención

### Medición y límites

La complejidad se describe mediante sus módulos, contratos, dependencias y rutas de datos. **No existe una medición estadística reproducible del porcentaje de degradación**, por lo que no se asigna un porcentaje ni una puntuación sintética. Para cuantificarlo se necesitarían una línea base, métricas de defectos/regresiones, tiempos de ejecución y observabilidad comparables.

## 1. Diagnóstico Forense

### Estructura real observada

- **PERCEIVE:** lectura de observaciones y validación de frescura.
- **REASON:** motor financiero, reglas, restricciones dinámicas, orquestación y composición del estado.
- **FEX/GOVERNANCE:** restricciones de sostenibilidad y ledger del ciclo económico.
- **FEX/FEEDBACK:** evaluación offline de predicciones y outcomes; ahora también feedback explícito de usuario, en un ledger separado.
- **DSX/DEFENSE:** controles, guardas y autorizaciones.
- **AEX/DECISION:** intención y ejecución bajo autorización.
- **MSX:** procedencia.
- **contracts:** construcción, esquema y persistencia del resultado.
- **elite/bin + BIN/catedral:** comandos de una sola ejecución.
- **tests:** pruebas unitarias, contratos e integración.
- **deploy/systemd:** especificaciones de servicio/timer; el código versionado no demuestra que estén habilitados.

### Inconsistencias verificadas

1. **Hallazgo histórico corregido:** versiones anteriores de docs/FLUJOS_SISTEMA.md confundían BIN/motor.py con la entrada canónica. El punto de entrada versionado es BIN/catedral; docs/legacy/motor.py es un wrapper histórico.
2. **Hallazgo histórico corregido:** elite/bin/inyector-vitral sí existe en el árbol actual. Es un endpoint HTTP opcional de solo lectura que enlaza a 127.0.0.1:5050 cuando se ejecuta explícitamente; no forma parte de la imagen CLI ni está acreditado como servicio desplegado. docs/FLUJOS_SISTEMA.md y docker-compose.yml ya reflejan esa separación.
3. El ledger de FEX evalúa predicciones contra resultados de mercado. No captura la valoración humana de claridad, utilidad o corrección de una respuesta.
4. El comentario de contracts/builder.py decía que los diagnósticos no podían sobrescribir un veto, pero una disonancia alta podía cambiar un estado bloqueado a REJECTED. Se corrigió para aplicar el downgrade diagnóstico únicamente cuando la regla central había producido ACCEPTED.
5. El hotfix P0 ya exige puntajes BP enteros explícitos. Hasta que exista un productor verificado de central_dimensions_bp, la falta de dimensiones debe seguir bloqueando la aceptación.

## 2. Limpieza y Correcciones

### Limpieza regenerable

Se pueden retirar cachés generadas como __pycache__, .pytest_cache y .ruff_cache; no son fuente ni estado empresarial canónico. No se elimina el entorno virtual, historiales JSONL externos ni datos de trabajo.

### Candidatos para borrar — requieren confirmación

| Archivo o grupo | Evidencia | Recomendación |
|---|---|---|
| docs/legacy/MCX-OPTIMIZE-optimize.py | Script histórico; no apareció una referencia de import en el barrido textual. Eso no demuestra que sea inútil. | Confirmar si debe conservarse como histórico. |
| docs/legacy/MCX-optimize.py | Script histórico separado; no se comprobó equivalencia total. | No borrar sin revisar procedencia/propósito. |
| docs/legacy/OPTIMIZE-optimize.py | Script histórico separado; no se comprobó equivalencia total. | No borrar sin revisar procedencia/propósito. |
| docs/legacy/motor.py | Se etiqueta como wrapper DEPRECATED; BIN/catedral es el punto de entrada canónico. | Candidato tras comprobar consumidores externos. |
| elite/FEX/trainer.py | Fachada de compatibilidad que delega en FEX/FEEDBACK/trainer.py; test_acceptance_contract.py prueba ambos caminos. | No borrar ahora; migrar consumidores primero y retirar solo tras una versión de compatibilidad. |
| docs/archive/MAPA_MAESTRO_DECOX_v0.2 a v0.7 | Versiones históricas referenciadas por documentación. No son duplicados byte a byte demostrados. | Mantener archivadas hasta confirmar política de retención. |

No se borró ninguno de estos archivos. Los nombres similares y la ausencia de una referencia textual no demuestran que un módulo sea prescindible.

## 3. Arquitectura Recomendada

Mantener la estructura modular por responsabilidades sin una migración masiva de rutas:

    BIN/catedral                 CLI canónica
    elite/PERCEIVE               datos y frescura
    elite/REASON                 análisis y regla central determinista
    elite/FEX/GOVERNANCE         restricciones y ciclo económico
    elite/FEX/FEEDBACK           métricas offline + feedback de usuario
    elite/DSX/DEFENSE            gobierno de ejecución
    elite/AEX/DECISION           intención/ejecución autorizada
    elite/MSX                    procedencia
    elite/contracts              contratos de salida y almacenamiento
    elite/bin                    comandos one-shot
    tests                        pruebas
    docs                         arquitectura, contratos y runbooks

Dirección de dependencia: PERCEIVE → REASON → contrato de resultado → verificación/entrega. FEX aporta evidencia y señales de retroalimentación. DSX gobierna permisos. AEX no sustituye la aceptación de CatedralX.

Separación obligatoria de tres planos:
- **Control:** tarea, prioridad, permisos, límites, deadline y parada.
- **Evidencia:** datos, fuente, timestamp, digest, supuestos y contraevidencia.
- **Entrega:** resultado validado, estado, razones y siguiente acción.

## 4. Mecánica Interna Optimizada

- Validar tipos y límites antes de mutar estado o escribir un ledger.
- Mantener separados ACCEPTED, REJECTED, BLOCKED_EVIDENCE, BLOCKED_UNCERTAINTY y BLOCKED_DEFICIT.
- No permitir que señales heurísticas cambien un veto central.
- Persistir resultados con result_id, cycle_id, trace_id y evaluation_hash.
- Separar tres ledgers por significado: predicción/outcome, eventos de impacto económico y feedback del usuario.
- Mantener escritura append-only, rutas fuera del checkout y reportes de solo lectura.
- Si falla la regla central, devolver un estado bloqueado con hash cuando la función central está disponible. Si el propio módulo no puede importarse, el contrato debe rechazar el resultado incompleto.
- Los cambios de política pasan por revisión, versionado, pruebas de regresión y aprobación explícita.

## 5. Retroalimentación Usuario ↔ Sistema

### Captura explícita

- result_id y/o cycle_id para trazabilidad.
- rating: entero exacto de 1 a 5.
- assessment: useful, partly_useful, not_useful, unclear o incorrect.
- reason_code: correctness, clarity, relevance, missing_context, level_of_detail, workflow, other o unspecified.
- preferred_next_step: none, explain, verify, revise o human_review.
- correction opcional de hasta 1000 caracteres.
- No captura nombre, correo, IP ni user_id. No introducir secretos ni datos personales en correction.

### Análisis

1. Validar el esquema, las enumeraciones, el rating y el vínculo de trazabilidad.
2. Guardar un evento append-only en user_feedback.jsonl.
3. Agregar promedio de rating y conteos por evaluación, motivo y siguiente paso.
4. Con menos de cinco eventos, pedir más muestra y evitar generalizaciones.
5. Con muestra suficiente, proponer revisión humana si los ratings son bajos o aparecen problemas de exactitud, claridad o contexto.
6. Contrastar correcciones con evidencia antes de cambiar código, reglas o prompts.

### Devolución de claridad

La captura devuelve FEEDBACK_RECORDED_FOR_REVIEW y explica que el comentario fue guardado para análisis. No promete cambios y no ajusta automáticamente umbrales, permisos, pesos ni modo de ejecución.

### Pseudocódigo

    recibir_feedback(evento):
        validar(evento)
        exigir(result_id o cycle_id)
        append_only(ledger_usuario, evento)
        devolver_confirmacion_sin_prometer_cambio()

    analizar_feedback():
        muestra = leer_ledger_solo_lectura()
        si muestra < 5:
            devolver("recolectar_mas_feedback")
        señales = agregar_por_rating_motivo_y_evaluacion(muestra)
        propuesta = recomendar_revision(señales)
        enviar_a_revision_humana(propuesta)

    aplicar_cambio(propuesta):
        exigir_contraste_con_evidencia()
        exigir_aprobacion_humana()
        versionar_cambio_y_pruebas()
        no_ajustar_umbrales_criticos_automaticamente()

## 6. Código y uso

Registrar una valoración asociada a un resultado:

    ./BIN/catedral user-feedback --result-id RESULT_ID --cycle-id CYCLE_ID --rating 2 --assessment unclear --reason-code missing_context --preferred-next-step explain

Consultar estadísticas de feedback:

    ./BIN/catedral user-feedback --report

Ruta por defecto: ~/.local/state/chalamandra/catedralx/user_feedback.jsonl. Se puede especificar una ruta externa con --path o CATEDRALX_USER_FEEDBACK_PATH. La API/formulario web debe invocar el mismo contrato desde Agents/producto; esa conexión externa todavía no se afirma como terminada.

## 7. Explicación Senior

El feedback de mercado responde «¿qué pasó después de una señal?». El feedback de usuario responde «¿el resultado ayudó, fue claro y estaba bien fundamentado?». Son señales distintas, deben quedar en ledgers distintos y jamás mezclarse como si una valoración humana demostrara que una predicción es correcta.

El sistema aprende primero en el sentido operativo de acumular evidencia y detectar patrones; no modifica su política automáticamente. La adaptación controlada exige una propuesta revisable, evidencia, aprobación, versión y prueba.

## 8. Recomendaciones Futuras

1. Conectar el formulario de la API/producto con el contrato de feedback y autenticar la escritura en la frontera API.
2. Proveer central_dimensions_bp mediante una fuente con esquema, procedencia y validación, no con defaults.
3. Unificar IDs de request, task, candidate, result y cycle entre CatedralX y Agents.
4. Preparar pruebas de extremo a extremo para cada uno de los tres flujos antes de habilitar cualquier automatización periódica.
5. Revisar los candidatos de eliminación uno por uno; no realizar borrados históricos por coincidencia de nombres.
