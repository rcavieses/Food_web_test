# 🌍 Dashboard de Grupos Funcionales

## Características

✨ **Vista General**: Resumen completo de todos los grupos con estadísticas
- Total de grupos
- Total de especies
- Promedio de especies por grupo
- Grupo con mayor número de especies

📊 **Tabla Interactiva**: Visualiza todos los grupos en una tabla ordenable y filtrable
- ID del grupo
- Nombre del grupo
- Descripción
- Cantidad de especies
- Hábitat
- Nivel trófico

🔍 **Exploración de Grupos**: Selecciona un grupo para ver:
- Descripción detallada del grupo
- Características completas (hábitat, nivel trófico, tamaño, afinidad taxonómica)
- Lista completa de especies
- Búsqueda/filtrado dentro de las especies del grupo
- Visualización en columnas o como texto expandible

📥 **Descarga de Datos**:
- Descargar especies del grupo actual en CSV
- Descargar todos los grupos con información detallada en CSV
- Descargar resumen de grupos en CSV

## Requisitos

```bash
pip install streamlit pandas
```

## Cómo ejecutar

### Opción 1: Desde la línea de comandos
```bash
streamlit run dashboard.py
```

### Opción 2: Desde PowerShell (en el directorio del proyecto)
```powershell
streamlit run dashboard.py
```

El dashboard se abrirá automáticamente en tu navegador en `http://localhost:8501`

## Estructura de datos esperada

El dashboard carga automáticamente el archivo `output/optimized_groups.json` que debe tener la siguiente estructura:

```json
[
  {
    "group_id": "FG46",
    "group_name": "Phytoplankton",
    "description": "...",
    "characteristics": {
      "habitat": "pelagic",
      "trophic_level": "primary_producer",
      "size_class": "small",
      "taxonomic_affinity": "..."
    },
    "species": ["especie1", "especie2", ...]
  }
]
```

## Funcionalidades principales

1. **Métricas en tiempo real**: Se actualizan automáticamente basándose en los datos cargados
2. **Búsqueda inteligente**: Filtra especies dentro de un grupo específico
3. **Descarga flexible**: Exporta los datos en el formato que necesites
4. **Interfaz responsiva**: Se adapta a diferentes tamaños de pantalla
5. **Caché de datos**: Los datos se cargan una sola vez para mejor rendimiento

## Tips de uso

- 💡 Ordena la tabla haciendo clic en los encabezados
- 🔍 Usa la barra de búsqueda para encontrar rápidamente una especie dentro de un grupo
- 📥 Descarga los datos en cualquier momento para análisis posterior
- ⌨️ Presiona `Ctrl+C` en la terminal para detener el servidor de Streamlit

## Solución de problemas

Si la aplicación no se abre:
1. Asegúrate de estar en el directorio correcto
2. Verifica que `output/optimized_groups.json` existe
3. Intenta actualizar Streamlit: `pip install --upgrade streamlit`

¡Disfruta explorando tus grupos funcionales! 🌟
