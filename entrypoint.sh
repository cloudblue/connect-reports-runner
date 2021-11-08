#!/bin/bash

if [[ "$@" == *"cextrun"* ]]; then

    if [[ -z "${REPOSITORY_URL}" ]]; then
      echo "Environment variable REPOSITORY_URL not set"
      exit 1
    fi

    if [[ -z "${COMMIT_ID}" ]]; then
      echo "Environment variable COMMIT_ID not set"
      exit 1
    fi

    EXTENSION_DIR=${EXTENSION_DIR:-'/reports/reports'}
    git clone ${REPOSITORY_URL} ${EXTENSION_DIR}
    if [[ $? -ne 0 ]]; then
        echo "Error cloning repository"
        exit 1
    fi
    cd $EXTENSION_DIR && git checkout -b report_run ${COMMIT_ID}
    if [[ $? -ne 0 ]]; then
        echo "Error switching to commit"
        exit 1
    fi
fi

exec "$@"