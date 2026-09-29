"""Exercise 04 — WASM / Pyodide の仕組みを確認するデモ。

このファイルは2つの役割を持つ:

1. 手元の普通の CPython として実行できる「座学の確認問題」を出す。
   実行環境（CPython / Pyodide）の違いを、観察可能な事実として並べる。
   `python exercises/04_wasm/wasm_demo.py` で動く。

2. Cloudflare Workers 上で同じ観察を行うための WorkerEntrypoint。
   JS の Request を FFI 経由で読み、Pyodide/WASM の情報を JSON で返す。
   `uv run pywrangler dev` で起動して GET / を叩くと確認できる。
   （このファイルを Worker として起動した検証は未実施。同じ観察は
   `worker.py` で行っており、実測は README の「実測記録」にある）

実行モデルやデプロイ時のスナップショットの説明は README.md を読むこと。
"""

from __future__ import annotations

import platform
import sys


def collect_facts() -> dict[str, object]:
    """実行環境について、CPython / Pyodide の両方で取れる客観的事実を集める。"""
    return {
        "python_version": platform.python_version(),
        "implementation": platform.python_implementation(),
        "platform": sys.platform,
        "maxsize": sys.maxsize,
        "byteorder": sys.byteorder,
        # Pyodide 上では "emscripten" になる。CPython では OS 名。
        "uname_system": platform.uname().system,
        "uname_machine": platform.uname().machine,
        # Pyodide 判定: 公式には sys.platform == "emscripten" で判定する。
        "is_emscripten": sys.platform == "emscripten",
    }


def detect_wasm_limits() -> dict[str, str]:
    """WASM VM の制約を、import の可否として観察する。

    公式ドキュメントの区分（Exercise 05）に対応:
      - excluded          : import 不可（除外モジュール）
      - importable_but_dead: import はできるが機能しない
      - present_but_broken: import 不可（依存先が除外されている）
    """
    import importlib
    import importlib.util

    # import すると副作用があるものがあるので、find_spec で「見つかるか」を見る。
    observations: dict[str, str] = {}
    for name in (
        "curses",
        "fcntl",
        "tkinter",
        "venv",
        "multiprocessing",
        "threading",
        "pty",
        "tty",
    ):
        try:
            spec = importlib.util.find_spec(name)
        except (ImportError, ModuleNotFoundError) as exc:
            observations[name] = f"find_spec error: {type(exc).__name__}"
            continue
        observations[name] = "found" if spec else "not found"
    return observations


def main() -> None:
    print("=== Exercise 04: WASM / Pyodide の仕組み ===")
    print()

    facts = collect_facts()
    print("[1] 実行環境の事実")
    for key, value in facts.items():
        print(f"    {key:18} = {value}")
    print()

    if facts["is_emscripten"]:
        print("    => これは Pyodide (WASM) 上で動いている。")
    else:
        print("    => これは通常の CPython。Workers 上では sys.platform が")
        print("       'emscripten' になり、machine も WASM を示す値になる。")
    print()

    print("[2] WASM が制約するモジュールの観察")
    print("    (ローカル CPython の結果。Pyodide 上では not found / 除外になる)")
    for name, result in detect_wasm_limits().items():
        print(f"    {name:16} : {result}")
    print()

    print("[3] 結論")
    print("    - Workers の Python は CPython そのもの（Pyodide 経由）。")
    print("    - 走る土台は V8 isolate 内の WebAssembly。OS プロセスではない。")
    print("    - だから fork/スレッドが無く、FS はメモリ上だけになる。")
    print("    - 重い初期化はデプロイ時にスナップショットされる。")


if __name__ == "__main__":
    main()
