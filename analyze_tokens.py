"""
analyze_tokens.py - Token Analysis Report for LLM Prompts
===========================================================
Analyzes the number of tokens sent to Ollama models and estimates
response token requirements for each prompt type.
"""

import re
import json
from pathlib import Path

# Try to import tiktoken, fallback to approximation
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
    encoding = tiktoken.get_encoding("cl100k_base")
except ImportError:
    TIKTOKEN_AVAILABLE = False
    print("⚠️  tiktoken not installed. Using approximation (1 token ≈ 4 characters)")


def approximate_tokens(text: str) -> int:
    """Approximate token count if tiktoken unavailable."""
    return len(text) // 4


def count_tokens(text: str) -> int:
    """Count tokens in text."""
    if TIKTOKEN_AVAILABLE:
        return len(encoding.encode(text))
    else:
        return approximate_tokens(text)


def extract_prompts_from_file(filepath: str) -> dict:
    """Extract all prompts from llm_classifier.py."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    prompts = {}

    # Pattern to find function definitions and their prompts
    # Look for functions that contain system_prompt and user_prompt
    
    # 1. classify_species prompts
    classify_match = re.search(
        r'def classify_species.*?system_prompt = """(.*?)""".*?user_prompt = f"""(.*?)"""',
        content,
        re.DOTALL
    )
    if classify_match:
        prompts["classify_species"] = {
            "system": classify_match.group(1).strip(),
            "user_template": classify_match.group(2).strip(),
        }

    # 2. create_new_groups prompts
    create_match = re.search(
        r'def create_new_groups.*?system_prompt = """(.*?)""".*?user_prompt = f"""(.*?)"""',
        content,
        re.DOTALL
    )
    if create_match:
        prompts["create_new_groups"] = {
            "system": create_match.group(1).strip(),
            "user_template": create_match.group(2).strip(),
        }

    # 3. score_groups prompts
    score_match = re.search(
        r'def score_groups.*?system_prompt = """(.*?)""".*?user_prompt = f"""(.*?)"""',
        content,
        re.DOTALL
    )
    if score_match:
        prompts["score_groups"] = {
            "system": score_match.group(1).strip(),
            "user_template": score_match.group(2).strip(),
        }

    # 4. optimize_groups prompts
    optimize_match = re.search(
        r'def optimize_groups.*?system_prompt = """(.*?)""".*?user_prompt = f"""(.*?)"""',
        content,
        re.DOTALL
    )
    if optimize_match:
        prompts["optimize_groups"] = {
            "system": optimize_match.group(1).strip(),
            "user_template": optimize_match.group(2).strip(),
        }

    return prompts


def estimate_response_tokens(task_type: str) -> int:
    """Estimate expected response tokens for each task type."""
    estimates = {
        "classify_species": 1500,      # JSON with species assignments
        "create_new_groups": 1200,     # JSON with new group definitions
        "score_groups": 800,            # Scores and explanations
        "optimize_groups": 1000,        # Merge recommendations
    }
    return estimates.get(task_type, 1000)


def load_config():
    """Load model context window information."""
    ollama_models = {
        "orca-mini": {"context": 4096, "description": "~2GB, muy rápido pero limitado"},
        "neural-chat": {"context": 4096, "description": "~4GB, buena relación"},
        "nous-hermes2": {"context": 4096, "description": "~7GB, recomendado"},
        "mistral": {"context": 8192, "description": "~5GB, versatil"},
        "qwen3:8b": {"context": 8192, "description": "~6GB, potente"},
        "llama2": {"context": 4096, "description": "Meta, completo"},
    }
    return ollama_models


def generate_report(filepath: str = "llm_classifier.py"):
    """Generate comprehensive token analysis report."""
    
    print("\n" + "="*80)
    print("🔍 TOKEN ANALYSIS REPORT FOR LLM PROMPTS")
    print("="*80)

    # Check if file exists
    filepath_obj = Path(filepath)
    if not filepath_obj.exists():
        filepath_obj = Path(__file__).parent / filepath
    
    if not filepath_obj.exists():
        print(f"❌ Error: Could not find {filepath_obj}")
        return

    # Extract prompts
    prompts = extract_prompts_from_file(str(filepath_obj))
    
    if not prompts:
        print("⚠️  No prompts found. Check file path and format.")
        return

    models = load_config()
    
    # Analyze each prompt
    total_system_tokens = 0
    total_user_tokens = 0
    task_data = []

    print("\n📊 PROMPT TOKEN COUNTS:")
    print("-" * 80)

    for task_name, prompt_data in prompts.items():
        system_tokens = count_tokens(prompt_data["system"])
        user_tokens = count_tokens(prompt_data["user_template"])
        response_tokens = estimate_response_tokens(task_name)
        total_tokens = system_tokens + user_tokens + response_tokens

        total_system_tokens += system_tokens
        total_user_tokens += user_tokens

        task_data.append({
            "name": task_name,
            "system_tokens": system_tokens,
            "user_tokens": user_tokens,
            "response_tokens": response_tokens,
            "total": total_tokens,
        })

        print(f"\n🎯 {task_name.upper()}")
        print(f"   System prompt:    {system_tokens:>6} tokens ({len(prompt_data['system']):>6} chars)")
        print(f"   User prompt:      {user_tokens:>6} tokens ({len(prompt_data['user_template']):>6} chars)")
        print(f"   Est. response:    {response_tokens:>6} tokens (estimated)")
        print(f"   TOTAL:            {total_tokens:>6} tokens")

    # Summary
    total_all = sum(t["total"] for t in task_data)
    
    print("\n" + "-" * 80)
    print("📈 SUMMARY:")
    print(f"   Total system tokens (all prompts):    {total_system_tokens:>6} tokens")
    print(f"   Total user tokens (all prompts):      {total_user_tokens:>6} tokens")
    print(f"   Total response tokens (estimated):    {sum(t['response_tokens'] for t in task_data):>6} tokens")
    print(f"   GRAND TOTAL (all tasks combined):     {total_all:>6} tokens")

    # Compatibility check
    print("\n" + "="*80)
    print("✅ MODEL COMPATIBILITY CHECK")
    print("="*80)

    max_task_tokens = max(t["total"] for t in task_data)
    
    for model, info in models.items():
        context = info["context"]
        available = context - total_system_tokens  # After system prompt
        compatibility = "✅ OK" if available > 2000 else "⚠️  TIGHT" if available > 1000 else "❌ NO"
        
        print(f"\n🤖 {model:15} | Context: {context:>5} tokens | {info['description']}")
        print(f"   {'─'*70}")
        print(f"   System overhead:        {total_system_tokens:>6} tokens")
        print(f"   Avg user prompt:        {total_user_tokens//len(prompts):>6} tokens")
        print(f"   Avg response space:     {(available - total_user_tokens//len(prompts)):>6} tokens")
        print(f"   Status: {compatibility}")

    # Recommendations
    print("\n" + "="*80)
    print("💡 RECOMMENDATIONS")
    print("="*80)

    current_model = None
    with open(".env", "r") as f:
        for line in f:
            if line.startswith("OLLAMA_MODEL"):
                current_model = line.split("=")[1].strip()

    if current_model:
        print(f"\n📌 Current model: {current_model}")
        if current_model in models:
            model_info = models[current_model]
            available = model_info["context"] - total_system_tokens - total_user_tokens
            if available < 1000:
                print(f"   ⚠️  CAUTION: Only {available} tokens for response/buffer!")
                print(f"   Suggestion: Use a model with larger context window")
            else:
                print(f"   ✅ {available} tokens available for responses (safe margin)")

    print("\n" + "="*80)
    print("📝 NOTES:")
    print("="*80)
    print("""
  • Token counts are approximate (using tiktoken cl100k_base encoding)
  • Response tokens are ESTIMATED based on typical JSON outputs
  • User prompts include variables like species list and group definitions
  • Recommended buffer: min 500 tokens for safety margin
  • For stability, keep total tokens < 80% of context window
    """)

    print("\n" + "="*80)


if __name__ == "__main__":
    generate_report()
