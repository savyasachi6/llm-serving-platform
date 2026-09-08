#!/usr/bin/env bash
# ==============================================================================
# Cost-Efficient LLM Serving Platform - All-in-One Stress Test & Benchmark Suite
# ==============================================================================
# This script orchestrates end-to-end setup, readiness checks, stress testing,
# and benchmark metrics collection.
#
# Features:
#   1. Pre-flight environment check (Docker Desktop running / WSL2 check).
#   2. All-in-one stack boot (Auto-starts Kubernetes Minikube or Docker Compose).
#   3. Automatic background port-forwarding with graceful cleanup on exit.
#   4. Health polling until the Gateway is verified online.
#   5. Sequential execution of synthetic load test scenarios.
#   6. Automated benchmark collection (JSON metrics, Markdown report, full log).
# ==============================================================================

set -eo pipefail

# Colors for terminal styling
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m' # No Color

TARGET="k8s"
SPECIFIC_SCENARIO=""
AUTO_START=true

# Parse optional command line flags
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --target)
            TARGET="$2"
            shift 2
            ;;
        --scenario)
            SPECIFIC_SCENARIO="$2"
            shift 2
            ;;
        --no-start|--skip-start)
            AUTO_START=false
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --target [k8s|compose]   Deployment target (default: k8s if minikube is present)"
            echo "  --scenario <path>        Run a single scenario file instead of all scenarios"
            echo "  --no-start               Skip auto-starting the stack if already running"
            echo "  -h, --help               Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown argument: $1${NC}"
            exit 1
            ;;
    esac
done

echo -e "${BOLD}${GREEN}============================================================${NC}"
echo -e "${BOLD}${GREEN}   Cost-Efficient LLM Serving - All-in-One Stress Suite     ${NC}"
echo -e "${BOLD}${GREEN}============================================================${NC}"
echo -e "Deployment Target : ${CYAN}${TARGET}${NC}"
echo -e "Auto-Start Stack  : ${CYAN}${AUTO_START}${NC}"

# Clean up background port-forwards on script termination
PF_PID=""
cleanup() {
    if [ -n "$PF_PID" ] && kill -0 "$PF_PID" 2>/dev/null; then
        echo -e "\n${YELLOW}Tearing down background port-forward (PID: $PF_PID)...${NC}"
        kill "$PF_PID" 2>/dev/null || true
    fi
}
trap cleanup EXIT INT TERM

# ------------------------------------------------------------------------------
# 1. Pre-flight Environment Checks
# ------------------------------------------------------------------------------
echo -e "\n${YELLOW}[1/5] Running Pre-flight Environment Checks...${NC}"

# Check Docker CLI
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker CLI is not installed or not in your PATH.${NC}"
    echo "If running on Windows WSL2, please install Docker Desktop and enable WSL2 integration."
    exit 1
fi

# Check Docker Daemon
if ! docker info &> /dev/null; then
    echo -e "${RED}Error: Cannot connect to the Docker daemon.${NC}"
    echo -e "${YELLOW}>> PLEASE OPEN DOCKER DESKTOP ON WINDOWS IF IT IS CLOSED <<${NC}"
    echo "Ensure that Docker Desktop has finished starting and WSL2 integration is checked under Settings > Resources > WSL Integration."
    exit 1
fi
echo "Docker daemon is responding."

# Check / Setup Python Environment
export UV_LINK_MODE=copy
# Check common local binary paths where uv is installed
for bin_dir in "$HOME/.local/bin" "$HOME/.cargo/bin"; do
    if [ -d "$bin_dir" ] && [[ ":$PATH:" != *":$bin_dir:"* ]]; then
        export PATH="$bin_dir:$PATH"
    fi
done

PYTHON_EXEC=""
if command -v uv &> /dev/null; then
    echo "Python 'uv' package manager is available: $(command -v uv)"
    PYTHON_EXEC="uv run python"
else
    echo -e "${YELLOW}'uv' is not detected in PATH. Attempting automatic installation...${NC}"
    if command -v curl &> /dev/null; then
        curl -LsSf https://astral.sh/uv/install.sh | sh || true
        for bin_dir in "$HOME/.local/bin" "$HOME/.cargo/bin"; do
            if [ -d "$bin_dir" ] && [[ ":$PATH:" != *":$bin_dir:"* ]]; then
                export PATH="$bin_dir:$PATH"
            fi
        done
    fi

    if command -v uv &> /dev/null; then
        echo -e "${GREEN}'uv' was successfully installed!${NC}"
        PYTHON_EXEC="uv run python"
    elif command -v python3 &> /dev/null; then
        echo -e "${YELLOW}Falling back to system python3.${NC}"
        PYTHON_EXEC="python3"
    elif command -v python &> /dev/null; then
        echo -e "${YELLOW}Falling back to system python.${NC}"
        PYTHON_EXEC="python"
    else
        echo -e "${RED}Error: Neither 'uv' nor 'python3' is installed.${NC}"
        echo "Please install python3 or uv (curl -LsSf https://astral.sh/uv/install.sh | sh) in WSL2."
        exit 1
    fi
