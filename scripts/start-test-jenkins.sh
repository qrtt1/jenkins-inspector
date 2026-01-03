#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( dirname "$SCRIPT_DIR" )"
FIXTURES_DIR="$PROJECT_ROOT/tests/fixtures"

IMAGE_NAME="jenkins-inspector:test"
CONTAINER_NAME="jenkee-qa-jenkins"
PORT=${1:-8081}

echo "Building Jenkins image: $IMAGE_NAME..."
docker build -t "$IMAGE_NAME" "$FIXTURES_DIR"

# Stop and remove existing container if it exists
if [ "$(docker ps -aq -f name=$CONTAINER_NAME)" ]; then
    echo "Stopping and removing existing container: $CONTAINER_NAME..."
    docker stop "$CONTAINER_NAME" > /dev/null
    docker rm "$CONTAINER_NAME" > /dev/null
fi

echo "Starting Jenkins container: $CONTAINER_NAME on port $PORT..."
docker run -d \
    --name "$CONTAINER_NAME" \
    -p "$PORT:8080" \
    -v "$FIXTURES_DIR:/usr/share/jenkins/ref/init.groovy.d:ro" \
    "$IMAGE_NAME"

echo "----------------------------------------------------------"
echo "Jenkins is starting up..."
echo "URL: http://localhost:$PORT"
echo "Username: jenkins-test"
echo "Password: test-password-for-jenkins-inspector"
echo "API Token: 1100000000000000000000000000000000"
echo "----------------------------------------------------------"
echo "Pre-configured Resources:"
echo "Jobs: test-job-1, test-job-2, test-job-3, long-running-job"
echo "Views: test-view (contains job 1 & 2), empty-view"
echo "Credentials: test-credential-1 (user/pass), test-credential-2 (secret text)"
echo "----------------------------------------------------------"
echo ""
echo "You can follow the logs with: docker logs -f $CONTAINER_NAME"
echo "Wait for 'Jenkins is fully up and running' message before logging in."
echo ""
echo "To stop the container: docker stop $CONTAINER_NAME"
