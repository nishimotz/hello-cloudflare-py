"""Exercise 02: JSON と env

- `Response.json(dict)` で Content-Type 付きの JSON を返す。
- `self.env` で vars / secret / binding を読む。

`vars` は wrangler.jsonc に、secret は `wrangler secret put` に置く。
どちらも Python 側では `self.env.NAME` で見える。

動かすには:
    cd exercises/02_json_env
    uv run pywrangler dev
    # 別ターミナルで: curl http://localhost:8787
"""

from workers import Response, WorkerEntrypoint


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        # self.env は vars / secret / binding の入口。
        # vars の値は文字列で入ってくる点に注意。
        greeting = self.env.GREETING
        host = self.env.API_HOST

        return Response.json(
            {
                "greeting": greeting,
                "api_host": host,
                "status": "ok",
            }
        )
