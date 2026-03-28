# PRD - Pull, Otimização e Avaliação de Prompts com LangChain e LangSmith

**Versão:** 1.0
**Data:** 2026-03-28
**Status:** Ativo

---

## 1. Visão Geral do Produto

Este documento descreve os requisitos para o desenvolvimento de um software de engenharia de prompts capaz de recuperar prompts de baixa qualidade do LangSmith Prompt Hub, refatorá-los utilizando técnicas avançadas de Prompt Engineering, publicar as versões otimizadas de volta ao LangSmith e validar a qualidade resultante por meio de métricas customizadas.

O produto é parte de um desafio acadêmico do MBA em Inteligência Artificial, cujo foco é demonstrar proficiência na cadeia completa de gerenciamento de prompts: extração, análise, otimização, publicação e avaliação quantitativa.

O ciclo de trabalho é iterativo: o engenheiro de prompts executa avaliações, analisa os resultados, refina os prompts e repete o processo até que todas as métricas atinjam o limiar mínimo de aprovação de 0.9 (90%).

---

## 2. Objetivo

Desenvolver um conjunto de scripts Python e artefatos de prompts que:

1. Realizem o pull automatizado do prompt `leonanluppi/bug_to_user_story_v1` a partir do LangSmith Prompt Hub.
2. Persistam o prompt recuperado localmente em formato YAML para análise e edição.
3. Produzam uma versão otimizada do prompt (`bug_to_user_story_v2.yml`) aplicando ao menos duas técnicas reconhecidas de Prompt Engineering.
4. Realizem o push do prompt otimizado ao LangSmith com metadados descritivos.
5. Avaliem ambas as versões do prompt utilizando quatro métricas customizadas com limiar mínimo de 0.9 por métrica.
6. Forneçam uma suíte de testes automatizados (pytest) que valide a conformidade estrutural dos prompts.

O objetivo final é demonstrar que o prompt otimizado (`v2`) supera o original (`v1`) em todas as métricas de avaliação de forma mensurável e reproduzível.

---

## 3. Escopo

### 3.1 Dentro do Escopo

- Script de pull de prompts do LangSmith Hub.
- Script de push de prompts otimizados ao LangSmith Hub.
- Script de avaliação com métricas customizadas via LangSmith Evaluation.
- Prompt original salvo localmente (`bug_to_user_story_v1.yml`).
- Prompt otimizado com técnicas de Prompt Engineering (`bug_to_user_story_v2.yml`).
- Suíte de testes automatizados com pytest.
- Documentação técnica no `README.md`.
- Suporte a dois provedores de LLM: OpenAI e Google Gemini.

### 3.2 Fora do Escopo

- Interface gráfica (GUI) ou API REST.
- Banco de dados persistente para armazenamento de histórico de avaliações.
- Integração com provedores de LLM além de OpenAI e Google Gemini.
- Deploy em infraestrutura de nuvem.
- CI/CD automatizado.
- Otimização de outros prompts além do `bug_to_user_story`.

---

## 4. Requisitos Funcionais

### 4.1 Módulo de Pull de Prompts (`src/pull_prompts.py`)

**RF-01** - O script deve estabelecer conexão autenticada com o LangSmith utilizando as credenciais definidas no arquivo `.env`.

**RF-02** - O script deve recuperar o prompt identificado como `leonanluppi/bug_to_user_story_v1` a partir do LangSmith Prompt Hub utilizando o pacote `langchain hub`.

**RF-03** - O prompt recuperado deve ser serializado e salvo localmente no arquivo `prompts/raw_prompts.yml`, preservando todos os campos originais incluindo system prompt, user prompt, metadados e versão.

**RF-04** - O script deve exibir no console uma confirmação de sucesso após o pull, incluindo o nome do prompt recuperado e o caminho do arquivo salvo.

**RF-05** - O script deve tratar erros de autenticação, erros de rede e prompts inexistentes com mensagens de erro claras e código de saída adequado.

### 4.2 Módulo de Otimização de Prompts

**RF-06** - O engenheiro deve analisar o arquivo `prompts/bug_to_user_story_v1.yml` e identificar as deficiências em clareza, estrutura, exemplos e critérios de aceitação.

**RF-07** - O prompt otimizado deve ser criado no arquivo `prompts/bug_to_user_story_v2.yml` seguindo o formato YAML estruturado.

