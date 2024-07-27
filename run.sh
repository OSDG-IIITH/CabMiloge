#!/bin/bash

if [[ $CAB_DIR == "" ]]; then
    CAB_DIR=.
fi

docker-compose -f $CAB_DIR/docker-compose.yml -p cas up --build
