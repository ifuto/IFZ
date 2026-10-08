#!/usr/bin/env python3
"""付与されるが戻されない状態 (grant と reset の対応) を全ツリーから洗い出す。

各「付与 API」ごとに呼び出し箇所を集め、対応する「戻す API」の有無を数える。
戻す側が 0 件、または付与側に比べて明らかに少ないものを要調査として印を付ける。
使い方: python3 state_grant_scan.py [リポジトリルート]
"""
import os
import re
import sys
from collections import defaultdict

ROOT = sys.argv[1] if len(sys.argv) > 1 else "/home/user/RumilancePractice"
SRC = os.path.join(ROOT, "src/main/java")

# (ラベル, 付与パターン, 戻すパターン群)
PAIRS = [
    ("potion effect", r"addPotionEffect\s*\(", r"removePotionEffect\s*\(|clearActivePotionEffects|clearCombatState"),
    ("attribute base", r"\.setBaseValue\s*\(", r"\.setBaseValue\s*\(.*20\.0|resetMaxHealth|resetAttackSpeed|removeModifier"),
    ("attribute modifier", r"\.addModifier\s*\(", r"\.removeModifier\s*\("),
    ("allow flight", r"setAllowFlight\s*\(true\)", r"setAllowFlight\s*\(false\)"),
    ("flying", r"setFlying\s*\(true\)", r"setFlying\s*\(false\)"),
    ("invulnerable", r"setInvulnerable\s*\(true\)", r"setInvulnerable\s*\(false\)"),
    ("collidable", r"setCollidable\s*\(false\)", r"setCollidable\s*\(true\)"),
    ("gravity off", r"setGravity\s*\(false\)", r"setGravity\s*\(true\)"),
    ("invisible", r"setInvisible\s*\(true\)", r"setInvisible\s*\(false\)"),
    ("glowing", r"setGlowing\s*\(true\)", r"setGlowing\s*\(false\)"),
    ("walk speed", r"setWalkSpeed\s*\(", r"setWalkSpeed\s*\("),
    ("fly speed", r"setFlySpeed\s*\(", r"setFlySpeed\s*\("),
    ("absorbtion", r"setAbsorptionAmount\s*\((?!0)", r"setAbsorptionAmount\s*\(0"),
    ("no damage ticks", r"setNoDamageTicks\s*\((?!0)", r"setNoDamageTicks\s*\(0"),
    ("silent", r"setSilent\s*\(true\)", r"setSilent\s*\(false\)"),
    ("AI off", r"setAI\s*\(false\)", r"setAI\s*\(true\)"),
    ("can pick up", r"setCanPickupItems\s*\(false\)", r"setCanPickupItems\s*\(true\)"),
    ("hide player", r"hidePlayer\s*\(", r"showPlayer\s*\("),
    ("flight speed fly", r"setFlySpeed\s*\((?!0\.1)", r"setFlySpeed\s*\(0\.1"),
    ("health boost", r"MAX_HEALTH\)\s*$", r"resetMaxHealth"),
    ("permission attachment", r"addAttachment\s*\(", r"removeAttachment\s*\("),
    ("player list name", r"setPlayerListName\s*\(", r"setPlayerListName\s*\(null"),
    ("max air", r"setMaximumAir\s*\(", r"setMaximumAir\s*\("),
    ("scale attr", r"SCALE", r"SCALE"),
    ("fire ticks", r"setFireTicks\s*\((?!0)", r"setFireTicks\s*\(0\)"),
]


def hits(pattern):
    rx = re.compile(pattern)
    out = []
    for base, _dirs, files in os.walk(SRC):
        for f in files:
            if not f.endswith(".java"):
                continue
            p = os.path.join(base, f)
            rel = os.path.relpath(p, ROOT)
            try:
                lines = open(p, encoding="utf-8").read().splitlines()
            except OSError:
                continue
            for i, line in enumerate(lines, 1):
                s = line.strip()
                if s.startswith("*") or s.startswith("//"):
                    continue
                if rx.search(line):
                    out.append((rel, i, s[:110]))
    return out


def main():
    for label, grant, resets in PAIRS:
        g = hits(grant)
        r = hits(resets)
        flag = ""
        if g and not r:
            flag = "  <<< NO RESET AT ALL"
        elif g and len(r) < max(1, len(g) // 3):
            flag = "  <<< few resets vs grants"
        print("=" * 100)
        print(f"{label}: grants={len(g)} resets={len(r)}{flag}")
        for rel, i, s in g[:14]:
            print(f"   G {rel}:{i}  {s}")
        for rel, i, s in r[:6]:
            print(f"   R {rel}:{i}  {s}")
        if len(g) > 14:
            print(f"   ... {len(g)-14} more grants")
    print("=" * 100)


if __name__ == "__main__":
    main()