**RF-08** - O prompt otimizado deve incorporar ao menos duas das seguintes técnicas de Prompt Engineering:
  - Few-shot Learning
  - Chain of Thought (CoT)
  - Tree of Thought
  - Skeleton of Thought
  - ReAct
  - Role Prompting

**RF-09** - O prompt otimizado deve conter os seguintes elementos obrigatórios:
  - Definição explícita de persona ou papel (Role Prompting).
  - Instruções claras, específicas e sem ambiguidade.
  - Regras explícitas de comportamento e restrições.
  - Ao menos dois exemplos completos de entrada e saída (Few-shot).
  - Tratamento documentado de casos extremos (edge cases).
  - Separação clara entre System Prompt e User Prompt.
  - Campo de metadados com lista das técnicas aplicadas.

**RF-10** - As técnicas aplicadas e suas justificativas devem estar documentadas no `README.md` na seção "Técnicas Aplicadas".

### 4.3 Módulo de Push de Prompts (`src/push_prompts.py`)

**RF-11** - O script deve ler o arquivo `prompts/bug_to_user_story_v2.yml` e validar sua estrutura antes de qualquer operação de rede.

**RF-12** - O script deve realizar o push do prompt otimizado ao LangSmith como `{username}/bug_to_user_story_v2`, onde `{username}` é o identificador do usuário autenticado.

**RF-13** - O push deve incluir os seguintes metadados:
  - Tags descritivas (ex: `optimized`, `few-shot`, `chain-of-thought`).
  - Descrição textual do prompt e sua finalidade.
  - Lista das técnicas de Prompt Engineering aplicadas.

**RF-14** - O prompt publicado deve ser configurado como público no LangSmith.

**RF-15** - O script deve exibir no console a URL pública do prompt publicado após conclusão bem-sucedida.

### 4.4 Módulo de Avaliação (`src/evaluate.py` e `src/metrics.py`)

**RF-16** - O script de avaliação deve executar ambas as versões do prompt (`v1` e `v2`) contra o dataset de bugs disponível.

**RF-17** - A avaliação deve utilizar as seguintes quatro métricas customizadas, todas com limiar mínimo de 0.9:
  - **Tone Score**: avalia se o tom da user story gerada é adequado e profissional.
  - **Acceptance Criteria Score**: avalia se os critérios de aceitação estão presentes, claros e mensuráveis.
  - **User Story Format Score**: avalia se o formato padrão de user story ("Como... Quero... Para...") é seguido corretamente.
  - **Completeness Score**: avalia se a user story cobre todos os aspectos relevantes do bug informado.

**RF-18** - O resultado de cada avaliação deve ser exibido no console no seguinte formato:
  ```
  Prompt: {nome_do_prompt}
  - Tone Score: {valor}
  - Acceptance Criteria Score: {valor}
  - User Story Format Score: {valor}
  - Completeness Score: {valor}
  - Media: {valor}
  Status: APROVADO | FALHOU
  ```

**RF-19** - O status de aprovação deve ser `APROVADO` somente quando todas as quatro métricas individuais atingirem valor maior ou igual a 0.9 E a média das quatro métricas também for maior ou igual a 0.9.

**RF-20** - As avaliações devem ser registradas no LangSmith para rastreabilidade e visualização no dashboard.

**RF-21** - O módulo de métricas (`src/metrics.py`) deve implementar cada uma das quatro métricas como funções avaliadas por LLM, utilizando os modelos configurados.

### 4.5 Módulo de Dataset (`src/dataset.py`)

**RF-22** - O módulo deve prover acesso ao dataset de bugs composto por ao menos 15 exemplos, distribuídos em:
  - 5 bugs simples.
  - 7 bugs de complexidade média.
  - 3 bugs complexos.

**RF-23** - O dataset deve conter ao menos 20 exemplos anotados para uso nas avaliações do LangSmith.

**RF-24** - Cada exemplo do dataset deve conter: descrição do bug de entrada e a user story esperada como saída de referência.

### 4.6 Módulo Utilitário (`src/utils.py`)

**RF-25** - O módulo deve prover funções auxiliares reutilizáveis, incluindo: carregamento de variáveis de ambiente, inicialização de clientes LangSmith e instanciação de modelos LLM configurados.

