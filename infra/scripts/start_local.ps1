# PowerShell script to start the local stack
Write-Host "Starting local LLM Serving stack..."
docker compose -f infra/compose/docker-compose.yml --profile local up -d --build
Write-Host "Stack started in background. Use docker compose logs to view output."
