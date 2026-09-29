# Exercise 02: JSON と env

前回は `await request.json()` で**読み**をした。今回は**返し**を構造化し、
あわせて**環境変数・secret・binding** を扱う。

## その1: `Response.json()`

辞書を返したいだけなら、自分で `json.dumps` して文字列にする必要はない。

```python
return Response.json({"message": "Hello", "status": "ok"})
```

`Response.json()` が `Content-Type: application/json` を付けてくれる。
（公式 Basics より）

```python
data = {"message": "Hello", "status": "ok"}
return Response.json(data)
```

## その2: `self.env`

`env` は `WorkerEntrypoint` の属性。
環境変数・secret・各種 binding（KV/D1/R2 など）はすべてここから見える。

```python
class Default(WorkerEntrypoint):
    async def fetch(self, request):
        return Response.json({"api_host": self.env.API_HOST})
```

`vars` に書いた環境変数は `wrangler.jsonc` で設定する:

```jsonc
{
  "name": "hello-cloudflare-py-02",
  "main": "src/entry.py",
  "compatibility_date": "2026-09-29",
  "compatibility_flags": ["python_workers"],
  "vars": {
    "API_HOST": "example.com",
    "GREETING": "こんにちは"
  }
}
```

### vars と secret の違い

| | 置き場所 | 用途 |
|---|---|---|
| `vars` | `wrangler.jsonc` に平文 | 公開してよい設定値（ホスト名、しきい値など） |
| secret | `wrangler secret put NAME` | トークン・鍵。**リポジトリに書かない** |

どちらも Python 側では `self.env.NAME` で同じように見える。

## この回の Worker

`env` を読みつつ、入力に応じて JSON を返す:

```python
class Default(WorkerEntrypoint):
    async def fetch(self, request):
        host = self.env.API_HOST          # vars から
        greeting = self.env.GREETING      # vars から
        return Response.json({
            "greeting": greeting,
            "api_host": host,
            "status": "ok",
        })
```

### ローカルでの secret

`pywrangler dev` 実行中は secret の扱いが本番と少し違う。
ローカルで secret を試すときは `.dev.vars` ファイルに書く流儀が一般的だが、
**本番の `wrangler secret put` とは別物**である点に注意。

```bash
# 本番用（デプロイ対象）
npx wrangler secret put API_TOKEN

# ローカル開発用（.dev.vars、git 管理しない）
# API_TOKEN=local-test-value
```

このリポジトリでは secret を扱わない。env の読み方を覚えるのが目的。

## 動かす

```bash
cd exercises/02_json_env
uv run pywrangler dev
# 別ターミナルで:
curl http://localhost:8787
# => {"greeting": "こんにちは", "api_host": "example.com", "status": "ok"}
```

## つまずきやすい点

- **`vars` の値は必ず文字列** … 数値を書いて `int` を期待すると面食らう。Python 側で変換する
- **secret を `wrangler.jsonc` に書く** … 漏洩する。secret は jsonc に書かない
- **`env` を `request` から取ろうとする** … `env` は `self` 側の属性

## 出典

- <https://developers.cloudflare.com/workers/languages/python/basics/>
- <https://developers.cloudflare.com/workers/configuration/environment-variables/>
- <https://developers.cloudflare.com/workers/configuration/secrets/>
- <https://developers.cloudflare.com/workers/runtime-apis/bindings/>
