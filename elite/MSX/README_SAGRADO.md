# MSX — Testigo de procedencia

## Responsabilidad canónica

MSX construye y verifica evidencia de procedencia. No interpreta señales,
no decide estrategias, no autoriza órdenes y no ejecuta acciones.

Implementación actual:

- `elite/MSX/provenance.py` — construcción de registros, hash SHA-256 de
  entradas canónicas, hash del registro y verificación de cada registro
  contra el payload original recibido al cierre del ciclo.
- `aggregate_cycle()` — verifica todos los registros del ciclo, exige que
  se proporcione el payload original asociado a cada ID y genera un digest
  ordenado del manifiesto del ciclo.
- `elite/REASON/report_composition.py` — cierra la verificación de
  procedencia del informe cognitivo cuando recibe un `cycle_id`.
- `elite/REASON/master_cycle.py` — verifica los registros de su ciclo
  sintético antes de devolver el resultado.

## Garantías demostradas por el código

1. Serialización JSON canónica y determinista; los valores no serializables
   o no finitos se rechazan.
2. El hash de entrada se recalcula contra el payload original.
3. El hash del registro cubre sus campos, incluido el hash de entrada.
4. El agregador rechaza registros alterados, entradas originales ausentes,
   IDs duplicados y payloads sobrantes.
5. El manifiesto produce un hash SHA-256 sobre el ciclo y el orden de sus
   registros.

## Límites explícitos — todavía no equivalen a inmutabilidad

Los hashes anteriores permiten verificar correspondencia e integridad
cuando se dispone de los payloads originales. Por sí solos NO demuestran:

- identidad del productor o del firmante;
- autenticidad criptográfica del autor;
- almacenamiento append-only o inmutable;
- resistencia frente a la sustitución coordinada de un registro y su hash;
- anclaje externo del hash final del ciclo;
- detección de eliminación de un ciclo completo del almacenamiento.

No se debe describir MSX como un ledger persistente e inmutable hasta que
existan almacenamiento durable, política de identidad/firma, encadenamiento
o anclaje verificable y pruebas de manipulación/recuperación.

## Frontera de responsabilidad

Las herramientas de `elite/bin/` son CLI, puentes o despachadores. No son
la implementación interna de MSX. En particular, el envío a Agents no debe
clasificarse como una función de procedencia ni confundirse con el registro
de evidencia.

## Criterio de aceptación de esta etapa

La verificación de procedencia se considera implementada para los ciclos que
invocan `aggregate_cycle()` con los payloads originales. La identidad del
firmante y la persistencia inmutable siguen abiertas y bloquean la afirmación
de que el testigo MSX está completo.
