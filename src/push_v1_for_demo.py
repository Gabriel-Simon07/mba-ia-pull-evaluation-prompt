"""
Script para fazer push do prompt ruim (v1) para o seu LangSmith Hub.
Usado para demonstrar o contraste entre v1 (baixo desempenho) e v2 (otimizado).
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain import hub
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header

load_dotenv()

PROMPT_FILE = "prompts/bug_to_user_story_v1.yml"
PROMPT_KEY = "bug_to_user_story_v1"


def main():
    print_section_header("PUSH DO PROMPT RUIM (v1) PARA DEMONSTRAÇÃO")

    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return 1

    username = os.getenv("USERNAME_LANGSMITH_HUB", "").strip()
    if not username:
        print("❌ USERNAME_LANGSMITH_HUB não configurado no .env")
        return 1

    data = load_yaml(PROMPT_FILE)
    if not data or PROMPT_KEY not in data:
        print(f"❌ Arquivo {PROMPT_FILE} não encontrado ou chave '{PROMPT_KEY}' ausente")
        print("   Execute primeiro: python src/pull_prompts.py")
        return 1

    prompt_data = data[PROMPT_KEY]
    system_prompt = prompt_data.get("system_prompt", "").strip()
    user_prompt = prompt_data.get("user_prompt", "{bug_report}").strip()

    repo_full_name = f"{username}/{PROMPT_KEY}"
    print(f"Fazendo push de: {repo_full_name}")

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", user_prompt),
    ])

    try:
        url = hub.push(
            repo_full_name,
            prompt_template,
            new_repo_is_public=True,
            new_repo_description="Prompt inicial de baixa qualidade (sem técnicas de engenharia de prompts)",
        )
        print(f"✅ Push realizado com sucesso!")
        print(f"   URL: {url}")
        print(f"\nAgora avalie o v1 para capturar as notas baixas:")
        print(f"   python src/evaluate.py --prompt {repo_full_name}")
        return 0
    except Exception as e:
        err = str(e)
        if "already exists" in err.lower() or "conflict" in err.lower():
            try:
                url = hub.push(repo_full_name, prompt_template)
                print(f"✅ Atualizado com sucesso! URL: {url}")
                print(f"\nAgora avalie o v1:")
                print(f"   python src/evaluate.py --prompt {repo_full_name}")
                return 0
            except Exception as e2:
                print(f"❌ Falha: {e2}")
        else:
            print(f"❌ Erro: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
