"""Exercise 03: ルーティングとエラー

- `request.method` と URL のパスで `fetch` 内を分岐する。
- ステータスコードを明示する（400 / 404 / 405 / 500）。
- 例外を握って統制された JSON エラーに変換する。

URL のパス取り出しには標準ライブラリ urllib.parse を使う
（Workers の Python でも使える）。

動かすには:
    cd exercises/03_routing
    uv run pywrangler dev
    # 別ターミナルで README の curl 例を順に叩く
"""

from urllib.parse import urlsplit

from workers import Response, WorkerEntrypoint


async def handle_root(request):
    """GET / — 疎通確認。"""
    return Response.json({"message": "index"})


async def handle_hello(request):
    """GET /hello — 小さい固定応答。"""
    return Response.json({"message": "hello"})


async def handle_echo(request):
    """POST /echo — 受け取った JSON をそのまま返す。不正入力は 400。"""
    if request.method != "POST":
        # パスは存在するがメソッドが違う => 405
        return Response.json(
            {"error": "method not allowed"}, status=405
        )
    try:
        body = await request.json()
    except Exception:
        # 本文が JSON でない / Content-Type が無い。
        return Response.json({"error": "invalid json"}, status=400)
    return Response.json({"echo": body})


# パス -> ハンドラの対応表。末尾スラッシュは rstrip で正規化する。
ROUTES = {
    "/": handle_root,
    "/hello": handle_hello,
    "/echo": handle_echo,
}


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        try:
            path = urlsplit(request.url).path
            # "/" は rstrip すると "" になるので戻す。
            normalized = path.rstrip("/") or "/"
            handler = ROUTES.get(normalized)
            if handler is None:
                return Response.json({"error": "not found"}, status=404)
            return await handler(request)
        except Exception:
            # 内部情報は本文に出さない。詳細は runtime 側のログで見る。
            return Response.json({"error": "internal error"}, status=500)
