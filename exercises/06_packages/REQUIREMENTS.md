# Exercise 06 用の依存（この exercise 単体で試すとき用）

本体の Worker はリポジトリ root の `pyproject.toml` に依存を書く。
このファイルは「Exercise 06 のパッケージ挙動を手元 CPython で確かめる」
ためのメモ。

## 使うパッケージ

| パッケージ | 種別 | 用途 |
|---|---|---|
| `humanize` | pure Python | 数値・サイズの人間向け表記 |
| `python-slugify` | pure Python | 文字列 → slug |

## root pyproject.toml に足す行

```toml
dependencies = [
    "workers-runtime-sdk",
    "humanize>=4",
    "python-slugify>=8",
]
```

## 手元で動かす

```bash
uv lock
uv sync
uv run python exercises/06_packages/packages_demo.py
```

## Workers 上で動かす

```bash
uv run pywrangler dev
curl http://localhost:8787/
```

## 注意

- C 拡張を含むパッケージは PyEmscripten ホイールが無い限り動かない。
- 依存を足したら `uv lock` を忘れない（`pywrangler` はロックを見る）。
