#!/usr/bin/env bash
# =============================================================================
# demo-up.sh — Puesta en marcha con un solo comando.
#
# Levanta el server COMBINADO (API FastAPI + UI Flet montada en el mismo
# puerto, app/server.py) y un Cloudflare Quick Tunnel frente a ese puerto.
# Imprime el link https://...trycloudflare.com para abrir desde el celular
# desde cualquier lugar (no necesita estar en la misma Wi-Fi).
#
# Uso:
#   ./demo-up.sh          Arranca todo y muestra el link vigente.
#   ./demo-up.sh stop     Detiene el server y el túnel.
#
# Nota: el Quick Tunnel genera una URL ALEATORIA en cada arranque. Si la
# sesión se cae o querés un link fresco, volvé a correr ./demo-up.sh —
# el link viejo deja de existir y aparece uno nuevo.
#
# Logs: var/demo-server.log y var/cloudflared.log (gitignored).
# =============================================================================
set -euo pipefail

cd "$(dirname "$0")"

PORT="${DEMO_PORT:-8080}"
BASE_URL="http://127.0.0.1:${PORT}"
SERVER_LOG="var/demo-server.log"
TUNNEL_LOG="var/cloudflared.log"

stop_everything() {
  echo "==> Deteniendo túnel y server de demo (si estaban corriendo)"
  pkill -f "cloudflared tunnel --url ${BASE_URL}" 2>/dev/null || true
  pkill -f "uvicorn app.server:app" 2>/dev/null || true
  sleep 1
  echo "Listo. Para volver a levantar: ./demo-up.sh"
}

if [[ "${1:-}" == "stop" ]]; then
  stop_everything
  exit 0
fi

# --- 1. Limpieza de corridas anteriores -------------------------------------
stop_everything >/dev/null
echo "==> Server combinado (API + UI) en ${BASE_URL}"

# --- 2. Server combinado -----------------------------------------------------
mkdir -p var
nohup uv run uvicorn app.server:app --host 127.0.0.1 --port "${PORT}" \
  >"${SERVER_LOG}" 2>&1 &
SERVER_PID=$!

server_ready() { curl -sf -o /dev/null "${BASE_URL}/docs"; }

for _ in $(seq 1 120); do
  if server_ready; then
    break
  fi
  if ! kill -0 "${SERVER_PID}" 2>/dev/null; then
    echo "ERROR: el server murió al arrancar. Últimas líneas del log:"
    tail -20 "${SERVER_LOG}"
    exit 1
  fi
  sleep 0.5
done

if ! server_ready; then
  echo "ERROR: el server no respondió en ${BASE_URL}/docs en 60 s. Log: ${SERVER_LOG}"
  tail -20 "${SERVER_LOG}"
  exit 1
fi
echo "    OK — API y UI respondiendo en ${BASE_URL}"

# --- 3. Cloudflare Quick Tunnel ----------------------------------------------
if ! command -v cloudflared >/dev/null 2>&1; then
  echo "ERROR: cloudflared no está instalado. Instalalo y volvé a correr el script."
  exit 1
fi

: >"${TUNNEL_LOG}"
nohup cloudflared tunnel --url "${BASE_URL}" >"${TUNNEL_LOG}" 2>&1 &
echo "==> Túnel Cloudflare (URL nueva en cada arranque)"

TUNNEL_URL=""
for _ in $(seq 1 60); do
  TUNNEL_URL="$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "${TUNNEL_LOG}" | head -1 || true)"
  [[ -n "${TUNNEL_URL}" ]] && break
  sleep 0.5
done

echo
if [[ -n "${TUNNEL_URL}" ]]; then
  echo "=================================================="
  echo "  Link para el celular (válido hasta que se caiga"
  echo "  o hasta que corras de nuevo ./demo-up.sh):"
  echo
  echo "  ${TUNNEL_URL}"
  echo "=================================================="
  echo
  echo "Local:   ${BASE_URL}   Swagger: ${BASE_URL}/docs"
  echo "Logs:    ${SERVER_LOG} · ${TUNNEL_LOG}"
  echo "Parar:   ./demo-up.sh stop"
else
  echo "No pude extraer la URL del túnel. Mirá ${TUNNEL_LOG}"
  exit 1
fi
