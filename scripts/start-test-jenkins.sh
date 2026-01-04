#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( dirname "$SCRIPT_DIR" )"
FIXTURES_DIR="$PROJECT_ROOT/tests/fixtures"

IMAGE_NAME="jenkins-inspector:test"
CONTAINER_NAME="jenkee-qa-jenkins"
PORT=8081
DELETE_EXISTING=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --port)
            PORT="$2"
            shift 2
            ;;
        --delete-existing-container)
            DELETE_EXISTING=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--port <port>] [--delete-existing-container]"
            echo "  --port <port>: Specify the port to expose Jenkins (default: 8081)"
            echo "  --delete-existing-container: Delete existing container if it exists"
            exit 1
            ;;
    esac
done

# Function to print connection info
print_connection_info() {
    echo "----------------------------------------------------------"
    echo "Jenkins Connection Information"
    echo "----------------------------------------------------------"
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
}

# Check if container already exists
if [ "$(docker ps -aq -f name=$CONTAINER_NAME)" ]; then
    if [ "$DELETE_EXISTING" = false ]; then
        echo "=========================================="
        echo "WARNING: Existing container detected"
        echo "=========================================="
        echo "Container name: $CONTAINER_NAME"

        # Check if it's running
        if [ "$(docker ps -q -f name=$CONTAINER_NAME)" ]; then
            echo "Status: RUNNING"
        else
            echo "Status: STOPPED"
        fi

        echo ""
        echo "This container may contain a carefully configured test baseline"
        echo "that you or another team member has set up."
        echo ""
        echo "⚠️  IMPORTANT FOR AI AGENTS:"
        echo "    Please confirm with the user before proceeding."
        echo "    The user may have spent significant time building"
        echo "    this test environment with specific configurations."
        echo ""
        echo "To delete the existing container and start fresh, run:"
        echo "  $0 --delete-existing-container"
        echo ""
        print_connection_info
        echo ""
        echo "You can follow the logs with: docker logs -f $CONTAINER_NAME"
        echo ""
        exit 1
    else
        echo "Deleting existing container: $CONTAINER_NAME..."
        if [ "$(docker ps -q -f name=$CONTAINER_NAME)" ]; then
            docker stop "$CONTAINER_NAME" > /dev/null
        fi
        docker rm "$CONTAINER_NAME" > /dev/null
        echo "Existing container deleted."
    fi
fi

echo "Building Jenkins image: $IMAGE_NAME..."
docker build -t "$IMAGE_NAME" "$FIXTURES_DIR"

echo "Starting Jenkins container: $CONTAINER_NAME on port $PORT..."
docker run -d \
    --name "$CONTAINER_NAME" \
    -p "$PORT:8080" \
    -v "$FIXTURES_DIR:/usr/share/jenkins/ref/init.groovy.d:ro" \
    "$IMAGE_NAME"

echo ""
echo "Jenkins is starting up..."
print_connection_info
echo ""
echo "You can follow the logs with: docker logs -f $CONTAINER_NAME"
echo "Wait for 'Jenkins is fully up and running' message before logging in."
echo ""
echo "To stop the container: docker stop $CONTAINER_NAME"
