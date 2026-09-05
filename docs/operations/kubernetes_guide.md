# Kubernetes Deployment Guide

This guide covers deploying the LLM Serving Platform both locally and to Google Cloud Platform (GCP).

## 1. Local Kubernetes Testing (Docker Desktop)

Testing Kubernetes manifests locally ensures your configuration works before touching expensive cloud resources. Docker Desktop provides a built-in Kubernetes cluster.

### Prerequisites
1. Open Docker Desktop settings.
2. Navigate to the **Kubernetes** tab and check "Enable Kubernetes".
3. Wait for the cluster to start. Verify with:
   ```bash
   kubectl cluster-info
   ```

### 1.1 Docker Desktop (Single Node - Quick Test)
If you just want to verify the manifests apply successfully without advanced networking:

```bash
# Apply the Kustomize overlay
kubectl apply -k infra/kubernetes/overlays/local

# Verify pods are running
kubectl get pods

# To test the Gateway locally, use port-forwarding:
kubectl port-forward svc/gateway 8000:80
```

### 1.2 KIND (Multi-Node & Local Ingress - Advanced Learning)
If you want to simulate a production environment (with 2 nodes and a real Ingress load balancer) for learning:

1. **Create the 2-Node Cluster:** We use a custom configuration that maps port 80 to your computer so we can use Ingress.
   ```bash
   kind create cluster --config infra/kubernetes/kind/kind-config.yaml
   ```

2. **Install the NGINX Ingress Controller:** This simulates the cloud load balancer.
   ```bash
   kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
   ```

3. **Deploy the GCP Overlay Locally:** We can actually deploy the production `gcp` overlay here because NGINX will pick up the Ingress resource!
   ```bash
   kubectl apply -k infra/kubernetes/overlays/gcp
   ```

4. **Test the Ingress:** Once the gateway pods and ingress-nginx pods are running, you can hit localhost on port 80 directly, and NGINX will route it to your 2-node cluster!
   ```bash
   curl http://localhost/health
   ```

### 1.3 Heterogeneous Multi-Model Deployments & GPU Time-Slicing
By default, Kubernetes locks a GPU to a single Pod. If you attempt to run two vLLM models (e.g. `vllm-responder` and `vllm-agents`) on a machine with a single GPU, the second pod will hang in `Pending` forever.

To solve this locally, we use **NVIDIA GPU Time-Slicing**. This configuration tricks the Kubernetes NVIDIA device plugin into advertising a single physical GPU as multiple "Virtual GPUs" (e.g., 4 GPUs). 

**How to enable Time-Slicing locally:**
```bash
# Apply the time-slicing ConfigMap
kubectl apply -f infra/kubernetes/kind/gpu-time-slicing.yaml

# Patch the NVIDIA device plugin DaemonSet to use the ConfigMap
kubectl patch daemonset nvidia-device-plugin-daemonset -n kube-system --type='json' -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args", "value": ["--config-file=/etc/kubernetes/nvidia-config/any"]}]'
```

*Note: Since the 12GB of VRAM is shared between multiple pods, the Kubernetes base manifests (`infra/kubernetes/base/`) deploy the lightweight Qwen model family: `vllm-responder` uses `Qwen/Qwen2.5-1.5B-Instruct` with `--gpu-memory-utilization 0.38` (~4.6GB), and `vllm-agents` uses `Qwen/Qwen2.5-0.5B-Instruct` with `--gpu-memory-utilization 0.22` (~2.7GB). This sums to 60% VRAM, providing a stable 40% buffer against OOM errors.*

### 1.4 Multi-LoRA Dynamic Hot-Swapping
To maximize cost-efficiency, the throughput node (`vllm-agents`) is configured to host multiple LoRA adapters simultaneously on top of `Qwen/Qwen2.5-0.5B-Instruct`. 
By passing `--enable-lora` and `--lora-modules` in the Kubernetes deployment, vLLM dynamically registers the adapters (`reasoning-lora` for classification and `reflection-lora` for PII redaction). 
When the Gateway or Agent Worker forwards a request, it specifies the desired adapter in the `model` payload (e.g. `model="reasoning-lora"`), and vLLM dynamically applies the adapter delta weights in milliseconds.

## 2. Deploying to Google Cloud Platform (GKE)

The `gcp` overlay includes configurations specifically designed for Google Kubernetes Engine (GKE), including an Ingress controller and safe-to-evict annotations for the Cluster Autoscaler.

### Prerequisites
1. Create a GKE cluster with autoscaling enabled.
2. Reserve a static IP address in GCP named `gateway-ip` for the Ingress.
3. Push your Docker images to Google Container Registry (GCR) or Artifact Registry.

### Deploying the GCP Overlay

```bash
# Update the image references in your kustomization (optional, via kustomize edit)
# kustomize edit set image gateway=gcr.io/your-project/gateway:latest

# Apply the GCP overlay
kubectl apply -k infra/kubernetes/overlays/gcp

# Monitor the Ingress allocation
kubectl get ingress gateway-ingress --watch
```

### Autoscaling
The base configuration includes a Horizontal Pod Autoscaler (HPA) for the Gateway, which will scale the FastAPI pods from 3 to 20 based on 75% CPU utilization. 

Scaling vLLM GPU nodes requires KEDA or GCP Cluster Autoscaler monitoring the vLLM HTTP queue depth, which should be configured at the cluster level.
