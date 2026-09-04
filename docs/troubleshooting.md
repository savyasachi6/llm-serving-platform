# Troubleshooting Guide

This guide covers common issues you might encounter when running the application locally via Docker Compose or in a Kubernetes cluster.

## 1. Docker Compose: Container Exits Immediately

**Symptom**: `docker compose up` starts containers, but one or more immediately exit with code `1` or `137`.

**Likely Causes**:
- **OOM (Out of Memory)** (Code 137): The container exceeded its memory limits. This is common if the vLLM engines try to allocate more VRAM/RAM than available.
- **Configuration Error** (Code 1): A missing environment variable, incorrect startup flag, or missing dependency.

**Diagnostic Commands**:
```bash
docker compose ps
docker compose logs <failing-service-name>
```

**Remediation**:
- Verify you have a `.env` file present and populated based on `.env.example`.
- Ensure your machine has sufficient RAM and VRAM. If running locally with vLLM, ensure `kvcached` is healthy.
- If Redis exited, ensure the `/data` volume doesn't have corrupted files or permissions issues (run `docker compose down -v` to reset data).

## 2. Docker Compose: `depends_on` Healthcheck Failures

**Symptom**: Services like `gateway` or `vllm-responder` are stuck in "Waiting" or fail to start because a dependency is unhealthy.

**Likely Causes**:
- The `kvcached` daemon is not creating the `/tmp/kvcached-ipc/kvcached.sock` socket.
- Redis is failing to boot.
- The vLLM engines are taking too long to load weights, causing the healthcheck to timeout.

**Diagnostic Commands**:
```bash
# Check the health status of a specific container
docker inspect --format='{{json .State.Health}}' <container-id> | jq
```

**Remediation**:
- View the logs of the dependency (e.g., `docker compose logs -f kvcached`).
- If the vLLM model download is slow on your network, you may need to temporarily increase the `start_period` in the `healthcheck` section of the `docker-compose.yml` for the vLLM services.

## 3. Kubernetes: Pod Stuck in `Pending`

**Symptom**: `kubectl get pods` shows a pod in the `Pending` state indefinitely.

**Likely Causes**:
- Insufficient CPU or Memory available on the cluster nodes.
- Insufficient GPU resources available (`nvidia.com/gpu`).
- No nodes match the `nodeSelector` or `tolerations` (if configured).
- PVC (PersistentVolumeClaim) cannot be provisioned.

**Diagnostic Commands**:
```bash
kubectl describe pod <pod-name>
```
*Look at the "Events" section at the bottom of the output.*

**Remediation**:
- Add more nodes to the cluster.
- Ensure the NVIDIA Device Plugin is installed and running on the GPU nodes.
- Check the StorageClass for the PVC using `kubectl get pvc`.

## 4. Kubernetes: Pod Stuck in `CrashLoopBackOff`

**Symptom**: `kubectl get pods` shows a pod in `CrashLoopBackOff`.

**Likely Causes**:
- The application is crashing on startup due to a fatal error (e.g., invalid configuration, missing secret).
- The `livenessProbe` is consistently failing, causing Kubernetes to kill and restart the pod.
- `kvcached` IPC socket is unavailable to the `vllm` engines.

**Diagnostic Commands**:
```bash
# Check the logs of the previous crashed instance
kubectl logs <pod-name> --previous

# Check the events to see if probes are failing
kubectl describe pod <pod-name>
```

**Remediation**:
- If it's a configuration issue, fix the ConfigMap/Secret and rollout a restart.
- For `vllm` pods, ensure the `kvcached` DaemonSet is running on the node (`kubectl get pods -l app=kvcached -o wide`) and that the `hostPath` volumes are correctly mounted.

## 5. Kubernetes: Pod Stuck in `ImagePullBackOff`

**Symptom**: Pod fails to start with `ErrImagePull` or `ImagePullBackOff`.

**Likely Causes**:
- The image name or tag is misspelled in the manifest.
- The image is in a private registry and Kubernetes lacks the `imagePullSecrets`.
- The node cannot reach the internet to pull the image.

**Diagnostic Commands**:
```bash
kubectl describe pod <pod-name>
```
*Look for authentication errors or repository not found errors in the Events.*

**Remediation**:
- Verify the image tag exists.
- Ensure `imagePullSecrets` are configured correctly for the service account or pod spec.

## 6. Traffic Routing: 502/504 Bad Gateway / Gateway Timeout

**Symptom**: Requests to the `gateway` ingress return HTTP 502 or 504.

**Likely Causes**:
- The `gateway` pods are not running or their readiness probes are failing, so the Ingress/Service has no endpoints to route to.
- The `gateway` is timing out when talking to the `vllm` engines or `agent-worker`.

**Diagnostic Commands**:
```bash
# Verify the Service has endpoints
kubectl get endpoints gateway

# Check ingress status
kubectl describe ingress gateway-ingress

# Check gateway logs for upstream connection errors
kubectl logs deployment/gateway -f
```

**Remediation**:
- Ensure all downstream pods (`vllm-responder`, `vllm-agents`, `agent-worker`) have successfully passed their readiness probes.
- Check if upstream requests are taking longer than the gateway's HTTP client timeouts (e.g., `httpx` timeouts). Adjust timeouts if necessary.

## 7. Data Loss After Restart

**Symptom**: Redis data or model weights are re-downloaded/lost after a pod restart or `docker compose down`.

**Likely Causes**:
- Using ephemeral storage instead of persistent volumes.
- Running `docker compose down -v` which explicitly removes volumes.

**Remediation**:
- In Docker Compose, omit the `-v` flag to retain volumes.
- In Kubernetes, ensure StatefulSets or Deployments are using PersistentVolumeClaims rather than `emptyDir`.
