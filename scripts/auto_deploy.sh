#!/usr/bin/env bash

# Directorio del repositorio
REPO_DIR="/home/admin-server/servidor-hybridge"
LOG_FILE="$REPO_DIR/logs/auto-deploy.log"

# Asegurar que el directorio de logs exista
mkdir -p "$REPO_DIR/logs"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

cd "$REPO_DIR" || exit 1

# Traer últimos cambios de origin/main
git fetch origin main > /dev/null 2>&1

LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" != "$REMOTE" ]; then
    log "Se detectaron nuevos commits en el repositorio (Local: ${LOCAL:0:7} -> Remoto: ${REMOTE:0:7}). Desplegando cambios..."
    
    if git pull origin main >> "$LOG_FILE" 2>&1; then
        log "Git pull exitoso. Reconstruyendo e iniciando contenedor Docker..."
        
        if docker compose up -d --build >> "$LOG_FILE" 2>&1; then
            log "¡Despliegue automático completado con éxito!"
            docker image prune -f > /dev/null 2>&1
        else
            log "ERROR: Falló 'docker compose up -d --build'."
        fi
    else
        log "ERROR: Falló 'git pull origin main'."
    fi
fi
