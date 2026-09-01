import os
import sys

# Ensure the agent-worker's 'app' package is found first by inserting its
# parent directory at the beginning of sys.path. This is necessary because
# the root pyproject.toml pythonpath also includes apps/gateway, which has
# its own 'app' package, causing a namespace collision during test collection.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
