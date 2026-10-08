#!/usr/bin/env python3
"""GUI-side message keys + the locale regression guard (idempotent).

Usage: python3 gui_fix.py [repo-root]

Four GUIs asked for message keys that exist nowhere, so the label rendered as
"!gui.selected!" / "!menu.next!". Each is pointed at the key that already carries that text.
EditKitGui.configToggle also accepted a hint key and never rendered it - the two preset toggles
now show their hint line, which is what the parameter was for. Finally the local test loop gains
a guard so an unreachable locale key fails the build instead of reaching players.
"""
import pathlib
import sys

REPO = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else \
    pathlib.Path(__file__).resolve().parent.parent / 'RumilancePractice'

applied, skipped, failed = [], [], []


def patch(rel, old, new, label, count=1, absent=None):
    """Apply one edit; skip when it is already in place, fail loudly on drift.

    absent is a snippet that the edit removes, needed when the replacement text also occurs
    elsewhere in the file (two identical "next page" arrows, for instance).
    """
    path = REPO / rel
    text = path.read_text(encoding='utf-8')
    if old not in text and (absent is None or absent not in text):
        skipped.append(label)
        return
    if text.count(old) != count:
        failed.append(f"{label}: anchor x{text.count(old)}, want {count}")
        return
    path.write_text(text.replace(old, new), encoding='utf-8')
    applied.append(label)


patch('src/main/java/com/rumilance/practice/gui/menus/TeamHubGui.java',
      '.name(t(player, "menu.next").color(UiTheme.MUTED))',
      '.name(t(player, "menu.page-next").color(UiTheme.MUTED))',
      "team hub: the second next arrow uses menu.page-next",
      absent='"menu.next"')

patch('src/main/java/com/rumilance/practice/gui/menus/PartyBattleModeGui.java',
      'UiTheme.status(line(player, "gui.selected"), UiTheme.SUCCESS)',
      'UiTheme.status(line(player, "party.selected"), UiTheme.SUCCESS)',
      "party battle mode: the SELECTED chip uses party.selected",
      count=2, absent='"gui.selected"')

patch('src/main/java/com/rumilance/practice/gui/menus/SettingsGui.java',
      't(player, "gui.settings-title").color(UiTheme.PRIMARY)',
      't(player, "menu.settings").color(UiTheme.PRIMARY)',
      "settings hub: title uses the existing menu.settings label",
      absent='"gui.settings-title"')

patch('src/main/java/com/rumilance/practice/gui/menus/EditKitGui.java',
      """    private ItemStack configToggle(Player player, String nameKey, String hintKey, boolean on,
                                   String action) {
        return GuiDecorator.button(on ? Material.LIME_DYE : Material.GRAY_DYE,
                Component.text(line(player, nameKey), on ? UiTheme.SUCCESS : UiTheme.MUTED)
                        .decoration(TextDecoration.ITALIC, false), action);
    }""",
      """    private ItemStack configToggle(Player player, String nameKey, String hintKey, boolean on,
                                   String action) {
        return ItemBuilder.of(on ? Material.LIME_DYE : Material.GRAY_DYE)
                .name(Component.text(line(player, nameKey), on ? UiTheme.SUCCESS : UiTheme.MUTED)
                        .decoration(TextDecoration.ITALIC, false))
                .lore(UiTheme.divider(), UiTheme.line(line(player, hintKey)))
                .action(action)
                .build();
    }""",
      "edit kit: configToggle renders the hint it was always given",
      absent="GuiDecorator.button(on ? Material.LIME_DYE")

GUARD_ANCHOR = "sys.exit(1 if failed else 0)"
GUARD_MARKER = "dead = [k for k in sorted(keys) if not resolves(document, k)]"
GUARD = '''# The plugin reads messages back with YamlConfiguration.getString(path), which splits the path
# on '.'. A key that repeats its section name ("gui.foo:" inside the gui: section) is therefore
# stored as gui.gui.foo and the code's lookup misses, printing "!gui.foo!" in a GUI. Checking
# every declared key resolves is exact: no heuristics, no false alarms.
REACHABLE = re.compile(r'^[a-z][a-z0-9_-]*$', re.I)
def resolves(document, path):
    node = document
    for part in path.split('.'):
        if not isinstance(node, dict) or part not in node:
            return False
        node = node[part]
    return isinstance(node, str)

for label, keys in sorted(sets.items()):
    locale_file = os.path.join(root, label.replace('/', os.sep))
    with open(locale_file, encoding='utf-8') as handle:
        document = yaml.load(handle, Loader=Loader) or {}
    dead = [k for k in sorted(keys) if not resolves(document, k)]
    if dead:
        failed = True
        print('local-test: FAIL \\u2014 %s declares %d key(s) the message loader can never '
              'resolve (a key must not repeat its own section name, and must sit in the '
              'section the code asks for): %s' % (label, len(dead), dead[:5]), file=sys.stderr)
    with open(locale_file, encoding='utf-8') as handle:
        for number, line in enumerate(handle, 1):
            key_part = line.split(':', 1)[0].strip()
            if not key_part or key_part[0] in '\\'"' or ' ' in key_part:
                continue
            if key_part.lower() in ('y', 'yes', 'on', 'true', 'n', 'no', 'off', 'false'):
                print('local-test: WARNING \\u2014 %s line %d: "%s" is a YAML 1.1 boolean; '
                      'quote the key or the loader stores it as true/false'
                      % (label, number, key_part), file=sys.stderr)

sys.exit(1 if failed else 0)'''


def patch_guard():
    path = REPO / 'tools/localtest/localtest.sh'
    text = path.read_text(encoding='utf-8')
    if GUARD_MARKER in text:
        skipped.append("localtest guard")
        return
    assert text.count(GUARD_ANCHOR) == 1, "guard anchor"
    text = text.replace('import glob, os, sys, yaml\n', 'import glob, os, re, sys, yaml\n')
    path.write_text(text.replace(GUARD_ANCHOR, GUARD), encoding='utf-8')
    applied.append("localtest guard: fail on unreachable keys, warn on YAML 1.1 boolean keys")


patch_guard()
print("applied :", applied)
print("skipped :", skipped or "-")
if failed:
    for f in failed:
        print("   !", f)
    sys.exit(1)
