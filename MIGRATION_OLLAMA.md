# 🔄 Migración a Ollama - Resumen de Cambios

## Cambios Realizados

Este documento resume la migración del proyecto de **Anthropic Claude (API en la nube)** a **Ollama (LLM local)**.

### ¿Por qué Ollama?

✅ **Sin API keys** - Sin necesidad de credenciales en la nube
✅ **Privacidad** - Los datos nunca salen de tu máquina
✅ **Económico** - Sin costos de API o suscripción
✅ **Offline** - Funciona sin conexión a internet
✅ **Rápido** - Latencia muy baja (proceso local)
✅ **Flexible** - Puedes cambiar de modelo fácilmente

---

## Archivos Modificados

### 1. **config.py**
- ❌ Removido: `ANTHROPIC_API_KEY`
- ✅ Agregado: `OLLAMA_API_URL = "http://localhost:11434/api/generate"`
- ✅ Agregado: `OLLAMA_MODEL = "mistral"` (configurable)
- ✅ Agregado: `OLLAMA_TIMEOUT = 300` segundos

### 2. **llm_classifier.py**
- ❌ Removido: `from anthropic import Anthropic`
- ✅ Agregado: `import requests`
- ❌ Removido: `_get_client()` (función de Anthropic)
- ✅ Reescrito: `_call_llm()` para usar Ollama API

**Cambios en `_call_llm()`:**
```python
# Antes: Anthropic client
client = Anthropic(api_key=ANTHROPIC_API_KEY)
message = client.messages.create(...)

# Después: HTTP request a Ollama
requests.post(OLLAMA_API_URL, json=payload, timeout=OLLAMA_TIMEOUT)
```

### 3. **main.py**
- ❌ Removido: Verificación de `ANTHROPIC_API_KEY`
- ✅ Agregado: Verificación de conexión a Ollama
- ✅ Actualizado: Mensajes de error con instrucciones de Ollama
- ✅ Actualizado: Docstring con instrucciones de setup

### 4. **requirements.txt** (Nuevo)
```
pandas>=2.0.0
python-dotenv>=1.0.0
requests>=2.31.0
```

**Removido:** `anthropic` (ya no es necesario)

### 5. **.env.example** (Nuevo)
Plantilla para configuración local:
```env
OLLAMA_API_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=mistral
OLLAMA_TIMEOUT=300
```

### 6. **OLLAMA_SETUP.md** (Nuevo)
Guía completa de instalación y configuración:
- Instrucciones para Linux, macOS, Windows
- Modelos recomendados
- Solución de problemas
- Referencia rápida

### 7. **check_ollama.py** (Nuevo)
Script de validación para verificar:
- ✅ Ollama está instalado
- ✅ Ollama está ejecutándose
- ✅ Modelo seleccionado está disponible
- ✅ Lista de modelos instalados

Uso:
```bash
python check_ollama.py
```

### 8. **README.md**
- ✅ Actualizado: Descripción de sistema con Ollama
- ✅ Reescrito: Sección de instalación
- ✅ Actualizado: Instrucciones de uso
- ✅ Agregado: Link a OLLAMA_SETUP.md
- ✅ Agregado: Tabla comparativa Ollama vs servicios en la nube

---

## Cómo Utilizarlo

### Paso 1: Instalar Ollama

Descargar desde https://ollama.ai

### Paso 2: Descargar un modelo

```bash
# Recomendado (mistral - buen balance velocidad/calidad)
ollama pull mistral

# Alternativas:
ollama pull llama2          # Muy popular
ollama pull neural-chat     # Optimizado para chat
ollama pull orca-mini       # Más rápido, requiere menos memoria
```

### Paso 3: Ejecutar Ollama

En una terminal separada, mantén Ollama en ejecución:

```bash
ollama serve
```

Deberías ver:
```
2024/01/15 10:30:45 Listening on 127.0.0.1:11434
```

### Paso 4: Instalar dependencias

```bash
pip install -r requirements.txt
```

