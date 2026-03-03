#!/usr/bin/env python3
"""
translate_to_english.py - Automated translation of remaining Spanish content to English
=======================================================================================

This script translates the remaining Spanish prompts and messages to English.
It provides a mapping of Spanish to English translations for critical LLM prompts.
"""

TRANSLATION_MAP = {
    # Step 3: Evaluate Group Importance
    "Eres un ecólogo marino experto evaluando la importancia de grupos funcionales\npara un modelo ecosistémico ATLANTIS del Golfo de California.\n\nEvalúa cada grupo según los criterios proporcionados, asignando puntajes de 0.0 a 1.0.\nEl puntaje final es la suma ponderada.\nResponde ÚNICAMENTE con un JSON válido.": 
    "You are an expert marine ecologist evaluating the importance of functional groups\nfor an ATLANTIS ecosystem model of the Gulf of California.\n\nEvaluate each group according to the provided criteria, assigning scores from 0.0 to 1.0.\nFinal score is the weighted sum.\nRespond ONLY with valid JSON.",
    
    "## GRUPOS FUNCIONALES:":
    "## FUNCTIONAL GROUPS:",
    
    "## CRITERIOS DE EVALUACIÓN:":
    "## EVALUATION CRITERIA:",
    
    "## INSTRUCCIÓN:\nPara cada grupo, asigna un puntaje (0.0-1.0) en cada criterio.\nCalcula el puntaje total ponderado.\n\nResponde con:":
    "## INSTRUCTION:\nFor each group, assign a score (0.0-1.0) for each criterion.\nCalculate the weighted total score.\n\nRespond with:",
    
    "\"species_richness\": 0.8,\n        \"trophic_importance\": 0.9,\n        \"commercial_value\": 0.7,\n        \"ecological_role\": 0.8,\n        \"conservation_status\": 0.3,\n        \"uniqueness\": 0.6":
    "\"species_richness\": 0.8,\n        \"trophic_importance\": 0.9,\n        \"commercial_value\": 0.7,\n        \"ecological_role\": 0.8,\n        \"conservation_status\": 0.3,\n        \"uniqueness\": 0.6",
    
    "\"total_score\": 0.75,\n      \"justification\": \"Breve justificación\"":
    "\"total_score\": 0.75,\n      \"justification\": \"Brief justification\"",
    
    "[LLM] Evaluando importancia de grupos funcionales...":
    "[LLM] Evaluating functional group importance...",
    
    "[LLM] Evaluación de importancia completada":
    "[LLM] Importance evaluation completed",
    
    # Step 4: Propose Group Merges
    "Eres un ecólogo marino experto en modelación ecosistémica ATLANTIS.\nNecesitas reducir el número de grupos funcionales fusionando grupos similares.\n\nREGLAS PARA FUSIONAR:\n- Solo fusionar grupos con roles funcionales SIMILARES.\n- Priorizar la fusión de grupos con bajo puntaje de importancia.\n- Mantener la diversidad funcional del ecosistema.\n- Asegurar que las especies fusionadas sigan teniendo sentido ecológico juntas.\n- NO fusionar grupos de niveles tróficos muy diferentes.\n- Responde ÚNICAMENTE con un JSON válido.":
    "You are an expert marine ecologist in ATLANTIS ecosystem modeling.\nYou need to reduce the number of functional groups by merging similar groups.\n\nRULES FOR MERGING:\n- Only merge groups with SIMILAR functional roles.\n- Prioritize merging groups with low importance scores.\n- Maintain ecosystem functional diversity.\n- Ensure merged species still make ecological sense together.\n- DO NOT merge groups from very different trophic levels.\n- Respond ONLY with valid JSON.",
    
    "## GRUPOS FUNCIONALES ACTUALES":
    "## CURRENT FUNCTIONAL GROUPS",
    
    "## NECESIDAD:\nReducir a": 
    "## REQUIREMENT:\nReduce to",
    
    "## INSTRUCCIÓN:\nPropón qué grupos fusionar. Para cada fusión, define el grupo resultante.\n\nResponde con:":
    "## INSTRUCTION:\nPropose which groups to merge. For each merge, define the resulting group.\n\nRespond with:",
    
    "\"merge_groups\": [\"FG_id_1\", \"FG_id_2\"],\n      \"result\": {{":
    "\"merge_groups\": [\"FG_id_1\", \"FG_id_2\"],\n      \"result\": {{",
    
    "\"group_name\": \"Nuevo nombre del grupo fusionado\",\n        \"description\": \"Nueva descripción del grupo fusionado\",":
    "\"group_name\": \"New merged group name\",\n        \"description\": \"New merged group description\",",
    
    "\"taxonomic_affinity\": \"...\"":
    "\"taxonomic_affinity\": \"...\"",
    
    "\"reason\": \"Justificación de la fusión\"":
    "\"reason\": \"Justification for the merge\"",
    
    "[LLM] Proponiendo fusiones":
    "[LLM] Proposing merges",
    
    "[LLM] Fusiones aplicadas:":
    "[LLM] Merges applied:",
    
    "grupos":
    "groups",
}

if __name__ == "__main__":
    print("Spanish to English Translation Map Created")
    print(f"Total translations: {len(TRANSLATION_MAP)}")
    print("\nUse this map to replace Spanish text in llm_classifier.py")
