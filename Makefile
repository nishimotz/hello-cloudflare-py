UV := uv
PYTHON := /usr/bin/python3

# Worker 本体（各 exercise の src/entry.py）は構文検査のみ行う。
# `workers` モジュールは Workers runtime が提供するため、ローカル venv には無い。
# py_compile は import を実行せず構文だけを見るので、ここでは安全に通る。
ENTRIES := \
	exercises/00_hello/src/entry.py \
	exercises/01_request/src/entry.py \
	exercises/02_json_env/src/entry.py \
	exercises/03_routing/src/entry.py

# Exercise 04〜06 は担当Bの成果物。存在するものだけを対象にする。
EXTRA_PY := $(wildcard exercises/04_wasm/*.py exercises/05_stdlib/*.py exercises/06_packages/*.py)

.PHONY: help sync check lint \
	run-00 run-01 run-02 run-03 \
	check-extra lint-extra \
	dev-00 dev-01 dev-02 dev-03

help:
	@printf '%s\n' \
		'make sync        - install dev dependencies with uv sync' \
		'make check       - py_compile all Worker entries (+ extra *.py if present)' \
		'make lint        - run Ruff static checks' \
		'make dev-00      - Exercise 00: start pywrangler dev (Hello World)' \
		'make dev-01      - Exercise 01: start pywrangler dev (POST + FFI)' \
		'make dev-02      - Exercise 02: start pywrangler dev (JSON + env)' \
		'make dev-03      - Exercise 03: start pywrangler dev (routing + errors)' \
		'' \
		'Note: Worker は `uv run pywrangler dev` でローカル起動する。' \
		'      CPython では実行できない（workers SDK は runtime 提供）。' \
		'      Exercise 04-06 の *.py は存在すれば構文検査の対象になる。'

sync:
	$(UV) sync

check:
	$(PYTHON) -m py_compile $(ENTRIES) $(EXTRA_PY)
	@echo "py_compile OK: $(words $(ENTRIES) $(EXTRA_PY)) file(s)"

lint:
	$(UV) run ruff check .

# --- ローカル開発サーバ（要 Node、pywrangler が sync → wrangler へ委譲） ---
# 既定ポートは wrangler が選ぶ（通常 http://localhost:8787）。
# Ctrl-C で停止する。curl 例は各 exercise の README を参照。

dev-00:
	cd exercises/00_hello && $(UV) run pywrangler dev

dev-01:
	cd exercises/01_request && $(UV) run pywrangler dev

dev-02:
	cd exercises/02_json_env && $(UV) run pywrangler dev

dev-03:
	cd exercises/03_routing && $(UV) run pywrangler dev
