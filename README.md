# hello-cloudflare-py

Cloudflare Workers を **Python で書く**ための日本語ハンズオン。

`hello-*` シリーズの一角。実行環境は **Pyodide**（CPython を WebAssembly に
コンパイルしたもの）で、コードは 100% Python。JS の Request / Response は
FFI（foreign function interface）経由でそのまま触れる。

## 動機

Workers はこれまで JS/TS のものだった。Python Workers が入ったことで、
Python の標準ライブラリとエコシステムをそのままエッジに持っていける。
FastAPI / Langchain / Pydantic などのパッケージも対象。

一方で「なぜ Python がエッジで動くのか」は自明ではない。
Pyodide・V8 isolate・デプロイ時のスナップショットという仕組みを押さえないと、
インメモリ FS やスレッド不可といった制約の理由が見えない。
この教材は**動かしながら仕組みまで踏み込む**。

## 構成

| Exercise | 内容 | 形式 |
|----------|------|------|
| `00_hello` | 最小の Worker。4 行の `fetch` | 実行 (`pywrangler dev`) |
| `01_request` | POST、`await request.json()`、FFI | 実行 |
| `02_json_env` | `Response.json()`、`env` で vars / secret / binding | 実行 |
| `03_routing` | `fetch` 内の分岐、ステータスコード、例外の扱い | 実行 |
| `04_wasm` | なぜ動くのか。CPython→WASM、V8 isolate、スナップショット、制約の理由 | 座学＋任意で実機 |
| `05_stdlib` | 標準ライブラリの使える / 使えない、インメモリ FS の実験 | 座学＋実験 |
| `06_packages` | `pyproject.toml` に依存を追加（pure Python パッケージ） | 実行 |
| `07_flask_wsgi` | Flask + Jinja2 を `workers.wsgi.entrypoint` で載せる | 実行 |

## クイックスタート

前提: **uv** と **Node.js** が入っていること（`pywrangler` の動作条件）。

```bash
# 開発依存（workers-py / ruff）を入れる
uv sync

# Exercise 00 をローカル起動
make dev-00
# 別ターミナルで:
curl http://localhost:8787      # => Hello World!
```

各 exercise の起動:

```bash
make dev-00   # 最小の Worker
make dev-01   # POST + FFI
make dev-02   # JSON + env
make dev-03   # ルーティング + エラー
make dev-04   # WASM / Pyodide（Worker 版）
make dev-05   # 標準ライブラリの制約
make dev-06   # パッケージ
```

CPython だけで動く座学デモ（pywrangler 不要）:

```bash
make demo-04  # WASM 環境の検出（この Mac の CPython で実行）
make demo-06  # humanize / python-slugify の出力を見る
```

静的検査:

```bash
make check    # 全 Worker エントリを py_compile（構文検査）
make lint     # Ruff
```

## プロジェクトの初期化（この教材の流儀）

新しい Python Worker プロジェクトはこう作る（公式の手順）:

```bash
uvx --from workers-py pywrangler init   # pyproject.toml と wrangler 設定を生成
uv run pywrangler dev                   # ローカル開発サーバ
uv run pywrangler deploy                # デプロイ
```

このリポジトリは `init` の生成物を手で整えた形。各 exercise は
`src/entry.py`（Worker 本体）と `wrangler.jsonc`（設定）を持つ。

## 検証状況

**正直な記録。** この環境で実際に確認できたこと / できないことを分けて書く。

| 項目 | 状態 |
|------|------|
| `pywrangler` の入手・起動 (`uvx --from workers-py pywrangler --help`) | 確認済み（このマシン） |
| Exercise 00〜06 の `src/*.py` の構文（`make check`） | 確認済み |
| `uv run pywrangler dev` の実起動と `curl` 疎通 | **確認済み（04〜06、担当B）**（pywrangler 1.17.4 / wrangler 4.143.0 / Pyodide 3.14.2） |
| `uv run pywrangler deploy` | 未検証（remote を作らない方針のため） |

**04〜06 の実測記録**は `VERIFICATION.md` に残す。公式ドキュメントの除外リストに
ある `fcntl` / `termios` / `pty` / `tty` が `find_spec` で「見つかる」という
食い違いも記録した（実使用は未検証。断定しない）。

`workers` SDK は Workers runtime が提供する。ローカルの venv には入らないため、
`make check` は **import ではなく構文だけ** を見る。

## つまずきやすい点（共通）

- **`python_workers` フラグ忘れ** … Python として解釈されない。全 exercise で必須
- **`compatibility_date` 未指定** … 挙動が不定。今日の日付を入れる
- **`await` 忘れ** … `request.json()` など JS 由来のメソッドは Promise を返す
- **secret を `wrangler.jsonc` に書く** … 漏洩する。`wrangler secret put` を使う

## 主要な前提（公式ドキュメント準拠）

- 実行環境は **Pyodide**。CPython を WebAssembly にコンパイルしたもの
- エントリは `Default` クラス。`WorkerEntrypoint` を継承し `async def fetch(self, request)`
- 必須フラグは `python_workers`
- CLI は **`pywrangler`**（`workers-py` / `uv` 管理）
- ファイル FS は**エフェメラルなインメモリ**。`open()` は使えるが isolate 破棄で消える
- デプロイ時にトップレベルを実行し **WASM 線形メモリのスナップショット**を保存

## 出典

- <https://developers.cloudflare.com/workers/languages/python/>
- <https://developers.cloudflare.com/workers/languages/python/basics/>
- <https://developers.cloudflare.com/workers/languages/python/how-python-workers-work/>
- <https://developers.cloudflare.com/workers/languages/python/packages/>
- <https://developers.cloudflare.com/workers/languages/python/stdlib/>
- <https://developers.cloudflare.com/workers/languages/python/ffi/>
