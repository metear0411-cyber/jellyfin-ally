# jellyfin-ally

ROG Ally(CachyOS deckify 게임 모드)에 Jellyfin Desktop을 한 번에 설치하는 스크립트.

```bash
./install.sh            # 설치 + 실행기 + Steam 바로가기 (Steam 잠깐 재시작)
./install.sh --no-steam # Steam 바로가기는 직접 추가할 때
```

일반 사용자로 실행한다. 비밀번호는 시스템 flatpak 설치 때만 묻는다.

## 하는 일
1. `org.jellyfin.JellyfinDesktop`을 Flathub에서 시스템 범위로 설치
2. `~/.local/bin/jellyfin-ally` 실행기 설치. 실행할 때마다:
   - flatpak 입력 장치 권한(`--device=input`) 확인. 없으면 SDL이 컨트롤러를 0개로 봄
   - Steam 가상 패드("Microsoft X-Box 360 pad")용 버튼 배치를 모든 프로필에 복사. 없으면 입력이 전부 "No match"
   - 첫 실행이면 기본 프로필을 미리 만들어 첫 실행부터 버튼이 먹게 함
   - `--fullscreen --tv`로 실행
3. Steam의 "Jellyfin Desktop" 비-Steam 바로가기를 이 실행기로 바꾸거나 새로 추가.
   Steam이 켜져 있으면 shortcuts.vdf를 덮어쓰므로 Steam을 껐다가 다시 켠다.
   원본은 `shortcuts.vdf.bak-jellyfin-ally-*`로 백업.

## 버튼
십자키·왼쪽 스틱 이동, A 선택, B 뒤로(길게: 홈), Y 검색, X 오디오 트랙,
보기 버튼 자막, 메뉴 버튼 홈, LB/RB 되감기/빨리감기, 오른쪽 스틱 위아래 볼륨.
배치를 바꾸려면 `rog-ally-steam-pad.json`을 고치고 다시 `./install.sh`.

서버 주소는 첫 실행 때 앱에서 직접 입력한다.

## 다른 Ally에서 받기
```bash
git clone https://github.com/metear0411-cyber/jellyfin-ally.git ~/Projects/jellyfin-ally
~/Projects/jellyfin-ally/install.sh
```
