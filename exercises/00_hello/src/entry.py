"""Exercise 00: 最小の Worker

これは「4 行の Worker」そのもの。ローカルでは CPython で走らせられない
（`workers` モジュールは Workers runtime が提供する）ので、
このファイルは runtime に配る実際のエントリであり、
同時に `make check` の構文検査対象でもある。

動かすには:
    cd exercises/00_hello
    uv run pywrangler dev
    # 別ターミナルで: curl http://localhost:8787   => Hello World!
"""

from workers import Response, WorkerEntrypoint


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        return Response("Hello World!")
