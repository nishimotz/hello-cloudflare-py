"""Exercise 04 — Cloudflare Workers 上で動かす版（Pyodide/WASM の観察）。

`uv run pywrangler dev` で起動し、`curl http://localhost:8787/` を叩くと、
Worker が動いている Pyodide/WASM 環境の情報を JSON で返す。

注意: このファイルは Workers 上でのみ import できる `workers` を
トップレベルで import する。通常の CPython では実行できない
（Exercise 04 の座学用デモは wasm_demo.py の方）。
"""

from workers import Response, WorkerEntrypoint

import platform
import sys


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        """実行環境の事実を JSON で返す。

        - sys.platform は Pyodide 上で "emscripten" になる
        - platform.machine() も WASM を示す値になる
        - 除外モジュールは import できないので find_spec で観察する
        """
        import importlib.util

        def probe(name: str) -> str:
            try:
                spec = importlib.util.find_spec(name)
            except (ImportError, ModuleNotFoundError) as exc:
                return f"error:{type(exc).__name__}"
            return "found" if spec else "not_found"

        excluded_probe = {
            name: probe(name)
            for name in ("curses", "fcntl", "tkinter", "venv", "dbm", "pwd")
        }
        limited_probe = {
            name: probe(name) for name in ("multiprocessing", "threading")
        }
        broken_probe = {name: probe(name) for name in ("pty", "tty")}

        # インメモリ FS の実験: 書く→読む。isolate が生きている間だけ有効。
        fs_result: str
        try:
            with open("/tmp/_cfpy_probe.txt", "w") as f:
                f.write("hello")
            with open("/tmp/_cfpy_probe.txt") as f:
                fs_result = f"read_back={f.read()!r}"
        except OSError as exc:
            fs_result = f"OSError:{exc}"

        return Response.json(
            {
                "python_version": platform.python_version(),
                "implementation": platform.python_implementation(),
                "sys_platform": sys.platform,
                "machine": platform.machine(),
                "is_emscripten": sys.platform == "emscripten",
                "maxsize": sys.maxsize,
                "probe_excluded": excluded_probe,
                "probe_limited": limited_probe,
                "probe_broken": broken_probe,
                "in_memory_fs": fs_result,
                "note": "isolate が破棄されると in_memory_fs の内容は消える。",
            }
        )
