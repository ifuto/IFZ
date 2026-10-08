# サンドボックス復旧手順 (RumilancePractice デバッグ)

`/tmp` が消えても、この手順だけで「フルツリー javac + Paper 実機 + Fabric 参照」まで戻せる。
作業ブランチは `arena/01a106b3-rumilancepractice`、修正は `000{1,2,3}-*.patch`。

## 0. 何が残るか

| 場所 | 内容 | wipe 耐性 |
|---|---|---|
| `/home/user/RumilancePractice` | 本体クローン + パッチ適用 | ✗ (消える) |
| `/home/user/IFZ/.rumilance-harness/` | **パッチ・スタブ生成器・rcon クライアント** (git 追跡) | ✓ |
| `/tmp/toolchain`, `/tmp/dl`, `/tmp/testsrv` … | JDK / サーバー / ビルド | ✗ |

## 1. 本体 + パッチ

```bash
git clone --branch arena/01a106b3-rumilancepractice \
  https://github.com/ifuto/RumilancePractice /home/user/RumilancePractice
cd /home/user/RumilancePractice
# 0001 → 0002 → 0003 の順で (この 3 本で clone 直後の c5a78aa から HEAD と同一になる)。
for p in /home/user/IFZ/.rumilance-harness/000[1-9]-*.patch; do git apply "$p"; done
```

`000[1-9]-*.patch` は `c5a78aa` (clone 直後) からの連番。番号順に当てること (後の番号が
前の番号の入れたファイルを編集する)。2026-10-07 時点で 0001..0007。`rumilance-fixes.patch` は 0001 に完全に含まれるので**もう当てない**
(当てると二重適用で失敗する)。

## 2. 配送ブランチ (JDK / Fabric / Paper / 土台 jar)

配送は **GitHub Actions が git ブランチに置いたもの**が唯一の入手経路 (release/artifact は遮断)。
ワークフロー正本は repo の `.github/workflows/`、実処理は `ci/`。**サンドボックスからは push も
dispatch もできない** (App トークンが read-only、403)。届いているものを使う:

```bash
for b in java-env-delivery mc-server-delivery paper-server-delivery plugin-delivery; do
  git clone -q --depth 1 --single-branch --branch $b \
    https://github.com/ifuto/RumilancePractice /tmp/dl/$b
done
mkdir -p /tmp/dl
cp /tmp/dl/plugin-delivery/plugin/*.jar /tmp/dl/
cp /tmp/dl/java-env-delivery/delivery/*.part-* /tmp/dl/
cp /tmp/dl/mc-server-delivery/mcserver/*.part-* /tmp/dl/
cp /tmp/dl/paper-server-delivery/paperserver/*.part-* /tmp/dl/
cat /tmp/dl/jdk21.tar.gz.part-* > /tmp/jdk21.tar.gz && mkdir -p /tmp/toolchain/x
tar xzf /tmp/jdk21.tar.gz -C /tmp/toolchain/x && ln -sfn /tmp/toolchain/x/jdk-21.0.12.1+1 /tmp/jdk21
```

## 3. コンパイル専用スタブ (**順番が命**)

PacketEvents / WorldEdit(FAWE) / LuckPerms / Hikari は jar が入手できないので、シグネチャだけの
スタブを生成してクラスパスに載せる。生成器は `make_stubs1.py` → `2` → `3` → `4` → `5` の順
(後のものが前のものを上書き・拡張する)。

```bash
cd /home/user/RumilancePractice
for s in 1 2 3 4 5; do python3 /home/user/IFZ/.rumilance-harness/make_stubs$s.py; done
# make_stubs1 は repo 内 tools/parity-runner/stubs/ (NotNull/Nullable) も取り込む
```

## 4. ビルドと動作確認

```bash
cd /home/user/RumilancePractice
JDK=/tmp/jdk21 STUB_CLASSES=/tmp/toolchain/stubs/classes \
  tools/parity-runner/build_plugin.sh /tmp/ship/plugin-patched.jar     # 861 classes
# フルの javac 単体確認:
CP="/tmp/dl/RumilancePractice-1.92.17.jar:/tmp/papersrv/paper-run/versions/1.21.11/paper-1.21.11.jar:/tmp/toolchain/stubs/classes:$(find /tmp/papersrv/paper-run/libraries -name '*.jar' | tr '\n' ':')"
/tmp/jdk21/bin/javac -nowarn -proc:none -cp "$CP" -d /tmp/out \
  $(find src/main/java -name '*.java' | grep -v database/DatabaseService.java)   # 0 errors
```

## 5. Paper + Fabric 実機

```bash
STUB_CLASSES=/tmp/toolchain/stubs/classes tools/parity-runner/env_up.sh    # 展開・配置 (起動はしない)
bash /tmp/run_paper.sh    # testsrv / 25566 / RCON 25576 / -Drumilance.harness=true
bash /tmp/run_fabric.sh   # mcref/mcserver / 25565 / RCON 25575
# 起動後にキットを再適用 (quantum.yml は初回起動で生成される):
python3 tools/parity-runner/server_preset.py apply --dir /tmp/testsrv
```

`run_paper.sh` / `run_fabric.sh` は FIFO console.in を作って素の java を exec するだけ
(start.sh の再起動ループは使わない = `kill` で確実に止まる)。

## 6. 計測

- プラグイン側 (practice bot 戦): RCON `narena-harness ground 40 100` → `room r1 CRYSTAL 40 0 64 0`
  → `dummy HarnessBot 4 64 4` → `fight CRYSTAL 150 INTERMEDIATE 1` → `tools/plugin_bot_report.py`
- パリティ (Fabric 参照 ↔ Paper): `tools/parity-runner/pair.sh <tag> sword_k10v11 30 15` →
  `tools/parity_verify.py` (**Paper 側は現状 bot が動かない。理由は `tools/plugin_runtime.md` 8 節**)

## wipe #12〜#14 (2026-10-08) で分かったこと

- **`git am` は使えない**: `src/main/resources/kb/*.json` に CRLF が混ざっており、
  `git am` は "quoted CRLF detected" で `patch does not apply` になる。`restore.sh` と同じく
  `git apply` で流す (改行はそのまま入る)。適用後に `git add -A && git commit` で 1 コミット化してよい。
- **GitHub への push は 403** (ifuto/RumilancePractice への書き込み権限が無い)。
  成果の永続化は「このハーネスのパッチ列 + restore.sh」が唯一の経路。
- パッチ列は 0001..0005 (kbprobe base / regen+eval+duel / 連鎖段間隔 / 瓶ウィンドウ / kbprobe docs)。
  `rumilance-fixes.patch` は**適用しない** (旧系列)。
- このリポジトリの /tmp 環境は 100 秒程度で全再構築できる (`restore.sh` 一発)。
