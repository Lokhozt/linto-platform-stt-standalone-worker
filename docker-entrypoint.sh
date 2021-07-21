#!/bin/bash
set -e

echo "RUNNING service"

supervisord -c supervisor/supervisor.conf
if [[ ! -z "$SERVICE_BROKER" ]]
then
    supervisorctl -c supervisor/supervisor.conf start transcribe_worker
fi

supervisorctl -c supervisor/supervisor.conf tail -f ingress stderr