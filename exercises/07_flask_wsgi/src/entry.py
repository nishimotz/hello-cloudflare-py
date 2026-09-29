"""Exercise 07 — Flask + Jinja2 を Workers に載せる。

Flask は WSGI アプリ。`workers.wsgi.entrypoint(app)` が WSGI ブリッジとして
包んでくれるので、Flask 側はほぼ無修正で載る。

実行（このディレクトリで）:
    uv run pywrangler dev
別ターミナルで:
    curl http://localhost:8787/
"""

from flask import Flask, redirect, render_template_string, request
from workers.wsgi import entrypoint

app = Flask(__name__)

PAGE = """<!doctype html>
<html><head><title>{{ title }}</title></head>
<body>
<h1>Hello {{ name }}</h1>
<p>path={{ request.path }}</p>
<p>method={{ request.method }}</p>
<p>q={{ request.args.get('q', '-') }}</p>
<p>form={{ form_value }}</p>
</body></html>"""


@app.route("/")
def index():
    return render_template_string(
        PAGE, title="Flask on Workers", name="Workers", form_value="-"
    )


@app.route("/hello/<name>")
def hello(name):
    return render_template_string(PAGE, title="Hello", name=name, form_value="-")


@app.route("/post", methods=["GET", "POST"])
def post_demo():
    val = request.form.get("x", "-") if request.method == "POST" else "-"
    return render_template_string(
        PAGE, title="POST", name="form-test", form_value=val
    )


@app.route("/json")
def json_route():
    return {"ok": True, "route": "json", "items": [1, 2, 3]}


@app.route("/go")
def go():
    return redirect("/hello/redirected")


@app.route("/teapot")
def teapot():
    return "I am a teapot", 418


@app.errorhandler(404)
def not_found(e):
    return "custom 404", 404


# Flask アプリをそのまま Worker のエントリポイントに変換する。
Default = entrypoint(app)
