#!/bin/sh
BASEDIR=$(dirname "$0")

swagger-cli bundle -o ${BASEDIR}/build/openapi.yaml -t yaml ${BASEDIR}/openapi.yaml
