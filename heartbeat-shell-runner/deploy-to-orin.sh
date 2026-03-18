#!/usr/bin/env bash
# Deploy Heartbeat shell-runner add-on to the Orin and rebuild the heartbeat container.
# Requires: sshpass (brew install sshpass), or use SSH keys for dog@100.68.165.28
set -e
ORIN="dog@100.68.165.28"
HEARTBEAT_DIR="/home/dog/heartbeat"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Deploying shell-runner add-on to Orin ==="
echo "Target: $ORIN"
echo ""

# 1. Copy add-on files into heartbeat on Orin
echo "1. Copying add-on files to $ORIN:$HEARTBEAT_DIR ..."
if command -v sshpass &>/dev/null; then
  sshpass -p 'r00t' scp -o StrictHostKeyChecking=no \
    "$SCRIPT_DIR/shell_routes.py" \
    "$SCRIPT_DIR/shell_runner_section.html" \
    "$SCRIPT_DIR/merge_shell_runner.py" \
    "$ORIN:$HEARTBEAT_DIR/"
else
  echo "Using ssh (install sshpass for password auth: brew install sshpass)"
  scp -o StrictHostKeyChecking=no \
    "$SCRIPT_DIR/shell_routes.py" \
    "$SCRIPT_DIR/shell_runner_section.html" \
    "$SCRIPT_DIR/merge_shell_runner.py" \
    "$ORIN:$HEARTBEAT_DIR/"
fi

# 2. Run merge on Orin
echo "2. Merging into app.py and index.html on Orin ..."
if command -v sshpass &>/dev/null; then
  sshpass -p 'r00t' ssh -o StrictHostKeyChecking=no "$ORIN" "cd $HEARTBEAT_DIR && python3 merge_shell_runner.py"
else
  ssh -o StrictHostKeyChecking=no "$ORIN" "cd $HEARTBEAT_DIR && python3 merge_shell_runner.py"
fi

# 3. Rebuild and redeploy heartbeat container
echo "3. Rebuilding and redeploying heartbeat container ..."
if command -v sshpass &>/dev/null; then
  sshpass -p 'r00t' ssh -o StrictHostKeyChecking=no "$ORIN" "cd $HEARTBEAT_DIR && \
    docker build -t heartbeat . && \
    docker stop heartbeat 2>/dev/null || true && \
    docker rm heartbeat 2>/dev/null || true && \
    docker run -d --name heartbeat --restart unless-stopped --privileged \
      -v /proc:/host/proc:ro -v /sys:/host/sys:ro -v /var/run/docker.sock:/var/run/docker.sock \
      -p 8888:8888 heartbeat"
else
  ssh -o StrictHostKeyChecking=no "$ORIN" "cd $HEARTBEAT_DIR && \
    docker build -t heartbeat . && \
    docker stop heartbeat 2>/dev/null || true && \
    docker rm heartbeat 2>/dev/null || true && \
    docker run -d --name heartbeat --restart unless-stopped --privileged \
      -v /proc:/host/proc:ro -v /sys:/host/sys:ro -v /var/run/docker.sock:/var/run/docker.sock \
      -p 8888:8888 heartbeat"
fi

echo ""
echo "=== Done. Heartbeat with shell-runner at http://100.68.165.28:8888 ==="
