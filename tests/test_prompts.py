"""
Testes automatizados para validação do prompt otimizado bug_to_user_story_v2.
"""
import pytest
import yaml
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

PROMPT_FILE = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"
PROMPT_KEY = "bug_to_user_story_v2"


def load_prompts(file_path: str = None):
    """Carrega prompts do arquivo YAML."""
    path = file_path or str(PROMPT_FILE)
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def get_prompt_data():
    """Carrega e retorna os dados do prompt v2."""
    data = load_prompts()
    assert data is not None, f"Não foi possível carregar {PROMPT_FILE}"
    assert PROMPT_KEY in data, f"Chave '{PROMPT_KEY}' não encontrada no YAML"
    return data[PROMPT_KEY]


class TestPrompts:
    def test_prompt_has_system_prompt(self):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        prompt = get_prompt_data()

        assert "system_prompt" in prompt, (
            "Campo 'system_prompt' não encontrado no YAML. "
            "Adicione um system_prompt ao seu prompt otimizado."
        )

        system_prompt = prompt["system_prompt"]
        assert system_prompt is not None, "system_prompt é None"
        assert isinstance(system_prompt, str), "system_prompt deve ser uma string"
        assert len(system_prompt.strip()) > 0, (
            "system_prompt está vazio. "
            "O prompt deve conter instruções no system_prompt."
        )
        assert len(system_prompt.strip()) >= 100, (
            f"system_prompt muito curto ({len(system_prompt.strip())} chars). "
            "Um bom system_prompt deve ter pelo menos 100 caracteres."
        )

    def test_prompt_has_role_definition(self):
        """Verifica se o prompt define uma persona (ex: 'Você é um Product Manager')."""
        prompt = get_prompt_data()
        system_prompt = prompt.get("system_prompt", "")

        role_keywords = [
            "você é",
            "voce é",
            "você é um",
            "você é uma",
            "product manager",
            "especialista",
            "analista",
            "você atua",
            "seu papel",
            "sua função",
        ]

        system_lower = system_prompt.lower()
        has_role = any(keyword in system_lower for keyword in role_keywords)

        assert has_role, (
            "O prompt não define uma persona/role. "
            "Use Role Prompting: ex. 'Você é um Product Manager Sênior...'. "
            f"Palavras-chave buscadas: {role_keywords}"
        )

    def test_prompt_mentions_format(self):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        prompt = get_prompt_data()
        system_prompt = prompt.get("system_prompt", "")

        format_keywords = [
            "markdown",
            "user story",
            "como [",
            "como um",
            "eu quero",
            "para que",
            "critérios de aceitação",
            "criterios de aceitacao",
            "dado que",
            "quando",
            "então",
            "formato",
            "estrutura",
            "**user story",
            "**critérios",
        ]

        system_lower = system_prompt.lower()
        has_format = any(keyword in system_lower for keyword in format_keywords)

        assert has_format, (
            "O prompt não menciona o formato esperado de saída. "
            "Especifique o formato Markdown ou User Story (Como/Eu quero/Para que). "
            f"Palavras-chave buscadas: {format_keywords}"
        )

    def test_prompt_has_few_shot_examples(self):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        prompt = get_prompt_data()
        system_prompt = prompt.get("system_prompt", "")

        few_shot_indicators = [
            "exemplo",
            "example",
            "bug report:",
            "user story gerada",
            "---",
            "###",
            "input:",
            "output:",
            "entrada:",
            "saída:",
        ]

        system_lower = system_prompt.lower()
        matches = [kw for kw in few_shot_indicators if kw in system_lower]

        assert len(matches) >= 2, (
            "O prompt não parece conter exemplos Few-shot. "
            "Adicione pelo menos um exemplo de entrada/saída para guiar o modelo. "
            f"Indicadores buscados: {few_shot_indicators}. "
            f"Encontrados: {matches}"
        )

        # Verificar que há pelo menos um exemplo concreto (Bug Report + User Story)
        has_bug_report_example = "bug report" in system_lower or "relato de bug" in system_lower
        has_story_example = "user story" in system_lower and (
            "como um" in system_lower or "eu quero" in system_lower
        )

        assert has_bug_report_example and has_story_example, (
            "O prompt deve conter ao menos um exemplo completo de Bug Report -> User Story. "
            "Use a técnica Few-shot com exemplos reais de entrada e saída."
        )

    def test_prompt_no_todos(self):
        """Garante que não há [TODO] no texto do prompt."""
        prompt = get_prompt_data()

        # Checar todos os campos de texto
        fields_to_check = {
            "system_prompt": prompt.get("system_prompt", ""),
            "user_prompt": prompt.get("user_prompt", ""),
            "description": prompt.get("description", ""),
        }

        todos_found = {}
        todo_variants = ["[TODO]", "[todo]", "[Todo]", "TODO:", "FIXME", "[PLACEHOLDER]"]

        for field_name, field_value in fields_to_check.items():
            if not isinstance(field_value, str):
                continue
            found = [variant for variant in todo_variants if variant in field_value]
            if found:
                todos_found[field_name] = found

        assert not todos_found, (
            f"TODOs encontrados no prompt: {todos_found}. "
            "Remova todos os placeholders [TODO] antes de publicar o prompt."
        )

    def test_minimum_techniques(self):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        prompt = get_prompt_data()

        assert "techniques_applied" in prompt, (
            "Campo 'techniques_applied' não encontrado no YAML. "
            "Adicione uma lista de técnicas aplicadas nos metadados do prompt."
        )

        techniques = prompt["techniques_applied"]

        assert isinstance(techniques, list), (
            f"'techniques_applied' deve ser uma lista, mas é {type(techniques).__name__}"
        )

        assert len(techniques) >= 2, (
            f"Mínimo de 2 técnicas requeridas, encontradas: {len(techniques)}. "
            f"Técnicas atuais: {techniques}. "
            "Exemplos: Role Prompting, Few-shot Learning, Chain of Thought, Tree of Thought, ReAct"
        )

        # Verificar que as técnicas não são strings vazias
        non_empty = [t for t in techniques if isinstance(t, str) and t.strip()]
        assert len(non_empty) >= 2, (
            f"Mínimo de 2 técnicas não-vazias requeridas, encontradas: {len(non_empty)}. "
            f"Técnicas: {techniques}"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