**RF-26** - O módulo deve suportar instanciação de LLM para dois provedores:
  - OpenAI: `gpt-4o-mini` para geração de respostas e `gpt-4o` para avaliação.
  - Google Gemini: `gemini-2.5-flash` para geração e avaliação, respeitando os limites de 15 requisições por minuto e 1.500 requisições por dia.

### 4.7 Suíte de Testes (`tests/test_prompts.py`)

**RF-27** - Implementar os seguintes casos de teste com pytest:

| ID do Teste | Nome da Função | Descrição |
|---|---|---|
| T-01 | `test_prompt_has_system_prompt` | Valida que o campo de system prompt existe e não está vazio. |
| T-02 | `test_prompt_has_role_definition` | Valida que o prompt define uma persona explícita (ex: "Você é um Product Manager"). |
| T-03 | `test_prompt_mentions_format` | Valida que o prompt exige saída em formato Markdown ou User Story padrão. |
| T-04 | `test_prompt_has_few_shot_examples` | Valida que o prompt contém ao menos dois exemplos de entrada e saída. |
| T-05 | `test_prompt_no_todos` | Valida que o prompt não contém marcadores `[TODO]` no texto. |
| T-06 | `test_minimum_techniques` | Valida que os metadados YAML listam ao menos duas técnicas de Prompt Engineering. |

**RF-28** - Todos os testes devem passar para o prompt `bug_to_user_story_v2.yml`. Os testes para `bug_to_user_story_v1.yml` podem falhar intencionalmente, demonstrando as deficiências da versão original.

---

## 5. Requisitos Não-Funcionais

### 5.1 Desempenho

**RNF-01** - O script de pull deve concluir a operação de recuperação de prompt em até 30 segundos em condições normais de rede.

**RNF-02** - O script de push deve concluir a publicação do prompt em até 30 segundos em condições normais de rede.

**RNF-03** - A avaliação completa do dataset (15 exemplos, 4 métricas) deve concluir em tempo razoável. Para o provedor Gemini, o sistema deve respeitar automaticamente o limite de 15 requisições por minuto implementando controle de rate limit.

### 5.2 Confiabilidade

**RNF-04** - Os scripts devem implementar tratamento de erros robusto para falhas de autenticação, erros de rede e timeouts de API.

**RNF-05** - Em caso de falha durante a avaliação de um exemplo do dataset, o sistema deve registrar o erro e continuar processando os demais exemplos, sem interromper a execução completa.

**RNF-06** - O sistema deve ser idempotente: executar o push múltiplas vezes com o mesmo prompt deve resultar em atualização da versão existente, sem criação de duplicatas.

### 5.3 Manutenibilidade

**RNF-07** - O código deve seguir as convenções PEP 8 para estilo e formatação Python.

**RNF-08** - Cada módulo deve ter responsabilidade única e bem definida, evitando acoplamento excessivo entre scripts.

**RNF-09** - As credenciais e configurações sensíveis devem ser gerenciadas exclusivamente via variáveis de ambiente, nunca hardcoded no código-fonte.

**RNF-10** - O arquivo `.env.example` deve listar todas as variáveis de ambiente necessárias com descrições e exemplos de valores, sem expor credenciais reais.

### 5.4 Segurança

**RNF-11** - O arquivo `.env` contendo credenciais reais deve estar listado no `.gitignore` e nunca deve ser versionado no repositório.

**RNF-12** - As chaves de API (OpenAI, Google, LangSmith) devem ser carregadas exclusivamente de variáveis de ambiente.

### 5.5 Portabilidade

**RNF-13** - O software deve ser executável em sistemas operacionais Windows, macOS e Linux com Python 3.9 ou superior.

**RNF-14** - Todas as dependências devem estar listadas no arquivo `requirements.txt` com versões mínimas especificadas.

### 5.6 Rastreabilidade

**RNF-15** - Todas as execuções de avaliação devem gerar traces no LangSmith, permitindo auditoria e análise detalhada de cada chamada de LLM.

**RNF-16** - O tracing detalhado de ao menos três exemplos de avaliação deve ser acessível publicamente no dashboard do LangSmith.

---

## 6. Critérios de Aceite

### 6.1 Critérios de Aceite do Prompt Otimizado

**CA-01** - O arquivo `prompts/bug_to_user_story_v2.yml` deve existir e ser um YAML válido e bem-formado.

**CA-02** - O prompt otimizado deve obter **Tone Score >= 0.9** na avaliação automatizada.

**CA-03** - O prompt otimizado deve obter **Acceptance Criteria Score >= 0.9** na avaliação automatizada.

