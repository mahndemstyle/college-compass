#!/usr/bin/env python3
"""Encrypt educators-src.html into educators.enc.json with a password.

The site is public, so the educator content is never committed in plain text.
Run this whenever you change the content or the password:

    python3 tools/encrypt_educators.py

Scheme (decrypted in index.html with the browser's Web Crypto API):
  PBKDF2-SHA256 -> 64 bytes: first 32 = encryption key, last 32 = MAC key.
  Keystream block i = HMAC-SHA256(enc_key, nonce || i as 4-byte big-endian).
  MAC = HMAC-SHA256(mac_key, salt || nonce || ciphertext).
"""
import base64
import getpass
import hashlib
import hmac
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "educators-src.html"
OUT = ROOT / "educators.enc.json"
ITERATIONS = 310_000


def main():
    if not SRC.exists():
        sys.exit(f"Missing {SRC.name}. Put the educator content there first.")
    password = getpass.getpass("New educator password: ")
    if not password:
        sys.exit("Password can't be empty.")
    if len(password) < 8:
        print("Warning: short passwords are easy to guess.")
    if getpass.getpass("Type it again: ") != password:
        sys.exit("Passwords didn't match.")

    plaintext = SRC.read_bytes()
    salt, nonce = os.urandom(16), os.urandom(16)
    keys = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS, 64)
    enc_key, mac_key = keys[:32], keys[32:]

    stream = b"".join(
        hmac.new(enc_key, nonce + i.to_bytes(4, "big"), hashlib.sha256).digest()
        for i in range((len(plaintext) + 31) // 32)
    )
    ciphertext = bytes(p ^ k for p, k in zip(plaintext, stream))
    mac = hmac.new(mac_key, salt + nonce + ciphertext, hashlib.sha256).digest()

    b64 = lambda b: base64.b64encode(b).decode()
    OUT.write_text(json.dumps({
        "iterations": ITERATIONS,
        "salt": b64(salt),
        "nonce": b64(nonce),
        "ciphertext": b64(ciphertext),
        "mac": b64(mac),
    }, indent=2) + "\n")
    print(f"Wrote {OUT.name}. Commit and push it to update the site.")


if __name__ == "__main__":
    main()
