"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Detecta/configura automaticamente o handle do workspace no LangSmith
2. Lê o prompt otimizado de prompts/bug_to_user_story_v2.yml
3. Valida a estrutura do prompt
4. Faz push PÚBLICO para o LangSmith Hub como {handle}/bug_to_user_story_v2
5. Salva o handle no .env para uso futuro
"""

import os
import sys
import re
import requests
from pathlib import Path
from dotenv import load_dotenv, set_key
from langchain import hub
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header, validate_prompt_structure

load_dotenv()

PROMPT_FILE = "prompts/bug_to_user_story_v2.yml"
PROMPT_KEY = "bug_to_user_story_v2"
LANGSMITH_ENDPOINT = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
ENV_FILE = ".env"


def get_api_headers() -> dict:
    return {"x-api-key": os.getenv("LANGSMITH_API_KEY", "")}


def get_workspace_info() -> dict:
    """Retorna informações do workspace atual."""
    r = requests.get(f"{LANGSMITH_ENDPOINT}/api/v1/workspaces", headers=get_api_headers(), timeout=10)
    r.raise_for_status()
    workspaces = r.json()
    # Pegar o workspace pessoal (is_personal=True)
    for ws in workspaces:
        if ws.get("is_personal"):
            return ws
    return workspaces[0] if workspaces else {}


def slugify(text: str) -> str:
    """Converte texto em slug válido para handle (apenas letras, números e hífens)."""
    text = text.lower().split("@")[0]          # pegar só parte antes do @
    text = re.sub(r"[^a-z0-9]+", "-", text)   # substituir caracteres inválidos por hífen
    text = text.strip("-")                      # remover hífens das bordas
    return text[:39]                            # máximo 39 caracteres


def set_workspace_handle(workspace_id: str, handle: str) -> bool:
    """Tenta configurar o handle do workspace via API."""
    try:
        r = requests.patch(
            f"{LANGSMITH_ENDPOINT}/api/v1/workspaces/{workspace_id}",
            headers={**get_api_headers(), "Content-Type": "application/json"},
            json={"tenant_handle": handle},
            timeout=10,
        )
        if r.status_code in (200, 201, 204):
            return True
        print(f"   Aviso: PATCH retornou {r.status_code}: {r.text[:200]}")
        return False
    except Exception as e:
        print(f"   Aviso: Erro ao configurar handle via API: {e}")
        return False


def resolve_handle() -> str:
    """
    Resolve o handle do LangSmith Hub:
    1. Usa USERNAME_LANGSMITH_HUB do .env se já configurado
    2. Tenta obter do workspace via API
    3. Gera automaticamente a partir do email e salva no .env
    """
    # 1. Verificar se já está no .env
    handle = os.getenv("USERNAME_LANGSMITH_HUB", "").strip()
    if handle:
        print(f"   Handle encontrado no .env: {handle}")
        return handle

    print("   USERNAME_LANGSMITH_HUB não configurado, detectando automaticamente...")

    # 2. Tentar obter do workspace
    try:
        ws = get_workspace_info()
        workspace_id = ws.get("id", "")
        tenant_handle = ws.get("tenant_handle")

        if tenant_handle:
            handle = tenant_handle
            print(f"   Handle detectado via API: {handle}")
        else:
            # 3. Gerar a partir do email (via display_name ou workspace name)
            display_name = ws.get("display_name", "")
            # Tentar pegar email do token
            token_r = requests.get(
                f"{LANGSMITH_ENDPOINT}/api/v1/api-key",
                headers=get_api_headers(),
                timeout=10,
            )
            email = ""
            if token_r.ok:
                keys = token_r.json()
                if isinstance(keys, list) and keys:
                    email = keys[0].get("created_by", {}).get("email", "")

            if email:
                handle = slugify(email)
            elif display_name:
                handle = slugify(display_name)
            else:
                handle = "meu-prompt-hub"

            print(f"   Handle gerado automaticamente: {handle}")

            # Tentar configurar no workspace
            if workspace_id:
                print(f"   Configurando handle '{handle}' no workspace...")
                if set_workspace_handle(workspace_id, handle):
                    print(f"   Handle '{handle}' configurado com sucesso!")
                else:
                    print(f"   Nao foi possivel configurar via API. Usando localmente.")

        # Salvar no .env para uso futuro
        env_path = Path(ENV_FILE)
        if env_path.exists():
            set_key(str(env_path), "USERNAME_LANGSMITH_HUB", handle)
            print(f"   Handle salvo no .env: USERNAME_LANGSMITH_HUB={handle}")

        return handle

    except Exception as e:
        print(f"   Erro ao detectar handle: {e}")
        return ""


def validate_prompt(prompt_data: dict) -> tuple:
    return validate_prompt_structure(prompt_data)


def push_prompt_to_langsmith(handle: str, prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).
    """
    repo_full_name = f"{handle}/{prompt_name}"

    system_prompt_text = prompt_data.get("system_prompt", "").strip()
    user_prompt_text = prompt_data.get("user_prompt", "{bug_report}").strip()

    print(f"   Criando ChatPromptTemplate...")
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt_text),
        ("human", user_prompt_text),
    ])

    description = prompt_data.get("description", f"Prompt otimizado: {prompt_name}")
    tags = prompt_data.get("tags", [])
    techniques = prompt_data.get("techniques_applied", [])

    readme_lines = [
        f"# {prompt_name}",
        "",
        f"**Descricao:** {description}",
        "",
        "## Tecnicas Aplicadas",
        "",
    ]
    for tech in techniques:
        readme_lines.append(f"- {tech}")
    readme_lines += [
        "",
        "## Variaveis de Entrada",
        "",
        "- `bug_report`: Relato do bug a ser convertido em User Story",
        "",
        "## Formato de Saida",
        "",
        "User Story no formato padrao agil com:",
        "- Como [persona] / Eu quero / Para que",
        "- Criterios de Aceitacao (Dado/Quando/Entao)",
        "- Contexto Tecnico",
        "- Tarefas Tecnicas",
    ]
    readme = "\n".join(readme_lines)

    print(f"   Fazendo push para: {repo_full_name}")

    try:
        url = hub.push(
            repo_full_name,
            prompt_template,
            new_repo_is_public=True,
            new_repo_description=description,
            tags=tags if tags else None,
            readme=readme,
        )
        print(f"   Push realizado com sucesso!")
        print(f"   URL: {url}")
        return True

    except Exception as e:
        err = str(e)
        print(f"   Erro ao fazer push: {err}")

        if "already exists" in err.lower() or "conflict" in err.lower():
            print("\n   Prompt ja existe no hub. Tentando atualizar (push sem new_repo_is_public)...")
            try:
                url = hub.push(repo_full_name, prompt_template)
                print(f"   Atualizado com sucesso! URL: {url}")
                return True
            except Exception as e2:
                print(f"   Falha na atualizacao: {e2}")

        if "handle" in err.lower() or "tenant" in err.lower() or "not found" in err.lower():
            print("\n   O handle do workspace pode nao estar configurado corretamente.")
            print(f"   Tente acessar: https://smith.langchain.com/settings")
            print(f"   E configure manualmente: USERNAME_LANGSMITH_HUB={handle}")

        return False