**CA-04** - O prompt otimizado deve obter **User Story Format Score >= 0.9** na avaliação automatizada.

**CA-05** - O prompt otimizado deve obter **Completeness Score >= 0.9** na avaliação automatizada.

**CA-06** - A média aritmética das quatro métricas deve ser **>= 0.9**.

**CA-07** - Todas as quatro métricas devem ser **>= 0.9 individualmente**, sem exceção.

### 6.2 Critérios de Aceite dos Testes Automatizados

**CA-08** - Todos os seis testes definidos em `tests/test_prompts.py` devem passar ao ser executados contra `bug_to_user_story_v2.yml`.

**CA-09** - A suíte de testes deve ser executável com o comando `pytest tests/` sem erros de importação ou configuração.

### 6.3 Critérios de Aceite da Infraestrutura LangSmith

**CA-10** - O prompt `{username}/bug_to_user_story_v2` deve estar publicado e acessível publicamente no LangSmith Prompt Hub.

**CA-11** - O dataset de avaliação deve conter ao menos 20 exemplos anotados no LangSmith.

**CA-12** - Devem existir execuções de avaliação registradas no LangSmith para ambas as versões do prompt (v1 com notas baixas, v2 com notas >= 0.9).

**CA-13** - O tracing detalhado de ao menos três exemplos individuais de avaliação deve estar disponível no LangSmith.

### 6.4 Critérios de Aceite da Documentação

**CA-14** - O `README.md` deve conter a seção "Técnicas Aplicadas" com descrição de ao menos duas técnicas, justificativas de escolha e exemplos práticos de como foram aplicadas.

**CA-15** - O `README.md` deve conter a seção "Resultados Finais" com link público do LangSmith, tabela comparativa v1 vs v2 e evidências visuais (screenshots) das avaliações com notas >= 0.9.

**CA-16** - O `README.md` deve conter a seção "Como Executar" com pré-requisitos, instruções de configuração do ambiente e comandos de execução para cada script.

---

## 7. Estrutura do Projeto

```
desafio-prompt-engineer/
├── .env                          # Credenciais reais (não versionado)
├── .env.example                  # Template de variáveis de ambiente
├── .gitignore                    # Inclui .env e arquivos sensíveis
├── requirements.txt              # Dependências Python com versões
├── README.md                     # Documentação técnica completa
├── prompts/
│   ├── bug_to_user_story_v1.yml  # Prompt original (baixa qualidade) - gerado pelo pull
│   ├── raw_prompts.yml           # Output bruto do pull_prompts.py
│   └── bug_to_user_story_v2.yml  # Prompt otimizado (criado manualmente)
├── src/
│   ├── pull_prompts.py           # Script de pull do LangSmith Hub
│   ├── push_prompts.py           # Script de push para o LangSmith Hub
│   ├── evaluate.py               # Orquestrador de avaliação
│   ├── metrics.py                # Implementação das 4 métricas customizadas
│   ├── dataset.py                # Gerenciamento do dataset de bugs
│   └── utils.py                  # Funções utilitárias compartilhadas
└── tests/
    └── test_prompts.py           # Suíte de testes pytest
```

### 7.1 Descrição dos Artefatos

| Artefato | Responsabilidade | Status |
|---|---|---|
| `src/pull_prompts.py` | Recuperar e salvar prompt do LangSmith Hub | A criar |
| `src/push_prompts.py` | Publicar prompt otimizado no LangSmith Hub | A criar |
| `src/evaluate.py` | Orquestrar avaliação e exibir resultados | Parcialmente pronto |
| `src/metrics.py` | Funções das 4 métricas de avaliação | Já disponível |
| `src/dataset.py` | Dataset de 15+ bugs para avaliação | Já disponível |
| `src/utils.py` | Funções utilitárias e inicialização de clientes | Já disponível |
| `prompts/bug_to_user_story_v2.yml` | Prompt otimizado com técnicas aplicadas | A criar |
| `tests/test_prompts.py` | Testes de conformidade estrutural dos prompts | A criar |
| `README.md` | Documentação técnica e evidências | A criar |

---

## 8. Fluxo de Execução

### 8.1 Fluxo Completo do Desafio

