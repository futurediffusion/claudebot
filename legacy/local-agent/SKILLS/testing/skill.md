# Testing Skill

## Propósito
Ejecutar pruebas y reportar resultados. Soporta múltiples frameworks
de testing (pytest, unittest, node test, etc.).

## Archivos
- `run_tests.py` - Script principal de ejecución de pruebas

## Uso

### run_tests.py
```bash
python SKILLS/testing/run_tests.py [path] [--framework pytest|unittest|all]
```
- `[path]`: Carpeta o archivo a probar (default: actual directory)
- `--framework`: Framework específico a usar
- Sin argumentos: auto-detecta y ejecuta todas las pruebas

## Output ejemplo
```
TEST RUN: /path/to/project
FRAMEWORK: pytest
COLLECTED: 47 tests
RESULTS:
  PASSED: 44
  FAILED: 2
  SKIPPED: 1
DURATION: 12.3s

FAILURES:
1. test_user_login - AssertionError: expected 'admin' got 'user'
2. test_api_timeout - timeout after 30s
```

## Dependencias
- pytest (para tests Python)
- unittest (stdlib)
- node test / jest (para JS/TS)

## Loggers
- Los resultados completos se guardan en `LOGS/test_<timestamp>.log`
- Los fracasos se registran en `MEMORY/failures.md`