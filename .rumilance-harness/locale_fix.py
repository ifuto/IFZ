#!/usr/bin/env python3
"""Repair the bundled locale files (idempotent).

Usage: python3 locale_fix.py [repo-root]

Why this is needed: LocaleService reads a message back with
YamlConfiguration.getString(path), and Bukkit splits the path on '.'. A YAML child key that
already contains its section name therefore lands in the catalog as "gui.gui.foo" while the
code asks for "gui.foo", so the GUI prints "!gui.foo!". A whole flat block of keys was also
appended inside the wrong section - a comment line does not end a YAML block, so the indented
keys after it still belonged to the section above.

Run after fixes.py / fixes2.py / gui_fix.py. Idempotent: re-running reports skips.
"""
import pathlib
import sys

REPO = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else \
    pathlib.Path(__file__).resolve().parent.parent / 'RumilancePractice'
LANG = REPO / 'src/main/resources/lang'

NEW_KEYS = {
    'en_gb': {'kit': 'Kit', 'ranking': 'Ranking', 'percentile': 'Percentile',
              'battle-mode-title': 'Battle Mode', 'party-launch-map': 'Select a Map',
              'preset-removable-hint': 'Players may delete this preset item',
              'preset-more-enchant-hint': 'Also usable as an enchantment ingredient'},
    'en_us': {'kit': 'Kit', 'ranking': 'Ranking', 'percentile': 'Percentile',
              'battle-mode-title': 'Battle Mode', 'party-launch-map': 'Select a Map',
              'preset-removable-hint': 'Players may delete this preset item',
              'preset-more-enchant-hint': 'Also usable as an enchantment ingredient'},
    'es_es': {'kit': 'Kit', 'ranking': 'Clasificación', 'percentile': 'Percentil',
              'battle-mode-title': 'Modo de batalla', 'party-launch-map': 'Elegir mapa',
              'preset-removable-hint': 'Los jugadores pueden borrar este objeto',
              'preset-more-enchant-hint': 'También sirve para encantar otros objetos'},
    'fr_fr': {'kit': 'Kit', 'ranking': 'Classement', 'percentile': 'Percentile',
              'battle-mode-title': 'Mode de combat', 'party-launch-map': 'Choisir une carte',
              'preset-removable-hint': 'Les joueurs peuvent supprimer cet objet',
              'preset-more-enchant-hint': "Sert aussi d'ingrédient d'enchantement"},
    'ja_jp': {'kit': 'キット', 'ranking': 'ランキング', 'percentile': 'パーセンタイル',
              'battle-mode-title': 'バトルモード', 'party-launch-map': 'マップを選択',
              'preset-removable-hint': 'プレイヤーがこの項目を削除できるようにする',
              'preset-more-enchant-hint': 'エンチャントの素材としても使えるようにする'},
    'ko_kr': {'kit': '킷', 'ranking': '랭킹', 'percentile': '백분위',
              'battle-mode-title': '배틀 모드', 'party-launch-map': '맵 선택',
              'preset-removable-hint': '플레이어가 이 항목을 삭제할 수 있게 합니다',
              'preset-more-enchant-hint': '인챈트 재료로도 사용할 수 있게 합니다'},
    'zh_cn': {'kit': '套件', 'ranking': '排行榜', 'percentile': '百分位',
              'battle-mode-title': '对战模式', 'party-launch-map': '选择地图',
              'preset-removable-hint': '允许玩家删除此项目',
              'preset-more-enchant-hint': '也可作为附魔材料使用'},
}

done, skipped = [], []


def block(lines, name):
    """[start, end) indexes of a top-level section; blank/comment lines do not end a block."""
    start = next(i for i, l in enumerate(lines) if l.startswith(name + ':'))
    end = len(lines)
    for i in range(start + 1, len(lines)):
        stripped = lines[i].strip()
        if stripped and not stripped.startswith('#') and not lines[i][0].isspace():
            end = i
            break
    return start, end


def has_child(lines, name, prefix):
    start, end = block(lines, name)
    return any(lines[i].startswith(prefix) for i in range(start + 1, end))


for path in sorted(LANG.glob('*.yml')):
    lines = path.read_text(encoding='utf-8').splitlines(keepends=True)
    changed = False

    # 1. doubled prefix inside the gui: section
    start, end = block(lines, 'gui')
    strays = [i for i in range(start + 1, end) if lines[i].startswith('  gui.')]
    for i in strays:
        head, _, tail = lines[i][2:].partition(':')
        lines[i] = f"  {head.removeprefix('gui.')}:{tail}"
    changed |= bool(strays)

    # 2. keys parked under tournament: that belong to gui: / party:
    start, end = block(lines, 'tournament')
    body = lines[start + 1:end]
    keep = [True] * len(body)
    for i, line in enumerate(body):
        if line.startswith('  gui.') or line.startswith('  party.'):
            keep[i] = False
            # a comment directly above a moved key travels with it, so it keeps describing
            # the keys it was written for
            if i and body[i - 1].strip().startswith('#') and keep[i - 1]:
                keep[i - 1] = False
    moved = [line for line, k in zip(body, keep) if not k]
    if moved:
        lines = lines[:start + 1] + [l for l, k in zip(body, keep) if k] + lines[end:]
        pending = None
        for line in moved:
            if not line.startswith('  '):
                pending = line                     # the comment above a key group
                continue
            head, _, tail = line[2:].partition(':')
            section_name, leaf = head.split('.', 1)
            dest_start, dest_end = block(lines, section_name)
            if pending is not None:
                lines.insert(dest_end, pending)
                dest_end += 1
                pending = None
            lines.insert(dest_end, f"  {leaf}:{tail}")
        changed = True

    # 3. the duel KB labels live under general: but the duel GUIs ask for duel-gui.kb-*
    start, end = block(lines, 'general')
    kb = [i for i in range(start + 1, end) if lines[i].startswith('  kb-')]
    if kb:
        moved_kb = [lines[i] for i in kb]
        lines = [l for i, l in enumerate(lines) if i not in kb]
        dest_start, dest_end = block(lines, 'duel-gui')
        lines = lines[:dest_end] + moved_kb + lines[dest_end:]
        changed = True

    # 4. a bare yes:/no: key is a YAML 1.1 boolean: the catalog would store true/false
    start, end = block(lines, 'menu')
    for i in range(start + 1, end):
        if lines[i].startswith('  yes:') or lines[i].startswith('  no:'):
            lines[i] = lines[i].replace('  yes:', '  "yes":', 1).replace('  no:', '  "no":', 1)
            changed = True

    # 5. the same-IP queue notice belongs to queue: (QueueCoordinator sends queue.same-ip-notice)
    if not has_child(lines, 'queue', '  same-ip-notice:'):
        start, end = block(lines, 'party')
        hit = [i for i in range(start + 1, end) if lines[i].startswith('  same-ip-notice:')]
        if hit:
            notice = lines.pop(hit[0])
            q_start, q_end = block(lines, 'queue')
            anchor = next(i for i in range(q_start + 1, q_end)
                          if lines[i].startswith('  already-queued:'))
            lines.insert(anchor + 1, notice)
            changed = True

    # 6. labels the GUIs ask for that were never added
    for key, value in NEW_KEYS[path.stem].items():
        if not has_child(lines, 'gui', f'  {key}:'):
            end = block(lines, 'gui')[1]
            lines.insert(end, f'  {key}: "{value}"\n')
            changed = True

    if changed:
        path.write_text(''.join(lines), encoding='utf-8')
        done.append(path.stem)
    else:
        skipped.append(path.stem)

print("locale_fix: applied to", done or "nothing", "| already clean:", skipped)