```
FASE 1 - EXTRAÇÃO
    Executar: python src/pull_prompts.py
    |
    +-- Autentica no LangSmith com credenciais do .env
    |
    +-- Pull de leonanluppi/bug_to_user_story_v1 via langchain hub
    |
    +-- Salva em prompts/raw_prompts.yml
    |
    v
FASE 2 - ANÁLISE E OTIMIZAÇÃO (manual)
    Analisar prompts/bug_to_user_story_v1.yml
    |
    +-- Identificar deficiências: falta de persona, ausência de exemplos,
    |   instruções ambíguas, sem critérios de aceitação explícitos
    |
    +-- Selecionar ao menos 2 técnicas de Prompt Engineering
    |
    +-- Criar prompts/bug_to_user_story_v2.yml com melhorias
    |
    +-- Adicionar metadados YAML com técnicas aplicadas
    |
    v
FASE 3 - AVALIAÇÃO INICIAL (baseline)
    Executar: python src/evaluate.py --prompt v1
    |
    +-- Carrega dataset de bugs
    |
    +-- Executa prompt v1 para cada bug (LLM: gpt-4o-mini ou gemini-2.5-flash)
    |
    +-- Avalia cada resposta com 4 métricas (LLM: gpt-4o ou gemini-2.5-flash)
    |
    +-- Exibe resultados (esperado: métricas abaixo de 0.9)
    |
    +-- Registra traces no LangSmith
    |
    v
FASE 4 - PUBLICAÇÃO DO PROMPT OTIMIZADO
    Executar: python src/push_prompts.py
    |
    +-- Lê e valida prompts/bug_to_user_story_v2.yml
    |
    +-- Push para LangSmith como {username}/bug_to_user_story_v2
    |
    +-- Adiciona tags, descrição e metadados de técnicas
    |
    +-- Configura visibilidade como público
    |
    +-- Exibe URL pública do prompt publicado
    |
    v
FASE 5 - AVALIAÇÃO DO PROMPT OTIMIZADO
    Executar: python src/evaluate.py --prompt v2
    |
    +-- Carrega dataset de bugs
    |
    +-- Executa prompt v2 para cada bug
    |
    +-- Avalia cada resposta com 4 métricas
    |
    +-- Verifica se todas as métricas >= 0.9
    |
    +-- Exibe status: APROVADO ou FALHOU
    |
    +-- Registra traces no LangSmith
    |
    v
DECISÃO
    Todas as métricas >= 0.9?
    |
    +-- SIM: Desafio concluído. Documentar evidências no README.md
    |
    +-- NAO: Retornar à Fase 2 para nova iteração de otimização
         (esperado: 3-5 iterações até aprovação)

FASE 6 - VALIDAÇÃO AUTOMATIZADA
    Executar: pytest tests/
    |
    +-- Todos os 6 testes devem passar para bug_to_user_story_v2.yml
    |
    v
FASE 7 - DOCUMENTAÇÃO FINAL
    Atualizar README.md com:
    - Técnicas aplicadas e justificativas
    - Resultados finais com tabela comparativa v1 vs v2
    - Link público do LangSmith e screenshots
    - Instruções de execução
```

### 8.2 Ciclo Iterativo de Otimização

O processo de otimização é inerentemente iterativo. A expectativa é que sejam necessárias entre 3 e 5 iterações para atingir aprovação em todas as métricas. Cada iteração consiste em:

1. Analisar quais métricas ficaram abaixo de 0.9.
2. Identificar as causas no prompt (ex: ausência de critérios de aceitação claros, formato não prescrito).
3. Editar `prompts/bug_to_user_story_v2.yml` com melhorias direcionadas.
4. Executar `python src/push_prompts.py` para atualizar o prompt no LangSmith.
5. Executar `python src/evaluate.py` para medir o impacto das mudanças.
6. Repetir até aprovação.

---

## 9. Métricas de Sucesso

### 9.1 Métricas de Avaliação do Prompt

| Métrica | Limiar Mínimo | Descrição |
|---|---|---|
| Tone Score | >= 0.9 | Tom profissional e adequado para documentação de produto |
| Acceptance Criteria Score | >= 0.9 | Critérios de aceitação presentes, claros e mensuráveis |
| User Story Format Score | >= 0.9 | Formato "Como... Quero... Para..." seguido corretamente |
| Completeness Score | >= 0.9 | Cobertura completa dos aspectos relevantes do bug |
| Media Geral | >= 0.9 | Media aritmética das quatro métricas acima |

### 9.2 Métricas de Qualidade do Projeto