def main():
    """Funcao principal"""
    print_section_header("PUSH DE PROMPTS OTIMIZADOS PARA O LANGSMITH HUB")

    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return 1

    # Resolver handle automaticamente
    print("Resolvendo handle do LangSmith Hub...")
    handle = resolve_handle()

    if not handle:
        print("\nNao foi possivel determinar o handle do LangSmith Hub.")
        print("Configure manualmente no .env:")
        print("  USERNAME_LANGSMITH_HUB=seu_handle_aqui")
        print("\nExemplo: USERNAME_LANGSMITH_HUB=gabrielsimon")
        return 1

    print(f"\nHandle: {handle}")

    # Carregar prompt otimizado
    prompt_file = Path(PROMPT_FILE)
    if not prompt_file.exists():
        print(f"\nArquivo nao encontrado: {PROMPT_FILE}")
        return 1

    print(f"\nCarregando prompt de: {PROMPT_FILE}")
    data = load_yaml(str(prompt_file))

    if not data or PROMPT_KEY not in data:
        print(f"Erro ao carregar {PROMPT_FILE} ou chave '{PROMPT_KEY}' nao encontrada")
        return 1

    prompt_data = data[PROMPT_KEY]
    print(f"   Prompt carregado: {PROMPT_KEY}")

    # Validar
    print("\nValidando prompt...")
    is_valid, errors = validate_prompt(prompt_data)
    if not is_valid:
        print("Prompt invalido. Erros:")
        for error in errors:
            print(f"   - {error}")
        return 1

    techniques = prompt_data.get("techniques_applied", [])
    print(f"   Prompt valido")
    print(f"   Tecnicas: {', '.join(techniques)}")

    # Push
    print(f"\nFazendo push para o LangSmith Hub...")
    success = push_prompt_to_langsmith(handle, PROMPT_KEY, prompt_data)

    if success:
        print(f"\nPush concluido com sucesso!")
        print(f"\nProximos passos:")
        print(f"  1. Verifique: https://smith.langchain.com/hub/{handle}/{PROMPT_KEY}")
        print(f"  2. Confirme que esta publico")
        print(f"  3. Execute: python src/evaluate.py")
        return 0
    else:
        print("\nPush falhou. Veja os erros acima.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
