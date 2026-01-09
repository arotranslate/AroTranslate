#/bin/bash

COMPOSE_FILE="${1:-docker-compose.yml}"

echo "Using ${COMPOSE_FILE}"

git pull && \
docker compose -f $COMPOSE_FILE pull && \
#docker compose -f $COMPOSE_FILE build && \
docker compose -f $COMPOSE_FILE up -d && \
echo "Done!"
#sleep 5
#&& \
#docker compose logs
