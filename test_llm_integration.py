#!/usr/bin/env python3
"""
test_llm_integration.py - Test breve de integración LLM + main
==============================================================
Verifica rápidamente que:
1. Ollama está conectado y funcionando
2. El LLM puede responder una consulta simple
3. El classify_species_into_groups funciona
4. El pipelina completo funciona (con pocas especies)

Ejecución: ~30 segundos (vs ~5 min el main.py completo)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import OLLAMA_MODEL, OLLAMA_API_URL
from llm_classifier import _call_llm, classify_species_into_groups
from data_loader import (
    load_species_data,
    get_unique_species,
    load_existing_groups,
    species_to_text_list,
    groups_to_text,
)


def test_0_ollama_connection():
    """Test 0: Verificar que Ollama está disponible"""
    print("\n" + "="*70)
    print("TEST 0: Verificar conexión a Ollama")
    print("="*70)
    print(f"URL: {OLLAMA_API_URL}")
    print(f"Modelo: {OLLAMA_MODEL}")
    
    try:
        import requests
        response = requests.post(
            OLLAMA_API_URL,
            json={"model": OLLAMA_MODEL, "prompt": "test", "stream": False},
            timeout=60,
        )
        if response.status_code == 200:
            print("✅ Ollama conectado y respondiendo")
            return True
        else:
            print(f"❌ Ollama respondió con estado {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        print(f"   Asegúrate que ejecutaste: ollama serve")
        return False


def test_1_simple_llm_call():
    """Test 1: Llamada simple al LLM"""
    print("\n" + "="*70)
    print("TEST 1: Llamada simple al LLM")
    print("="*70)
    
    try:
        system_prompt = "Eres un ecólogo marino breve y conciso."
        user_prompt = "¿Qué es un grupo funcional? (respuesta en 1 línea)"
        
        print(f"\nPrompt: '{user_prompt}'")
        print("Esperando respuesta del LLM...")
        
        response = _call_llm(system_prompt, user_prompt)
        
        if response and len(response) > 10:
            print(f"✅ Respuesta recibida ({len(response)} caracteres):")
            print(f"   {response[:150]}..." if len(response) > 150 else f"   {response}")
            return True
        else:
            print(f"❌ Respuesta vacía o demasiado corta: {response}")
            return False
            
    except Exception as e:
        print(f"❌ Error en llamada LLM: {e}")
        return False


def test_2_json_extraction():
    """Test 2: Extracción de JSON de respuesta"""
    print("\n" + "="*70)
    print("TEST 2: Extracción de JSON de respuesta")
    print("="*70)
    
    try:
        from llm_classifier import _extract_json_from_response
        
        # Respuesta simulada de LLM
        test_response = """Aquí está la clasificación:
```json
{
  "assignments": [
    {"species": "Sardinops sagax", "group_id": "FG02", "reason": "small pelagic schooling fish"},
    {"species": "Atractoscion nobilis", "group_id": "FG05", "reason": "demersal drum"}
  ]
}
```
"""
        
        print("Parseando JSON de respuesta simulada...")
        result = _extract_json_from_response(test_response)
        
        if "assignments" in result and len(result["assignments"]) == 2:
            print(f"✅ JSON extraído correctamente ({len(result['assignments'])} items)")
            for item in result["assignments"]:
                print(f"   - {item['species']} → {item['group_id']}")
            return True
        else:
            print(f"❌ JSON inválido o incompleto: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Error en extracción JSON: {e}")
        return False


def test_3_small_species_classification():
    """Test 3: Clasificar pocas especies (prueba real)"""
    print("\n" + "="*70)
    print("TEST 3: Clasificar 5 especies (prueba real del LLM)")
    print("="*70)
    
    try:
        # Cargar datos
        raw_df = load_species_data()
        species_df = get_unique_species(raw_df)
        
        # Usar solo 5 especies
        test_species_df = species_df.iloc[:5].copy()
        initial_groups = load_existing_groups()
        
        print(f"\nEspecies de prueba ({len(test_species_df)}):")
        for i, (_, sp) in enumerate(test_species_df.iterrows(), 1):
            print(f"  {i}. {sp['species_name']}")
        
        # Preparar texto
        species_text = species_to_text_list(test_species_df)
        groups_text = groups_to_text(initial_groups)
        
        print(f"\nClasificando con LLM ({OLLAMA_MODEL})...")
        groups, unassigned = classify_species_into_groups(
            species_text, 
            groups_text, 
            initial_groups.copy()
        )
        
        assigned_count = sum(len(g['species']) for g in groups)
        print(f"\n✅ Clasificación completada:")
        print(f"   - Asignadas: {assigned_count}")
        print(f"   - Sin grupo: {len(unassigned)}")
        
        if assigned_count > 0:
            print(f"\nAsignaciones:")
            for group in groups:
                if group['species']:
                    print(f"   {group['group_id']} ({group['group_name']}): {group['species']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en clasificación: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Ejecuta todos los tests"""
    print("\n" + "╔" + "="*68 + "╗")
    print("║" + " "*15 + "TEST DE INTEGRACIÓN LLM + MAIN" + " "*21 + "║")
    print("╚" + "="*68 + "╝")
    
    tests = [
        ("Conexión a Ollama", test_0_ollama_connection),
        ("Llamada simple LLM", test_1_simple_llm_call),
        ("Extracción JSON", test_2_json_extraction),
        ("Clasificación 5 especies", test_3_small_species_classification),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except KeyboardInterrupt:
            print("\n\n⚠️  Test interrumpido por usuario")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Error no esperado: {e}")
            results.append((test_name, False))
    
    # Resumen
    print("\n" + "="*70)
    print("RESUMEN DE TESTS")
    print("="*70)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:<40} {status}")
    
    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)
    
    print("="*70)
    print(f"\nResultado: {passed_count}/{total_count} tests pasados\n")
    
    if passed_count == total_count:
        print("🎉 ¡TODO FUNCIONA! El LLM está integrado correctamente.")
        print("\nAhora puedes ejecutar:")
        print("  python main.py              # Con todas las especies")
        print("  python test_quick.py        # Test rápido (300 especies)")
        return 0
    elif passed_count >= 2:
        print("⚠️  Algunos tests fallaron. Revisa los errores arriba.")
        print("\nComandos para debug:")
        print("  python check_ollama.py      # Verificar Ollama")
        print("  ollama list                 # Listar modelos")
        print("  OLLAMA_MODEL=llama2 python test_llm_integration.py  # Cambiar modelo")
        return 1
    else:
        print("❌ Múltiples fallos. Ollama probablemente no está ejecutándose.")
        print("\nSoluciones:")
        print("  1. ollama pull mistral      # Descargar modelo")
        print("  2. ollama serve             # Ejecutar Ollama en otra terminal")
        print("  3. python check_ollama.py   # Verificar configuración")
        return 1


if __name__ == "__main__":
    sys.exit(main())
