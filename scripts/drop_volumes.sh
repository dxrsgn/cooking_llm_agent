#!/bin/bash

# drop volumes except redis
docker compose down
docker volume rm cooking_llm_agent_postgres_data

