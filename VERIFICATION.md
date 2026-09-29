# Exercise 04〜06 検証記録（担当B）

担当B（04 WASM / 05 stdlib / 06 packages）の実測結果。

## できたこと

`uv run pywrangler dev` で **実際に Worker を起動して HTTP 応答を確認した**。
フィクスチャ（最小構成の `pyproject.toml` + `wrangler.jsonc`）を別ディレクトリに用意し、
各 exercise の `worker.py` を `main` に向けて起動・curl した。

環境:

| 項目 | 値 |
|---|---|
| pywrangler | 1.17.4 |
| wrangler | 4.143.0 |
| Pyodide | 3.14.2 (emscripten-wasm32-musl) |
| CPython（Pyodide 内） | 3.14.2 |
| sys.platform | `emscripten` |
| platform.machine() | `wasm32` |
| sys.maxsize | `2147483647`（WASM 32bit） |

`uvx --from workers-py pywrangler --version` → `pywrangler, version 1.17.4` で
ツールチェインは動いた。`pywrangler dev` は `uv lock` が作る `pylock.toml` を読み、
`.venv-workers` と `python_modules` を生成し、`npx wrangler dev` にパスした。

## exercise 04 の実測（GET /）

```json
{"python_version": "3.14.2", "implementation": "CPython",
 "sys_platform": "emscripten", "machine": "wasm32", "is_emscripten": true,
 "maxsize": 2147483647, "in_memory_fs": "read_back='hello'"}
```

- WASM/Pyodide 上で動いていることを実データで確認
- `maxsize` が 2**31-1 = WASM 32bit。native の 2**63-1 と異なる

## exercise 05 の実測

```json
{"excluded": {"curses":"not_found","dbm":"not_found","ensurepip":"not_found",
 "fcntl":"found","grp":"not_found","idlelib":"not_found","lib2to3":"not_found",
 "msvcrt":"not_found","pwd":"not_found","resource":"not_found","syslog":"not_found",
 "termios":"found","tkinter":"not_found","turtle":"not_found","turtledemo":"not_found",
 "venv":"not_found","winreg":"not_found","winsound":"not_found"},
 "limited_importable": {"multiprocessing":"found","threading":"found"},
 "broken_by_dependency": {"pty":"found","tty":"found"}}
```

### 公式ドキュメントと食い違った点（要確認）

| モジュール | doc 区分 | 実測 | 
|---|---|---|
| `fcntl` | 除外（import 不可） | **found** |
| `termios` | 除外（import 不可） | **found** |
| `pty` | import 不可 | **found** |
| `tty` | import 不可 | **found** |

`fcntl`/`termios` は doc の除外リストにあるのに `find_spec` で見つかる。
`pty`/`tty` は「termios が除外されているため import 不可」と doc にあるが、
termios が見つかるため連鎖も外れて found になる。

**注意:** `find_spec` の found は「import できうる」だけで、動作を保証しない。
`fcntl`/`termios`/`pty`/`tty` の実使用は未検証（OS syscall 依存なので
実行時に失敗する可能性が高い）。doc 側の更新遅れか、Pyodide 3.14 の実装差か、
この環境固有かは未確認。断定せず実測のみ記録。

### インメモリ FS（実測）

- `GET /fs` → `{"ok": true, "read_back": "hello from exercise 05"}`（書けた・読めた）
- `GET /fs/count` 2回 → `count: 1` → `count: 2`（**同じ isolate が使い回されて残った**）

「isolate 生存中は残る」を実測で確認。isolate 破棄で消える点は doc どおり。

### threading（実測）

`{"imported": true, "current_thread": "MainThread", "has_Thread": true}`
import は成功。本物の並行実行はできない（doc どおり）。

## exercise 06 の実測（GET /）

```json
{"intcomma": {"1234567": "1,234,567", "1000000000": "1,000,000,000"},
 "naturalsize": {"1234567": "1.2 MB", "1000000000": "1.0 GB"},
 "slugify": {"Hello, Cloudflare Workers!": "hello-cloudflare-workers"}}
```

pure Python パッケージ（humanize, python-slugify）が Worker 上で動いた。
`uv lock` → `pylock.toml` → `python_modules`/`.venv-workers` への
インストール・バンドルの流れもログで確認。

ローカル CPython（`packages_demo.py`）でも同じ出力を確認済み。

## できなかったこと / 制約

- **`deploy` は未検証。** 指示どおり GitHub remote を作らず、Cloudflare への
  アカウントデプロイもしない（`make` / ローカル dev のみ）。
- **`fcntl`/`termios`/`pty`/`tty` の「実使用可否」は未検証。**
  `find_spec` は found を返すが、機能するかは別。
- **`multiprocessing`/`threading` の「機能しない」挙動の詳細は未検証。**
  import 成功のみ確認。
- **スナップショット（デプロイ時の WASM 線形メモリ保存）は実測できていない。**
  これはデプロイ時のみ発生する。doc に基づく記述。
- Python 3.14.2 が Pyodide 側のデフォルト。doc の例は `>=3.13`。

## doc と実測が食い違う可能性がある点（まとめ）

1. **除外モジュールの一部（`fcntl`, `termios`）が found になる** — 05 の表参照
2. **`pty`/`tty` が found になる** — doc は import 不可と記載
3. `sys.maxsize` が WASM 32bit（doc には明記なし、当然の帰結）

いずれも「実測した事実」であり、doc の誤りと断定はしない。
環境（Pyodide バージョン・compatibility_date）依存の可能性がある。

## 生成物

```
repos/hello-cloudflare-py/
├── wrangler.jsonc                    # 担当Aが最終統合（06 を main に設定した暫定版）
├── VERIFICATION.md                   # このファイル
└── exercises/
    ├── 04_wasm/
    │   ├── README.md                 # WASM/Pyodide の仕組み（座学）
    │   ├── wasm_demo.py              # CPython で動く座学デモ（実行確認済み）
    │   └── worker.py                 # Worker 版（pywrangler dev で検証済み）
    ├── 05_stdlib/
    │   ├── README.md                 # 標準ライブラリ制約 + 実測記録
    │   └── worker.py                 # Worker 版（検証済み・全エンドポイント）
    └── 06_packages/
        ├── README.md                 # パッケージ + 実測記録
        ├── worker.py                 # Worker 版（検証済み）
        ├── packages_demo.py          # CPython で動く座学デモ（実行確認済み）
        └── REQUIREMENTS.md           # 依存メモ
```

## 担当Aへの申し送り

- **`wrangler.jsonc` の暫定版を置いた。** `main` は最終的に担当Aが決めてよい。
  検証時は exercise ごとに `main` を差し替えて起動した。
- **root `pyproject.toml` に `humanize>=4` と `python-slugify>=8` が必要**（06）。
  `workers-runtime-sdk` と `workers-py`（dev）も入れる。
- **Makefile**: `make run-04` / `run-05` / `run-06` は
  `wasm_demo.py` / `packages_demo.py` を CPython で走らせる形にすると
  pywrangler 無しでも動く（04 と 06）。05 は座学のみで Worker 版しか無いので、
  `run-05` は `uv run pywrangler dev` の案内、または skip でもよい。
- `py_compile` は全4ファイルで通る。
