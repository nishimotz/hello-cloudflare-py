# Exercise 05 — 標準ライブラリの制約

Pyodide は CPython の移植なので、標準ライブラリはほぼ全部使える。ただし
**全部ではない**。この回は「何が使えて、何が使えず、なぜか」を押さえ、
インメモリ FS を実験して「isolate で消える」ことを体感する。

## 3つの区分

公式ドキュメント（Standard Library）は制約を3つに分けている。
丸暗記ではなく、**理由**まで結びつけて覚える。

### 1. 除外モジュール（import 不可）

```
curses  dbm  ensurepip  fcntl  grp  idlelib  lib2to3  msvcrt  pwd
resource  syslog  termios  tkinter  turtle.py  turtledemo  venv
winreg  winsound
```

理由はほぼすべて **OS 依存 / 端末・GUI 依存**:

- `fcntl` `termios` `syslog` `resource` `pwd` `grp` — Unix の syscall・端末・
  ユーザー DB に依存。WASM VM には OS が無い。
- `msvcrt` `winreg` `winsound` — Windows 専用。
- `curses` `turtle` `turtledemo` `tkinter` `idlelib` — 端末制御・GUI。
- `dbm` — OS のファイルベース DB 実装に依存。
- `venv` `ensurepip` — 「環境を作る/インストーラを起動する」ための機能。
  Worker の実行モデルと合わない。
- `lib2to3` — 非推奨の 2to3 ツール。

### 2. import できるが機能しない

```
multiprocessing
threading
```

理由は **WASM VM の制約**。OS プロセスもネイティブスレッドも無いため、
「本物の並列」はできない。import 自体は成功するので、**動くと思い込むと
ハマる**。並行処理の代わりに使えるのは:

- `asyncio`（I/O 待ちの並行。Workers の `fetch` は元々 async）
- Cloudflare 側の非同期機構（`ctx.waitUntil` など binding 経由）
- 処理を複数のリクエスト/Worker に分けてスケールさせる

### 3. import 不可（依存先が除外されている）

```
pty
tty
```

`pty`/`tty` は `termios` に依存し、その `termios` が除外されているため
import できない。除外リストを消すだけでなく「その依存で連鎖的に落ちる」
例として重要。

### おまけ: 機能が限定されるモジュール

- `decimal` — C 実装（`_decimal`）のみ。Python 実装（`_pydecimal`）は無い。
  機能は同じ（C 実装だけが使える）。
- `pydoc` — 組み込みの help メッセージが無い。
- `webbrowser` — 元のモジュールが無い。

## インメモリ FS（この回の実験）

Python Workers は **エフェメラルなインメモリ filesystem** を持つ。

- `open()` や `pathlib.Path` で普通にファイル I/O ができる
- ただし **isolate が破棄されると全データが消える**
- **isolate 間で共有されない**

だから永続化には使えない。永続化が要るなら KV / R2 / Durable Objects を
使う。一時ファイルの処理（CSV を組み立てて返す、画像を加工して返す等）には
使える。

### 実験: 書いて読んで、リクエストをまたいで残るか見る

`worker.py` は `/tmp/` にファイルを書き、同じリクエスト内で読み返して
`read_back=...` を返す。加えて、プロセス寿命の観察用に「リクエスト間で
ファイルが残っているか」を返すエンドポイントを用意している。

- 同じ isolate が使い回されている間は残って見えることがある
- しかし isolate は **いつ破棄されてもおかしくない**。破棄後は消える
- 「残ったから永続だ」と判断してはいけない

## 手を動かす（要 `pywrangler dev`）

```bash
uv run pywrangler dev
# 別ターミナルで
curl http://localhost:8787/           # 標準ライブラリの観察結果
curl http://localhost:8787/fs         # ファイルを書いて読む
curl http://localhost:8787/fs         # 2回目: 残っているか
curl http://localhost:8787/threading  # threading が機能しないことの確認
```

`threading` の確認では、スレッドを起動しても本当の並行にはならず、
WASM VM の制約で期待した動きにならないことを観察する。

## 出典

- <https://developers.cloudflare.com/workers/languages/python/stdlib/>
- <https://pyodide.org/en/stable/usage/packages-in-pyodide.html>
