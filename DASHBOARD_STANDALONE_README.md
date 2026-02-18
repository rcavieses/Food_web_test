# Dashboard Grupos Funcionales - Versión Standalone

## ¿Qué es esto?

Un dashboard completamente **independiente** que no requiere servidor. Puedes abrirlo directamente con tu navegador.

## Cómo usar

### Opción 1: Abrir directamente (La más fácil)
1. Localiza el archivo `dashboard-standalone.html` en esta carpeta
2. **Haz doble clic** para abrir en tu navegador
3. ¡Listo! El dashboard cargará automáticamente con todos los datos

### Opción 2: Arrastrar y soltar
- Arrastra `dashboard-standalone.html` a tu navegador

### Opción 3: Desde Terminal
```bash
# Windows
start dashboard-standalone.html

# macOS
open dashboard-standalone.html

# Linux
xdg-open dashboard-standalone.html
```

## ¿Por qué no necesita servidor?

- **Datos incrustados**: Todos los datos JSON están embebidos directamente en el HTML (~137 KB)
- **JavaScript local**: Toda la lógica funciona en tu navegador
- **Sin dependencias externas**: Es un archivo completamente autónomo

## Compatibilidad

✅ Chrome / Chromium  
✅ Firefox  
✅ Safari  
✅ Edge  
✅ Opera  

## Funcionalidades

- 📊 Visualización de todos los grupos funcionales
- 🔍 Búsqueda por nombre o descripción
- 📋 Lista de especies por grupo
- 📈 Estadísticas generales
- 🎨 Interfaz responsiva

## Límites del navegador

- Funciona mejor con grupos de datos hasta ~150 KB (este tiene ~137 KB ✅)
- Los navegadores modernos manejan sin problema archivos de este tamaño
- No hay límites de funcionalidad

## ¿Qué versiones tienes?

- **dashboard.html** - Original que requiere servidor (`python serve.py`)
- **dashboard-standalone.html** ⭐ - Nuevo, sin servidor, ideal para compartir

## Para compartir

Solo necesitas compartir el archivo `dashboard-standalone.html` a otros usuarios. Ellos pueden:
- Descargarlo
- Abrirlo directamente sin instalar nada
- Usar todos los datos sin conexión a internet

---

**¿Problema?** Si algo no funciona:
1. Asegúrate de que el archivo sea `dashboard-standalone.html`
2. Intenta en otro navegador
3. Borra el caché del navegador (Ctrl+Shift+Delete en Chrome)

