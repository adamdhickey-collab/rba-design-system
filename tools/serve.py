#!/usr/bin/env python3
"""Static dev server for this site. Identical to `python3 -m http.server` except
that it refuses to let anything be cached.

Why this exists rather than the one-liner it replaces: `http.server` sends a
`Last-Modified` and no `Cache-Control`, so browsers apply heuristic freshness and
hold on to `styles.css` and `app.js` without revalidating. On this project that
cost real time more than once — an edit lands, the page keeps running the old
script, and the stale behaviour gets debugged as if it were a live bug. It is the
worst kind of false signal, because the page looks like it is telling you the
truth.

`no-store` means the response is never written to the cache at all, so there is no
stale copy to serve and no revalidation to skip. Slower over the wire; the wire is
localhost.

    ./tools/serve.py [port]        # default 3477
"""

import functools
import http.server
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def send_header(self, keyword, value):
        # Drop the validator too. Without it there is nothing for a browser to make
        # a conditional request against, so it cannot decide a cached copy is good.
        if keyword.lower() == "last-modified":
            return
        super().send_header(keyword, value)

    def log_message(self, fmt, *args):
        # One line per request is noise at 1,490 icons; keep errors only.
        if args and str(args[1]).startswith(("4", "5")):
            super().log_message(fmt, *args)


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 3477
    handler = functools.partial(NoCacheHandler, directory=ROOT)
    http.server.ThreadingHTTPServer(("", port), handler).serve_forever()


if __name__ == "__main__":
    main()
