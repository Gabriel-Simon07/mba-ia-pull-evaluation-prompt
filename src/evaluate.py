"""
Script COMPLETO para avaliar prompts otimizados.

Este script:
1. Carrega dataset de avaliação de arquivo .jsonl (datasets/bug_to_user_story.jsonl)
2. Cria/atualiza dataset no LangSmith
3. Puxa prompts otimizados do LangSmith Hub (fonte única de verdade)
4. Executa prompts contra o dataset
5. Calcula 4 métricas específicas para Bug to User Story:
   - Tone Score
   - Acceptance Criteria Score
   - User Story Format Score
   - Completeness Score
6. Publica resultados no dashboard do LangSmith
7. Exibe resumo no terminal

Suporta múltiplos providers de LLM:
- OpenAI (gpt-4o, gpt-4o-mini)
- Google Gemini (gemini-2.5-flash)

Configure o provider no arquivo .env através da variável LLM_PROVIDER.
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
from langchain import hub
from langchain_core.prompts import ChatPromptTemplate
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


def get_llm():
    return get_configured_llm(temperature=0)


def load_dataset_from_jsonl(jsonl_path: str) -> List[Dict[str, Any]]:
    examples = []

    try:
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    example = json.loads(line)
                    examples.append(example)

        return examples

    except FileNotFoundError:
        print(f"❌ Arquivo não encontrado: {jsonl_path}")
        print("\nCertifique-se de que o arquivo datasets/bug_to_user_story.jsonl existe.")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ Erro ao parsear JSONL: {e}")
        return []
    except Exception as e:
        print(f"❌ Erro ao carregar dataset: {e}")
        return []


def create_evaluation_dataset(client: Client, dataset_name: str, jsonl_path: str) -> str:
    print(f"Criando dataset de avaliação: {dataset_name}...")

    examples = load_dataset_from_jsonl(jsonl_path)

    if not examples:
        print("❌ Nenhum exemplo carregado do arquivo .jsonl")
        return dataset_name

    print(f"   ✓ Carregados {len(examples)} exemplos do arquivo {jsonl_path}")

    try:
        datasets = client.list_datasets(dataset_name=dataset_name)
        existing_dataset = None

        for ds in datasets:
            if ds.name == dataset_name:
                existing_dataset = ds
                break

        if existing_dataset:
            print(f"   ✓ Dataset '{dataset_name}' já existe, usando existente")
            return dataset_name
        else:
            dataset = client.create_dataset(dataset_name=dataset_name)

            for example in examples:
                client.create_example(
                    dataset_id=dataset.id,
                    inputs=example["inputs"],
                    outputs=example["outputs"]
                )

            print(f"   ✓ Dataset criado com {len(examples)} exemplos")
            return dataset_name

    except Exception as e:
        print(f"   ⚠️  Erro ao criar dataset: {e}")
        return dataset_name


def pull_prompt_from_langsmith(prompt_name: str) -> ChatPromptTemplate:
    try:
        print(f"   Puxando prompt do LangSmith Hub: {prompt_name}")
        prompt = hub.pull(prompt_name)
        print(f"   ✓ Prompt carregado com sucesso")
        return prompt

    except Exception as e:
        error_msg = str(e).lower()

        print(f"\n{'=' * 70}")
        print(f"❌ ERRO: Não foi possível carregar o prompt '{prompt_name}'")
        print(f"{'=' * 70}\n")

        if "not found" in error_msg or "404" in error_msg:
            print("⚠️  O prompt não foi encontrado no LangSmith Hub.\n")
            print("AÇÕES NECESSÁRIAS:")
            print("1. Verifique se você já fez push do prompt otimizado:")
            print(f"   python src/push_prompts.py")
            print()
            print("2. Confirme se o prompt foi publicado com sucesso em:")
            print(f"   https://smith.langchain.com/prompts")
            print()
            print(f"3. Certifique-se de que o nome do prompt está correto: '{prompt_name}'")
            print()
            print("4. Se você alterou o prompt no YAML, refaça o push:")
            print(f"   python src/push_prompts.py")
        else:
            print(f"Erro técnico: {e}\n")
            print("Verifique:")
            print("- LANGSMITH_API_KEY está configurada corretamente no .env")
            print("- Você tem acesso ao workspace do LangSmith")
            print("- Sua conexão com a internet está funcionando")

        print(f"\n{'=' * 70}\n")
        raise


def evaluate_prompt_on_example(
    prompt_template: ChatPromptTemplate,
    example: Any,
    llm: Any
) -> Dict[str, Any]:
    try:
        inputs = example.inputs if hasattr(example, 'inputs') else {}
        outputs = example.outputs if hasattr(example, 'outputs') else {}

        chain = prompt_template | llm

        response = chain.invoke(inputs)
        answer = response.content

        reference = outputs.get("reference", "") if isinstance(outputs, dict) else ""

        if isinstance(inputs, dict):
            question = inputs.get("bug_report", inputs.get("question", inputs.get("pr_title", "N/A")))
        else:
            question = "N/A"

        return {
            "answer": answer,
            "reference": reference,
            "question": question
        }

    except Exception as e:
        print(f"      ⚠️  Erro ao avaliar exemplo: {e}")
        import traceback
        print(f"      Traceback: {traceback.format_exc()}")
        return {
            "answer": "",
            "reference": "",
            "question": ""
        }


def evaluate_prompt(
    prompt_name: str,
    dataset_name: str,
    client: Client
) -> Dict[str, float]:
    print(f"\n🔍 Avaliando: {prompt_name}")

    try:
        prompt_template = pull_prompt_from_langsmith(prompt_name)

        examples = list(client.list_examples(dataset_name=dataset_name))
        print(f"   Dataset: {len(examples)} exemplos")

        llm = get_llm()

        f1_scores = []
        tone_scores = []
        acceptance_scores = []
        format_scores = []
        completeness_scores = []

        print("   Avaliando exemplos...")

        # 3 exemplos × 6 chamadas = 18 chamadas total (dentro do limite de 20/dia)
        # Sleep de 13s entre cada chamada para respeitar 5 req/min do free tier
        RATE_LIMIT_SLEEP = 13

        for i, example in enumerate(examples[:3], 1):
            print(f"\n   Exemplo {i}/3...")

            result = evaluate_prompt_on_example(prompt_template, example, llm)
            time.sleep(RATE_LIMIT_SLEEP)

            if result["answer"]:
                f1 = evaluate_f1_score(result["question"], result["answer"], result["reference"])
                time.sleep(RATE_LIMIT_SLEEP)
                tone = evaluate_tone_score(result["question"], result["answer"], result["reference"])
                time.sleep(RATE_LIMIT_SLEEP)
                acceptance = evaluate_acceptance_criteria_score(result["question"], result["answer"], result["reference"])
                time.sleep(RATE_LIMIT_SLEEP)
                fmt = evaluate_user_story_format_score(result["question"], result["answer"], result["reference"])
                time.sleep(RATE_LIMIT_SLEEP)
                completeness = evaluate_completeness_score(result["question"], result["answer"], result["reference"])

                f1_scores.append(f1["score"])
                tone_scores.append(tone["score"])
                acceptance_scores.append(acceptance["score"])
                format_scores.append(fmt["score"])
                completeness_scores.append(completeness["score"])

                print(
                    f"      [{i}/3] "
                    f"F1:{f1['score']:.2f} "
                    f"Tone:{tone['score']:.2f} "
                    f"Acceptance:{acceptance['score']:.2f} "
                    f"Format:{fmt['score']:.2f} "
                    f"Completeness:{completeness['score']:.2f}"
                )

        def avg(lst):
            return round(sum(lst) / len(lst), 4) if lst else 0.0

        return {
            "f1_score": avg(f1_scores),
            "tone": avg(tone_scores),
            "acceptance_criteria": avg(acceptance_scores),
            "user_story_format": avg(format_scores),
            "completeness": avg(completeness_scores),
        }

    except Exception as e:
        print(f"   ❌ Erro na avaliação: {e}")
        return {
            "tone": 0.0,
            "acceptance_criteria": 0.0,
            "user_story_format": 0.0,
            "completeness": 0.0,
        }


def display_results(prompt_name: str, scores: Dict[str, float]) -> bool:
    print("\n" + "=" * 50)
    print(f"Prompt: {prompt_name}")
    print("=" * 50)

    metric_labels = {
        "f1_score": "F1-Score",
        "tone": "Tone Score",
        "acceptance_criteria": "Acceptance Criteria Score",
        "user_story_format": "User Story Format Score",
        "completeness": "Completeness Score",
    }

    print("\nMétricas Bug to User Story:")
    all_passed = True
    for key, label in metric_labels.items():
        score = scores.get(key, 0.0)
        passed = score >= MINIMUM_SCORE
        if not passed:
            all_passed = False
        print(f"  - {label}: {format_score(score, threshold=MINIMUM_SCORE)}")

    average_score = sum(scores.values()) / len(scores) if scores else 0.0

    print("\n" + "-" * 50)
    print(f"📊 MÉDIA GERAL: {average_score:.4f}")
    print("-" * 50)

    # Critério: TODAS as métricas >= 0.9 E média >= 0.9
    passed = all_passed and average_score >= MINIMUM_SCORE

    if passed:
        print(f"\n✅ STATUS: APROVADO - Todas as métricas >= {MINIMUM_SCORE}")
    else:
        print(f"\n❌ STATUS: REPROVADO")
        if not all_passed:
            below = [
                metric_labels[k] for k, v in scores.items() if v < MINIMUM_SCORE
            ]
            print(f"   Métricas abaixo de {MINIMUM_SCORE}: {', '.join(below)}")
        if average_score < MINIMUM_SCORE:
            print(f"   Média atual: {average_score:.4f} | Necessário: {MINIMUM_SCORE}")

    return passed


def main():
    parser = argparse.ArgumentParser(description="Avalia prompts do LangSmith Hub")
    parser.add_argument("--prompt", type=str, default=None, help="Nome completo do prompt no hub (ex: usuario/bug_to_user_story_v1)")
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

    # Usar --prompt se fornecido, senão montar a partir do username
    if args.prompt:
        prompt_full_name = args.prompt
    else:
        username = os.getenv("USERNAME_LANGSMITH_HUB", "").strip()
        if not username:
            print("⚠️  USERNAME_LANGSMITH_HUB não configurado no .env")
            print("   Configure com seu username do LangSmith para avaliar o prompt correto.")
            print("   Tentando avaliar sem prefixo de username...\n")
            prompt_full_name = "bug_to_user_story_v2"
        else:
            prompt_full_name = f"{username}/bug_to_user_story_v2"

    client = Client()
    project_name = os.getenv("LANGCHAIN_PROJECT", "prompt-optimization-challenge-resolved")

    jsonl_path = "datasets/bug_to_user_story.jsonl"

    if not Path(jsonl_path).exists():
        print(f"❌ Arquivo de dataset não encontrado: {jsonl_path}")
        print("\nCertifique-se de que o arquivo existe antes de continuar.")
        return 1

    dataset_name = f"{project_name}-eval"
    create_evaluation_dataset(client, dataset_name, jsonl_path)

    print("\n" + "=" * 70)
    print("INICIANDO AVALIAÇÃO")
    print("=" * 70)
    print(f"\nPrompt a avaliar: {prompt_full_name}")
    print("\nCertifique-se de ter feito push do prompt antes de avaliar:")
    print("  python src/push_prompts.py\n")

    all_passed = True
    evaluated_count = 0
    results_summary = []

    try:
        evaluated_count += 1
        scores = evaluate_prompt(prompt_full_name, dataset_name, client)
        passed = display_results(prompt_full_name, scores)
        all_passed = passed

        results_summary.append({
            "prompt": prompt_full_name,
            "scores": scores,
            "passed": passed
        })

    except Exception as e:
        print(f"\n❌ Falha ao avaliar '{prompt_full_name}': {e}")
        all_passed = False
        results_summary.append({
            "prompt": prompt_full_name,
            "scores": {"f1_score": 0.0, "tone": 0.0, "acceptance_criteria": 0.0, "user_story_format": 0.0, "completeness": 0.0},
            "passed": False
        })

    print("\n" + "=" * 50)
    print("RESUMO FINAL")
    print("=" * 50 + "\n")

    if evaluated_count == 0:
        print("⚠️  Nenhum prompt foi avaliado")
        return 1

    print(f"Prompts avaliados: {evaluated_count}")
    print(f"Aprovados: {sum(1 for r in results_summary if r['passed'])}")
    print(f"Reprovados: {sum(1 for r in results_summary if not r['passed'])}\n")

    if all_passed:
        print("✅ Todos os prompts atingiram as métricas mínimas de 0.9!")
        print(f"\n✓ Confira os resultados em:")
        print(f"  https://smith.langchain.com/projects/{project_name}")
        print("\nPróximos passos:")
        print("1. Documente o processo no README.md")
        print("2. Capture screenshots das avaliações")
        print("3. Faça commit e push para o GitHub")
        return 0
    else:
        print("⚠️  O prompt não atingiu todas as métricas >= 0.9")
        print("\nPróximos passos:")
        print("1. Analise as métricas baixas e refatore o prompt")
        print("2. Atualize prompts/bug_to_user_story_v2.yml")
        print("3. Faça push novamente: python src/push_prompts.py")
        print("4. Execute novamente: python src/evaluate.py")
        return 1


if __name__ == "__main__":
    sys.exit(main())
