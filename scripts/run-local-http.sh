#! /bin/bash

ROOT="$( pwd )"

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

SOURCE_FILE="src/main.py"

source "${ROOT}/.env"

functions-framework \
  --source=${SOURCE_FILE} \
  --target=${FUNCTION_NAME_HTTP} \
  --signature-type=http \
  --port=${FUNCTION_PORT_HTTP} \
  --debug
