#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( dirname "$SCRIPT_DIR" )"

IMAGE_NAME="jenkins-inspector:test"
CONTAINER_NAME="jenkee-qa-jenkins"
REMOVE_IMAGE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --remove-image)
            REMOVE_IMAGE=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--remove-image]"
            echo "  --remove-image: Also remove the Docker image after stopping the container"
            exit 1
            ;;
    esac
done

# Check if container exists
if [ ! "$(docker ps -aq -f name=$CONTAINER_NAME)" ]; then
    echo "Container $CONTAINER_NAME does not exist."
    exit 0
fi

# Stop container if running
if [ "$(docker ps -q -f name=$CONTAINER_NAME)" ]; then
    echo "Stopping container: $CONTAINER_NAME..."
    docker stop "$CONTAINER_NAME"
else
    echo "Container $CONTAINER_NAME is already stopped."
fi

# Remove container
echo "Removing container: $CONTAINER_NAME..."
docker rm "$CONTAINER_NAME"

# Remove image if requested
if [ "$REMOVE_IMAGE" = true ]; then
    if [ "$(docker images -q $IMAGE_NAME)" ]; then
        echo "Removing image: $IMAGE_NAME..."
        docker rmi "$IMAGE_NAME"
    else
        echo "Image $IMAGE_NAME does not exist."
    fi
fi

echo "----------------------------------------------------------"
echo "Jenkins test environment stopped."
echo "----------------------------------------------------------"
