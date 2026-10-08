#!/usr/bin/env python3
"""Tiny RCON client for driving the Paper smoke test from scripts.

Usage: python3 rcon.py "command" ["command" ...]
Env: RCON_HOST (127.0.0.1), RCON_PORT (25575), RCON_PASSWORD (arena-rcon)
"""
import os
import socket
import struct
import sys

HOST = os.environ.get("RCON_HOST", "127.0.0.1")
PORT = int(os.environ.get("RCON_PORT", "25575"))
PASSWORD = os.environ.get("RCON_PASSWORD", "arena-rcon")


class Rcon:
    def __init__(self, host=HOST, port=PORT, password=PASSWORD):
        self.sock = socket.create_connection((host, port), timeout=10)
        self.rid = 0
        self._send(3, password)
        rid, _type, _body = self._recv()
        if rid == -1:
            raise SystemExit("rcon auth failed")

    def _send(self, ptype, body):
        self.rid += 1
        payload = struct.pack("<ii", self.rid, ptype) + body.encode("utf-8") + b"\x00\x00"
        self.sock.sendall(struct.pack("<i", len(payload)) + payload)

    def _recv(self):
        raw = self._read_exact(4)
        (length,) = struct.unpack("<i", raw)
        payload = self._read_exact(length)
        rid, ptype = struct.unpack("<ii", payload[:8])
        return rid, ptype, payload[8:-2].decode("utf-8", "replace")

    def _read_exact(self, n):
        buf = b""
        while len(buf) < n:
            chunk = self.sock.recv(n - len(buf))
            if not chunk:
                raise SystemExit("rcon connection closed")
            buf += chunk
        return buf

    def run(self, command):
        self._send(2, command)
        return self._recv()[2]

    def close(self):
        self.sock.close()


if __name__ == "__main__":
    rcon = Rcon()
    for cmd in sys.argv[1:]:
        out = rcon.run(cmd)
        print(f"$ {cmd}\n{out}")
    rcon.close()
