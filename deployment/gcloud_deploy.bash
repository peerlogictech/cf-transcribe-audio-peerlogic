#!/bin/bash
set -x #echo on

# 1. gcloud init
# 2. run as ./deployment/gcloud_deploy.bash from the root of cf-transcribe-audio repo

PROJECT_ID=$(gcloud config list --format='value(core.project)')
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
LOCAL_DEVELOPMENT_SERVICE_ACCOUNT="local-development@${PROJECT_ID}.iam.gserviceaccount.com"
CLOUDBUILD_SERVICE_ACCOUNT="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"
VAULT_ID="wlmpasbyyncmhpjji3lfc7ra4a"
REGION=$(gcloud config list --format='value(compute.region)')
ZONE=$(gcloud config list --format='value(compute.zone)')

textred=$(tput setaf 1) # Red
textgreen=$(tput setaf 2) # Green
textylw=$(tput setaf 3) # Yellow
textblue=$(tput setaf 4) # Blue
textpurple=$(tput setaf 5) # Purple
textcyn=$(tput setaf 6) # Cyan
textwht=$(tput setaf 7) # White
textreset=$(tput sgr0) # Text reset.


# TODO: check project name before continuing to avoid fat-fingering
# and deploying to the wrong environment

ENV_FILE="./deployment/${PROJECT_ID}.env"




if [ -f $ENV_FILE ];
then
  echo "${textgreen}loading env file $ENV_FILE ${textreset}"
  source $ENV_FILE
fi



gcloud components update


echo "${textgreen}Enabling services ${textreset}"
# see which service to enable: gcloud services list --available
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable speech.googleapis.com




echo "${textgreen}Adding Cloudbuild roles${textreset}"
gcloud projects add-iam-policy-binding $PROJECT_ID \
      --member="serviceAccount:${CLOUDBUILD_SERVICE_ACCOUNT}" \
      --role="roles/cloudfunctions.developer"

echo "${textgreen}Adding Local Development roles${textreset}"
gcloud projects add-iam-policy-binding $PROJECT_ID \
      --member="serviceAccount:${LOCAL_DEVELOPMENT_SERVICE_ACCOUNT}" \
      --role="roles/speech.client"

echo "${textgreen}Adding cf-transcribe-audio-env Secret${textreset}"
gcloud secrets create cf-transcribe-audio-env --data-file=$ENV_FILE


if  [[ "$PROJECT_ID" ==  *"dev" ]]; then
      echo "${textgreen}Creating cloud build trigger using development branch${textreset}"
      gcloud beta builds triggers create github \
      --name="cf-transcribe-audio-dev" \
      --repo-name="cf-transcribe-audio" \
      --repo-owner=peerlogictech \
      --branch-pattern="^development$" \
      --build-config="deployment/cloudbuild.yaml"
fi

if [[ "$PROJECT_ID" ==  *"stage" ]]; then
      echo "${textgreen}Creating cloud build trigger using hotfix/ branch prefix${textreset}"
      gcloud beta builds triggers create github \
      --name="cf-transcribe-audio-hotfixes" \
      --repo-name=cf-transcribe-audio \
      --repo-owner=peerlogictech \
      --branch-pattern="^hotfix/.*$" \
      --build-config="deployment/cloudbuild.yaml"

      echo "${textgreen}Creating cloud build trigger using tags${textreset}"
      gcloud beta builds triggers create github \
      --name="cf-transcribe-audio-releases" \
      --repo-name=cf-transcribe-audio \
      --repo-owner=peerlogictech \
      --tag-pattern="^.*$" \
      --build-config="deployment/cloudbuild.yaml"
fi

if [[ "$PROJECT_ID" ==  *"prod" ]]; then
      echo "${textgreen}Creating cloud build trigger using main branch${textreset}"
      gcloud beta builds triggers create github \
      --name="cf-transcribe-audio-prod" \
      --repo-name=cf-transcribe-audio \
      --repo-owner=peerlogictech \
      --branch-pattern="^main$" \
      --build-config="deployment/cloudbuild.yaml"
fi
