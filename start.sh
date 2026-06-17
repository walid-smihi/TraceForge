#!/bin/bash
# Démarre TraceForge + Ollama local
set -e

echo "→ Arrêt de l'ancien service Ollama systemd..."
sudo systemctl stop ollama 2>/dev/null || true

echo "→ Démarrage d'Ollama (host, toutes interfaces)..."
OLLAMA_HOST=0.0.0.0:11434 CUDA_VISIBLE_DEVICES="" ollama serve &
OLLAMA_PID=$!

echo "→ Attente démarrage Ollama..."
until curl -s http://localhost:11434/api/tags > /dev/null 2>&1; do sleep 1; done
echo "✓ Ollama prêt"

echo "→ Démarrage Docker Compose..."
docker compose up -d

echo ""
echo "✓ TraceForge disponible sur http://localhost:3000"
echo "  (Ollama PID: $OLLAMA_PID — Ctrl+C pour tout arrêter)"

# Garde le script actif, kill Ollama à la sortie
trap "kill $OLLAMA_PID 2>/dev/null; docker compose down" EXIT
wait $OLLAMA_PID
