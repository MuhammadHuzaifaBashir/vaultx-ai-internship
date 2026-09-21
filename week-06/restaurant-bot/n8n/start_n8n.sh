#!/bin/bash
# Start n8n on Podman for SpiceRoute Restaurant
podman run -d \
  --name n8n-boutique \
  -p 5678:5678 \
  -v n8n-data:/home/node/.n8n \
  -e N8N_HOST=0.0.0.0 \
  -e N8N_PORT=5678 \
  -e GENERIC_TIMEZONE=Asia/Karachi \
  -e TZ=Asia/Karachi \
  -e N8N_ENCRYPTION_KEY=boutique-ai-2026 \
  -e N8N_DIAGNOSTICS_ENABLED=false \
  docker.io/n8nio/n8n:latest
echo "n8n started on port 5678"
