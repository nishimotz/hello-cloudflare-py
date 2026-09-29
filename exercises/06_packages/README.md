# Exercise 06 — パッケージを使う

pure Python の軽いパッケージを `pyproject.toml` の dependencies に足して、
Worker から import する回。デプロイ時にパッケージがバンドルされることを
押さえる。

## 対応パッケージの条件

Python Workers で使えるのは次のいずれか（公式ドキュメント "Packages" より）:

1. **pure Python** パッケージ（PyPI）
2. **PyEmscripten ホイール**（[PEP 783](https://peps.python.org/pep-0783/)）が
   PyPI にあるパッケージ
3. **Pyodide 同梱**のパッケージ

C 拡張を含む通常のパッケージはそのままでは動かない。PyEmscripten ホイールが
無いパッケージが必要なら、メンテナに要望を出すか、Cloudflare の
[Python Packages Discussions](https://github.com/cloudflare/workerd/discussions/categories/python-packages)
で相談する。

**重要:** WASM 対応はまだ初期段階。使いたいパッケージが PyEmscripten
ホイールを持っているかは、PyPI で確認するまで断定できない。

## pyproject.toml に依存を書く

`pyproject.toml` の `dependencies` に書くと、デプロイ時に Worker バンドルへ
自動でバンドルされる。

```toml
[project]
name = "hello-cloudflare-py"
version = "0.1.0"
description = "Cloudflare Workers Python ハンズオン"
requires-python = ">=3.13"
dependencies = [
    "workers-runtime-sdk",
    "humanize",          # ← この回で足す pure Python パッケージ
    "python-slugify",    # ← もう一つの候補
]

[dependency-groups]
dev = [
    "workers-py",
]
```

`pywrangler` は wrangler のラッパーで、デプロイ時にパッケージをバンドルする
環境を整えてくれる。

- ローカル起動: `uv run pywrangler dev`
- デプロイ: `uv run pywrangler deploy`
- wrangler のコマンドは全部使える: `uv run pywrangler --help`

## この回の題材選び

**pure Python で依存が軽い**ものを選ぶ。理由:

- C 拡張が無いので PyEmscripten ホイールを待たなくてよい
- デプロイ時のバンドルが小さい
- 動作確認が速い

`humanize`（数値・サイズを人間向け表記に）と `python-slugify`
（文字列を slug に）はどちらも pure Python。ここでは `humanize` を使う。

## worker.py でやっていること

- `humanize` を import して、数値を人間向け表記に変換して返す
- `slugify` を使うエンドポイントも用意（同じ pyproject に足す場合）

```python
from humanize import intcomma, naturalsize
from workers import Response, WorkerEntrypoint


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        data = {
            "intcomma": intcomma(1234567),      # '1,234,567'
            "naturalsize": naturalsize(10**9),  # '1.0 GB'
        }
        return Response.json(data)
```

## 依存を足したあとの手順

```bash
# 1. pyproject.toml の dependencies に足す（この exercise の pyproject.toml 参照）
# 2. ロックを更新
uv lock
# 3. ローカル起動（pywrangler がバンドルして Pyodide 用に解決する）
uv run pywrangler dev
# 4. 叩く
curl http://localhost:8787/
```

## つまずきやすい点

- **依存を足したら `uv lock` を忘れない。** `pywrangler` はロックを見る。
- **C 拡張入りのパッケージは動かない。** import エラーになる。
  pure Python に置き換えるか、PyEmscripten ホイールの有無を確認する。
- **`workers-runtime-sdk` は型補完にも使う。** `dependencies` に入れておくと
  IDE で `env` などの型が効く。`uv run pywrangler types` で設定から型生成もできる。
- **バンドルサイズはコールドスタートに効く。** スナップショットに焼かれるので、
  重い依存は初期化コストに跳ねる。Exercise 04 の話とつながる。

## 実測記録（pywrangler dev + 実パッケージ）

この exercise は `uv run pywrangler dev` で実際に起動して検証済み。
環境: `pywrangler 1.17.4` / `wrangler 4.143.0` / Pyodide 3.14.2。
`pyproject.toml` に `humanize>=4` と `python-slugify>=8` を含め、
`uv lock` → `pywrangler dev` → `curl` で確認した。

本 exercise の `worker.py` (`GET /`) のレスポンス（実測）:

```json
{
  "intcomma": {"1234567": "1,234,567", "1000000000": "1,000,000,000"},
  "naturalsize": {"1234567": "1.2 MB", "1000000000": "1.0 GB"},
  "slugify": {"Hello, Cloudflare Workers!": "hello-cloudflare-workers"}
}
```

**pure Python パッケージ（humanize, python-slugify）は Worker 上で問題なく動いた。**
`uv lock` が `pylock.toml` を作り、`pywrangler` が `python_modules` と
`.venv-workers` にインストールしてバンドルする流れもログで確認できた。

### ローカル CPython での確認

同じパッケージを普通の CPython でも動かせる（`packages_demo.py`）。
ローカルと Worker で同じ出力になることを確認済み:

```
1,234,567  intcomma='1,234,567'  naturalsize='1.2 MB'
1,000,000,000  intcomma='1,000,000,000'  naturalsize='1.0 GB'
'Hello, Cloudflare Workers!' -> 'hello-cloudflare-workers'
```

## 出典

- <https://developers.cloudflare.com/workers/languages/python/packages/>
- <https://peps.python.org/pep-0783/>
- <https://pyodide.org/en/stable/usage/packages-in-pyodide.html>
