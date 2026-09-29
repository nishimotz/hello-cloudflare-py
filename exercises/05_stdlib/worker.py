"""Exercise 05 — 標準ライブラリの制約を Cloudflare Workers 上で観察する。

`uv run pywrangler dev` で起動して以下を叩く:

  GET /           除外/限定/壊れているモジュールの観察結果を JSON で返す
  GET /fs         /tmp にファイルを書いて読む（エフェメラル FS の実験）
  GET /fs/count   リクエストをまたいで残るかを見るための連番カウンタ
  GET /threading  threading が機能しないことを確認する

注意: このファイルは Workers 上でのみ動く。通常の CPython では
`workers` が無いので実行できない（座学は README.md を読む）。
"""

from workers import Response, WorkerEntrypoint

import importlib.util


EXCLUDED = (
    "curses", "dbm", "ensurepip", "fcntl", "grp", "idlelib", "lib2to3",
    "msvcrt", "pwd", "resource", "syslog", "termios", "tkinter",
    "turtle", "turtledemo", "venv", "winreg", "winsound",
)
LIMITED = ("multiprocessing", "threading")
BROKEN_BY_DEPENDENCY = ("pty", "tty")

PROBE_PATH = "/tmp/_cfpy_counter.txt"


def _probe(name: str) -> str:
    """import せずに「見つかるか」だけを見る。副作用を避ける。"""
    try:
        spec = importlib.util.find_spec(name)
    except (ImportError, ModuleNotFoundError) as exc:
        return f"error:{type(exc).__name__}"
    return "found" if spec else "not_found"


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        # pathlib で URL を安全に読む（FFI 経由の JS URL を使う）。
        path = "/"
        try:
            url = request.url
            # クエリを除いたパスだけを取り出す。
            without_query = url.split("?", 1)[0]
            # "https://host/path" -> "/path"
            after_scheme = without_query.split("//", 1)[-1]
            slash = after_scheme.find("/")
            path = after_scheme[slash:] if slash != -1 else "/"
        except Exception:  # noqa: BLE001 - パース失敗時はルート扱い
            path = "/"

        if path == "/fs":
            return self._fs_experiment()
        if path == "/fs/count":
            return self._fs_counter()
        if path == "/threading":
            return self._threading_probe()
        return self._stdlib_report()

    def _stdlib_report(self):
        return Response.json(
            {
                "excluded": {n: _probe(n) for n in EXCLUDED},
                "limited_importable": {n: _probe(n) for n in LIMITED},
                "broken_by_dependency": {n: _probe(n) for n in BROKEN_BY_DEPENDENCY},
                "note": (
                    "excluded は not_found になる想定。"
                    "limited_importable は found だが機能しない。"
                    "broken_by_dependency は termios 依存で import 不可。"
                ),
            }
        )

    def _fs_experiment(self):
        """書いて読み返す。isolate が生きている間だけ有効。"""
        try:
            with open(PROBE_PATH, "w") as f:
                f.write("hello from exercise 05")
            with open(PROBE_PATH) as f:
                read_back = f.read()
        except OSError as exc:
            return Response.json({"ok": False, "error": f"OSError:{exc}"})
        return Response.json(
            {
                "ok": True,
                "read_back": read_back,
                "note": "isolate が破棄されるとこの内容は消える。永続化には使えない。",
            }
        )

    def _fs_counter(self):
        """リクエストをまたいでファイルが残るかを見る。"""
        try:
            if importlib.util.find_spec("os") is not None:
                pass
            try:
                with open(PROBE_PATH) as f:
                    prev = int(f.read().strip() or "0")
            except (OSError, ValueError):
                prev = 0
            current = prev + 1
            with open(PROBE_PATH, "w") as f:
                f.write(str(current))
        except OSError as exc:
            return Response.json({"ok": False, "error": f"OSError:{exc}"})
        return Response.json(
            {
                "count": current,
                "note": (
                    "同じ isolate が使い回されれば増えるが、"
                    "isolate はいつ破棄されてもおかしくない。増加を永続と誤解しない。"
                ),
            }
        )

    def _threading_probe(self):
        """threading が import できても「機能しない」ことを示す。

        本物のスレッドが無いので、ここでは import の成否と、
        threading の API が持つオブジェクトの存在だけを返す。
        実際の並行実行の可否は環境依存であり、断定しない。
        """
        import threading as _threading

        return Response.json(
            {
                "imported": True,
                "current_thread": _threading.current_thread().name,
                "has_Thread": hasattr(_threading, "Thread"),
                "note": (
                    "import はできるが WASM VM の制約で本物の並行実行はできない。"
                    "並行が要るなら asyncio か Cloudflare の非同期機構を使う。"
                ),
            }
        )
