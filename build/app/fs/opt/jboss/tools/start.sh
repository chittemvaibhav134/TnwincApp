#!/bin/bash

###################################
# JDBC Ping External Ip Discovery #
###################################

BONUS_PROPS=''

if [[ -n ${DISCOVER_IP:-} ]]; then
    case "$DISCOVER_IP" in
        aws)
            CONTAINER_IP=`curl http://169.254.170.2/v2/metadata/ | grep -oP '(10\\.\\d+\\.\\d+\\.\\d+)' | head -n1`
            ;;
        local)
            CONTAINER_IP=$(cat /etc/hosts | grep `hostname` | cut -f1)
            ;;
        *)
            CONTAINER_IP="127.0.0.1"
    esac
    echo "Setting container.ip system property to $CONTAINER_IP"
    BONUS_PROPS+=" -Dcontainer.ip=$CONTAINER_IP"
fi

exec /opt/jboss/tools/docker-entrypoint.sh $@ $BONUS_PROPS