### Paso 5: Ejecutar el proyecto

```bash
# Verificar que todo está configurado correctamente
python check_ollama.py

# Ejecutar con LLM
python main.py

# Ejecutar sin LLM (para testing rápido)
python main.py --no-llm

# Cambiar modelo
OLLAMA_MODEL=llama2 python main.py
```

---

## Configuración

### Variables de entorno (`.env`)

```env
# URL de Ollama (por defecto)
OLLAMA_API_URL=http://localhost:11434/api/generate

# Modelo a usar
OLLAMA_MODEL=mistral

# Timeout en segundos (si el modelo es lento)
OLLAMA_TIMEOUT=300
```

### Modelos disponibles

| Modelo | Tamaño | Velocidad | Calidad | Recomendado |
|--------|--------|-----------|---------|-------------|
| **mistral** | 7B | ⚡⚡⚡ | ⭐⭐⭐ | ✅ Sí |
| neural-chat | 7B | ⚡⚡⚡ | ⭐⭐⭐ | ✅ Sí |
| llama2 | 7B-70B | ⚡⚡ | ⭐⭐⭐ | ✅ Sí |
| orca-mini | 3-13B | ⚡⚡⚡⚡ | ⭐⭐ | Para testing |
| zephyr | 7B | ⚡⚡⚡ | ⭐⭐⭐ | ✅ Sí |

---

## Troubleshooting

### "No se pudo conectar a Ollama"
```bash
# Verifica que Ollama está ejecutándose
ollama serve

# Verifica que tienes un modelo descargado
ollama list
```

### "Model not found"
```bash
# Descarga el modelo que especificaste
ollama pull mistral

# O verifica qué modelos tienes
ollama list
```

### "Timeout esperando respuesta"
- El modelo es demasiado lento para tu hardware
- Intenta con un modelo más pequeño: `ollama pull orca-mini`
- O aumenta el timeout: `OLLAMA_TIMEOUT=600` en `.env`

### Bajo rendimiento
- GPU no está siendo usada: verifica drivers CUDA/Metal
- Cambiar a modelo más pequeño: `ollama pull orca-mini`
- Cerrar otras aplicaciones que usen RAM

---

## Compatibilidad con código anterior

El código es **totalmente compatible** con la estructura anterior:

- ✅ Las funciones de clasificación funcionan igual
- ✅ Los archivos de entrada/salida son los mismos
- ✅ La lógica de optimización no cambió
- ✅ El modo `--no-llm` funciona igual
- ✅ Los parámetros de scoring son los mismos

---

## Próximos pasos

1. **Instala Ollama** desde https://ollama.ai
2. **Ejecuta** `ollama pull mistral`
3. **Inicia** `ollama serve` en otra terminal
4. **Instala dependencias** `pip install -r requirements.txt`
5. **Verifica** `python check_ollama.py`
6. **Ejecuta** `python main.py`

¡Listo! El proyecto está completamente funcional sin API keys.

---

## Referencia de cambios técnicos

| Aspecto | Antes (Anthropic) | Después (Ollama) |
|--------|-------------------|------------------|
| **Librería** | anthropic | requests |
| **API Key** | ANTHROPIC_API_KEY | (No necesaria) |
| **Modelo** | claude-sonnet-4 | mistral (configurable) |
| **URL** | api.anthropic.com | localhost:11434 |
| **Prompt format** | messages API | text prompt |
| **Costo** | $$ por token | $ (Gratis) |
| **Privacidad** | API en nube | Completamente local |
| **Velocidad** | Depende de red | Muy rápida (local) |

---

## Documentación adicional

- [OLLAMA_SETUP.md](OLLAMA_SETUP.md) - Guía completa de instalación
- [README.md](README.md) - Información del proyecto
- [check_ollama.py](check_ollama.py) - Script de validación
- [.env.example](.env.example) - Variables de entorno

---

**Proyecto Migrado:** ✅ Completado  
**Fecha:** Marzo 2026  
**Estado:** Listo para usar con Ollama
