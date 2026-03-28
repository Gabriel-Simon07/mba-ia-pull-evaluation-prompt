"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull do prompt leonanluppi/bug_to_user_story_v1 do Hub
3. Extrai system_prompt e user_prompt
4. Salva localmente em prompts/bug_to_user_story_v1.yml
"""

import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain import hub
from utils import save_yaml, check_env_vars, print_section_header

load_dotenv()

# Adicionar src ao path para imports relativos
sys.path.insert(0, str(Path(__file__).parent))

PROMPT_TO_PULL = "leonanluppi/bug_to_user_story_v1"
OUTPUT_FILE = "prompts/bug_to_user_story_v1.yml"
RAW_OUTPUT_FILE = "prompts/raw_prompts.yml"


def extract_prompt_content(prompt_template) -> dict:
    """
    Extrai system_prompt e user_prompt de um ChatPromptTemplate.

    Args:
        prompt_template: ChatPromptTemplate retornado pelo hub.pull

    Returns:
        Dicionário com system_prompt e user_prompt extraídos
    """
    system_prompt = ""
    user_prompt = ""

    messages = getattr(prompt_template, "messages", [])

    for msg in messages:
        # Extrair template do prompt
        if hasattr(msg, "prompt") and hasattr(msg.prompt, "template"):
            template_text = msg.prompt.template
        elif hasattr(msg, "content"):
            template_text = msg.content
        else:
            continue

        # Classificar por tipo de mensagem
        msg_type = type(msg).__name__.lower()
        if "system" in msg_type:
            system_prompt = template_text
        elif "human" in msg_type or "user" in msg_type:
            user_prompt = template_text

    return {
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
    }


def pull_prompts_from_langsmith() -> bool:
    """
    Faz pull do prompt do LangSmith Hub e salva localmente.

    Returns:
        True se sucesso, False caso contrário
    """
    print_section_header("PULL DE PROMPTS DO LANGSMITH HUB")

    print(f"Fazendo pull do prompt: {PROMPT_TO_PULL}")

    try:
        prompt = hub.pull(PROMPT_TO_PULL)
        print(f"   ✓ Prompt '{PROMPT_TO_PULL}' carregado com sucesso")
    except Exception as e:
        print(f"   ❌ Erro ao fazer pull do prompt: {e}")
        print("\n   Verifique:")
        print("   - LANGSMITH_API_KEY está configurada no .env")
        print(f"   - O prompt '{PROMPT_TO_PULL}' existe no LangSmith Hub")
        print("   - Sua conexão com a internet está funcionando")
        return False

    # Extrair conteúdo do prompt
    content = extract_prompt_content(prompt)

    if not content["system_prompt"] and not content["user_prompt"]:
        # Fallback: serializar o prompt como string
        print("   ⚠️  Não foi possível extrair mensagens individuais, usando serialização direta")
        content["system_prompt"] = str(prompt)
        content["user_prompt"] = "{bug_report}"

    # Montar estrutura YAML
    prompt_data = {
        "bug_to_user_story_v1": {
            "description": "Prompt para converter relatos de bugs em User Stories (pull do LangSmith Hub)",
            "system_prompt": content["system_prompt"],
            "user_prompt": content["user_prompt"],
            "version": "v1",
            "source": f"https://smith.langchain.com/hub/{PROMPT_TO_PULL}",
            "tags": ["bug-analysis", "user-story", "product-management"],
        }
    }

    # Salvar localmente (versão nomeada)
    output_path = Path(OUTPUT_FILE)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    success = save_yaml(prompt_data, str(output_path))

    if not success:
        print(f"   ❌ Erro ao salvar arquivo {OUTPUT_FILE}")
        return False

    print(f"   ✓ Prompt salvo em: {OUTPUT_FILE}")

    # Salvar também como raw_prompts.yml (RF-03)
    raw_path = Path(RAW_OUTPUT_FILE)
    save_yaml(prompt_data, str(raw_path))
    print(f"   ✓ Output bruto salvo em: {RAW_OUTPUT_FILE}")

    print(f"\n   Conteúdo do system_prompt (primeiros 200 chars):")
    preview = content["system_prompt"][:200].replace("\n", " ")
    print(f"   {preview}...")
    return True


def main():
    """Função principal"""
    required_vars = ["LANGSMITH_API_KEY"]
    if not check_env_vars(required_vars):
        return 1

    success = pull_prompts_from_langsmith()

    if success:
        print("\n✅ Pull concluído com sucesso!")
        print(f"\nPróximos passos:")
        print(f"  1. Analise o prompt em {OUTPUT_FILE}")
        print(f"  2. Crie sua versão otimizada em prompts/bug_to_user_story_v2.yml")
        print(f"  3. Faça push: python src/push_prompts.py")
        return 0
    else:
        print("\n❌ Pull falhou. Verifique os erros acima.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
