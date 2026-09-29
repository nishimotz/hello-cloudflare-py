# Exercise 03: ルーティングとエラー

これまでは「1 URL・1 応答」だった。実用の Worker は**パスとメソッドで分岐**し、
**エラーを適切なステータスで返す**。

## ルーティング = `fetch` 内の分岐

Workers では、Python 側の `fetch` の中で
`request.method` と URL のパスを見て自分で分岐する。

```python
from urllib.parse import urlsplit

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        url = urlsplit(request.url)
        path = url.path
        ...
```

- `request.url` … フル URL（文字列）
- 標準ライブラリ `urllib.parse` は Workers でも使える（Exercise 05 の stdlib 参照）
- パスを正規化したいときは `rstrip("/")` などで揃える

## ハンドラを分ける

分岐が増えたら、パスごとに関数を切る:

```python
async def handle_root(request):
    return Response.json({"message": "index"})

async def handle_hello(request):
    return Response.json({"message": "hello"})

ROUTES = {
    "/": handle_root,
    "/hello": handle_hello,
}
```

`fetch` はディスパッチャに徹する:

```python
async def fetch(self, request):
    url = urlsplit(request.url)
    handler = ROUTES.get(url.path.rstrip("/") or "/")
    if handler is None:
        return Response.json({"error": "not found"}, status=404)
    return await handler(request)
```

## ステータスコードとエラーの扱い

`Response(text, status=...)` でコードを制御する。

| 状況 | コード | 例 |
|------|--------|-----|
| 正常 | 200 | 通常応答 |
| 入力が不正 | 400 | JSON でない、必須キー欠落 |
| 未知のパス | 404 | ルートに無い |
| メソッド違い | 405 | `GET` 専用に `POST` |
| 想定外の例外 | 500 | ハンドラ内で捕捉できなかったもの |

### 例外を握って 500 にする

`fetch` の外まで例外が漏れると runtime が 500 を返すが、
**内容を統制したい**なら `fetch` 内で `try/except` する:

```python
async def fetch(self, request):
    try:
        url = urlsplit(request.url)
        handler = ROUTES.get(url.path.rstrip("/") or "/")
        if handler is None:
            return Response.json({"error": "not found"}, status=404)
        return await handler(request)
    except json.JSONDecodeError:
        return Response.json({"error": "invalid json"}, status=400)
    except Exception:
        # 詳細を外に出さない。ログは runtime 側で見る。
        return Response.json({"error": "internal error"}, status=500)
```

**注意（推測ではなく原則）**: 例外メッセージをそのまま返すと内部情報が漏れる。
外向けには汎用メッセージ、詳細はログに留める。

### JSON パースの失敗を 400 に

`await request.json()` は不正な本文で例外を投げる。これを 400 に変換する:

```python
async def handle_echo(request):
    try:
        body = await request.json()
    except Exception:
        return Response.json({"error": "invalid json"}, status=400)
    return Response.json({"echo": body})
```

## 動かす

```bash
cd exercises/03_routing
uv run pywrangler dev
# 別ターミナルで:
curl http://localhost:8787/                         # {"message": "index"}
curl http://localhost:8787/hello                    # {"message": "hello"}
curl -X POST http://localhost:8787/echo \
  -H "Content-Type: application/json" -d '{"a": 1}' # {"echo": {"a": 1}}
curl http://localhost:8787/nope                     # 404
curl -X POST http://localhost:8787/hello            # 405
curl -X POST http://localhost:8787/echo \
  -H "Content-Type: application/json" -d 'not json' # 400
```

## つまずきやすい点

- **`url.path` の末尾スラッシュ** … `/hello` と `/hello/` は別文字列。正規化を決めておく
- **405 と 404 の取り違え** … 「パスは存在するがメソッド違い」は 405
- **例外メッセージの垂れ流し** … 500 の本文に内部情報を入れない
- **`await handler(request)` の await 忘れ** … ハンドラが `async` なら await が要る

## 出典

- <https://developers.cloudflare.com/workers/runtime-apis/handlers/fetch>
- <https://developers.cloudflare.com/workers/runtime-apis/request>
- <https://developers.cloudflare.com/workers/runtime-apis/response>