| Indicador | Meta | Forma de Verificação |
|---|---|---|
| Testes automatizados passando | 6 de 6 (100%) | `pytest tests/` retorna 0 falhas |
| Técnicas de PE aplicadas | >= 2 | Metadados YAML e README.md |
| Exemplos no dataset LangSmith | >= 20 | Dashboard do LangSmith |
| Traces registrados no LangSmith | >= 3 detalhados | Dashboard do LangSmith |
| Prompt v2 público no LangSmith | Sim | URL acessível sem autenticação |
| Iterações de otimização | 3 a 5 | Histórico de versões no LangSmith |

### 9.3 Demonstração de Melhoria

O projeto deve evidenciar a diferença de qualidade entre as versões. O exemplo abaixo ilustra o contraste esperado:

**Versão v1 (antes da otimização):**
- Tone Score: ~0.45
- Acceptance Criteria Score: ~0.52
- User Story Format Score: ~0.48
- Completeness Score: ~0.50
- Status: FALHOU

**Versão v2 (após otimização):**
- Tone Score: >= 0.94
- Acceptance Criteria Score: >= 0.96
- User Story Format Score: >= 0.93
- Completeness Score: >= 0.92
- Status: APROVADO

---

## 10. Entregáveis

### 10.1 Entregáveis de Código

| Entregável | Descrição | Obrigatoriedade |
|---|---|---|
| `src/pull_prompts.py` | Script funcional de extração de prompts do LangSmith Hub | Obrigatório |
| `src/push_prompts.py` | Script funcional de publicação de prompts no LangSmith Hub | Obrigatório |
| `prompts/bug_to_user_story_v2.yml` | Prompt otimizado com ao menos 2 técnicas aplicadas | Obrigatório |
| `tests/test_prompts.py` | Suíte de 6 testes pytest todos passando | Obrigatório |

### 10.2 Entregáveis de Documentação

| Entregável | Conteúdo | Obrigatoriedade |
|---|---|---|
| `README.md` - Seção "Técnicas Aplicadas" | Nome das técnicas, justificativas e exemplos práticos de aplicação | Obrigatório |
| `README.md` - Seção "Resultados Finais" | Link LangSmith, screenshots com notas >= 0.9, tabela comparativa v1 vs v2 | Obrigatório |
| `README.md` - Seção "Como Executar" | Pré-requisitos, configuração do `.env`, comandos de execução | Obrigatório |
| `.env.example` | Template com todas as variáveis necessárias e descrições | Obrigatório |
| `requirements.txt` | Dependências com versões mínimas | Obrigatório |

### 10.3 Entregáveis de Evidência no LangSmith

| Entregável | Descrição | Obrigatoriedade |
|---|---|---|
| Prompt v2 público | URL pública do `{username}/bug_to_user_story_v2` no LangSmith Hub | Obrigatório |
| Dataset anotado | Dataset com >= 20 exemplos no LangSmith | Obrigatório |
| Avaliação v1 | Execução registrada com métricas baixas (baseline) | Obrigatório |
| Avaliação v2 aprovada | Execução registrada com todas as métricas >= 0.9 | Obrigatório |
| Traces detalhados | Tracing de ao menos 3 exemplos individuais acessível | Obrigatório |

### 10.4 Entregável de Repositório

| Entregável | Descrição | Obrigatoriedade |
|---|---|---|
| Repositório público no GitHub | Fork do repositório base com todo o código e documentação | Obrigatório |

---

## 11. Tecnologias e Dependências

### 11.1 Linguagem e Ambiente

| Tecnologia | Versão | Papel |
|---|---|---|
| Python | 3.9+ | Linguagem principal do projeto |
| pip | Atual | Gerenciamento de dependências |
| python-dotenv | >= 1.0 | Carregamento de variáveis de ambiente |

### 11.2 Frameworks e Bibliotecas

| Pacote | Versão | Papel |
|---|---|---|
| `langchain` | >= 0.2 | Framework de orquestração de LLM e hub de prompts |
| `langchain-openai` | >= 0.1 | Integração com modelos OpenAI |
| `langchain-google-genai` | >= 1.0 | Integração com modelos Google Gemini |
| `langsmith` | >= 0.1 | Cliente LangSmith, avaliação e rastreamento |
| `pyyaml` | >= 6.0 | Leitura e escrita de arquivos YAML |
| `pytest` | >= 7.0 | Framework de testes automatizados |

