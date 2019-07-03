#!/bin/bash
if [[ $1 == "build" ]]; then
  docker build --tag heikomat/teufel-mqtt-remote .
elif [[ $1 == "run" ]]; then
  docker run --rm --name teufel-mqtt-remote heikomat/teufel-mqtt-remote
elif [[ $1 == "push" ]]; then
  docker push heikomat/teufel-mqtt-remote:latest
else
  echo "Unknown command '$1'"
fi