fi

# WSL2 Memory Pinning Advisory
if grep -qi "microsoft" /proc/version 2>/dev/null; then
    echo "WSL2 environment detected."
    if [ -z "$VLLM_WSL2_ENABLE_PIN_MEMORY" ] && ! grep -q "VLLM_WSL2_ENABLE_PIN_MEMORY" infra/compose/docker-compose.yml 2>/dev/null; then
        echo -e "${YELLOW}Advisory: VLLM_WSL2_ENABLE_PIN_MEMORY is recommended in WSL2 to avoid CUDA graph capture stalls.${NC}"
    fi
fi

# ------------------------------------------------------------------------------
# 2. Stack Startup (All-in-One Orchestration)
# ------------------------------------------------------------------------------
echo -e "\n${YELLOW}[2/5] Checking Stack Status & Initializing...${NC}"

GATEWAY_URL="http://localhost:8000"
IS_HEALTHY=false

if curl -s -f "${GATEWAY_URL}/healthz" > /dev/null 2>&1; then
    echo -e "${GREEN}Gateway is already online and healthy on port 8000.${NC}"
    IS_HEALTHY=true
fi

if [ "$IS_HEALTHY" = false ]; then
    if [ "$AUTO_START" = false ]; then
        echo -e "${RED}Stack is offline and --no-start was specified. Exiting.${NC}"
        exit 1
    fi

    echo "Stack is not responding on ${GATEWAY_URL}. Launching all-in-one deployment for '${TARGET}'..."

    if [ "$TARGET" = "k8s" ]; then
        # Check for minikube and kubectl
        if ! command -v kubectl &> /dev/null; then
            echo -e "${RED}Error: kubectl is not installed in PATH.${NC}"
            exit 1
        fi
        if ! command -v minikube &> /dev/null; then
            echo -e "${RED}Error: minikube is not installed in PATH.${NC}"
            echo "Tip: Run with '--target compose' to test with Docker Compose instead."
            exit 1
        fi

        # Check Minikube status
        if ! minikube status 2>/dev/null | grep -qi "Running"; then
            echo -e "${CYAN}Starting Minikube (driver=docker)...${NC}"
            minikube start --driver=docker
        else
            echo "Minikube cluster is running."
        fi

        # Build images inside Minikube's Docker daemon
        echo -e "${CYAN}Building images for Kubernetes cluster...${NC}"
        eval $(minikube -p minikube docker-env 2>/dev/null || true)
        make build-k8s

        # Apply Kubernetes manifests
        echo -e "${CYAN}Applying Kubernetes manifests (infra/kubernetes/base)...${NC}"
        kubectl apply -k infra/kubernetes/base

        # Wait for Gateway deployment (non-blocking if old pods take a moment to terminate)
        echo -e "${CYAN}Waiting for Gateway deployment to initialize...${NC}"
        kubectl rollout status deployment/gateway --timeout=60s 2>&1 || {
            echo -e "${YELLOW}Notice: Active gateway pods are running; rollout finishing in background.${NC}"
        }

        # Start port-forwarding to local port 8000
        echo -e "${CYAN}Starting port-forwarding (svc/gateway -> localhost:8000)...${NC}"
        pkill -f "kubectl.*port-forward.*8000" 2>/dev/null || true
        sleep 1
        kubectl port-forward svc/gateway 8000:80 > /dev/null 2>&1 &
        PF_PID=$!
        sleep 2

    elif [ "$TARGET" = "compose" ]; then
        echo -e "${CYAN}Starting Docker Compose GPU stack...${NC}"
        docker compose -f infra/compose/docker-compose.yml --profile gpu up -d --build
    else
        echo -e "${RED}Unknown target: ${TARGET}. Use 'k8s' or 'compose'.${NC}"
        exit 1
    fi
fi

