"""
Módulo de gerenciamento do dataset de bugs para avaliação de prompts.

Provê acesso ao dataset composto por 15 exemplos de bugs distribuídos em:
- 5 bugs simples
- 7 bugs de complexidade média
- 3 bugs complexos

Cada exemplo contém:
- inputs.bug_report: Descrição do bug de entrada
- outputs.reference: User story esperada como saída de referência
- metadata: Informações sobre domínio, tipo e complexidade
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional

DATASET_FILE = Path(__file__).parent.parent / "datasets" / "bug_to_user_story.jsonl"


def load_dataset(file_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Carrega o dataset de bugs a partir do arquivo JSONL.

    Args:
        file_path: Caminho alternativo para o arquivo JSONL.
                   Se None, usa o caminho padrão do projeto.

    Returns:
        Lista de exemplos, cada um com 'inputs', 'outputs' e 'metadata'.
    """
    path = Path(file_path) if file_path else DATASET_FILE

    if not path.exists():
        raise FileNotFoundError(
            f"Dataset não encontrado: {path}\n"
            "Verifique se o arquivo datasets/bug_to_user_story.jsonl existe."
        )

    examples = []
    with open(path, "r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                examples.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"⚠️  Erro ao parsear linha {line_number}: {e}")

    return examples


def get_examples_by_complexity(
    complexity: str,
    file_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Retorna exemplos filtrados por nível de complexidade.

    Args:
        complexity: 'simple', 'medium' ou 'complex'
        file_path: Caminho alternativo para o arquivo JSONL.

    Returns:
        Lista de exemplos com a complexidade especificada.
    """
    examples = load_dataset(file_path)
    return [
        ex for ex in examples
        if ex.get("metadata", {}).get("complexity") == complexity
    ]


def get_simple_bugs(file_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retorna os 5 bugs simples do dataset."""
    return get_examples_by_complexity("simple", file_path)


def get_medium_bugs(file_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retorna os 7 bugs de complexidade média do dataset."""
    return get_examples_by_complexity("medium", file_path)


def get_complex_bugs(file_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retorna os 3 bugs complexos do dataset."""
    return get_examples_by_complexity("complex", file_path)


def get_dataset_summary(file_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Retorna um resumo estatístico do dataset.

    Returns:
        Dicionário com total de exemplos, contagem por complexidade e domínios.
    """
    examples = load_dataset(file_path)

    complexity_count: Dict[str, int] = {}
    domain_count: Dict[str, int] = {}

    for ex in examples:
        meta = ex.get("metadata", {})
        complexity = meta.get("complexity", "unknown")
        domain = meta.get("domain", "unknown")

        complexity_count[complexity] = complexity_count.get(complexity, 0) + 1
        domain_count[domain] = domain_count.get(domain, 0) + 1

    return {
        "total": len(examples),
        "by_complexity": complexity_count,
        "by_domain": domain_count,
    }


def get_bug_reports(file_path: Optional[str] = None) -> List[str]:
    """
    Retorna apenas as descrições de bugs (inputs) do dataset.

    Returns:
        Lista de strings com os relatos de bugs.
    """
    examples = load_dataset(file_path)
    return [ex["inputs"]["bug_report"] for ex in examples if "inputs" in ex]


def get_references(file_path: Optional[str] = None) -> List[str]:
    """
    Retorna apenas as user stories de referência (outputs) do dataset.

    Returns:
        Lista de strings com as user stories esperadas.
    """
    examples = load_dataset(file_path)
    return [ex["outputs"]["reference"] for ex in examples if "outputs" in ex]


if __name__ == "__main__":
    print("=" * 50)
    print("DATASET - BUG TO USER STORY")
    print("=" * 50)

    summary = get_dataset_summary()
    print(f"\nTotal de exemplos: {summary['total']}")
    print("\nPor complexidade:")
    for complexity, count in summary["by_complexity"].items():
        print(f"  - {complexity}: {count}")
    print("\nPor domínio:")
    for domain, count in summary["by_domain"].items():
        print(f"  - {domain}: {count}")

    print("\nExemplo (bug simples):")
    simple = get_simple_bugs()
    if simple:
        ex = simple[0]
        print(f"  Bug: {ex['inputs']['bug_report']}")
        print(f"  Referência: {ex['outputs']['reference'][:100]}...")
