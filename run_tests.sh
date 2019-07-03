#!/bin/bash

echo "#########################################################"
echo "Stopping the istance if there is (This might take a few seconds)"
echo "#########################################################"
docker stop checktime-test-env
docker rm checktime-test-env

echo "#########################################################"
echo "Build the container"
echo "#########################################################"
docker build --file Dockerfile -t checktime-test-env .

echo "#########################################################"
echo "Run the container"
echo "#########################################################"
docker run -it checktime-test-env 