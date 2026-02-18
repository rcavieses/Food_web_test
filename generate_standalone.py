#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Genera una versión standalone del dashboard sin dependencia de servidor"""

import json
import sys

def generate_standalone_dashboard():
    # Leer los datos
    with open('output/optimized_groups.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Minificar JSON
    json_str = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
    
    # Leer el HTML original
    with open('dashboard.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Crear la nueva función loadData
    new_loadData = f'''        function loadData() {{
            // Datos incrustados directamente en el archivo (sin necesidad de servidor)
            const groupsData = {json_str};
            allGroups = groupsData;
            filteredGroups = [...allGroups];
            renderGroups();
            updateStats();
        }}'''
    
    # Encontrar y reemplazar la función loadData
    start_marker = '        async function loadData() {'
    
    start_idx = html_content.find(start_marker)
    if start_idx != -1:
        # Encontrar el cierre correcto de la función
        brace_count = 0
        i = start_idx
        end_idx = -1
        for j in range(start_idx + len(start_marker), len(html_content)):
            if html_content[j] == '{':
                brace_count += 1
            elif html_content[j] == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_idx = j + 1
                    break
        
        if end_idx != -1:
            # Reemplazar la función
            modified_html = html_content[:start_idx] + new_loadData + html_content[end_idx:]
            
            # Guardar el nuevo archivo
            with open('dashboard-standalone.html', 'w', encoding='utf-8') as f:
                f.write(modified_html)
            
            print("✅ Dashboard standalone creado exitosamente!")
            print(f"   Archivo: dashboard-standalone.html")
            print(f"   Tamaño: {len(modified_html) / 1024:.1f} KB")
            print(f"   Estado: Completamente independiente (sin servidor)")
            return True
        else:
            print("❌ Error: No se pudo encontrar el cierre de la función loadData")
            return False
    else:
        print("❌ Error: No se encontró la función loadData")
        return False

if __name__ == '__main__':
    success = generate_standalone_dashboard()
    sys.exit(0 if success else 1)
