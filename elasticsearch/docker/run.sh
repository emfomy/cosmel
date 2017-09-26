#!/bin/bash

ES_CONTAINER_NAME="pix_es"
ES_DOCKER_NAME=elasticsearch
ES_DOCKER_VERSION=5.5
ES_PORT_1=9200
ES_PORT_2=9300

KIBANA_CONTAINER_NAME="pix_kibana"
KIBANA_PORT=5601
KIBANA_DOCKER_NAME=kibana
KIBANA_DOCKER_VERSION=5.5

function start_es() {
    echo "Starting ElasticSearch Container..."

    if [ ! -z "$(docker ps -f name=${ES_CONTAINER_NAME} -f status=running -q)" ]; then
        echo "${ES_CONTAINER_NAME} already running."
    elif [ ! -z "$(docker ps -f name=${ES_CONTAINER_NAME} -f status=exited -q)" ]; then
        docker start ${ES_CONTAINER_NAME}
    else
        docker run -d -p ${ES_PORT_1}:${ES_PORT_1} -p ${ES_PORT_2}:${ES_PORT_2} --name ${ES_CONTAINER_NAME} ${ES_DOCKER_NAME}:${ES_DOCKER_VERSION}
    fi
}

function start_kibana() {
    echo "Starting Kibana Container..."

    if [ ! -z "$(docker ps -f name=${KIBANA_CONTAINER_NAME} -f status=running -q)" ]; then
        echo "${KIBANA_CONTAINER_NAME} already running."
    elif [ ! -z "$(docker ps -f name=${KIBANA_CONTAINER_NAME} -f status=exited -q)" ]; then
        docker start ${KIBANA_CONTAINER_NAME}
    else
        ES_HOST=$(docker exec ${ES_CONTAINER_NAME} ip addr show | grep inet | grep eth0 | awk '{print $2}' | awk -F '/' '{print $1}')
        echo "ElasticSearch Container Host: ${ES_HOST}"
        docker run --link ${ES_CONTAINER_NAME} -d -e ELASTICSEARCH_URL=http://${ES_HOST}:${ES_PORT_1} -p ${KIBANA_PORT}:${KIBANA_PORT} --name ${KIBANA_CONTAINER_NAME} ${KIBANA_DOCKER_NAME}:${KIBANA_DOCKER_VERSION}
    fi
}

function stop_es() {
    echo "Stopping ElasticSearch Container..."

    if [ ! -z "$(docker ps -f name=${ES_CONTAINER_NAME} -f status=running -q)" ]; then
        docker stop ${ES_CONTAINER_NAME}
    fi
}

function stop_kibana() {
    echo "Stopping Kibana Container..."
    if [ ! -z "$(docker ps -f name=${KIBANA_CONTAINER_NAME} -f status=running -q)" ]; then
        docker stop ${KIBANA_CONTAINER_NAME}
    fi
}

function clear_containers() {
    docker rm ${ES_CONTAINER_NAME}
    docker rm ${KIBANA_CONTAINER_NAME}
}

function usage() {
    echo "[run.sh]
    Start/Stop Elasticsearch and Kibana Containers.
    Usage: `basename $0` {arg}
    --start   Start Elasticsearch and Kibana Containers.
    --restart Restart Elasticsearch and Kibana Containers.
    --stop    Stop Elasticsearch and Kibana Containers.
    --clear   Stop and remove all containers.
    -h, --help
    "
}

if [ ! -n "$1" ];then
    usage
    exit 1
fi

while [ "$1" != "" ]; do
    case "$1" in
        --start)
            start_es
            sleep 3
            start_kibana
            ;;
        --restart)
            stop_es
            stop_kibana
            start_es
            sleep 3
            start_kibana
            ;;
        --stop)
            stop_es
            stop_kibana
            ;;
        --clear)
            stop_es
            stop_kibana
            clear_containers
            ;;
        *)
            usage
            exit 1
            ;;
        esac
    shift
done
