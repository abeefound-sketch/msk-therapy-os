SLUG="msk-therapy-os-m3-roadmap"
STAGE_DIR="/tmp/${SLUG}"
rm -rf "${STAGE_DIR}"
mkdir -p "${STAGE_DIR}"

# Copy core source files excluding pycache
mkdir -p "${STAGE_DIR}/msk_therapy_os"
rsync -av --exclude '__pycache__' --exclude '*.pyc' msk_therapy_os/ "${STAGE_DIR}/msk_therapy_os/"

# Copy tests excluding pycache
mkdir -p "${STAGE_DIR}/tests"
rsync -av --exclude '__pycache__' --exclude '*.pyc' tests/ "${STAGE_DIR}/tests/"

# Copy key documentation
mkdir -p "${STAGE_DIR}/docs"
rsync -av docs/ "${STAGE_DIR}/docs/"

# Copy root specs
cp SPEC.md "${STAGE_DIR}/"
cp README.md "${STAGE_DIR}/"
cp ENGINEERING_HANDOFF.md "${STAGE_DIR}/"

# Create zip
cd /tmp
rm -f "${SLUG}-source.zip"
zip -r "${SLUG}-source.zip" "${SLUG}" > /dev/null

ls -lh "/tmp/${SLUG}-source.zip"

# Copy to user desktops
DEST_WIN="/mnt/c/Users/tuanh/Desktop"
DEST_LINUX="/home/tuan/Desktop"

mkdir -p "${DEST_WIN}" 2>/dev/null || true
mkdir -p "${DEST_LINUX}" 2>/dev/null || true

cp "/tmp/${SLUG}-source.zip" "${DEST_WIN}/${SLUG}-source.zip"
cp "/tmp/${SLUG}-source.zip" "${DEST_LINUX}/${SLUG}-source.zip"

ls -lh "${DEST_WIN}/${SLUG}-source.zip"
