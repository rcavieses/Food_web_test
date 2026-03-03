# 🧪 Resumen de Tests Disponibles

## 📊 Árbol de Decisión

```
¿Quieres probar rápidamente el LLM?
│
├─→ SÍ, con 1 click (RECOMENDADO)
│   └─→ ./run_tests.sh  [TESTING AUTOMATIZADO]
│       ├─ Verifica Ollama
│       ├─ Test integración (30 seg)
│       └─ Pregunta por test_quick (2-3 min)
│
├─→ SÍ, pero elijo qué test ejecutar
│   ├─→ python check_ollama.py
│   │   └─ Verifica setup (5 seg)
│   │
│   ├─→ python test_llm_integration.py
│   │   └─ Test de integración (30 seg)
│   │
│   ├─→ python test_quick.py
│   │   └─ 300 especies (2-3 min)
│   │
│   └─→ python main.py
│       └─ Pipeline completo (5-10 min)
│
└─→ NO, voy directo al main
    └─→ python main.py --no-llm  [Sin LLM]
```

---

## 📁 Archivos de Test Creados

### Nuevos Scripts

| Script | Tiempo | Propósito | Ejecuta |
|--------|--------|----------|---------|
| `run_tests.sh` | ~2 min | ⭐ Suite automática | check + integración + quick |
| `test_llm_integration.py` | ~30 seg | Valida LLM funciona | 4 tests: conexión, LLM, JSON, clasificación |
| `check_ollama.py` | ~5 seg | Verifica setup | Estado Ollama, modelo, instalación |
| `test_quick.py` | 2-3 min | Test con datos | Clasificación de 300 especies |
| `main.py` | 5-10 min | Pipeline completo | Todas las especies (LENTO) |

---

## 🚀 Como Empezar: Recomendación

### Opción A: Automatizado (Recomendado) ⭐

```bash
# Paso 1: Terminal 1 - Ejecutar Ollama
ollama serve

# Paso 2: Terminal 2 - Ejecutar tests automáticos
cd Functional_groups_creator_clasiffier
./run_tests.sh

# Si TODO PASA, ejecuta:
python main.py
```

### Opción B: Manual (Control total)

```bash
# Terminal 1: Ollama
ollama serve

# Terminal 2: Tests específicos
python check_ollama.py
python test_llm_integration.py
python test_quick.py
python main.py
```

---

## 📝 Detalles de Cada Test

### `run_tests.sh` - Suite Automática ⭐
- **Usa:** Bash (Linux/Mac) o Python en Windows
- **Ejecuta:** Check + Integración + Pregunta por Quick
- **Tiempo:** ~2-3 minutos (configurável)
- **Mejor para:** Verificación rápida inicial

### `test_llm_integration.py` - Validación LLM
**4 Sub-tests:**
1. Conexión a Ollama ✅
2. Llamada simple LLM ✅
3. Extracción JSON ✅
4. Clasificación 5 especies ✅

**Éxito = El LLM está listo**

### `check_ollama.py` - Diagnóstico
Verifica:
- ✅ Ollama instalado
- ✅ Ollama ejecutándose
- ✅ Modelo disponible
- ✅ Lista de modelos

### `test_quick.py` - Datos Reales
- 300 especies (muestra representativa)
- Clasificación LLM completa
- Generación de scores
- ~2-3 minutos

### `main.py` - Pipeline Completo
- Todas las especies
- Iteraciones de optimización
- Reporte final
- ~5-10 minutos

---

## 🎯 Flujo Recomendado

```
INICIO
  ↓
[ollama serve] (Terminal 1)
  ↓
./run_tests.sh (Terminal 2)
  ↓
  ├─ TEST 1: ✅ Ollama instalado
  ├─ TEST 2: ✅ Ollama ejecutándose
  ├─ TEST 3: ✅ Integración LLM
  │
  ├─→ ¿Ejecutar test_quick? (s/n)
  │   ├─ SÍ  → ~2-3 min, valida con datos reales
  │   └─ NO  → salta al main directo
  │
  └─ ¿Resultado?
     ├─→ ✅ TODOS PASAN
     │   └─→ python main.py
     │
     └─→ ❌ ALGUNO FALLA
         └─→ Revisar mensajes de error
```

---

## 🔧 Troubleshooting

### Si `run_tests.sh` falla en Windows

Ejecuta manualmente en línea:
```bash
python check_ollama.py && python test_llm_integration.py
```

### Si `test_llm_integration.py` TEST 3 falla

Posibles causas:
- Modelo muy lento para clasificación (cambiar modelo)
- Timeout muy corto (aumentar `OLLAMA_TIMEOUT` en `.env`)
- Error de parsing JSON (revisar logs de Ollama)

### Si solo TEST 0-1 pasan

Ollama está ejecutándose pero el LLM es lento:
```bash
# Intenta con modelo más pequeño
ollama pull orca-mini
OLLAMA_MODEL=orca-mini python test_llm_integration.py
```

---

## 📊 Matriz de Decisión

| Necesito... | Usa... | Tiempo |
|-------------|--------|--------|
| Verificar setup rápido | `check_ollama.py` | 5 seg |
| Validar LLM funciona | `test_llm_integration.py` | 30 seg |
| Test con datos reales | `test_quick.py` | 2-3 min |
| Suite automática completa | `./run_tests.sh` | 2-3 min |
| Resultado final completo | `python main.py` | 5-10 min |

---

## ✨ Tips Pro

### Cambiar modelo durante tests
```bash
# Usar Llama2 en lugar de Mistral
OLLAMA_MODEL=llama2 ./run_tests.sh
OLLAMA_MODEL=llama2 python test_llm_integration.py
```

### Aumentar timeout para modelos lentos
```bash
# En .env o variable de entorno
OLLAMA_TIMEOUT=600 python test_quick.py
```

### Ejecutar solo un test específico en test_llm_integration.py
Edita el final del script y descomenta solo el test que quieras

### Ejecutar main sin LLM para debugging
```bash
python main.py --no-llm
```

---

## 📋 Checklist Inicial

- [ ] Ollama descargado e instalado
- [ ] Modelo descargado (`ollama pull mistral`)
- [ ] `ollama serve` ejecutándose
- [ ] Dependencias instaladas (`pip install -r requirements.txt`)
- [ ] `./run_tests.sh` ejecutado exitosamente
- [ ] Listo para `python main.py` 🎉

---

**¿Primer uso?** → Ejecuta `./run_tests.sh`  
**¿Problemas?** → Revisa `TESTING.md` o `OLLAMA_SETUP.md`  
**¿Listo?** → `python main.py` 🚀
