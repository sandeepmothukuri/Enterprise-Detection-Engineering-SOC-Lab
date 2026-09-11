.PHONY: help deploy-infra health-check test-detections test-all clean

help:
	@echo Available commands: deploy-infra, health-check, test-detections, test-all, clean

deploy-infra:
	@docker compose up -d

health-check:
	@python scripts/health_checks/health_check.py --ci

test-detections:
	@python tests/integration/test_detections.py

test-all: test-detections health-check

clean:
	@docker compose down -v