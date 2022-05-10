#! /bin/bash

ROOT="$( pwd )"

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

SOURCE_FILE="src/main.py"

source "${ROOT}/.env"

functions-framework \
  --source=${SOURCE_FILE} \
  --target=${FUNCTION_NAME_PUBSUB} \
  --signature-type=event \
  --port=${FUNCTION_PORT_PUBSUB} \
  --debug
