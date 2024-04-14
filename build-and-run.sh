#!/bin/bash

# Build the Docker image
sudo docker build -t tapo-light-api .

# Run the Docker container
sudo docker run -d --name tapo-light-api-container --env-file .env -p 8080:8080 tapo-light-api
