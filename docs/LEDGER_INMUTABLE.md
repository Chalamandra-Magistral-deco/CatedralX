# Ledger inmutable encadenado

El archivo `01-TARGETS/ledger.json` es el registro de eventos. El mecanismo
Python vive en `elite/targets/ledger.py` y aplica:

- IDs secuenciales `evt-0000001`, `evt-0000002`, etc.
- SHA-256 sobre JSON canónico (claves ordenadas, UTF-8, sin espacios y sin NaN).
- Encadenamiento desde un hash génesis de 64 ceros.
- Firma Ed25519 del hash hexadecimal de entrada codificado en UTF-8.
- Verificación completa de la cadena antes y después de cada anexado.
- Escritura atómica y bloqueo exclusivo local durante el append.

## Claves

El llamador proporciona la clave privada Ed25519 y el mapa de claves públicas
autorizadas. La clave privada no se serializa ni se guarda en el repositorio.
El identificador de clave forma parte del hash de entrada.

## Límites de seguridad

Este mecanismo aporta detección criptográfica de alteraciones y serialización
de escrituras cooperantes en un único sistema de archivos POSIX. No convierte
por sí solo el archivo en almacenamiento físicamente inmutable: una persona con
permisos suficientes puede reemplazar el archivo, la clave pública autorizada
o reescribir toda la cadena. Para resistencia adicional se requieren permisos
de almacenamiento, copias de seguridad protegidas, gestión externa de claves
y anclajes periódicos del último hash en un sistema independiente.

El archivo de bloqueo `ledger.json.lock` es operativo; no forma parte del ledger.
