#! /bin/bash

# Usage: PROJECT_ID=peerlogic-api-dev ./deployment/deploy-pubsub.sh
# Dependency:
#   - ./deployment/peerlogic-api-dev.env (secret)
#   - ./src/requirements.txt

ENV_FILE="./deployment/${PROJECT_ID}.env"

if [ -f $ENV_FILE ];
then
  echo "${textgreen}loading env file $ENV_FILE ${textreset}"
  source $ENV_FILE  # necessary for other facets of deployment below
  ENV_VARS_STRING=$(grep -o '^[^#]*$' $ENV_FILE)
  ENV_VARS_STRING=$(echo $ENV_VARS_STRING | tr -s '[:blank:]' ',')
fi

gcloud functions \
  deploy ${FUNCTION_NAME_PUBSUB} \
  --source="./src" \
  --runtime=python39 \
  --trigger-topic="${PUBSUB_TOPIC}" \
  --set-env-vars="${ENV_VARS_STRING}"
