# SPDX-License-Identifier: GPL-3.0-or-later
PY := .venv/bin/python
PIP := .venv/bin/pip
COLLECTION ?= samples/mac-victim
PORT ?= 8000

.PHONY: help setup setup-py setup-web test test-py test-web \
        demo serve web build-web es kibana stack up down clean

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
	@echo "  up          one-command Docker demo: API + SPA, no ES -> http://localhost:8080"
	@echo "  down        stop and remove the Docker demo"
	@echo "  stack       build+run the whole app in Docker (ES+Kibana+API+SPA)"
	@echo "  clean       remove venv, node_modules, build artifacts"
	@echo ""
	@echo "One-stop shop (Docker):  make up      # then open http://localhost:8080"
	@echo "Local dev quickstart:    make setup && make demo   (then 'make web')"

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

up: ## one-command Docker demo (API + SPA, no ES) -> http://localhost:8080
	docker compose -f docker-compose.demo.yml up -d --build 2>/dev/null || \
	docker-compose -f docker-compose.demo.yml up -d --build
	@echo "Raptorscope is starting → http://localhost:8080  (give it a few seconds)"

down:
	docker compose -f docker-compose.demo.yml down 2>/dev/null || \
	docker-compose -f docker-compose.demo.yml down

stack:
	docker compose --profile app up -d --build 2>/dev/null || \
	docker-compose --profile app up -d --build

clean:
	rm -rf .venv web/node_modules web/dist build dist *.egg-info
	find . -type d -name __pycache__ -prune -exec rm -rf {} +

certs: ## generate a self-signed TLS cert for local HTTPS (deploy/tls/certs)
	mkdir -p deploy/tls/certs
	openssl req -x509 -newkey rsa:2048 -nodes -days 365 \
	  -keyout deploy/tls/certs/raptorscope.key \
	  -out    deploy/tls/certs/raptorscope.crt \
	  -subj "/CN=raptorscope.local"
