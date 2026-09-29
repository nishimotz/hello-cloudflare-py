# Exercise 07: Flask + Jinja2 を Workers に載せる

**結論:** Flask アプリは `workers.wsgi.entrypoint(app)` の**1行**で Worker に載る。
テンプレートは `render_template_string` に寄せれば、Flask 側の書き換えはほぼ無い。

Flask は WSGI アプリで、Python Workers の `workers` SDK には **WSGI ブリッジが
同梱**されている。自前のグルーは書かなくてよい。

## なぜ載るのか

| 層 | 役割 |
|----|------|
| `workers.wsgi` | runtime 同梱の **WSGI ⇄ Workers fetch** ブリッジ。`wsgi.input` を async body から同期的に読ませる橋渡しまで実装 |
| Flask | 普通の WSGI アプリ。ルーティング・リクエストコンテキスト・レスポンス生成 |
| Jinja2 | Flask が使うテンプレートエンジン。pure Python なので WASM で動く |

Flask / Werkzeug / Jinja2 / MarkupSafe / itsdangerous / click / blinker は
**すべて pure Python**。C 拡張が無いので PyEmscripten ホイールを待たずに載る
（Exercise 06 の条件を満たす）。

## 依存を足す

`pyproject.toml` の `dependencies` に Flask を足す（Jinja2 は Flask の依存で入る）:

```toml
[project]
name = "hello-cloudflare-py"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = [
    "workers-runtime-sdk",
    "flask",
]

[dependency-groups]
dev = [
    "workers-py",
]
```

## 最小のエントリ

`exercises/07_flask_wsgi/src/entry.py` の骨格:

```python
from flask import Flask, render_template_string
from workers.wsgi import entrypoint   # ← SDK 同梱のブリッジ

app = Flask(__name__)

@app.route("/")
def index():
    return render_template_string("<h1>Hello {{ name }}</h1>", name="Workers")

# Flask アプリをそのまま Worker のエントリポイントに変換する
Default = entrypoint(app)
```

**ポイント:**

- `if __name__ == "__main__": app.run()` は**削除する**（runtime がリクエストを流す）
- `templates/` のファイルを読む `render_template` は、インメモリ FS に
  置く仕組みが別途要る。**まずは `render_template_string` に寄せる**のが最小修正
- `Default = entrypoint(app)` の1行が Worker としての入口になる

## 動かす

```bash
cd exercises/07_flask_wsgi
uv run pywrangler dev          # ローカル開発サーバ（既定 http://localhost:8787）
```

別ターミナルで:

```bash
curl http://localhost:8787/                     # テンプレート展開
curl http://localhost:8787/hello/Cloudflare     # URL 変数
curl "http://localhost:8787/?q=test"            # クエリ
curl -X POST -d "x=value" http://localhost:8787/post   # フォーム
curl http://localhost:8787/json                 # 辞書 → JSON
curl -i http://localhost:8787/go                # 302 redirect
curl -i http://localhost:8787/teapot            # 418
curl -i http://localhost:8787/nonexistent       # custom 404
```

## 実測記録

Flask 3.1.3 / Jinja2 3.1.6 / wrangler 4.143.0 / pywrangler 1.17.4 で
`uv run pywrangler dev` を起動して確認した。**8項目すべて期待どおり**:

| # | リクエスト | 結果 |
|---|---|---|
| 1 | `GET /` | 200、テンプレート展開（`Hello Workers`） |
| 2 | `GET /hello/Cloudflare` | 200、URL 変数が動的展開 |
| 3 | `GET /?q=test` | 200、`request.args` が読める |
| 4 | `POST /post` (form) | 200、**`request.form` が読める**（WSGI ブリッジの `wsgi.input` が機能） |
| 5 | `GET /json` | 200、辞書返しが JSON になる |
| 6 | `GET /go` | 302 + `Location: /hello/redirected` |
| 7 | `GET /teapot` | 418（ステータスコード透過） |
| 8 | `GET /nonexistent` | 404 + `custom 404`（errorhandler 動作） |

バンドル: **222 modules / 2,216 KiB**（Flask 一式 + WSGI ブリッジ）。
1リクエスト 5〜20ms。

## 制約（実測で残るもの）

- **スレッド不可・ブロッキング I/O 不可**（Exercise 04/05 の制約はそのまま）。
  WSGI は同期前提なので、ブロッキング処理を書くと詰まる
- **ファイルテンプレート**（`render_template`）は未検証。FS に `templates/` を
  置く仕組みが必要
- `request.files`（アップロード）、`flask.session`（クッキー）は未検証
- 長時間処理は不可（CPU/実行時間の上限）

## つまずきやすい点

- **`entrypoint` を忘れる** … `Flask` インスタンスだけでは Worker にならない
- **`app.run()` を残す** … runtime がリクエストを流すので不要。削除する
- **`render_template` を使う** … テンプレートファイルが無いので失敗する。
  `render_template_string` に寄せる
- **C 拡張入りの Flask 拡張**（DB ドライバ等）を足す … PyEmscripten ホイールが
  無いと動かない

## 出典

- <https://developers.cloudflare.com/workers/languages/python/>
- <https://developers.cloudflare.com/workers/languages/python/packages/>
