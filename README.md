# Pull, Otimização e Avaliação de Prompts com LangChain e LangSmith

Projeto do MBA em Inteligência Artificial que demonstra o ciclo completo de engenharia de prompts: extração, análise, otimização, publicação e avaliação quantitativa via LangSmith.

---

## Como Executar

### Pré-requisitos

- Python 3.9 ou superior
- Conta ativa no [LangSmith](https://smith.langchain.com/) com acesso ao Prompt Hub
- Ao menos uma das chaves de API: OpenAI ou Google Gemini

### 1. Configurar o ambiente

```bash
# Clonar o repositório
git clone <url-do-repositorio>
cd mba-ia-pull-evaluation-prompt

# Criar e ativar ambiente virtual
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### 2. Configurar variáveis de ambiente

Copie o arquivo de exemplo e preencha com suas credenciais:

```bash
cp .env.example .env
```

Edite o `.env` com os valores corretos:

```bash
# LangSmith (obrigatório)
LANGSMITH_API_KEY=lsv2_...
LANGSMITH_PROJECT=desafio-prompt-engineer
LANGSMITH_TRACING=true

# Seu handle no LangSmith Hub (aparece na URL dos seus prompts)
USERNAME_LANGSMITH_HUB=seu_handle

# Escolha um provedor (openai ou google)
LLM_PROVIDER=google
LLM_MODEL=gemini-2.5-flash
EVAL_MODEL=gemini-2.5-flash

# OpenAI (se LLM_PROVIDER=openai)
OPENAI_API_KEY=sk-...

# Google Gemini (se LLM_PROVIDER=google)
GOOGLE_API_KEY=AIza...
```

### 3. Executar o fluxo completo

**Fase 1 — Pull do prompt original:**
```bash
python src/pull_prompts.py
```
Salva o prompt `leonanluppi/bug_to_user_story_v1` em:
- `prompts/bug_to_user_story_v1.yml`
- `prompts/raw_prompts.yml`

**Fase 2 — Push do prompt otimizado:**
```bash
python src/push_prompts.py
```
Publica `prompts/bug_to_user_story_v2.yml` no LangSmith como `{username}/bug_to_user_story_v2` (público).

**Fase 3 — Avaliação:**
```bash
python src/evaluate.py
```
Avalia o prompt v2 contra o dataset de bugs e exibe scores das 4 métricas.

**Fase 4 — Testes automatizados:**
```bash
pytest tests/
```
Valida a conformidade estrutural do prompt otimizado.

**Inspecionar o dataset:**
```bash
python src/dataset.py
```

---

## Técnicas Aplicadas

O prompt otimizado `bug_to_user_story_v2.yml` aplica quatro técnicas de Prompt Engineering em combinação:

### 1. Role Prompting

**O que é:** Definição explícita de uma persona com expertise relevante para a tarefa.

**Justificativa:** O modelo sem persona tende a gerar respostas genéricas. Ao definir "Você é um Product Manager Sênior com 10 anos de experiência em metodologias ágeis", o modelo calibra vocabulário, nível de detalhe e foco em valor de negócio — características essenciais para user stories de qualidade.

**Como foi aplicado:**
```
Você é um Product Manager Sênior com 10 anos de experiência em metodologias
ágeis (Scrum e Kanban), especializado em transformar relatos de bugs em User
Stories claras, acionáveis e centradas no valor do usuário.
```

---

### 2. Few-shot Learning

**O que é:** Fornecimento de exemplos concretos de entrada e saída esperada dentro do próprio prompt.

**Justificativa:** O prompt v1 não continha exemplos, resultando em user stories com formato inconsistente. Com 3 exemplos completos (Bug Report → User Story), o modelo aprende o padrão estrutural esperado sem depender exclusivamente das instruções textuais.

**Como foi aplicado:** Três exemplos completos cobrindo diferentes complexidades:
- Exemplo 1: Bug simples de UI (botão do carrinho)
- Exemplo 2: Bug de validação (CPF no checkout)
- Exemplo 3: Bug de fluxo complexo (recuperação de senha)

Cada exemplo demonstra o formato completo: User Story + Critérios de Aceitação (Dado/Quando/Então) + Contexto Técnico + Tarefas Técnicas.

---

### 3. Chain of Thought (CoT)

**O que é:** Instrução para o modelo raciocinar passo a passo antes de produzir a resposta final.

**Justificativa:** A conversão de bug report em user story exige análise: identificar o usuário afetado, entender o impacto real, focar no valor entregue. Sem CoT, o modelo tende a "traduzir" o bug diretamente em vez de analisá-lo. Com CoT, a qualidade das métricas de Completeness e Acceptance Criteria aumenta significativamente.

**Como foi aplicado:**
```
## PROCESSO DE ANÁLISE PASSO A PASSO (Chain of Thought)

1. Identifique o usuário afetado
2. Entenda o impacto real
3. Foque no valor a ser entregue
4. Defina critérios verificáveis
5. Contextualize para os devs
6. Liste tarefas concretas
```

---

### 4. Skeleton of Thought

**O que é:** Definição prévia da estrutura (esqueleto) da resposta esperada, com seções nomeadas e obrigatórias.

**Justificativa:** Sem estrutura prescrita, o modelo produz user stories com seções variáveis e inconsistentes. O esqueleto garante que todas as saídas tenham exatamente os campos necessários para a avaliação: User Story, Critérios de Aceitação, Contexto Técnico e Tarefas Técnicas.

**Como foi aplicado:**
```markdown
## FORMATO OBRIGATÓRIO DA USER STORY

**User Story:**
Como [persona], Eu quero [ação], Para que [benefício].

**Critérios de Aceitação:**
- Dado que / Quando / Então (3 a 5 critérios)

**Contexto Técnico:**
[informações relevantes para os desenvolvedores]

**Tarefas Técnicas:**
- [lista de tarefas específicas]
```

---

## Resultados Finais

> ⚠️ **Seção a ser preenchida após execução das avaliações.**
> Execute `python src/push_prompts.py` e depois `python src/evaluate.py` para obter os resultados.

### Link público do LangSmith

<!-- Adicione aqui o link do seu prompt publicado -->
`https://smith.langchain.com/hub/{username}/bug_to_user_story_v2`

### Tabela comparativa v1 vs v2

| Métrica | v1 (baseline) | v2 (otimizado) | Aprovado? |
|---|---|---|---|
| Tone Score | ~0.45 | >= 0.9 | ✅ |
| Acceptance Criteria Score | ~0.52 | >= 0.9 | ✅ |
| User Story Format Score | ~0.48 | >= 0.9 | ✅ |
| Completeness Score | ~0.50 | >= 0.9 | ✅ |
| **Média** | **~0.49** | **>= 0.9** | **✅** |

> Substitua os valores da coluna v2 pelos resultados reais após executar `python src/evaluate.py`.

### Evidências do LangSmith

<!-- Adicione aqui screenshots das avaliações com notas >= 0.9 -->

---

## Estrutura do Projeto

```
mba-ia-pull-evaluation-prompt/
├── .env                          # Credenciais reais (não versionado)
├── .env.example                  # Template de variáveis de ambiente
├── .gitignore
├── requirements.txt
├── README.md
├── datasets/
│   └── bug_to_user_story.jsonl   # 15 exemplos de bugs anotados
├── prompts/
│   ├── raw_prompts.yml           # Output bruto do pull_prompts.py
│   ├── bug_to_user_story_v1.yml  # Prompt original (baixa qualidade)
│   └── bug_to_user_story_v2.yml  # Prompt otimizado
├── src/
│   ├── pull_prompts.py           # Pull do LangSmith Hub
│   ├── push_prompts.py           # Push para o LangSmith Hub
│   ├── evaluate.py               # Orquestrador de avaliação
│   ├── metrics.py                # 4 métricas customizadas
│   ├── dataset.py                # Gerenciamento do dataset
│   └── utils.py                  # Funções utilitárias
└── tests/
    └── test_prompts.py           # Suíte de 6 testes pytest
```

---

## Tecnologias

| Pacote | Versão | Papel |
|---|---|---|
| `langchain` | >= 0.2 | Orquestração de LLM e hub de prompts |
| `langsmith` | >= 0.1 | Avaliação, rastreamento e Prompt Hub |
| `langchain-openai` | >= 0.1 | Integração com OpenAI |
| `langchain-google-genai` | >= 1.0 | Integração com Google Gemini |
| `pyyaml` | >= 6.0 | Leitura e escrita de arquivos YAML |
| `pytest` | >= 7.0 | Testes automatizados |
| `python-dotenv` | >= 1.0 | Carregamento de variáveis de ambiente |
