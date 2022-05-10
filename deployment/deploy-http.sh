#! /bin/bash

ENV_FILE="./deployment/${PROJECT_ID}.env"

if [ -f $ENV_FILE ];
then
  echo "${textgreen}loading env file $ENV_FILE ${textreset}"
  source $ENV_FILE
fi


gcloud functions \
  deploy ${FUNCTION_NAME_HTTP} \
  --source="./src" \
  --runtime=python39 \
  --trigger-http \
  --allow-unauthenticated