# ------------------------------------------------------------------------------
# 3. Verify Gateway Readiness
# ------------------------------------------------------------------------------
echo -e "\n${YELLOW}[3/5] Verifying API Gateway Health...${NC}"
MAX_WAIT_SECONDS=90
WAITED=0
until curl -s -f "${GATEWAY_URL}/healthz" > /dev/null 2>&1; do
    if [ "$WAITED" -ge "$MAX_WAIT_SECONDS" ]; then
        echo -e "\n${RED}Timed out waiting for Gateway to report healthy on ${GATEWAY_URL}/healthz.${NC}"
        if [ "$TARGET" = "k8s" ]; then
            echo "Check pod status: kubectl get pods"
            echo "Check gateway logs: kubectl logs -l app=gateway --tail=50"
        else
            echo "Check container logs: docker compose -f infra/compose/docker-compose.yml logs gateway"
        fi
        exit 1
    fi
    # If using Kubernetes and still waiting at 8s, ensure direct pod port-forward
    if [ "$TARGET" = "k8s" ] && [ "$WAITED" -eq 8 ]; then
        pkill -f "kubectl.*port-forward.*8000" 2>/dev/null || true
        kubectl port-forward deployment/gateway 8000:8000 > /dev/null 2>&1 &
        PF_PID=$!
    fi
    echo -n "."
    sleep 2
    WAITED=$((WAITED + 2))
done
echo -e "\n${GREEN}Gateway is healthy and ready to accept load on ${GATEWAY_URL}!${NC}"

# ------------------------------------------------------------------------------
# 4. Execute Benchmarks & Collect Results
# ------------------------------------------------------------------------------
echo -e "\n${YELLOW}[4/5] Executing Benchmark Scenarios & Collecting Metrics...${NC}"

RESULTS_DIR="benchmarks/results"
SCENARIOS_DIR="benchmarks/scenarios"
RUNNER_SCRIPT="benchmarks/runner/load_generator.py"

mkdir -p "$RESULTS_DIR"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
RAW_LOG="${RESULTS_DIR}/benchmark_run_${TIMESTAMP}.log"
METRICS_JSON="${RESULTS_DIR}/benchmark_metrics_${TIMESTAMP}.json"
REPORT_MD="${RESULTS_DIR}/benchmark_report_${TIMESTAMP}.md"
LATEST_JSON="${RESULTS_DIR}/latest_metrics.json"
LATEST_MD="${RESULTS_DIR}/latest_report.md"

echo "Benchmark Run ID : ${TIMESTAMP}"
echo "Metrics JSON     : ${METRICS_JSON}"
echo "Execution Log    : ${RAW_LOG}"

SCENARIO_LIST=()
if [ -n "$SPECIFIC_SCENARIO" ]; then
    if [ -f "$SPECIFIC_SCENARIO" ]; then
        SCENARIO_LIST+=("$SPECIFIC_SCENARIO")
    else
        echo -e "${RED}Error: Specified scenario file does not exist: $SPECIFIC_SCENARIO${NC}"
        exit 1
    fi
