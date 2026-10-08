#!/usr/bin/env python3
"""JDWP(jdb) で Paper にアタッチし、ゲームモード書き換え経路のスタックを採取する。

jdb のプロンプト "> " は改行で終わらないので、行単位ではなく生バイトを読んで判定する。
使い方: python3 jdb_drive.py <seconds>
出力: /tmp/jdb_hits.txt
"""
import os
import select
import subprocess
import sys
import time

SECONDS = float(sys.argv[1]) if len(sys.argv) > 1 else 120
OUT = "/tmp/jdb_hits.txt"

BREAKPOINTS = [
    "net.minecraft.server.level.ServerPlayerGameMode.setGameModeForPlayer",
    "net.minecraft.server.level.ServerPlayer.setGameMode",
    "net.minecraft.server.level.ServerPlayerGameMode.changeGameModeForPlayer",
]


def main() -> int:
    proc = subprocess.Popen(
        ["/tmp/jdk21/bin/jdb", "-attach", "127.0.0.1:5005"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        bufsize=0)
    fd = proc.stdout.fileno()
    hits = open(OUT, "w", encoding="utf-8")
    deadline = time.time() + SECONDS
    set_count = 0
    started = False

    def send(cmd):
        proc.stdin.write((cmd + "\n").encode())
        proc.stdin.flush()

    try:
        while time.time() < deadline:
            r, _, _ = select.select([fd], [], [], 0.4)
            text = ""
            if r:
                chunk = os.read(fd, 65536)
                if not chunk:
                    break
                text = chunk.decode("utf-8", "replace")
            if text and not started and ">" in text:
                if set_count < len(BREAKPOINTS):
                    send("stop in " + BREAKPOINTS[set_count])
                    print("[jdb] set breakpoint " + BREAKPOINTS[set_count], flush=True)
                    set_count += 1
                    if set_count == len(BREAKPOINTS):
                        send("cont")
                        print("[jdb] cont (running)", flush=True)
                        started = True
            if "Breakpoint hit" in text:
                print("[jdb] HIT", flush=True)
                send("where")
                time.sleep(0.8)
                stack = []
                stop_at = time.time() + 3
                while time.time() < stop_at:
                    rr, _, _ = select.select([fd], [], [], 0.3)
                    if not rr:
                        continue
                    out = os.read(fd, 65536).decode("utf-8", "replace")
                    stack.append(out)
                    if "> " in out:
                        break
                hits.write("==== hit @ %s ====\n" % time.strftime("%H:%M:%S"))
                hits.write("".join(stack)[:6000] + "\n")
                hits.flush()
                send("cont")
                time.sleep(0.3)
    finally:
        try:
            send("quit")
        except Exception:
            pass
        hits.close()
        proc.terminate()
        print("hits -> " + OUT, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
