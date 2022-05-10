#! /bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

source "${DIR}/.env"

gcloud pubsub topics \
  create ${PUBSUB_TOPIC}
