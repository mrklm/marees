#!/usr/bin/env bash
set -euo pipefail

# ------------------------------------------------------------
# Build macOS pour marees.py -> .app -> .dmg + .sha256
# ------------------------------------------------------------

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_PY="${ROOT_DIR}/marees.py"
VENV_DIR="${ROOT_DIR}/.venv"
RELEASES_DIR="${ROOT_DIR}/releases"

APP_NAME="marees"                 # nom du binaire / bundle
VOL_NAME="Marees"                 # nom du volume DMG (affiché au montage)
ICON_ICNS="${ROOT_DIR}/assets/Marees.icns"

if [[ ! -f "${APP_PY}" ]]; then
  echo "Erreur: marees.py introuvable: ${APP_PY}"
  exit 1
fi

if [[ ! -f "${ICON_ICNS}" ]]; then
  echo "Erreur: icône .icns introuvable: ${ICON_ICNS}"
  echo "Attendu: assets/Marees.icns"
  exit 1
fi

if ! command -v hdiutil >/dev/null 2>&1; then
  echo "Erreur: hdiutil introuvable. Ce script doit être lancé sur macOS."
  exit 1
fi

mkdir -p "${RELEASES_DIR}"

echo "==> Création/activation du venv..."
if [[ ! -d "${VENV_DIR}" ]]; then
  python3 -m venv "${VENV_DIR}"
fi

# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

echo "==> Mise à jour pip + installation PyInstaller..."
python -m pip install --upgrade pip
python -m pip install --upgrade pyinstaller

echo "==> Lecture de la version depuis marees.py..."
VERSION="$(python -c 'import importlib.util, pathlib; p=pathlib.Path("marees.py").resolve(); s=importlib.util.spec_from_file_location("marees", str(p)); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); print(getattr(m, "__VERSION__", "0.0.0"))')"

DMG_NAME="${APP_NAME}-${VERSION}-macos.dmg"
DMG_PATH="${RELEASES_DIR}/${DMG_NAME}"

echo "==> Nettoyage build/dist/spec..."
rm -rf "${ROOT_DIR}/build" "${ROOT_DIR}/dist"
rm -f  "${ROOT_DIR}"/*.spec

echo "==> Build PyInstaller (.app, windowed)..."
# Important:
# - pas de --onefile pour obtenir un .app
# - --windowed produit un bundle app macOS
python -m PyInstaller \
  --noconfirm \
  --clean \
  --onedir \
  --windowed \
  --name "${APP_NAME}" \
  --icon "${ICON_ICNS}" \
  "${APP_PY}"

APP_BUNDLE="${ROOT_DIR}/dist/${APP_NAME}.app"
if [[ ! -d "${APP_BUNDLE}" ]]; then
  echo "Erreur: bundle .app attendu introuvable: ${APP_BUNDLE}"
  exit 1
fi

echo "==> Création du DMG..."
# Dossier de staging (contiendra l'app + lien Applications)
STAGE_DIR="$(mktemp -d)"
cleanup() {
  rm -rf "${STAGE_DIR}" || true
}
trap cleanup EXIT

# Copie de l'app dans le stage
cp -R "${APP_BUNDLE}" "${STAGE_DIR}/"

# Lien /Applications (pratique dans un DMG)
ln -s /Applications "${STAGE_DIR}/Applications"

# Supprimer l'ancien dmg si présent
rm -f "${DMG_PATH}"

# Créer le dmg (compressé)
hdiutil create \
  -volname "${VOL_NAME} ${VERSION}" \
  -srcfolder "${STAGE_DIR}" \
  -ov \
  -format UDZO \
  "${DMG_PATH}" >/dev/null

if [[ ! -f "${DMG_PATH}" ]]; then
  echo "Erreur: DMG non créé: ${DMG_PATH}"
  exit 1
fi

echo "==> SHA256 du DMG..."
if command -v shasum >/dev/null 2>&1; then
  (cd "${RELEASES_DIR}" && shasum -a 256 "${DMG_NAME}" > "${DMG_NAME}.sha256")
else
  (cd "${RELEASES_DIR}" && openssl dgst -sha256 "${DMG_NAME}" > "${DMG_NAME}.sha256")
fi

echo "==> Nettoyage post-build..."
rm -rf "${ROOT_DIR}/build" "${ROOT_DIR}/dist"
rm -f  "${ROOT_DIR}"/*.spec

echo "==> OK"
echo "DMG    : ${DMG_PATH}"
echo "SHA256 : ${DMG_PATH}.sha256"