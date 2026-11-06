# Identidad Canónica — CatedralX
## Registro: 2026-11-06

### Definición Oficial
- **Canónica**: Chalamandra-Magistral-deco/CatedralX
- **Remoto canónico configurado**: https://github.com/Chalamandra-Magistral-deco/CatedralX.git (`origin`)
- **Remotos heredados**: `canonico` y `chalamandrax` → git@github.com:ChalamandraX/CatedralX.git
- **Estado**: `main` alineada con `origin/main`; los alias SSH heredados se conservan temporalmente

### Resolución
- Mantener como referencia canónica: Chalamandra-Magistral-deco/CatedralX
- Opción elegida: A) Alias local sin cambio en GitHub; `origin` queda como remoto canónico y `main` sigue `origin/main`. Los alias SSH heredados se conservan, sin uso operativo.

### Trazabilidad
- Documento creado: 2026-11-06
- Alineación ejecutada: 2026-11-06 (upstream local; sin push ni cambios remotos)

### Estado operativo verificado — 2026-11-06
- Remoto canónico configurado en `origin`: `https://github.com/Chalamandra-Magistral-deco/CatedralX.git`.
- `main` sigue ahora a `origin/main`.
- HEAD local y remoto verificado: `e1dcd47376b5016c4acb2103de1711fa6abc65a8`.
- Los remotos SSH heredados `canonico` y `chalamandrax` se conservaron; ambos apuntan al repositorio antiguo `ChalamandraX/CatedralX` y su autenticación SSH no está disponible en esta VM.
- No se renombró ni eliminó ningún repositorio remoto y no se hizo push.
- La imagen base `catedralx:v1.0-canonico` fue reconstruida desde el snapshot Git de `e1dcd47376b5016c4acb2103de1711fa6abc65a8` y lleva esa revisión como etiqueta OCI.
