# Exercise 04 — WASM / Pyodide の仕組み

「なぜ Python が Workers で動くのか」を理解する回。ここはコードを書いて
動かす回ではなく、**仕組みと制約の理由**を押さえる回。

## この回の狙い

- Cloudflare Workers の基本単位（V8 isolate）を知る
- Pyodide = CPython を WebAssembly にコンパイルしたもの、と理解する
- 「isolate 内で Pyodide が Python を解釈する」実行モデルを図で説明できる
- なぜコールドスタートが速いのか（デプロイ時のスナップショット）を理解する
- そこで生まれる制約（インメモリ FS、スレッド/プロセス不可）の**理由**を結びつける

## 実行モデル

```
┌─────────────────────────────────────────────────────────┐
│ V8 isolate（JavaScript の実行単位。OS プロセスではない） │
│                                                          │
│   ┌───────────────────────────────────────────────┐     │
│   │ Pyodide（CPython を WebAssembly に コンパイル）│     │
│   │                                                │     │
│   │   WebAssembly 線形メモリ  ← ここに Python の   │     │
│   │   オブジェクト・ヒープ・スタックが載る          │     │
│   │                                                │     │
│   │   Default.fetch(request) が Python として走る  │     │
│   └───────────────────────────────────────────────┘     │
│                                                          │
│   JS の Request / Response は FFI 経由で Python から見える │
└─────────────────────────────────────────────────────────┘
```

ポイント:

- **OS プロセスではない。** プロセスでもコンテナでもないため、`fork()` も
  スレッドも「本物」は無い。これが `multiprocessing` / `threading` が
  「import できるが機能しない」理由になる（Exercise 05 で扱う）。
- **CPython そのもの。** 別実装の独自言語ではなく、参照実装 CPython を
  WASM に移植したもの。だから標準ライブラリと CPython テスト群の
  大半がそのまま通る。
- **Pyodide は runtime が自動注入する。** 自分で Pyodide をインストールする
  必要はない。`uv run pywrangler dev` のときも、デプロイ後も、
  runtime が isolate を作って Pyodide を差し込む。

## ローカル開発で runtime がやること

`uv run pywrangler dev` を実行すると、Workers runtime は以下を行う
（公式ドキュメント "How Python Workers Work" より）:

1. `compatibility_date` に基づいて必要な Pyodide のバージョンを決める
2. `pyproject.toml` に基づいて必要なパッケージをインストールする
3. Worker 用に新しい V8 isolate を作り、Pyodide を自動注入する
4. その Pyodide 上で Python コードをサーブする

ツールチェインの追加もプリコンパイル手順も無い。JS の Worker と同じ感覚で
`dev` を叩けば、実行環境は runtime 側が用意する。

## デプロイ時のコールドスタート最適化

`uv run pywrangler deploy` を実行したときの流れ（同ドキュメントより）:

1. Wrangler が Python コードと `pyproject.toml` のパッケージを Workers API に上げる
2. Cloudflare がコードを runtime に送って検証する
3. 新しい V8 isolate を作り、Pyodide を自動注入する
4. **Worker のエントリモジュールと、それがトップレベルで import するものを実行し、
   WebAssembly 線形メモリのスナップショットを取る**
5. そのスナップショットを Worker の Python コードと一緒にネットワークへ配る

リクエストが来たら、このスナップショットをロードして isolate を
ブートストラップする。**重い初期化を「デプロイ時に済ませておく」** ので、
リクエスト時の初期化コストが消える、という仕組み。

### この最適化が読者に要求すること

デプロイ時に**トップレベルが実行される**。つまり:

- トップレベルに重い初期化（巨大なテーブル構築、外部への問い合わせ）を
  書くと、そのコストはデプロイ時に払う。結果はスナップショットに焼き込まれる。
- 逆に「リクエストごとに違う値」を持たせたいものをトップレベルで作ると、
  スナップショット時点の値が固定されうる。**リクエスト依存の初期化は
  `fetch` の中でやる**のが安全。

## Pyodide / Python のバージョン

- Python は毎年 8 月、Pyodide はその 6 か月後にリリースされる。
- 新しい Pyodide は **compatibility flag** でゲートされ、指定した
  `compatibility_date` 以降で有効になる。破壊的変更を避けつつ更新を届ける仕組み。
- Python 各版のサポート窓は 5 年。窓を過ぎた版でも動き続けるが、
  セキュリティパッチは来ない。新規プロジェクトでは窓内の版を使う。

## 自分で確かめるなら

この回は座学。手を動かしたい場合は Exercise 00〜03 の Worker に対して
以下を試す（**要 `pywrangler dev`**。このマシンでは未検証、後述）:

- `compatibility_date` を変えて、`platform.python_version()` が変わるか見る
- トップレベルで `print(...)` して、`dev` のログにいつ出るか観察する
- トップレベルで作った値を返すエンドポイントと、`fetch` 内で作る値を
  返すエンドポイントを比べる

## 実測記録（pywrangler dev 実行時の生データ）

`uv run pywrangler dev` で実際に起動して検証済み。
環境: `pywrangler 1.17.4` / `wrangler 4.143.0` / Pyodide 3.14.2 / CPython 3.14.2。
本 exercise の `worker.py` (`GET /`) のレスポンス（実測）:

```json
{
  "python_version": "3.14.2",
  "implementation": "CPython",
  "sys_platform": "emscripten",
  "machine": "wasm32",
  "is_emscripten": true,
  "maxsize": 2147483647,
  "in_memory_fs": "read_back='hello'"
}
```

読み取れること:

- `sys.platform == "emscripten"` — Pyodide（WASM）上で動いている証拠
- `machine == "wasm32"` — WASM 32bit ターゲット
- `maxsize == 2147483647` (= 2**31-1) — **ネイティブの 64bit ではなく WASM 32bit**。
  通常の CPython では `9223372036854775807` (= 2**63-1)
- `in_memory_fs` — `open()` で書いて読めた（isolate 生存中）

`maxsize` が 32bit なのは重要な観察点。整数が WASM 線形メモリの
アドレス空間に載るため、大きな値の扱いが native と変わる可能性がある。

### ローカル開発時の実測ログ（pywrangler dev 起動時）

```
Using CPython 3.14.2+freethreaded
Creating virtual environment at: .venv-workers
Downloading pyodide-3.14.2-emscripten-wasm32-musl (download) (7.2MiB)
...
INFO     Resolving... / Installing packages into python_modules...
INFO     Passing command to npx wrangler: npx --yes wrangler dev --port ...
 ⛅️ wrangler 4.143.0
```

ドキュメントの「1. Pyodide のバージョン決定 → 2. パッケージ取得 →
3. isolate 生成・Pyodide 注入 → 4. サーブ」が、実際のログに
`Pyodide のダウンロード` → `python_modules へのインストール` → `wrangler dev`
として現れる。

## 出典

- <https://developers.cloudflare.com/workers/languages/python/how-python-workers-work/>
- <https://developers.cloudflare.com/workers/reference/how-workers-works/>
- <https://pyodide.org/en/stable/index.html>
