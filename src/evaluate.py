"""
Script para avaliar prompts otimizados usando langsmith.evaluation.evaluate().

Os resultados aparecem na aba Experiments do LangSmith Dashboard com
métricas agregadas por experimento.

Uso:
    python src/evaluate.py                                        # avalia v2 (padrão)
    python src/evaluate.py --prompt usuario/bug_to_user_story_v1  # avalia v1 (ruim)
"""

import os
import sys
import json
import time
import argparse
from typing import List, Dict, Any
from pathlib import Path
from dotenv import load_dotenv
from langsmith import Client
from langsmith.evaluation import evaluate as ls_evaluate
from langchain import hub
from utils import check_env_vars, format_score, print_section_header, get_llm as get_configured_llm
from metrics import (
    evaluate_tone_score,
    evaluate_acceptance_criteria_score,
    evaluate_user_story_format_score,
    evaluate_completeness_score,
    evaluate_f1_score,
)

load_dotenv()

MINIMUM_SCORE = 0.9
# Sleep entre chamadas para respeitar o free tier do Gemini (15 req/min)
RATE_LIMIT_SLEEP = 5


def load_dataset_from_jsonl(jsonl_path: str) -> List[Dict[str, Any]]:
    examples = []
    try:
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    examples.append(json.loads(line))
        return examples
    except FileNotFoundError:
        print(f"❌ Arquivo não encontrado: {jsonl_path}")
        return []
    except Exception as e:
        print(f"❌ Erro ao carregar dataset: {e}")
        return []


def create_evaluation_dataset(client: Client, dataset_name: str, jsonl_path: str) -> str:
    print(f"Verificando dataset: {dataset_name}...")
    examples = load_dataset_from_jsonl(jsonl_path)

    if not examples:
        print("❌ Nenhum exemplo carregado do arquivo .jsonl")
        return dataset_name

    print(f"   ✓ {len(examples)} exemplos encontrados em {jsonl_path}")

    try:
        existing = None
        for ds in client.list_datasets(dataset_name=dataset_name):
            if ds.name == dataset_name:
                existing = ds
                break

        if existing:
            print(f"   ✓ Dataset '{dataset_name}' já existe")
        else:
            dataset = client.create_dataset(dataset_name=dataset_name)
            for ex in examples:
                client.create_example(
                    dataset_id=dataset.id,
                    inputs=ex["inputs"],
                    outputs=ex["outputs"],
                )
            print(f"   ✓ Dataset criado com {len(examples)} exemplos")

    except Exception as e:
        print(f"   ⚠️  Erro ao verificar/criar dataset: {e}")

    return dataset_name


def build_target(prompt_name: str):
    """Retorna a função target que o LangSmith usará para gerar respostas."""
    print(f"   Carregando prompt: {prompt_name}")
    prompt_template = hub.pull(prompt_name)
    llm = get_configured_llm(temperature=0)
    chain = prompt_template | llm

    def target(inputs: dict) -> dict:
        response = chain.invoke(inputs)
        return {"output": response.content}

    return target


def make_evaluators():
    """Cria os 5 evaluators compatíveis com langsmith.evaluation.evaluate()."""

    def f1_evaluator(run, example):
        time.sleep(RATE_LIMIT_SLEEP)
        output = (run.outputs or {}).get("output", "")
        reference = (example.outputs or {}).get("reference", "")
        question = (example.inputs or {}).get("bug_report", "")
        result = evaluate_f1_score(question, output, reference)
        return {"key": "f1_score", "score": result["score"]}

    def tone_evaluator(run, example):
        time.sleep(RATE_LIMIT_SLEEP)
        output = (run.outputs or {}).get("output", "")
        reference = (example.outputs or {}).get("reference", "")
        question = (example.inputs or {}).get("bug_report", "")
        result = evaluate_tone_score(question, output, reference)
        return {"key": "tone_score", "score": result["score"]}

    def acceptance_evaluator(run, example):
        time.sleep(RATE_LIMIT_SLEEP)
        output = (run.outputs or {}).get("output", "")
        reference = (example.outputs or {}).get("reference", "")
        question = (example.inputs or {}).get("bug_report", "")
        result = evaluate_acceptance_criteria_score(question, output, reference)
        return {"key": "acceptance_criteria_score", "score": result["score"]}

    def format_evaluator(run, example):
        time.sleep(RATE_LIMIT_SLEEP)
        output = (run.outputs or {}).get("output", "")
        reference = (example.outputs or {}).get("reference", "")
        question = (example.inputs or {}).get("bug_report", "")
        result = evaluate_user_story_format_score(question, output, reference)
        return {"key": "user_story_format_score", "score": result["score"]}

    def completeness_evaluator(run, example):
        time.sleep(RATE_LIMIT_SLEEP)
        output = (run.outputs or {}).get("output", "")
        reference = (example.outputs or {}).get("reference", "")
        question = (example.inputs or {}).get("bug_report", "")
        result = evaluate_completeness_score(question, output, reference)
        return {"key": "completeness_score", "score": result["score"]}

    return [f1_evaluator, tone_evaluator, acceptance_evaluator, format_evaluator, completeness_evaluator]


