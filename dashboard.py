import streamlit as st
import json
import pandas as pd
from pathlib import Path

# Configuración de la página
st.set_page_config(
    page_title="Functional Groups Dashboard",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos visuales mejorados
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .group-header {
        color: #0066cc;
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 20px;
    }
    .species-count {
        font-size: 18px;
        color: #ff6b6b;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def load_groups():
    """Carga los grupos desde el archivo JSON"""
    file_path = Path(__file__).parent / "output" / "optimized_groups.json"
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# Cargar datos
groups = load_groups()

# Título principal
st.title("🌍 Functional Groups Dashboard")
st.markdown("---")

# Crear resumen de grupos
groups_summary = []
for group in groups:
    groups_summary.append({
        "Grupo ID": group['group_id'],
        "Nombre": group['group_name'],
        "Descripción": group['description'],
        "Cantidad de Especies": len(group['species']),
        "Hábitat": group['characteristics']['habitat'],
        "Nivel Trófico": group['characteristics']['trophic_level']
    })

df_summary = pd.DataFrame(groups_summary)

# Sección 1: Vista General de Grupos
st.subheader("📊 Resumen de Grupos")

# Métricas generales
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total de Grupos", len(groups))
with col2:
    st.metric("Total de Especies", sum(len(g['species']) for g in groups))
with col3:
    st.metric("Promedio por Grupo", f"{sum(len(g['species']) for g in groups) / len(groups):.1f}")
with col4:
    st.metric("Grupo con más", f"{max(len(g['species']) for g in groups)} especies")

st.markdown("---")

# Tabla interactiva de grupos
st.subheader("📋 Todos los Grupos")
st.dataframe(
    df_summary.sort_values("Cantidad de Especies", ascending=False),
    use_container_width=True,
    height=400
)

st.markdown("---")

# Sección 2: Exploración de Grupos Individuales
st.subheader("🔍 Explorar Especies por Grupo")

# Selector de grupo
col1, col2 = st.columns([2, 1])
with col1:
    group_options = [f"{g['group_id']} - {g['group_name']}" for g in groups]
    selected_group = st.selectbox("Selecciona un grupo:", group_options)

# Obtener el grupo seleccionado
selected_group_id = selected_group.split(" - ")[0]
selected_group_data = next(g for g in groups if g['group_id'] == selected_group_id)

with col2:
    st.metric("Especies en este grupo", len(selected_group_data['species']))

# Mostrar detalles del grupo
st.markdown("#### 📝 Información del Grupo")
col1, col2 = st.columns(2)

with col1:
    st.write("**Descripción:**")
    st.write(selected_group_data['description'])
    
with col2:
    st.write("**Características:**")
    chars = selected_group_data['characteristics']
    st.write(f"- **Hábitat:** {chars['habitat']}")
    st.write(f"- **Nivel Trófico:** {chars['trophic_level']}")
    st.write(f"- **Clase de Tamaño:** {chars['size_class']}")
    st.write(f"- **Afinidad Taxonómica:** {chars['taxonomic_affinity']}")

st.markdown("---")

# Mostrar especies del grupo seleccionado
st.markdown("#### 🐟 Lista de Especies")
species_list = selected_group_data['species']

# Opción de búsqueda dentro del grupo
search_term = st.text_input("🔍 Buscar especie en este grupo:", placeholder="Escribe el nombre de una especie...")

if search_term:
    filtered_species = [s for s in species_list if search_term.lower() in s.lower()]
    st.write(f"Se encontraron {len(filtered_species)} especies coincidentes:")
else:
    filtered_species = species_list

# Mostrar especies en columnas
cols = st.columns(3)
for idx, species in enumerate(filtered_species):
    with cols[idx % 3]:
        st.markdown(f"**{idx + 1}. {species.title()}**")

# Expandible para ver todos en texto
with st.expander(f"Ver todas las {len(filtered_species)} especies como texto"):
    st.text("\n".join([f"{idx + 1}. {s.capitalize()}" for idx, s in enumerate(filtered_species)]))

# Opción de descargar como CSV
st.markdown("---")
st.subheader("📥 Descargar Datos")

col1, col2, col3 = st.columns(3)

with col1:
    # Descargar grupo actual
    csv_group = pd.DataFrame({
        "Especie": filtered_species,
        "Grupo": selected_group_id,
        "Nombre del Grupo": selected_group_data['group_name']
    })
    st.download_button(
        label="⬇️ Descargar especies del grupo actual",
        data=csv_group.to_csv(index=False),
        file_name=f"{selected_group_id}_species.csv",
        mime="text/csv"
    )

with col2:
    # Descargar todos los grupos
    all_data = []
    for group in groups:
        for species in group['species']:
            all_data.append({
                "Especie": species,
                "Grupo ID": group['group_id'],
                "Nombre del Grupo": group['group_name'],
                "Hábitat": group['characteristics']['habitat'],
                "Nivel Trófico": group['characteristics']['trophic_level']
            })
    
    csv_all = pd.DataFrame(all_data)
    st.download_button(
        label="⬇️ Descargar todos los grupos",
        data=csv_all.to_csv(index=False),
        file_name="all_functional_groups.csv",
        mime="text/csv"
    )

with col3:
    # Descargar resumen
    st.download_button(
        label="⬇️ Descargar resumen de grupos",
        data=df_summary.to_csv(index=False),
        file_name="groups_summary.csv",
        mime="text/csv"
    )

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; font-size: 12px;'>
    📊 Dashboard de Grupos Funcionales | Datos cargados desde: output/optimized_groups.json
</div>
""", unsafe_allow_html=True)
