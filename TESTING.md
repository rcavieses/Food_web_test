# 🧪 Testing Rápido del LLM

## 🎯 Opción Recomendada: Suite de Tests Automática

Ejecuta TODOS los tests de una vez:

```bash
./run_tests.sh
```

O en Windows:

```bash
python test_llm_integration.py
```

Esto ejecutará automáticamente:
1. ✅ Verificar Ollama instalado
2. ✅ Verificar Ollama ejecutándose  
3. ✅ Test de integración LLM (5 especies - ~30 seg)
4. ❓ Pregunta si deseas ejecutar test_quick.py (300 especies - ~2-3 min)

---

## 📋 Opciones de Testing Individual

### 1️⃣ **Test Completo de Integración** (Recomendado - ~30 segundos)

```bash
python test_llm_integration.py
```

**Valida:**
- ✅ Ollama está conectado
- ✅ LLM puede responder
- ✅ Extracción de JSON funciona
- ✅ Clasificación real (5 especies)

**Output:**
```
TEST 0: Verificar conexión a Ollama
✅ Ollama conectado y respondiendo

TEST 1: Llamada simple al LLM
✅ Respuesta recibida...

TEST 2: Extracción de JSON de respuesta
✅ JSON extraído correctamente

TEST 3: Clasificar 5 especies (prueba real del LLM)
✅ Clasificación completada

RESUMEN: 4/4 tests pasados
🎉 ¡TODO FUNCIONA!
```

---

### 2️⃣ **Test Rápido con 300 especies** (~2-3 minutos)

```bash
python test_quick.py
```

**Prueba:**
- Clasificación con 300 especies (en lugar de todas)
- Evaluación de grupos
- Genera reporte de scores

---

### 3️⃣ **Verificar Configuración de Ollama** (Instantáneo)

```bash
python check_ollama.py
```

**Verifica:**
- Ollama está instalado
- Ollama está ejecutándose
- Modelo disponible
- Lista de modelos descargados

---

### 4️⃣ **Test Completo con Main** (~5-10 minutos)

```bash
python main.py
```

**Nota:** Primera ejecución será más lenta porque procesa todas las especies.

---

## 🚀 Workflow Recomendado

```bash
# Paso 1: Asegúrate que Ollama esté ejecutándose
ollama serve  # En una terminal separada

# Paso 2: En otra terminal, verifica el setup
python check_ollama.py

# Paso 3: Test rápido de integración (30 seg)
python test_llm_integration.py

# Si TEST 3 pasa, el LLM funciona! ✅
# Ahora puedes ejecutar:

# Paso 4: Test con más datos (2-3 min)
python test_quick.py

# Paso 5: Test completo (5-10 min)
python main.py
```

---

## 🔧 Troubleshooting

### "Ollama no conecta"
```bash
# Verificar estado
python check_ollama.py

# Reiniciar Ollama en otra terminal
ollama serve
```

### "Modelo no disponible"
```bash
# Listar modelos
ollama list

# Descargar modelo faltante
ollama pull mistral

# Usar otro modelo disponible
OLLAMA_MODEL=llama2 python test_llm_integration.py
```

### "Timeout esperando respuesta"
- El modelo es lento para tu hardware
- Prueba con modelo más pequeño: `ollama pull orca-mini`
- Aumenta timeout: `OLLAMA_TIMEOUT=600` en `.env`

---

## 📊 Comparación de Tests

| Test | Tiempo | Cobertura | Propósito |
|------|--------|-----------|----------|
| test_llm_integration.py | ~30 seg | Integración | Verificar LLM funciona |
| test_quick.py | 2-3 min | 300 esp | Validar clasificación |
| main.py | 5-10 min | Todas | Resultado final |

---

## ✨ Tips

- **Primer test:** Siempre ejecuta `test_llm_integration.py` primero
- **Cambiar modelo:** `OLLAMA_MODEL=llama2 python test_llm_integration.py`
- **Debug:** Si algo falla, revisa los logs en la ventana de `ollama serve`
- **Más rápido:** Usa modelo más pequeño como `orca-mini`

---

## 📝 Ejemplos de Ejecución

### Verificación rápida
```bash
python check_ollama.py && python test_llm_integration.py
```

### Test con modelo alternativo
```bash
OLLAMA_MODEL=llama2 python test_llm_integration.py
```

### Test con timeout aumentado
```bash
OLLAMA_TIMEOUT=600 python main.py
```

---

**¡Listo para empezar!** 🎉
