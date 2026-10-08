#!/usr/bin/env python3
"""plugin_bot_report.py — プラグイン側 BOT 戦の実測レポートと参照(run8)との比較。

Paper の logs/latest.log(またはその抜粋)にある

    [N Arena][BotMatch] END player=… duration=<秒>s …
    [N Arena][BotMatch] trace (N events):
    [N Arena][BotMatch]   <0.1秒> <event>
    [N Arena][BotMatch] samples (N @0.1s):
    [N Arena][BotMatch]   <デシ秒> s p=… i=<item> …   (10 単位 = 1 秒)

を読み、参照側 qlog(docs/parity/fabric_normal_anchor_run8_400s.log.gz)から同じ統計を
出して並べる。参照側の行動数は手持ちアイテムの切り替え (= マップの hotbar 切り替え) と
`ec` (16blk 内のエンドクリスタル) の増加で数える。タイマの再装填はアンカーの段でも
起きるので数えられない (2026-10-07)。標準ライブラリのみ。

    python3 tools/plugin_bot_report.py /tmp/paper-run/logs/latest.log \
        --ref docs/parity/fabric_normal_anchor_run8_400s.log.gz
"""
from __future__ import annotations

import gzip
import re
import statistics
import sys
from collections import Counter

TRACE = re.compile(r"\[N Arena\]\[BotMatch\]\s+([\d.]+)s\s+(.+)$")
SAMPLE = re.compile(r"\[N Arena\]\[BotMatch\]\s+([\d.]+)\s+s p=")
END = re.compile(r"\[N Arena\]\[BotMatch\] END .*duration=(\d+)s.*difficulty=(\w+)")


def read_lines(path: str):
    if path.endswith(".gz"):
        with gzip.open(path, "rt", errors="replace") as fh:
            yield from fh
    else:
        with open(path, "r", errors="replace") as fh:
            yield from fh


# 集計の自己検証: レポートの数値を trace パーサとは別の素朴な部分一致で数え直す。
# 昔の計測ツールはここがずれて「参照 16.5/min のクリスタル」のような幻の数字を出した。
_RAW = {
    "anchor place": re.compile(r"\[N Arena\]\[BotMatch\]\s+[\d.]+s anchor place$"),
    "anchor charge": re.compile(r"\[N Arena\]\[BotMatch\]\s+[\d.]+s anchor charge$"),
    "anchor detonate": re.compile(r"\[N Arena\]\[BotMatch\]\s+[\d.]+s anchor detonate$"),
    "crystal place": re.compile(r"\[N Arena\]\[BotMatch\]\s+[\d.]+s crystal place$"),
    "swing": re.compile(r"\[N Arena\]\[BotMatch\]\s+[\d.]+s swing "),
    "hit": re.compile(r"\[N Arena\]\[BotMatch\]\s+[\d.]+s hit "),
    "gap eat": re.compile(r"\[N Arena\]\[BotMatch\]\s+[\d.]+s gap eat"),
    "totem POP": re.compile(r"\[N Arena\]\[BotMatch\]\s+[\d.]+s totem POP"),
    "pearl": re.compile(r"\[N Arena\]\[BotMatch\]\s+[\d.]+s pearl "),
}


def _raw_counts(path: str) -> dict[str, int]:
    """trace 解析を通さない生の部分一致カウント (自己検証用)。"""
    out: dict[str, int] = {k: 0 for k in _RAW}
    for line in read_lines(path):
        for key, rx in _RAW.items():
            if rx.search(line):
                out[key] += 1
    return out


def fight_windows(lines: list[str]) -> list[tuple[int, int]]:
    """[START, END] の行番号レンジ。latest.log に複数試合が入っていても分離できる。"""
    starts, ends = [], []
    for i, line in enumerate(lines):
        if "[BotMatch] START " in line:
            starts.append(i)
        elif "[BotMatch] END " in line:
            ends.append(i)
    out = []
    for a in starts:
        b = next((e for e in ends if e > a), len(lines) - 1)
        out.append((a, b))
    return out


