"""Exercise 06 — パッケージの挙動をローカル CPython で確認する座学用デモ。

Workers 上で動かす版は worker.py。こちらは same パッケージが手元で
どういう値を返すかを確認するためのもの（`pywrangler dev` 無しで動く）。

    uv run python exercises/06_packages/packages_demo.py

humanize / python-slugify が未インストールの場合は、その旨を表示して
終了する（この exercise の pyproject.toml を参照）。
"""

from __future__ import annotations


def main() -> None:
    print("=== Exercise 06: パッケージを使う ===")
    print()

    try:
        from humanize import intcomma, naturalsize
        from slugify import slugify
    except ImportError as exc:
        print(f"依存が未インストール: {exc}")
        print()
        print("インストールするには（リポジトリ root で）:")
        print("    uv lock && uv sync")
        print("または:")
        print("    uv pip install humanize python-slugify")
        return

    numbers = [1_234_567, 10**9, 1_500_000_000]
    print("[1] humanize")
    for n in numbers:
        comma = intcomma(n)
        size = naturalsize(n)
        print(f"    {n:>12,}  intcomma={comma!r:>12}  naturalsize={size!r}")

    print()
    print("[2] python-slugify")
    titles = [
        "Hello, Cloudflare Workers!",
        "Python で書く Workers 入門",
    ]
    for t in titles:
        print(f"    {t!r}")
        print(f"        -> {slugify(t, allow_unicode=True)!r}")

    print()
    print("[3] まとめ")
    print("    - pure Python パッケージは Workers でも動く（PyEmscripten 不要）。")
    print("    - pyproject.toml の dependencies に書けばデプロイ時にバンドルされる。")


if __name__ == "__main__":
    main()
