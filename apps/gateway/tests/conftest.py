import os
import sys

# Ensure the gateway's 'app' package is found first by inserting its
# parent directory at the beginning of sys.path.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
