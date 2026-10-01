#!/usr/bin/env bash

# Gera os arquivos técnicos do dbt e monta a página visual do projeto.
set -euo pipefail

RAIZ_PROJETO="$(cd "$(dirname "$0")/.." && pwd)"
PASTA_DBT="$RAIZ_PROJETO/readly_dbt"
PASTA_SITE="$PASTA_DBT/site"
PASTA_TARGET="$PASTA_DBT/target"

cd "$RAIZ_PROJETO"

# Exporta as variáveis necessárias para o profiles.yml do dbt.
set -a
source .env
set +a

# Cria manifest.json, catalog.json e a documentação técnica original.
"$RAIZ_PROJETO/.venv/bin/dbt" docs generate \
  --project-dir "$PASTA_DBT" \
  --profiles-dir "$PASTA_DBT"

# Preserva a interface técnica original do dbt em outro endereço.
cp "$PASTA_TARGET/index.html" "$PASTA_TARGET/dbt-docs.html"

# Coloca a página visual como entrada principal da documentação.
cp "$PASTA_SITE/index.html" "$PASTA_TARGET/index.html"
cp "$PASTA_SITE/styles.css" "$PASTA_TARGET/styles.css"
cp "$PASTA_SITE/app.js" "$PASTA_TARGET/app.js"

# Consulta os marts e grava os números no JSON lido pela página.
"$RAIZ_PROJETO/.venv/bin/python" "$RAIZ_PROJETO/scripts/exportar_metricas.py"

# Escreve as respostas às 23 perguntas (no JSON e em docs/respostas_perguntas.md).
"$RAIZ_PROJETO/.venv/bin/python" "$RAIZ_PROJETO/scripts/escrever_respostas.py"

echo "Documentação criada em: $PASTA_TARGET/index.html"
