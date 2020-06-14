#!/bin/bash

until nc -z ${RABBIT_HOST} ${RABBIT_PORT}; do
    echo nc -z ${RABBIT_HOST} ${RABBIT_PORT}
    echo "waiting for rabbit mq..."
    sleep 1
done

until nc -z ${REDIS_HOST} ${REDIS_PORT}; do
    echo nc -z ${REDIS_HOST} ${REDIS_PORT}
    echo "waiting for redis..."
    sleep 1
done

echo "Quote service started."
nameko run --config config.yml quotes
echo "Quote service stopped."