def plugin_stats(path: str) -> dict:
    lines = list(read_lines(path))
    warnings: list[str] = []
    windows = fight_windows(lines)
    if len(windows) > 1:
        # 複数試合が 1 ファイルに入っていると、events と duration が別試合のものになり
        # レートが混ざる。最後の試合だけを見る (明示的に警告も出す)。
        last_start, last_end = windows[-1]
        warnings.append(f"複数試合 ({len(windows)}) を検出: 最後の START..END のみ集計")
        lines = lines[last_start:last_end + 1]
    events: list[tuple[float, str]] = []
    items: Counter[str] = Counter()
    samples = 0
    duration = None
    difficulty = "?"
    for line in lines:
        m = END.search(line)
        if m:
            duration = int(m.group(1))
            difficulty = m.group(2)
            continue
        m = SAMPLE.search(line)
        if m:
            samples += 1
            m2 = re.search(r"\bi=([A-Za-z_]+)", line)
            if m2:
                # Bukkit enum 名で来るので小文字化(参照側 id と突き合わせるため)。
                items[(m2.group(1) or "-").lower()] += 1
            continue
        m = TRACE.search(line)
        if m and not m.group(2).startswith("s p="):
            events.append((float(m.group(1)), m.group(2)))

    # span は END 行 → trace 最終時刻 → 0 の順に落ちる。どれも無い場合 (fight 中に
    # 走らせた・ログが切れている等) は 0 にして max(..., 1.0) でゼロ除算を防ぐ。
    span = duration
    if span is None and events:
        span = events[-1][0]
        warnings.append("END 行が無い: trace の最終時刻を試合長に使った")
    if span is None:
        span = 0.0
        warnings.append("END 行も trace も無い: 試合長 0 として集計 (レートは /min が過大)")
    minutes = max(span, 1.0) / 60.0

    def count(*needles: str) -> int:
        return sum(1 for _, e in events if all(n in e for n in needles))

    def rate(n: int) -> float:
        return round(n / minutes, 1)

    def gaps(*needles: str) -> tuple[float, float]:
        ts = [t for t, e in events if all(n in e for n in needles)]
        if len(ts) < 3:
            return (0.0, 0.0)
        d = [ts[i + 1] - ts[i] for i in range(len(ts) - 1)]
        return (round(statistics.median(d), 2), round(min(d), 2))

    pearl = count("pearl")
    anchor = count("anchor place")
    charge = count("anchor charge")
    detonate = count("anchor detonate")
    crystal = count("crystal place")
    swings = count("swing")
    hits = count("hit ")
    gap_eat = count("gap eat")
    pops = count("totem POP")
    total_items = sum(items.values()) or 1

    return {
        "source": "plugin",
        "duration": span,
        "difficulty": difficulty,
        "events": len(events),
        "samples": samples,
        "pearl": (pearl, rate(pearl), gaps("pearl")[0]),
        "anchor": (anchor, rate(anchor), gaps("anchor place")[0]),
        "charge": (charge, rate(charge)),
        "detonate": (detonate, rate(detonate)),
        "crystal": (crystal, rate(crystal), gaps("crystal place")[0]),
        "swings": (swings, rate(swings)),
        "hits": (hits, rate(hits), gaps("hit ")[0]),
        "pops": pops,
        "gap_eat": gap_eat,
        "items": [(k, round(100.0 * v / total_items, 1)) for k, v in items.most_common()],
        "warnings": warnings,
        "raw": _raw_counts(path),
    }


def ref_stats(path: str) -> dict:
    """qlog(1行=1tick, 20 tick/s)から同じ統計を作る。"""
    rows = []
    for line in read_lines(path):
        body = line.strip()
        if not body or "t=" not in body:
            continue
        rows.append(dict(re.findall(r"(\w+)=([^\s]+)", body)))
    if not rows:
        raise SystemExit(f"no qlog rows in {path}")
    t0 = int(float(rows[0]["t"]))
    span = (int(float(rows[-1]["t"])) - t0) / 20.0
    minutes = span / 60.0

    def uses(key: str, thresh: int = 3) -> list[float]:
        vals = [int(float(r[key])) for r in rows if key in r]
        ts = [int(float(r["t"])) for r in rows if key in r]
        out = []
        for i in range(1, len(vals)):
            if vals[i] > vals[i - 1] + thresh:
                out.append((ts[i] - t0) / 20.0)
        return out

    def med(ts: list[float]) -> float:
        if len(ts) < 3:
            return 0.0
        return round(statistics.median([ts[i + 1] - ts[i] for i in range(len(ts) - 1)]), 2)

    def rate(n: int) -> float:
        return round(n / minutes, 1)

    # 参照側の「行動」は手持ちアイテムの切り替えで数える。タイマ(crystal_timer 等)の再装填は
    # アンカー段でも起きるため、ct の再装填を「クリスタル設置」と数えると 3 倍に水増しされる
    # (run8 実測: ct 再装填 111 回に対し実クリスタルは 33 回)。当側の trace は
    # anchor place / anchor charge / crystal place を直接記録しているので、同じ土台に載せる。
    def item_events(name: str) -> list[float]:
        out = []
        for i in range(1, len(rows)):
            before = rows[i - 1].get("i", "")
            now_item = rows[i].get("i", "")
            if now_item != before and now_item == f"minecraft:{name}":
                out.append((int(float(rows[i]["t"])) - t0) / 20.0)
        return out

    # 爆発はアイテムを持ち替えないので explosion_timer の 0 復帰で拾う (チェーン完了の代理)。
    pearl, hitcd = uses("pc"), uses("hit")
    anchor, charge = item_events("respawn_anchor"), item_events("glowstone")
    crystal = item_events("end_crystal")
    detonate = uses("exp")
    # 地面に実在したクリスタル数 (設置→即破壊の裏取り)。
    crystal_spawns = [(int(float(rows[i]["t"])) - t0) / 20.0 for i in range(1, len(rows))
                      if int(float(rows[i]["ec"])) > int(float(rows[i - 1]["ec"]))]
    # Bukkit の enum 名 (ENDER_PEARL) と参照側の id (ender_pearl) を同じ土台に載せる。
    items: Counter[str] = Counter(
        r["i"].replace("minecraft:", "").lower() for r in rows if "i" in r)
    total = sum(items.values()) or 1
    return {
        "source": "reference",
        "duration": span,
        "difficulty": "INTERMEDIATE",
        "pearl": (len(pearl), rate(len(pearl)), med(pearl)),
        "anchor": (len(anchor), rate(len(anchor)), med(anchor)),
        "charge": (len(charge), rate(len(charge))),
        "detonate": (len(detonate), rate(len(detonate))),
        "crystal": (len(crystal_spawns) if crystal_spawns else len(crystal),
                    rate(len(crystal_spawns) if crystal_spawns else len(crystal)),
                    med(crystal_spawns) if crystal_spawns else med(crystal)),
        "swings": (0, 0.0),
        "hits": (len(hitcd), rate(len(hitcd)), med(hitcd)),
        "pops": len(uses("tot")),
        "gap_eat": 0,
        "items": [(k, round(100.0 * v / total, 1)) for k, v in items.most_common()],
        "warnings": [],
    }


