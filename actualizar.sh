#!/bin/bash
set -Eeuo pipefail

REPO="$HOME/git/running_page"
PAGE_PYTHON="$REPO/.venv/bin/python"
SYNC_SCRIPT="$REPO/run_page/strava_sync.py"
CREDENTIALS_FILE="$HOME/.config/strava/credentials.json"

LOG_DIR="$REPO/logs"
LOG_FILE="$LOG_DIR/update.log"

mkdir -p "$LOG_DIR"
exec >> "$LOG_FILE" 2>&1

echo
echo "=========================================="
echo "$(date '+%Y-%m-%d %H:%M:%S')"
echo "Actualización running_page - Strava"
echo "=========================================="

cd "$REPO"

# Evitar ejecuciones simultáneas
exec 9>"$REPO/.update.lock"
flock -n 9 || {
    echo "Ya hay otra actualización ejecutándose."
    exit 0
}

# Comprobar dependencias
for FILE in "$SYNC_SCRIPT" "$CREDENTIALS_FILE"; do
    [[ -f "$FILE" ]] || {
        echo "ERROR: no existe $FILE"
        exit 1
    }
done

[[ -x "$PAGE_PYTHON" ]] || {
    echo "ERROR: no existe el Python $PAGE_PYTHON"
    exit 1
}

[[ "$(stat -c '%a' "$CREDENTIALS_FILE")" == "600" ]] || {
    echo "ERROR: las credenciales no tienen permisos 600."
    exit 1
}

# 1. Sincronizar actividades desde Strava
echo
echo "1. Sincronizando actividades desde Strava"

"$PAGE_PYTHON" "$SYNC_SCRIPT" \
    --credentials-file "$CREDENTIALS_FILE"

# 2. Publicar JSON si ha cambiado
echo
echo "2. Comprobando cambios en activities.json"

git add src/static/activities.json

if git diff --cached --quiet -- src/static/activities.json; then
    echo "No hay cambios en activities.json."
else
    echo "Hay cambios. Creando commit..."

    git commit -m "Update Strava activities" -- src/static/activities.json

    echo "Subiendo cambios a GitHub..."
    git push origin main

    echo "Push completado. GitHub Actions podrá desplegar la web."
fi

echo
echo "=========================================="
echo "$(date '+%Y-%m-%d %H:%M:%S')"
echo "Actualización completada correctamente."
echo "=========================================="
