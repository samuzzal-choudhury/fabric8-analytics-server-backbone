#!/usr/bin/bash

# Start API backbone service with time out
gunicorn --pythonpath /src/ -b 0.0.0.0:$API_BACKBONE_SERVICE_PORT -t $API_BACKBONE_SERVICE_TIMEOUT -k gevent -w $NUMBER_WORKER_PROCESS rest_api:app