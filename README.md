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

## デプロイ

ローカルで動いた Worker を Cloudflare のネットワークに公開する。
CLI は **wrangler**（現行）と **cf**（後継。2026-09 発表）の2通りを併記する。

### 前提

- **Cloudflare アカウント**（無料で作成できる）
- Node.js（`wrangler` は 20 以上、`cf` は 22 以上）

### ログイン

**wrangler（現行）:**

```bash
npx wrangler login     # ブラウザが開き、OAuth で認可
npx wrangler whoami    # 確認
```

**cf（後継）:**

```bash
npm i -g cf            # インストール（Node.js 22+）
cf auth login          # デフォルトプロファイルでログイン
cf auth whoami         # 確認
cf auth create work    # 名前付きプロファイルを使う場合
cf auth activate work
```

### デプロイする

**wrangler（現行）:**

```bash
uv run pywrangler deploy
```

`pywrangler` が `pyproject.toml` の依存をバンドルし、設定を整えてから、
内部で `npx wrangler deploy` に委譲する。

**cf（後継）:**

```bash
cf migrate wrangler.jsonc   # 既存の wrangler 設定から cloudflare.config.ts を生成
cf deploy                   # cloudflare.config.ts を読んでビルド・デプロイ
```

`cf migrate` は wrangler の設定ファイルを引数に取り、`cloudflare.config.ts`
（TypeScript 形式）を生成する。`--dry-run` で変更予定だけ確認できる。

やること:

1. `src/entry.py` をビルドし、依存パッケージをバンドルする
2. WASM（Pyodide）のブートストラップを実行し、線形メモリのスナップショットを作る
3. `wrangler.jsonc` / `cloudflare.config.ts` の `name` で Worker をアップロードする
4. ルート（`<name>.<account>.workers.dev`）を割り当てる

スナップショットの仕組みは Exercise 04 を参照。

### 動作確認

```bash
curl https://<name>.<account>.workers.dev/
```

`<name>` は設定ファイルの `name`。`<account>` は `npx wrangler whoami` の出力や
Cloudflare ダッシュボードで確認する。

### secret を設定する

コード・設定に書かず、CLI から登録する（Exercise 02 を参照）:

**wrangler（現行）:**

```bash
npx wrangler secret put API_TOKEN
```

**cf（後継）:**

```bash
cf workers secrets update API_TOKEN     # 新しいバージョンとして secret を登録
cf workers secrets list                 # 登録済み secret の一覧
cf workers secrets get API_TOKEN        # 値の確認
cf workers secrets delete API_TOKEN     # 削除
```

`cf workers secrets` の動詞は `update`（旧 `put` に相当）。`--worker` で対象
Worker を明示する。複数を一度に変えるときは `cf workers secrets bulk` を使う。

### ログを見る

**wrangler（現行）:**

```bash
npx wrangler tail
```

**cf（後継）:** `cf workers` に wrangler `tail` に相当するコマンドは確認できな
かった。`cf logs query`（Logpush ベース）、`cf builds logs get` などが近いが、
実行ログのライブストリームとしては未確認。

本番の Worker に届いたリクエストと出力がストリーム表示される。

### 消す

**wrangler（現行）:**

```bash
npx wrangler delete
```

**cf（後継）:**

```bash
cf workers delete <worker-id>   # worker-id を明示する
```

wrangler の `delete` は設定ファイルから名前を解決するが、`cf workers delete` は
**worker-id を引数に取る**。`cf workers list` で ID を確認する。

設定ファイルの `name` の Worker を削除する。動作確認が済んだら残さない。

### 補足

- Cloudflare は 2026-09 に **`cf`**（全 API を覆う統合 CLI）を発表した。
  **wrangler は 18 ヶ月の猶予期間で維持**され、新規は `cf` が推奨される
- 設定ファイルは `wrangler.jsonc`（JSONC）から **`cloudflare.config.ts`
  （TypeScript）** に移る。移行は `cf migrate` が補助する
- `cf` は `cf cli search "…"` でコマンドを検索できる（結果は JSON）。
  3,000 以上のサブコマンドがあるため、目的のコマンドを見つけるのに便利
- 本ページの `cf` コマンドは **cf v1.0.0-beta.5 の `--help` で確認**した範囲。
  ベータ版なので体系は変わりうる
- 主経路（`dev` / `deploy`）は **`pywrangler`** 経由に統一している。
  `pywrangler` は wrangler のラッパーなので、`cf` 移行の影響を受けにくいが、
  `pywrangler` が `cf` に追随するかは別途確認が要る
- Python Workers は初期段階の機能で、対応パッケージや API の範囲は変化する
  （Exercise 06 を参照）
- 無料プランでも Workers は使える。課金・上限は Cloudflare のダッシュボードで確認する

### デプロイ先の選択肢

同じ Flask アプリを「書き換えずに載せる」という観点で比較すると、次のようになる。

| | Cloudflare Workers | AWS Lambda + Zappa | AWS Lambda + Chalice |
|---|---|---|---|
| 既存 Flask の修正 | **1行**（`entrypoint(app)`） | `zappa_settings.json` のみ | **書き直しが要る** |
| 実行環境 | Pyodide（WASM） | 実 CPython | 実 CPython |
| C 拡張 | 原則不可（PyEmscripten 要） | 可 | 可 |
| 設定 | `wrangler.jsonc` / `cloudflare.config.ts` | `zappa_settings.json` | `.chalice/config.json` |
| 課金 | リクエスト + CPU（無料枠あり） | Lambda + API Gateway | Lambda + API Gateway |
| エッジ | **グローバル** | リージョン | リージョン |

- **Zappa** は「既存 WSGI アプリを変えずに Lambda へ」載せる道具。
  Exercise 07 の Workers × Flask と**同型の体験**になる
- **Chalice** は AWS の作法で書く道具。Flask を**そのまま載せるものではない**
  （この違いが比較の勘所）
- ASGI（FastAPI / Starlette）を Lambda に載せるなら **Mangum** が定番
- Cloudflare 内で WASM の制約を避けたい場合は **Containers**
  （`cf containers --help`）という選択肢もある

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