def display_results(prompt_name: str, results) -> bool:
    """Extrai scores dos resultados e exibe no terminal."""
    scores: Dict[str, List[float]] = {
        "f1_score": [],
        "tone_score": [],
        "acceptance_criteria_score": [],
        "user_story_format_score": [],
        "completeness_score": [],
    }

    for row in results._results:
        for eval_result in (row.evaluation_results or {}).get("results", []):
            key = eval_result.key
            if key in scores and eval_result.score is not None:
                scores[key].append(float(eval_result.score))

    def avg(lst):
        return round(sum(lst) / len(lst), 4) if lst else 0.0

    averages = {k: avg(v) for k, v in scores.items()}

    metric_labels = {
        "f1_score": "F1-Score",
        "tone_score": "Tone Score",
        "acceptance_criteria_score": "Acceptance Criteria Score",
        "user_story_format_score": "User Story Format Score",
        "completeness_score": "Completeness Score",
    }

    print("\n" + "=" * 50)
    print(f"Prompt: {prompt_name}")
    print("=" * 50)
    print("\nMétricas Bug to User Story:")

    all_passed = True
    for key, label in metric_labels.items():
        score = averages.get(key, 0.0)
        if score < MINIMUM_SCORE:
            all_passed = False
        print(f"  - {label}: {format_score(score, threshold=MINIMUM_SCORE)}")

    total_avg = sum(averages.values()) / len(averages) if averages else 0.0
    print("\n" + "-" * 50)
    print(f"📊 MÉDIA GERAL: {total_avg:.4f}")
    print("-" * 50)

    if all_passed and total_avg >= MINIMUM_SCORE:
        print(f"\n✅ STATUS: APROVADO - Todas as métricas >= {MINIMUM_SCORE}")
    else:
        print(f"\n❌ STATUS: REPROVADO")
        below = [metric_labels[k] for k, v in averages.items() if v < MINIMUM_SCORE]
        if below:
            print(f"   Métricas abaixo de {MINIMUM_SCORE}: {', '.join(below)}")

    return all_passed and total_avg >= MINIMUM_SCORE


def main():
    parser = argparse.ArgumentParser(description="Avalia prompts do LangSmith Hub")
    parser.add_argument(
        "--prompt", type=str, default=None,
        help="Nome completo do prompt no hub (ex: usuario/bug_to_user_story_v1)"
    )
    args = parser.parse_args()

    print_section_header("AVALIAÇÃO DE PROMPTS - BUG TO USER STORY")

    provider = os.getenv("LLM_PROVIDER", "openai")
    llm_model = os.getenv("LLM_MODEL", "gpt-4o-mini")
    eval_model = os.getenv("EVAL_MODEL", "gpt-4o")

    print(f"Provider: {provider}")
    print(f"Modelo Principal: {llm_model}")
    print(f"Modelo de Avaliação: {eval_model}\n")

    required_vars = ["LANGSMITH_API_KEY", "LLM_PROVIDER"]
    if provider == "openai":
        required_vars.append("OPENAI_API_KEY")
    elif provider in ["google", "gemini"]:
        required_vars.append("GOOGLE_API_KEY")

    if not check_env_vars(required_vars):
        return 1

    if args.prompt:
        prompt_full_name = args.prompt
    else:
        username = os.getenv("USERNAME_LANGSMITH_HUB", "").strip()
        if not username:
            print("⚠️  USERNAME_LANGSMITH_HUB não configurado no .env")
            prompt_full_name = "bug_to_user_story_v2"
        else:
            prompt_full_name = f"{username}/bug_to_user_story_v2"

    client = Client()
    project_name = os.getenv("LANGCHAIN_PROJECT", "prompt-optimization-challenge-resolved")
    jsonl_path = "datasets/bug_to_user_story.jsonl"

    if not Path(jsonl_path).exists():
        print(f"❌ Arquivo de dataset não encontrado: {jsonl_path}")
        return 1

    dataset_name = f"{project_name}-eval"
    create_evaluation_dataset(client, dataset_name, jsonl_path)

    print(f"\nPrompt a avaliar: {prompt_full_name}")
    print(f"Dataset: {dataset_name}")
    print("\nIniciando avaliação no LangSmith (aparecerá em Datasets & Experiments → Experiments)...")
    print("⏳ Aguarde — cada exemplo faz 6 chamadas ao LLM com delays para o free tier...\n")

    # Usar apenas 3 exemplos para economizar cota do free tier
    examples = list(client.list_examples(dataset_name=dataset_name))[:3]

    experiment_prefix = prompt_full_name.replace("/", "--")

    try:
        target = build_target(prompt_full_name)
        evaluators = make_evaluators()

        results = ls_evaluate(
            target,
            data=examples,
            evaluators=evaluators,
            experiment_prefix=experiment_prefix,
            client=client,
            max_concurrency=1,
            metadata={"prompt": prompt_full_name, "project": project_name},
        )

        passed = display_results(prompt_full_name, results)

        print(f"\n✓ Experimento registrado no LangSmith:")
        print(f"  https://smith.langchain.com/o/datasets/{dataset_name}/experiments")

        if passed:
            print("\n✅ Próximos passos:")
            print("1. Tire print do terminal e do LangSmith")
            print("2. Documente no README.md")
            return 0
        else:
            print("\n⚠️  Refatore o prompt e rode novamente: python src/evaluate.py")
            return 1

    except Exception as e:
        print(f"\n❌ Erro durante avaliação: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
