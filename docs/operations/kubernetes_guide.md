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

### Deploying the Local Overlay
The `local` overlay uses NodePorts instead of expensive cloud LoadBalancers, allowing you to access the gateway directly on `localhost`.

```bash
# Apply the Kustomize overlay
kubectl apply -k infra/kubernetes/overlays/local

# Verify pods are running
kubectl get pods

# To test the Gateway locally, the most reliable method across all cluster types (1-node or 2-node) is port-forwarding:
kubectl port-forward svc/gateway 8000:80

# In a separate terminal, test the endpoint:
curl http://localhost:8000/health
```

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