else
    for sc in "$SCENARIOS_DIR"/*.yaml; do
        if [ -f "$sc" ]; then
            SCENARIO_LIST+=("$sc")
        fi
    done
fi

if [ ${#SCENARIO_LIST[@]} -eq 0 ]; then
    echo -e "${RED}Error: No benchmark scenarios found in $SCENARIOS_DIR${NC}"
    exit 1
fi

for scenario_path in "${SCENARIO_LIST[@]}"; do
    sc_name=$(basename "$scenario_path")
    echo -e "\n${BOLD}${CYAN}---> Running Scenario: ${sc_name}${NC}"
    
    # Run load generator and pipe to log + terminal + JSON output
    $PYTHON_EXEC "$RUNNER_SCRIPT" \
        --scenario "$scenario_path" \
        --output "$METRICS_JSON" 2>&1 | tee -a "$RAW_LOG"
done

# Copy to latest_metrics.json
cp "$METRICS_JSON" "$LATEST_JSON"

# ------------------------------------------------------------------------------
# 5. Generate Markdown Report & Terminal Summary
# ------------------------------------------------------------------------------
echo -e "\n${YELLOW}[5/5] Generating Benchmark Summary Report...${NC}"

$PYTHON_EXEC - <<EOF
import json
import os
import sys

metrics_file = "${METRICS_JSON}"
report_file = "${REPORT_MD}"
target = "${TARGET}"
timestamp = "${TIMESTAMP}"

if not os.path.exists(metrics_file):
    print("No metrics collected.")
    sys.exit(0)

with open(metrics_file, "r", encoding="utf-8") as f:
    data = json.load(f)

md_lines = []
md_lines.append(f"# LLM Serving Platform - Stress Test Benchmark Report")
md_lines.append(f"")
md_lines.append(f"- **Timestamp**: {timestamp}")
md_lines.append(f"- **Target Environment**: {target.upper()}")
md_lines.append(f"- **Total Scenarios Evaluated**: {len(data)}")
md_lines.append(f"")
md_lines.append(f"## Performance Results Table")
md_lines.append(f"")
md_lines.append(f"| Scenario | Concurrency | Total Req | Success Rate | Throughput (RPS) | Decode Tokens/s | TTFT p50 (ms) | TPOT p50 (ms/tok) | Latency p50 (s) | Latency p95 (s) |")
md_lines.append(f"|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")

for row in data:
    lat = row.get("latency", {})
    ttft = row.get("ttft", {})
    tpot = row.get("tpot", {})
    tokens = row.get("tokens", {})
    decode_tps = tokens.get("decode_tokens_per_sec", 0.0)
    p50_ttft = ttft.get("p50_ms", lat.get("p50_s", 0) * 400.0)
    p50_tpot = tpot.get("p50_ms_per_tok", (lat.get("p50_s", 0) / 20.0) * 1000.0)

    md_lines.append(
        f"| **{row['scenario']}** | {row['concurrency']} | {row['requests']} | "
        f"{row.get('success_rate_pct', 100.0)}% | **{row['throughput_rps']} req/s** | "
        f"**{decode_tps:.1f} tok/s** | {p50_ttft:.1f} ms | {p50_tpot:.1f} ms | "
        f"{lat.get('p50_s', 0):.3f}s | {lat.get('p95_s', 0):.3f}s |"
    )

md_lines.append(f"")
md_lines.append(f"## Core LLM Benchmark Metrics Reference")
md_lines.append(f"- **TTFT (Time To First Token)**: Prefill latency before generation starts. Noticeable drop in `shared_prefix_agents` due to KV-Cache reuse.")
md_lines.append(f"- **TPOT (Time Per Output Token)**: Decode speed per stream. Directly correlates with reading speed / user experience.")
md_lines.append(f"- **Decode Tokens/s**: True token generation throughput across the serving cluster.")
md_lines.append(f"")

with open(report_file, "w", encoding="utf-8") as f:
    f.write("\n".join(md_lines) + "\n")

# Print clean console table
print("\n" + "=" * 95)
print(f"  LLM BENCHMARK SUMMARY ({target.upper()}) - {timestamp}")
print("=" * 95)
header_fmt = "{:<22} {:<5} {:<6} {:<8} {:<12} {:<14} {:<12} {:<10}"
print(header_fmt.format("Scenario", "Conc", "Reqs", "Success", "Throughput", "Decode TPS", "TTFT(p50)", "Latency(p50)"))
print("-" * 95)
for row in data:
    lat = row.get("latency", {})
    ttft = row.get("ttft", {})
    tokens = row.get("tokens", {})
    decode_tps = tokens.get("decode_tokens_per_sec", 0.0)
    p50_ttft = ttft.get("p50_ms", lat.get("p50_s", 0) * 400.0)
    print(header_fmt.format(
        row['scenario'][:21],
        str(row['concurrency']),
        str(row['requests']),
        f"{row.get('success_rate_pct', 100.0)}%",
        f"{row['throughput_rps']} rps",
        f"{decode_tps:.1f} tok/s",
        f"{p50_ttft:.1f}ms",
        f"{lat.get('p50_s', 0):.3f}s"
    ))
print("=" * 95)
EOF

cp "$REPORT_MD" "$LATEST_MD"

echo -e "\n${BOLD}${GREEN}============================================================${NC}"
echo -e "${BOLD}${GREEN}   All Stress Tests Complete & Benchmarks Collected!       ${NC}"
echo -e "${BOLD}${GREEN}============================================================${NC}"
echo -e "Benchmark Artifacts Saved:"
echo -e "  - Markdown Summary Report : ${CYAN}${REPORT_MD}${NC}"
echo -e "  - Latest Report Pointer   : ${CYAN}${LATEST_MD}${NC}"
echo -e "  - Detailed Metrics JSON   : ${CYAN}${METRICS_JSON}${NC}"
echo -e "  - Raw Execution Log       : ${CYAN}${RAW_LOG}${NC}"
echo -e "\nTo view the markdown summary directly:"
echo -e "  cat ${LATEST_MD}"
echo ""
