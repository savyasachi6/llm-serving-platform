# Script to automate the creation of the 2-node KIND cluster and NGINX Ingress
Write-Host "🚀 Starting Module 2: Local Kubernetes Orchestration" -ForegroundColor Cyan

# 0. Check for Kind CLI
$kind_cmd = "kind"
if (-not (Get-Command "kind" -ErrorAction SilentlyContinue)) {
    Write-Host "`n[0/3] 'kind' CLI not found. Downloading kind.exe locally..." -ForegroundColor Yellow
    Invoke-WebRequest -Uri "https://kind.sigs.k8s.io/dl/v0.24.0/kind-windows-amd64" -OutFile kind.exe
    $kind_cmd = ".\kind.exe"
}

# 1. Create the Cluster
Write-Host "`n[1/3] Creating 2-node kind cluster..." -ForegroundColor Yellow
& $kind_cmd create cluster --config infra/kubernetes/kind/kind-config.yaml

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to create kind cluster. Is Docker running?" -ForegroundColor Red
    exit 1
}

# 2. Install NGINX Ingress Controller
Write-Host "`n[2/3] Installing NGINX Ingress Controller..." -ForegroundColor Yellow
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

Write-Host "⏳ Waiting for Ingress Controller to be ready (this may take a minute)..." -ForegroundColor Yellow
kubectl wait --namespace ingress-nginx `
  --for=condition=ready pod `
  --selector=app.kubernetes.io/component=controller `
  --timeout=90s

# 3. Deploy the Platform
Write-Host "`n[3/3] Deploying the LLM Serving Platform (GCP Overlay)..." -ForegroundColor Yellow
kubectl apply -k infra/kubernetes/overlays/gcp

Write-Host "`n✅ Success! The cluster is running." -ForegroundColor Green
Write-Host "You can monitor the pods starting up by running: kubectl get pods -w" -ForegroundColor Gray
Write-Host "Once running, test the ingress by visiting: http://localhost/health" -ForegroundColor Gray
