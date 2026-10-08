#!/usr/bin/env python3
"""state_probe.py — 「付与された状態が戻っているか」を実測する道具。

使い方:
    python3 state_probe.py snapshot <player> [label]     # 状態を JSON で保存
    python3 state_probe.py diff <labelA> <labelB>         # 差分を表示
    python3 state_probe.py watch <player> <seconds>       # 変化を監視(どの状態がいつ変わるか)

Paper の `data get entity` を RCON 経由で読み、プレイヤー/フェイクプレイヤーの
「戦闘で付いた状態」(属性・効果・能力・ゲームモード…)を丸ごと記録する。
プラグイン側のフロー(ロビー帰還・練習部屋・AFK・FFA・キット適用…)を挟んで
前後を撮れば、リセットし忘れている状態がそのまま差分として出る。

環境変数: PORT(既定 25576) / PASS(既定 parity) / RCON_PY(既定 tools/parity-runner/rcon.py)
"""
import json
import os
import subprocess
import sys
import time

PORT = os.environ.get("PORT", "25576")
PASS = os.environ.get("PASS", "parity")
RCON = os.environ.get("RCON_PY", "/home/user/RumilancePractice/tools/parity-runner/rcon.py")
STORE = os.environ.get("STATE_DIR", "/tmp/rumistate")

# 「戦闘が付けて、ロビーが消すべき」ものを一通り。NBT のパス名で書く。
PATHS = [
    "Health", "foodLevel", "saturation", "absorption", "foodSaturationLevel",
    "Attributes",
    "abilities",
    "active_effects",
    "playerGameType",
    "XpLevel", "XpP", "XpTotal",
    "Fire", "FallDistance", "Air", "HurtByTimestamp", "HurtTime", "DeathTime",
    "Invulnerable", "Silent", "NoGravity", "Glowing", "Invisible",
    "Tags",
    "SelectedItem", "Inventory",
    "PortalCooldown", "SpawnX", "SpawnY", "SpawnZ",
    "SharedFlags",
    "neoforge:attachments",  # 無ければ空で返る(存在確認用)
]


def rcon(cmd: str) -> str:
    out = subprocess.run(["python3", RCON, PORT, PASS, cmd],
                         capture_output=True, text=True).stdout.strip()
    if " has the following entity data: " in out:
        return out.split(" has the following entity data: ", 1)[1]
    return out


def snapshot(player: str):
    state = {}
    for path in PATHS:
        state[path] = rcon(f"execute as {player} run data get entity @s {path}")
    return state


def normalize(value: str) -> str:
    """空白・順序の揺れを吸収して比較しやすくする。"""
    value = value.strip()
    try:
        return json.dumps(json.loads(value), sort_keys=True)
    except Exception:
        return value


def cmd_snapshot(player: str, label: str) -> int:
    os.makedirs(STORE, exist_ok=True)
    state = snapshot(player)
    path = os.path.join(STORE, f"{label}.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump({"player": player, "at": time.time(), "state": state}, handle,
                  ensure_ascii=False, indent=1)
    print(f"saved {path} ({len(state)} paths)")
    return 0


def cmd_diff(label_a: str, label_b: str) -> int:
    def load(label):
        with open(os.path.join(STORE, f"{label}.json"), encoding="utf-8") as handle:
            return json.load(handle)
    a, b = load(label_a), load(label_b)
    print(f"{label_a} -> {label_b}  ({a['player']})")
    diffs = 0
    for key in PATHS:
        va, vb = a["state"].get(key, ""), b["state"].get(key, "")
        if normalize(va) == normalize(vb):
            continue
        diffs += 1
        print(f"\n### {key}")
        print(f"  {label_a}: {va[:400]}")
        print(f"  {label_b}: {vb[:400]}")
    print(f"\n--- {diffs} differing path(s) ---")
    return 0


def cmd_watch(player: str, seconds: float) -> int:
    """0.25 秒ごとに見て、変化した「パス:値」だけを時系列で出す。"""
    base = snapshot(player)
    prev = {k: normalize(v) for k, v in base.items()}
    end = time.time() + seconds
    while time.time() < end:
        cur = snapshot(player)
        for key, value in cur.items():
            norm = normalize(value)
            if prev.get(key) != norm:
                stamp = time.strftime("%H:%M:%S")
                print(f"{stamp} {key}: {prev.get(key, '')[:120]!r} -> {norm[:160]!r}", flush=True)
                prev[key] = norm
        time.sleep(0.25)
    return 0


def main(argv) -> int:
    if len(argv) >= 3 and argv[1] == "snapshot":
        return cmd_snapshot(argv[2], argv[3] if len(argv) > 3 else "snap")
    if len(argv) >= 4 and argv[1] == "diff":
        return cmd_diff(argv[2], argv[3])
    if len(argv) >= 4 and argv[1] == "watch":
        return cmd_watch(argv[2], float(argv[3]))
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