### 11.3 Modelos de LLM

| Provedor | Modelo | Finalidade | Custo Estimado |
|---|---|---|---|
| OpenAI | `gpt-4o-mini` | Geração de respostas (user stories) | ~$1-3 |
| OpenAI | `gpt-4o` | Avaliação das métricas | ~$2-5 |
| Google Gemini | `gemini-2.5-flash` | Geração e avaliação (alternativa gratuita) | Gratuito* |

*Sujeito a limites: 15 requisições/minuto e 1.500 requisições/dia.

**Custo total estimado com OpenAI:** $1 a $5 para completar o desafio.

### 11.4 Plataformas Externas

| Plataforma | Finalidade | Autenticação |
|---|---|---|
| LangSmith | Rastreamento, avaliação e Prompt Hub | `LANGCHAIN_API_KEY` |
| OpenAI API | Modelos gpt-4o-mini e gpt-4o | `OPENAI_API_KEY` |
| Google AI Studio | Modelo gemini-2.5-flash | `GOOGLE_API_KEY` |
| GitHub | Repositório público do projeto | Token GitHub |

### 11.5 Variáveis de Ambiente Necessárias

```bash
# LangSmith
LANGCHAIN_API_KEY=lsv2_...
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=desafio-prompt-engineer
LANGSMITH_HUB_API_KEY=lsv2_...

# OpenAI (opcional se usar Gemini)
OPENAI_API_KEY=sk-...

# Google Gemini (opcional se usar OpenAI)
GOOGLE_API_KEY=AIza...

# Configuração do provedor padrão
LLM_PROVIDER=openai  # ou gemini

# Identificação do usuário no LangSmith Hub
LANGSMITH_USERNAME=seu_usuario
```

---

## 12. Restrições e Premissas

### 12.1 Restrições Técnicas

**R-01** - O projeto deve utilizar obrigatoriamente Python 3.9 ou superior. Versões anteriores não são suportadas.

**R-02** - O framework LangChain é obrigatório para integração com o LangSmith Hub. Implementações diretas via API REST do LangSmith não atendem ao requisito.

**R-03** - O formato de armazenamento dos prompts locais deve ser YAML. Outros formatos (JSON, TOML) não são aceitos.

**R-04** - O provedor Google Gemini (`gemini-2.5-flash`) está sujeito ao limite de 15 requisições por minuto e 1.500 requisições por dia. O sistema deve implementar controle de rate limit para não exceder esses limites.

**R-05** - O prompt otimizado deve aplicar ao menos duas técnicas de Prompt Engineering reconhecidas. A aplicação de apenas uma técnica não atende ao critério mínimo do desafio.

**R-06** - Todas as quatro métricas de avaliação devem atingir 0.9 individualmente. Compensar uma métrica baixa com outras altas não é suficiente para aprovação.

### 12.2 Premissas

**P-01** - O desenvolvedor possui acesso a uma conta ativa no LangSmith com permissão para criar e publicar prompts no Prompt Hub.

**P-02** - O prompt `leonanluppi/bug_to_user_story_v1` está disponível e acessível publicamente no LangSmith Prompt Hub no momento da execução.

**P-03** - O desenvolvedor possui ao menos uma das seguintes credenciais válidas: chave de API da OpenAI com créditos disponíveis, ou chave de API do Google AI Studio (Gemini).

**P-04** - O ambiente de desenvolvimento possui acesso à internet para comunicação com as APIs do LangSmith, OpenAI e Google.

**P-05** - O repositório base do desafio está disponível para fork no GitHub.

**P-06** - O processo de otimização é iterativo por natureza. Estima-se que entre 3 e 5 ciclos de refinamento sejam necessários para atingir aprovação em todas as métricas.

**P-07** - Os arquivos `src/metrics.py`, `src/dataset.py` e `src/utils.py` já estão parcialmente implementados no repositório base e servem como ponto de partida. O desenvolvedor deve completar e integrar esses módulos conforme necessário.

**P-08** - O custo financeiro total para completar o desafio utilizando OpenAI é estimado em $1 a $5 USD. O desenvolvedor deve ter créditos suficientes disponíveis antes de iniciar as avaliações.

---

*Documento elaborado com base na especificação do desafio "Pull, Otimização e Avaliação de Prompts com LangChain e LangSmith" - MBA em Inteligência Artificial.*
