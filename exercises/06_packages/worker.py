"""Exercise 06 — パッケージを使う Worker。

pure Python の軽いパッケージ（humanize, python-slugify）を
pyproject.toml の dependencies に足して、Worker から import する。

`uv run pywrangler dev` で起動して `curl http://localhost:8787/` を叩くと、
人間向け表記と slug 変換の結果を JSON で返す。

注意: このファイルは Workers 上でのみ動く。通常の CPython では
`workers` が無いので実行できない。パッケージの挙動だけを手元で確かめたい
場合は `packages_demo.py` を使う（座学用）。
"""

from workers import Response, WorkerEntrypoint


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        # 遅延 import: トップレベルで重い初期化をしない（Exercise 04 参照）。
        from humanize import intcomma, naturalsize
        from slugify import slugify

        sample_numbers = [1_234_567, 10**9, 1_500_000_000]
        sample_titles = [
            "Hello, Cloudflare Workers!",
            "Python で書く Workers 入門",
        ]

        return Response.json(
            {
                "intcomma": {
                    str(n): intcomma(n) for n in sample_numbers
                },
                "naturalsize": {
                    str(n): naturalsize(n) for n in sample_numbers
                },
                "slugify": {
                    title: slugify(title, allow_unicode=True)
                    for title in sample_titles
                },
                "note": (
                    "依存は pyproject.toml に書く。デプロイ時に Worker バンドルへ"
                    "自動でバンドルされる。pure Python か PyEmscripten ホイールが条件。"
                ),
            }
        )
