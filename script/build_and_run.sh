#!/usr/bin/env bash
set -euo pipefail

APP_NAME="Tremotino"
PRODUCT="Tremotino"
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DIST_DIR="$ROOT_DIR/dist"
APP_DIR="$DIST_DIR/$APP_NAME.app"
EXECUTABLE="$APP_DIR/Contents/MacOS/$APP_NAME"
BUILD_VERSION="$(git -C "$ROOT_DIR" rev-parse --short HEAD 2>/dev/null || date +%Y%m%d%H%M%S)"

cd "$ROOT_DIR"

if pgrep -x "$APP_NAME" >/dev/null 2>&1; then
  pkill -x "$APP_NAME" || true
fi

swift build

rm -rf "$APP_DIR"
mkdir -p "$APP_DIR/Contents/MacOS" "$APP_DIR/Contents/Resources"
cp ".build/debug/$PRODUCT" "$EXECUTABLE"
chmod +x "$EXECUTABLE"

if [[ -f "$ROOT_DIR/Resources/Tremotino.icns" ]]; then
  cp "$ROOT_DIR/Resources/Tremotino.icns" "$APP_DIR/Contents/Resources/Tremotino.icns"
fi

cat > "$APP_DIR/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleExecutable</key>
  <string>$APP_NAME</string>
  <key>CFBundleIdentifier</key>
  <string>local.tremotino.app</string>
  <key>CFBundleIconFile</key>
  <string>Tremotino</string>
  <key>CFBundleName</key>
  <string>Tremotino</string>
  <key>CFBundleShortVersionString</key>
  <string>0.1</string>
  <key>CFBundleVersion</key>
  <string>$BUILD_VERSION</string>
  <key>CFBundlePackageType</key>
  <string>APPL</string>
  <key>LSMinimumSystemVersion</key>
  <string>14.0</string>
  <key>NSPrincipalClass</key>
  <string>NSApplication</string>
</dict>
</plist>
PLIST

if [[ "${1:-}" == "--verify" ]]; then
  /usr/bin/open -n "$APP_DIR"
  sleep 2
  pgrep -x "$APP_NAME" >/dev/null
  echo "$APP_NAME launched"
elif [[ "${1:-}" == "--logs" ]]; then
  /usr/bin/open -n "$APP_DIR"
  /usr/bin/log stream --style compact --predicate "process == '$APP_NAME'"
else
  /usr/bin/open -n "$APP_DIR"
fi
