# Exercise 00: 最小の Worker（Hello World）

**この回の結論は1行だけ。** 4 行の Python が HTTP サーバになる。

```python
from workers import WorkerEntrypoint, Response

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        return Response("Hello World!")
```

## なぜこの4行で動くのか

| 要素 | 役割 |
|------|------|
| `workers` モジュール | Workers runtime が提供する Python SDK。`WorkerEntrypoint` と `Response` が入る |
| `class Default(WorkerEntrypoint)` | runtime が探す**エントリクラス**。名前は `Default` でなければならない |
| `async def fetch(self, request)` | HTTP リクエストごとに呼ばれるハンドラ。`request` は JS の `Request`（FFI 経由） |
| `return Response("Hello World!")` | JS の `Response` を Python から構築して返す |

`import` の解決、Pyodide の注入、isolate の作成は runtime 側がやる。
こちらは「クラスを1つ書く」だけでよい。仕組みは Exercise 04 で扱う。

## 4行では足りない部分

実際に動かすには、コードの外に**設定**が要る。`wrangler.jsonc`:

```jsonc
{
  "name": "hello-cloudflare-py-00",
  "main": "src/entry.py",
  "compatibility_date": "2026-09-29",
  "compatibility_flags": ["python_workers"]   // ← これが無いと動かない
}
```

- `main` … エントリファイルの場所
- `compatibility_date` … runtime の振る舞いを固定する日付
- `compatibility_flags` … `python_workers` は**必須**

## 動かす

```bash
cd exercises/00_hello
uv run pywrangler dev          # ローカル開発サーバ（既定 http://localhost:8787）
# 別ターミナルで:
curl http://localhost:8787
# => Hello World!
```

`dev` は `sync`（依存の vendor 化）を自動で先に走らせてから wrangler に委譲する。

## このリポジトリでの検証方針

この教材は `make check` で **Python 構文の検査**をする。
`workers` モジュールは runtime が提供し、ローカルの venv には入っていないため、
`py_compile` は構文だけを見る（import の可否は見ない）。

`pywrangler dev` を実際に起動できる環境では、上記の `curl` まで通ること。

## つまずきやすい点

- **`python_workers` フラグ忘れ** … 起動時に Python として解釈されない。最頻出
- **`compatibility_date` を書かない** … 警告が出て挙動が不定になる。今日の日付を入れる
- **`fetch` を `async` にしない** … runtime は await 可能な戻り値を期待する
- **クラス名を `Default` 以外にする** … エントリとして拾われない

## 出典

- <https://developers.cloudflare.com/workers/languages/python/>
- <https://developers.cloudflare.com/workers/languages/python/basics/>
