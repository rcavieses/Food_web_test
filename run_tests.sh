#!/bin/bash
# run_tests.sh - Script para ejecutar todos los tests de manera secuencial
# =========================================================================
# Uso: ./run_tests.sh
# O:   bash run_tests.sh

set -e  # Salir si algo falla

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║        SUITE DE TESTS - LLM + MAIN                    ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# TEST 1: Verificar Ollama está instalado
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}TEST 1: Verificar instalación de Ollama${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"

if command -v ollama &> /dev/null; then
    VERSION=$(ollama --version 2>/dev/null || echo "desconocida")
    echo -e "${GREEN}✅ Ollama está instalado: ${VERSION}${NC}"
else
    echo -e "${RED}❌ Ollama no está instalado${NC}"
    echo "   Descarga desde: https://ollama.ai"
    exit 1
fi

echo ""

# TEST 2: Verificar que Ollama está ejecutándose
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}TEST 2: Verificar que Ollama está ejecutándose${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"

python check_ollama.py
OLLAMA_CHECK=$?

if [ $OLLAMA_CHECK -ne 0 ]; then
    echo -e "${RED}❌ Ollama no está respondiendo correctamente${NC}"
    echo "   Ejecuta en otra terminal: ollama serve"
    exit 1
fi

echo ""

# TEST 3: Test de integración LLM
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}TEST 3: Test de Integración LLM (5 especies)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"

python test_llm_integration.py
INTEGRATION_CHECK=$?

echo ""

if [ $INTEGRATION_CHECK -eq 0 ]; then
    echo -e "${GREEN}✅ Integración LLM funcionando correctamente${NC}"
    echo ""
    
    # TEST 4: Test rápido (opcional)
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}TEST 4: Test Rápido (300 especies)${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${YELLOW}¿Deseas ejecutar test_quick.py ahora? (s/n)${NC}"
    read -r response
    
    if [[ "$response" =~ ^[sS] ]]; then
        python test_quick.py
    else
        echo "Test quick omitido."
    fi
    
    echo ""
    echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}🎉 ¡TODOS LOS TESTS PASARON!${NC}"
    echo -e "${GREEN}════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "Ahora puedes ejecutar:"
    echo -e "  ${BLUE}python main.py${NC}              # Pipeline completo"
    echo -e "  ${BLUE}python test_quick.py${NC}        # Test con 300 especies"
    echo ""
    echo "O cambiar modelo:"
    echo -e "  ${BLUE}OLLAMA_MODEL=llama2 python main.py${NC}"
    echo ""
else
    echo -e "${RED}❌ Test de integración falló${NC}"
    echo ""
    echo "Posibles soluciones:"
    echo "  1. Verifica Ollama: ps aux | grep ollama"
    echo "  2. Reinicia Ollama: ollama serve"
    echo "  3. Descarga modelo: ollama pull mistral"
    echo "  4. Revisa los logs en la ventana de Ollama"
    exit 1
fi
