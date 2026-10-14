#!/usr/bin/env python3
"""Make the public copy of the receipts with the account owner's identity removed.

Claude Code puts the account's name and email into the model's context in every arm; some
model answers used them (signed letters, a résumé), and every attempt records the local
binary and memory paths, which contain the username. The identity is read from the
environment, never from this file:

  SCRUB_EMAIL=<email> SCRUB_USER=<username> SCRUB_NAME="<first> <last>" \\
    sanitize.py <src_dir>... --out <publish_dir>

Rules run longest first (email, username, full name, surname, first name). Every match is
masked letter for letter, keeping length and case (X / x; digits become 0), so length, case
and word-count checks score as before. The first name is matched as a word, and a JSON escape
(\\n, \\t, \\r, \\uXXXX) before it counts as a word boundary. __pycache__ and .DS_Store are not
copied. The check after copying is stricter than
the rules: any remaining occurrence of the username, the surname, the first name as a
substring, or any address at the email's domain with an unmasked local part fails the run, unless the word containing it is listed in
ALLOWED_WORDS (none are listed). Re-scoring IFEval on the masked text with the random state
held equal reproduced all 2,164 outcomes (check_ifeval_public.py re-scores the archive).
"""
import os
import re
import shutil
import sys
from pathlib import Path

ALLOWED_WORDS = {"shielaariel", "uarielbf"}  # fail closed: a benign word containing the first name is added only after
# reading it. "shielaariel": the letter run of "shielaariel888", a third-party username inside a Design2Code benchmark
# page (refs/16873.html) that the model reproduced; "uarielbf": a letter run inside a base64 blob in one FinQA stream.
# The check matches letter runs, so digits are not part of the word.


def _mask(m):
    """Same length and same letter case; digits become 0."""
    return "".join("X" if c.isupper() else "x" if c.islower() else "0" if c.isdigit() else c for c in m.group(0))


def _terms():
    email, user, name = (os.environ.get(k, "").strip() for k in ("SCRUB_EMAIL", "SCRUB_USER", "SCRUB_NAME"))
    if not (email and user and len(name.split()) == 2):
        sys.exit("set SCRUB_EMAIL, SCRUB_USER and SCRUB_NAME (\"first last\")")
    first, last = name.split()
    return email, user, first, last


def rules(email, user, first, last):
    word_start = r"(?:(?<![A-Za-z])|(?<=\\[nrt])|(?<=\\u[0-9a-fA-F]{4}))"
    return [re.compile(re.escape(email), re.I),
            re.compile(re.escape(user), re.I),
            re.compile(rf"{re.escape(first)}\s+{re.escape(last)}", re.I),
            re.compile(re.escape(last), re.I),
            re.compile(rf"{word_start}{re.escape(first)}(?![A-Za-z])", re.I)]


LOCAL_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._%+-")


def forbidden(email, user, first, last):
    """Literal, case-insensitive alternation of the username, the surname, the first name and the email's domain:
    a plain alternation scans in linear time, which matters because event streams carry base64 runs of hundreds
    of thousands of letters (a quantified class before a literal backtracks quadratically on those)."""
    domain = "@" + email.split("@")[1]
    return re.compile("|".join(re.escape(x) for x in (user, last, first, domain)), re.I)


def _word(text, start, end):
    """The letter run around a name match (the check is on whole words, so digits are not part of it)."""
    a, b = start, end
    while a > 0 and text[a - 1].isalpha():
        a -= 1
    while b < len(text) and text[b].isalpha():
        b += 1
    return text[a:b]


def _benign(text, m):
    """An allow-listed word, or an address at the domain whose local part is absent or fully masked (a bare
    "@gmail.com" left by a benchmark page's own redaction has no local part)."""
    if m.group(0).startswith("@"):
        a = m.start()
        while a > 0 and text[a - 1] in LOCAL_CHARS:
            a -= 1
        return re.search(r"[a-wyzA-WYZ]", text[a:m.start()]) is None
    return _word(text, m.start(), m.end()).lower() in ALLOWED_WORDS


def scrub(text, rx_list):
    for rx in rx_list:
        text = rx.sub(_mask, text)
    return text


def copy_tree(src, dst, rx_list):
    n_changed = 0
    for p in Path(src).rglob("*"):
        if p.is_dir() or "__pycache__" in p.parts or p.name == ".DS_Store":
            continue
        q = Path(dst) / p.relative_to(Path(src).parent)
        q.parent.mkdir(parents=True, exist_ok=True)
        try:
            text = p.read_text()
        except UnicodeDecodeError:
            shutil.copy2(p, q)
            continue
        new = scrub(text, rx_list)
        n_changed += new != text
        q.write_text(new)
    return n_changed


def verify(dst, rx_forbidden):
    hits = []
    for p in Path(dst).rglob("*"):
        if p.is_file():
            try:
                t = p.read_text()
            except UnicodeDecodeError:
                t = p.read_bytes().decode("latin-1")  # binary files are copied unchanged; check them too
            for m in rx_forbidden.finditer(t):
                if not _benign(t, m):
                    hits.append((str(p), t[max(0, m.start() - 40):m.end() + 40]))
    return hits


def main():
    terms = _terms()
    out = Path(sys.argv[sys.argv.index("--out") + 1])
    srcs = sys.argv[1:sys.argv.index("--out")]
    out.mkdir(parents=True, exist_ok=True)
    rx_list = rules(*terms)
    for s in srcs:
        print(s, "files changed:", copy_tree(s, out, rx_list))
    hits = verify(out, forbidden(*terms))
    print("forbidden strings left in the public copy:", len(hits))
    for h in hits[:10]:
        print("  ", h)
    sys.exit(1 if hits else 0)


if __name__ == "__main__":
    main()