def _fmt(vals) -> str:
    """count / per-minute / median gap — a short tuple just omits the later columns."""
    if not vals:
        return "-"
    out = f"{int(vals[0]):>4d}  {float(vals[1]):>6.1f}/min"
    if len(vals) > 2 and float(vals[2]) > 0:
        out += f"  ギャップ中央 {float(vals[2]):.2f}s"
    return out


def line(label: str, p, r) -> str:
    return f"{label:<18} 当側: {_fmt(p):<40} 参照: {_fmt(r)}"


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    path = sys.argv[1]
    ref_path = None
    if "--ref" in sys.argv:
        ref_path = sys.argv[sys.argv.index("--ref") + 1]
    p = plugin_stats(path)
    r = ref_stats(ref_path) if ref_path else None

    print(f"=== プラグイン側 BOT 戦 {path} ===")
    print(f"試合長 {p['duration']}s / difficulty {p['difficulty']} / trace {p['events']} 件 / "
          f"samples {p['samples']} 件")
    for w in p.get("warnings", []):
        print(f"  [警告] {w}")
    if r:
        print(f"参照 {ref_path} — 試合長 {r['duration']:.0f}s "
              f"(difficulty {r['difficulty']})")
    print()
    print("                   [回数  /min  ギャップ]")
    for key, label in (("pearl", "パール"), ("anchor", "アンカー設置"),
                       ("charge", "アンカーチャージ"), ("detonate", "アンカー起爆"),
                       ("crystal", "クリスタル設置"), ("hits", "剣ヒット"),
                       ("gap_eat", "金リンゴ"), ("pops", "トーテムPOP")):
        if key in ("gap_eat", "pops"):
            ps = f"{p[key]:>4d} ({p[key] / max(p['duration'], 1) * 60:5.1f}/min)"
            rs = f"{r[key]:>4d} ({r[key] / max(r['duration'], 1) * 60:5.1f}/min)" if r else "-"
            print(f"{label:<18} 当側: {ps}   参照: {rs}")
        else:
            print(line(label, p[key], r[key] if r else None))
    # 自己検証: trace パーサの数値を素朴な部分一致で数え直して並べる。ずれていたら
    # パーサ側のバグ (昔 crystal_spawns を時刻でなく添字で数えていた等)。
    raw = p.get("raw")
    if raw:
        pairs = (("anchor place", "anchor"), ("anchor charge", "charge"),
                 ("anchor detonate", "detonate"), ("crystal place", "crystal"),
                 ("hit", "hits"), ("gap eat", "gap_eat"), ("pearl", "pearl"))
        bad = []
        for rk, pk in pairs:
            pv = p[pk][0] if isinstance(p[pk], tuple) else p[pk]
            if raw[rk] != pv:
                bad.append(f"{rk}: trace={pv} raw={raw[rk]}")
        print(f"  自己検証: 生カウント "
              + ("一致" if not bad else "不一致 → " + " / ".join(bad)))
    print()
    print("手持ちアイテム(サンプル)     当側                 参照")
    pm, rm = dict(p["items"]), dict(r["items"]) if r else {}
    for mat in sorted(set(pm) | set(rm), key=lambda k: -max(pm.get(k, 0), rm.get(k, 0))):
        print(f"  {mat:<22} {pm.get(mat, 0):5.1f}%            {rm.get(mat, 0):5.1f}%"
              if r else f"  {mat:<22} {pm.get(mat, 0):5.1f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
