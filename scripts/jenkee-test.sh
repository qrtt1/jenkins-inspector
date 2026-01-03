#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( dirname "$SCRIPT_DIR" )"
ENV_FILE="$PROJECT_ROOT/.env.test"

# Load environment variables from .env.test if it exists
if [ -f "$ENV_FILE" ]; then
    # Load values from file, but we won't overwrite already set environment variables
    set -a
    source "$ENV_FILE"
    set +a
fi

# Set default values if not already defined (prioritizes existing environment variables)
export JENKINS_URL="${JENKINS_URL:-http://localhost:8081/}"
export JENKINS_USER_ID="${JENKINS_USER_ID:-jenkins-test}"
export JENKINS_API_TOKEN="${JENKINS_API_TOKEN:-1100000000000000000000000000000000}"

# Check if QA mode is enabled
CONFIG_DIR="$HOME/.jenkins-inspector"
if [ -d "$CONFIG_DIR" ]; then
    echo "Error: Production config directory exists at: $CONFIG_DIR" >&2
    echo "" >&2
    echo "This script is intended for QA testing only." >&2
    echo "Please enable QA mode first to hide production config:" >&2
    echo "" >&2
    echo "  jenkee dev-qa --enable" >&2
    echo "" >&2
    echo "After QA testing, restore production config with:" >&2
    echo "  jenkee dev-qa --disable" >&2
    echo "" >&2
    exit 1
fi

echo "# [QA Tooling] Running via wrapper: $(realpath "$0")"
echo "# [QA Tooling] JENKINS_URL: $JENKINS_URL"
echo "# [QA Tooling] (Note: Official commands will not display [QA Tooling] messages)"
echo ""

# Execute jenkee with all arguments passed to this script
# Use 'python3 -m jenkins_tools.cli' or 'jenkee' if installed in venv
if [ -d "$PROJECT_ROOT/venv" ]; then
    source "$PROJECT_ROOT/venv/bin/activate"
    jenkee "$@"
else
    # Fallback to python module execution if venv not active/present
    python3 -m jenkins_tools.cli "$@"
fi
