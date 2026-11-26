#!/bin/bash
# One-shot Jellyfin Desktop setup for ROG Ally (CachyOS deckify / SteamOS-style game mode).
# Run as your normal user (NOT with sudo); it asks for the password only for the
# system-wide flatpak install.
#
#   1. installs org.jellyfin.JellyfinDesktop from Flathub (system scope)
#   2. installs the jellyfin-ally launcher + Ally button map
#      (launcher re-applies the input permission and button map on every start)
#   3. adds/updates the "Jellyfin Desktop" non-Steam shortcut to use the launcher
#      (Steam is restarted for this; skip with --no-steam)
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")"

APP=org.jellyfin.JellyfinDesktop
BIN="$HOME/.local/bin/jellyfin-ally"
SHARE="$HOME/.local/share/jellyfin-ally"
DO_STEAM=1
[[ "${1:-}" == "--no-steam" ]] && DO_STEAM=0

if [[ $EUID -eq 0 ]]; then
    echo "sudo 없이 일반 사용자로 실행하세요 (설치 단계에서만 비밀번호를 물어봅니다)." >&2
    exit 1
fi

echo "== 1/3 Jellyfin Desktop 설치 (Flathub, 시스템 범위)"
if flatpak info --system "$APP" >/dev/null 2>&1; then
    echo "이미 설치돼 있음"
else
    sudo flatpak install --system -y flathub "$APP"
fi

echo "== 2/3 실행기와 Ally 버튼 배치 설치"
install -Dm755 jellyfin-ally "$BIN"
install -Dm644 rog-ally-steam-pad.json "$SHARE/rog-ally-steam-pad.json"
flatpak override --user --device=input "$APP" 2>/dev/null || flatpak override --user --device=all "$APP"
echo "실행기: $BIN"

if [[ $DO_STEAM -eq 0 ]]; then
    echo "== 3/3 Steam 바로가기 건너뜀 (--no-steam)"
    echo "Steam에 비-Steam 게임으로 추가할 때 대상(Target)을 \"$BIN\" 로 지정하세요."
    exit 0
fi

echo "== 3/3 Steam 바로가기 등록 (Steam이 잠깐 꺼졌다 켜집니다)"
restart=""
if systemctl --user is-active --quiet steam-launcher.service; then
    systemctl --user stop steam-launcher.service
    restart=unit
elif pgrep -x steam >/dev/null || pgrep -f 'steamrt64/steam ' >/dev/null; then
    steam -shutdown >/dev/null 2>&1 || true
    restart=desktop
fi
for _ in $(seq 60); do
    pgrep -f 'steamrt64/steam ' >/dev/null || pgrep -x steam >/dev/null || break
    sleep 1
done
sleep 2

python3 -I steam_shortcut.py "$BIN"

case "$restart" in
    unit) systemctl --user start steam-launcher.service ;;
    desktop) (setsid steam >/dev/null 2>&1 &) ;;
esac
echo "완료. 게임 모드 라이브러리의 비-Steam 탭에서 Jellyfin Desktop을 실행하세요."
