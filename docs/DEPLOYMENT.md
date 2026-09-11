# Deployment
Prerequisites: Docker Engine >= 24.0.0, Docker Compose >= 2.20.0.
Steps: 1. copy .env.example .env 2. docker compose up -d 3. python scripts/health_checks/health_check.py --ci