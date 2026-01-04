#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( dirname "$SCRIPT_DIR" )"

IMAGE_NAME="jenkins-inspector:test"
CONTAINER_NAME="jenkee-qa-jenkins"
DELETE_CONTAINER=false
REMOVE_IMAGE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --delete-container)
            DELETE_CONTAINER=true
            shift
            ;;
        --remove-image)
            REMOVE_IMAGE=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--delete-container] [--remove-image]"
            echo "  --delete-container: Delete the container after stopping (requires confirmation)"
            echo "  --remove-image: Also remove the Docker image (implies --delete-container)"
            exit 1
            ;;
    esac
done

# If --remove-image is specified, also delete container
if [ "$REMOVE_IMAGE" = true ]; then
    DELETE_CONTAINER=true
fi

# Check if container exists
if [ ! "$(docker ps -aq -f name=$CONTAINER_NAME)" ]; then
    echo "Container $CONTAINER_NAME does not exist."
    exit 0
fi

# Stop container if running
if [ "$(docker ps -q -f name=$CONTAINER_NAME)" ]; then
    echo "Stopping container: $CONTAINER_NAME..."
    docker stop "$CONTAINER_NAME"
    echo "Container stopped successfully."
else
    echo "Container $CONTAINER_NAME is already stopped."
fi

# Handle container deletion
if [ "$DELETE_CONTAINER" = true ]; then
    echo ""
    echo "=========================================="
    echo "WARNING: About to delete container"
    echo "=========================================="
    echo "Container name: $CONTAINER_NAME"
    echo ""
    echo "This container may contain a carefully configured test baseline"
    echo "that you or another team member has set up."
    echo ""
    echo "⚠️  IMPORTANT FOR AI AGENTS:"
    echo "    Please confirm with the user before proceeding."
    echo "    The user may have spent significant time building"
    echo "    this test environment with specific configurations."
    echo ""
    echo "Deleting container: $CONTAINER_NAME..."
    docker rm "$CONTAINER_NAME"
    echo "Container deleted."

    # Remove image if requested
    if [ "$REMOVE_IMAGE" = true ]; then
        if [ "$(docker images -q $IMAGE_NAME)" ]; then
            echo "Removing image: $IMAGE_NAME..."
            docker rmi "$IMAGE_NAME"
            echo "Image removed."
        else
            echo "Image $IMAGE_NAME does not exist."
        fi
    fi
else
    echo ""
    echo "=========================================="
    echo "Container preserved"
    echo "=========================================="
    echo "The container has been stopped but NOT deleted."
    echo "You can restart it later with:"
    echo "  docker start $CONTAINER_NAME"
    echo ""
    echo "To delete the container, run:"
    echo "  $0 --delete-container"
    echo ""
    echo "To delete both container and image, run:"
    echo "  $0 --remove-image"
    echo "=========================================="
fi

echo ""
echo "Jenkins test environment stopped."
