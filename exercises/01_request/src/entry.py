"""Exercise 01: リクエストを読む

POST された JSON を読み、名前を差し込んだ挨拶を返す。

- `request` は FFI 経由で見えている JS の Request。
- `await request.json()` で本文を辞書にパースする（await 必須）。
- `request.method` で GET / POST を分岐する。

動かすには:
    cd exercises/01_request
    uv run pywrangler dev
    # 別ターミナルで:
    curl -X POST -H "Content-Type: application/json" \
      -d '{"name": "Python"}' http://localhost:8787   => Hello, Python!
"""

from workers import Response, WorkerEntrypoint


def greeting(name: str) -> str:
    """名前から挨拶文を組み立てる純粋関数。"""
    return "Hello, " + name + "!"


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        # GET は人間向けの案内を返す。
        if request.method != "POST":
            return Response(
                'POST で {"name": "..."} を送ってください\n',
                status=405,
            )

        # 本文は JS の Request 側にある。await で Python の dict になる。
        body = await request.json()
        name = body.get("name", "World")
        return Response(greeting(name))
