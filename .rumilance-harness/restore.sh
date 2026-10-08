#!/usr/bin/env bash
# サンドボックス再起動（/tmp と repo が消える）からの一発復旧。
#   1. repo を clone して 000[1-9]-*.patch を番号順に適用
#   2. delivery ブランチから JDK / Fabric / Paper / 土台 jar を取り出す
#   3. スタブを生成してビルド（build_plugin.sh）
#   4. Paper のテスト環境 (/tmp/testsrv) を用意し、プラグインと kb プロファイルを配置
#
#   bash restore.sh [--start]     # --start で Paper を起動まで行う
set -uo pipefail

H=/home/user/IFZ/.rumilance-harness
REPO=/home/user/RumilancePractice
DL=/tmp/dl
JDK=/tmp/jdk21
BRANCH=arena/01a106b3-rumilancepractice
START=0
[ "${1:-}" = "--start" ] && START=1

log() { echo "== $*"; }
fail() { echo "!! $*"; exit 1; }

# ---------------------------------------------------------------- 1. repo + patches
if [ ! -d "$REPO/.git" ]; then
  log "repo を clone"
  git clone -q --branch "$BRANCH" https://github.com/ifuto/RumilancePractice "$REPO" || fail "clone"
fi
cd "$REPO" || fail "cd repo"
if [ -n "$(git status --porcelain)" ]; then
  log "パッチは適用済み (作業ツリーに変更あり)"
else
  log "パッチを適用 (000[1-9])"
  for p in "$H"/000[1-9]-*.patch; do
    git apply "$p" || fail "apply $(basename "$p")"
  done
fi
log "HEAD: $(git log --oneline -1)"

# ---------------------------------------------------------------- 2. delivery blobs
mkdir -p "$DL"
if [ ! -f "$DL/RumilancePractice-1.92.17.jar" ] || [ ! -f "$DL/jdk21.tar.gz.part-00" ]; then
  log "delivery ブランチを取得"
  for b in java-env-delivery mc-server-delivery paper-server-delivery plugin-delivery; do
    [ -d "$DL/$b" ] && continue
    timeout 900 git clone -q --depth 1 --single-branch --branch "$b" \
      https://github.com/ifuto/RumilancePractice "$DL/$b" || fail "clone $b"
  done
  cp "$DL"/plugin-delivery/plugin/*.jar "$DL"/ 2>/dev/null
  cp "$DL"/java-env-delivery/delivery/*.part-* "$DL"/ 2>/dev/null
  cp "$DL"/mc-server-delivery/mcserver/*.part-* "$DL"/ 2>/dev/null
  cp "$DL"/paper-server-delivery/paperserver/*.part-* "$DL"/ 2>/dev/null
fi

if [ ! -x "$JDK/bin/java" ]; then
  log "JDK21 を展開"
  mkdir -p /tmp/toolchain/x
  cat "$DL"/jdk21.tar.gz.part-* > /tmp/jdk21.tar.gz
  tar xzf /tmp/jdk21.tar.gz -C /tmp/toolchain/x
  ln -sfn "$(ls -d /tmp/toolchain/x/jdk-* | head -1)" "$JDK"
fi
if [ ! -f /tmp/mcref/mcserver/fabric-server-launch.jar ]; then
  log "Fabric サーバーを展開"
  mkdir -p /tmp/mcref && cat "$DL"/mcserver.tar.gz.part-* | tar xz -C /tmp/mcref
fi
if [ ! -f /tmp/papersrv/paper-run/server.jar ]; then
  log "Paper サーバーを展開"
  mkdir -p /tmp/papersrv && cat "$DL"/paper-server.tar.gz.part-* | tar xz -C /tmp/papersrv
fi

# ---------------------------------------------------------------- 3. stubs + build
log "スタブ生成"
for s in 1 2 3 4 5; do python3 "$H/make_stubs$s.py" >/dev/null 2>&1; done
mkdir -p /tmp/toolchain/stubs/classes
( cd /tmp/toolchain/stubs/src && find . -name '*.java' > /tmp/stubsrcs.txt &&
  CP="$(find /tmp/papersrv/paper-run/libraries -name '*.jar' | tr '\n' ':')/tmp/papersrv/paper-run/versions/1.21.11/paper-1.21.11.jar" &&
  "$JDK/bin/javac" -nowarn -proc:none -cp "$CP" -d /tmp/toolchain/stubs/classes @/tmp/stubsrcs.txt ) \
  || fail "stub javac"
log "stub classes: $(find /tmp/toolchain/stubs/classes -name '*.class' | wc -l)"

mkdir -p /tmp/ship
log "プラグインをビルド"
DELIVERY="$DL/RumilancePractice-1.92.17.jar" STUB_CLASSES=/tmp/toolchain/stubs/classes \
  bash tools/parity-runner/build_plugin.sh /tmp/ship/kb-latest.jar || fail "build_plugin"

# ---------------------------------------------------------------- 4. Paper test env
if [ ! -d /tmp/testsrv ]; then
  log "テスト環境を用意 (env_up)"
  STUB_CLASSES=/tmp/toolchain/stubs/classes timeout 1500 bash tools/parity-runner/env_up.sh \
    || fail "env_up"
fi
cp /tmp/ship/kb-latest.jar /tmp/testsrv/plugins/RumilancePractice.jar
mkdir -p /tmp/testsrv/plugins/n-arena/kb
cp src/main/resources/kb/*.json /tmp/testsrv/plugins/n-arena/kb/

cat > /tmp/run_paper.sh <<'EOF'
#!/usr/bin/env bash
cd /tmp/testsrv
rm -f console.in && mkfifo console.in
( while true; do sleep 86400; done ) > console.in &
exec /tmp/jdk21/bin/java -Xmx1000M -Xms256M -Drumilance.harness=true -jar server.jar nogui < console.in
EOF
chmod +x /tmp/run_paper.sh

cat > /tmp/fightrun.sh <<'EOF'
#!/usr/bin/env bash
set -u
TAG="$1"; SECS="${2:-150}"
R=/home/user/RumilancePractice/tools/parity-runner/rcon.py
cd /tmp/testsrv
LINES_BEFORE=$(wc -l < logs/latest.log)
python3 "$R" 25576 parity "narena-harness fight CRYSTAL $SECS INTERMEDIATE 1" >/dev/null 2>&1
for i in $(seq 1 80); do
  sleep 5
  if tail -n +$LINES_BEFORE logs/latest.log | grep -aq "BotMatch\] END"; then break; fi
done
# END の直後に trace と samples が続いて出力される。フラッシュ待ちを入れずに切ると
# 末尾 (samples の最後の方) が欠けた状態で計測してしまう。
sleep 3
tail -n +$LINES_BEFORE logs/latest.log > "/tmp/$TAG.log"
grep -a "BotMatch\] END" "/tmp/$TAG.log" | tail -1
EOF
chmod +x /tmp/fightrun.sh

log "復旧完了: $(ls -la /tmp/ship/kb-latest.jar | awk '{print $5}') bytes"
echo "   Paper 起動: start_process 'bash /tmp/run_paper.sh' (cwd /tmp/testsrv)"
echo "   以降: narena-harness ground 40 100 → room r1 CRYSTAL 40 0 64 0 → dummy HarnessBot 4 64 4"
echo "         → fight CRYSTAL 150 INTERMEDIATE 1 (bash /tmp/fightrun.sh <tag> 150)"
[ "$START" = 1 ] && bash /tmp/run_paper.sh
