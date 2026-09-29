# Exercise 01: リクエストを読む（POST と FFI）

HTTP サーバの本質は「リクエストを読んで応答を返す」こと。
前回は固定文字列を返しただけ。今回は**入力を読む**。

## キモ: `request` は JS のオブジェクト

```python
body = await request.json()
```

`request` は Python のオブジェクトではなく、**JS の `Request`** が
FFI（foreign function interface）経由で Python に見えているもの。
だから:

- メソッドは JS 側の定義に従う（`json()`, `text()`, `formData()` など）
- `json()` は Promise を返すので **`await` が要る**

Python の `json.loads(request.body)` のような書き方はしない。
JS API をそのまま呼ぶのが Workers Python の流儀。

## この回の Worker

`src/entry.py`:

```python
from workers import Response, WorkerEntrypoint


def greeting(name):
    return "Hello, " + name + "!"


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        # GET は疎通確認用に固定応答
        if request.method != "POST":
            return Response("POST で {\"name": "..."} を送ってください\n", status=405)

        body = await request.json()
        name = body.get("name", "World")
        return Response(greeting(name))
```

ポイント:

- `request.method` で分岐できる（`"GET"`, `"POST"` …）
- `await request.json()` で本文を辞書にパース
- 不正入力に備えて `body.get("name", "World")` で既定値
- `Response(text, status=405)` でステータスコードも指定できる（詳しくは 03）

## 動かす

```bash
cd exercises/01_request
uv run pywrangler dev
# 別ターミナルで:
curl -X POST -H "Content-Type: application/json" \
  -d '{"name": "Python"}' http://localhost:8787
# => Hello, Python!
```

## なぜ `hello` を別モジュールに置けるのか

公式の Basics では `from hello import hello` のように複数ファイルに分割できる。
`pywrangler` はプロジェクト内のモジュールをまとめてバンドルするため、
自分でパスを通す必要はない。

ここでは 1 ファイルに収めているが、分割してもよい。

## つまずきやすい点

- **`await` 忘れ** … `request.json()` は Promise。await しないと JSON にならない
- **Content-Type が無い POST** … `json()` が失敗する。curl では `-H` を忘れずに
- **本文を Python の `io` で読もうとする** … 実際のリクエストボディは JS 側にある

## 出典

- <https://developers.cloudflare.com/workers/languages/python/basics/>
- <https://developers.cloudflare.com/workers/languages/python/ffi/>
- <https://developers.cloudflare.com/workers/runtime-apis/request>
