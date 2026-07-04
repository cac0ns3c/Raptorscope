# SPDX-License-Identifier: GPL-3.0-or-later
PY := .venv/bin/python
PIP := .venv/bin/pip
COLLECTION ?= samples/mac-victim
PORT ?= 8000

.PHONY: help setup setup-py setup-web test test-py test-web \
        demo serve web build-web es kibana stack clean

help:
	@echo "Raptorscope make targets:"
	@echo "  setup       create venv, install Python + web deps"
	@echo "  test        run Python + web test suites"
	@echo "  demo        serve the bundled sample case on :$(PORT) (offline)"
	@echo "  serve       serve COLLECTION=<dir|zip> on :$(PORT) (offline)"
	@echo "  web         run the Vite dev server (proxies /api -> :8000)"
	@echo "  build-web   type-check + production-bundle the SPA"
	@echo "  es          start Elasticsearch + Kibana (docker compose)"
	@echo "  kibana      start ES+Kibana and provision the raptorscope-* data view"
	@echo "  stack       build+run the whole app in Docker (ES+Kibana+API+SPA)"
	@echo "  clean       remove venv, node_modules, build artifacts"
	@echo ""
	@echo "Quickstart:  make setup && make demo   (then 'make web' in another shell)"

setup: setup-py setup-web

setup-py:
	python3 -m venv .venv
	$(PIP) install -r requirements.txt
	$(PIP) install -e .

setup-web:
	cd web && npm install

test: test-py test-web

test-py:
	$(PY) -m pytest tests/ -q

test-web:
	cd web && npm run verify

demo:
	$(PY) -m raptorscope demo --port $(PORT)

serve:
	$(PY) -m raptorscope serve --collection $(COLLECTION) --port $(PORT)

web:
	cd web && npm run dev

build-web:
	cd web && npm run build

es:
	docker compose up -d 2>/dev/null || docker-compose up -d

kibana: es
	./kibana/provision.sh

stack:
	docker compose --profile app up -d --build 2>/dev/null || \
	docker-compose --profile app up -d --build

clean:
	rm -rf .venv web/node_modules web/dist build dist *.egg-info
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
