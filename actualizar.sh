#!/bin/bash

set -u

REPO="$HOME/git/running_page"
DOWNLOAD_SCRIPT="$HOME/git/python-garminconnect/descargar_todo.py"
VENV="$REPO/.venv/bin/activate"
LOG_DIR="$REPO/logs"
LOG_FILE="$LOG_DIR/update.log"


mkdir -p "$LOG_DIR"

exec >> "$LOG_FILE" 2>&1

echo
echo "=========================================="
echo "$(date '+%Y-%m-%d %H:%M:%S')"
echo "Actualización running_page"
echo "=========================================="

cd "$REPO" || exit 1

# Evitar ejecuciones simultáneas
exec 9>"$REPO/.update.lock"

if ! flock -n 9; then
    echo "Ya hay otra actualización ejecutándose."
    exit 0
fi

if [ ! -f "$VENV" ]; then
    echo "ERROR: no existe el entorno virtual:"
    echo "$VENV"
    exit 1
fi

if [ ! -f "$DOWNLOAD_SCRIPT" ]; then
    echo "ERROR: no existe:"
    echo "$DOWNLOAD_SCRIPT"
    exit 1
fi

source "$VENV"

echo
echo "1. Descargando actividades desde Garmin..."
echo

START_DATE=$(date -d "1 days ago" +%Y-%m-%d)
END_DATE=$(date +%Y-%m-%d)

echo "Desde: $START_DATE"
echo "Hasta: $END_DATE"

python "$DOWNLOAD_SCRIPT" \
    --start "$START_DATE" \
    --end "$END_DATE"

if [ $? -ne 0 ]; then
    echo "ERROR descargando actividades Garmin."
    exit 1
fi

echo
echo "2. Sincronizando GPX con running_page..."
echo

python run_page/gpx_sync.py

if [ $? -ne 0 ]; then
    echo "ERROR ejecutando gpx_sync.py."
    exit 1
fi

echo
echo "3. Estado Git:"
git status --short

git add src/static/activities.json

if git diff --cached --quiet; then
    echo
    echo "No hay cambios en activities.json."
    echo "No se hace commit ni push."
    exit 0
fi

echo
echo "4. Cambios detectados. Creando commit..."

git commit -m "Update Garmin activities"

if [ $? -ne 0 ]; then
    echo "ERROR haciendo commit."
    exit 1
fi

echo
echo "5. Subiendo cambios a GitHub..."

git push origin main

if [ $? -ne 0 ]; then
    echo "ERROR haciendo git push."
    exit 1
fi

echo
echo "=========================================="
echo "$(date '+%Y-%m-%d %H:%M:%S')"
echo "Actualización completada correctamente."
echo "=========================================="


mv GPX_OUT/* ~/garmin_export/gpx/
mv FIT_OUT/* ~/garmin_export/fit/

