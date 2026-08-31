#!/bin/bash
# Validates the docker-compose configuration
echo "Validating docker compose config..."
docker compose -f infra/compose/docker-compose.yml config > /dev/null
if [ $? -eq 0 ]; then
    echo "Docker compose configuration is valid."
    exit 0
else
    echo "Docker compose configuration is invalid!"
    exit 1
fi
