"""Standalone entry point for the frozen local backend, launched by the
desktop app as a child process on the user's own machine. Listens on
localhost only -- this is not a server meant to accept connections from
anywhere but the desktop UI running alongside it on the same PC.

Working directory must be the folder containing academicos-data/ (the
desktop app sets this when it spawns the process); Config.load() resolves
data_root relative to cwd.
"""
import sys

import uvicorn


def main() -> None:
    port = 8010
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    uvicorn.run("academicos.api.main:app", host="127.0.0.1", port=port, reload=False)


if __name__ == "__main__":
    main()
