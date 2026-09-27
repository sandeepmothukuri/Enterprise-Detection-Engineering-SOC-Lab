# =============================================================================
# Enterprise Detection Engineering SOC Lab — Makefile
# =============================================================================

SHELL := /bin/bash
.DEFAULT_GOAL := help

.PHONY: help setup start stop restart status test test-live transpile simulate simulate-bruteforce dashboards clean

help:
	@echo "======================================================================"
	@echo "  Enterprise Detection Engineering SOC Lab - Command Palette"
	@echo "======================================================================"
	@echo "  make setup            - Generate .env, TLS certificates, and init dirs"
	@echo "  make start            - Start all 12 SOC services in the background"
	@echo "  make stop             - Stop all SOC services and preserve state"
	@echo "  make restart          - Restart all SOC services"
	@echo "  make status           - Run comprehensive health check"
	@echo "  make test             - Run offline detection & telemetry test harness"
	@echo "  make test-live        - Run live integration test against running cluster"
	@echo "  make transpile        - Compile Sigma rules into OpenSearch Query DSL"
	@echo "  make simulate         - Execute APT-29 13-stage attack simulation"
	@echo "  make simulate-spray   - Execute brute force attack simulation"
	@echo "  make dashboards       - Import pre-configured OpenSearch Dashboards"
	@echo "  make clean            - Stop containers and remove transient test data"
	@echo "======================================================================"

setup:
	@bash setup.sh

start:
	@docker compose up -d

stop:
	@docker compose down

restart:
	@docker compose restart

status:
	@bash health-check.sh

test:
	@python3 tools/test-e2e-harness.py --mode offline

test-live:
	@bash tools/test-e2e-harness.sh live

transpile:
	@python3 tools/transpile-sigma-to-opensearch.py

simulate:
	@bash simulate-attack.sh apt29

simulate-spray:
	@bash simulate-attack.sh bruteforce

dashboards:
	@bash tools/import-dashboards.sh http://localhost:5601 dashboards/opensearch_dashboards_export.ndjson

clean:
	@docker compose down -v --remove-orphans
	@rm -rf /tmp/soc-* soc_ai_jobs.db
