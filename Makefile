# =============================================================
# Pramana AI — Makefile
# Shortcut commands untuk development
# =============================================================

.PHONY: help dev dev-infra dev-services stop logs test migrate seed clean status

# Default target
help: ## Tampilkan bantuan
	@echo ""
	@echo "  Pramana AI — Smart-Claim Co-Pilot"
	@echo "  =================================="
	@echo ""
	@echo "  Perintah yang tersedia:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""

# --- Docker Compose Commands ---

dev: ## Jalankan semua services (docker compose up --build)
	docker compose up --build -d
	@echo ""
	@echo "✅ Semua service berjalan!"
	@echo "   API Gateway:  http://localhost:8000/docs"
	@echo "   Mock VClaim:  http://localhost:8001/docs"
	@echo "   NLP Engine:   http://localhost:8002/docs"
	@echo "   ML Engine:    http://localhost:8003/docs"
	@echo "   Auth Service: http://localhost:8004/docs"
	@echo ""

dev-infra: ## Jalankan hanya infrastructure (postgres + redis)
	docker compose up -d postgres redis
	@echo ""
	@echo "✅ Infrastructure berjalan!"
	@echo "   PostgreSQL: localhost:5432"
	@echo "   Redis:      localhost:6379"
	@echo ""

dev-services: ## Jalankan semua application services (tanpa rebuild)
	docker compose up -d mock-vclaim api-gateway nlp-engine ml-engine auth-service

stop: ## Hentikan semua services
	docker compose down

stop-clean: ## Hentikan semua services dan hapus volumes
	docker compose down -v

logs: ## Tampilkan logs semua services
	docker compose logs -f

logs-api: ## Tampilkan logs API Gateway
	docker compose logs -f api-gateway

logs-vclaim: ## Tampilkan logs Mock VClaim
	docker compose logs -f mock-vclaim

status: ## Tampilkan status semua services
	docker compose ps

# --- Database Commands ---

migrate: ## Jalankan database migrations (Alembic upgrade head)
	docker compose exec api-gateway alembic upgrade head

migrate-create: ## Buat migration baru (usage: make migrate-create MSG="deskripsi migrasi")
	docker compose exec api-gateway alembic revision --autogenerate -m "$(MSG)"

migrate-down: ## Rollback migration satu step
	docker compose exec api-gateway alembic downgrade -1

seed: ## Jalankan seed data
	docker compose exec api-gateway python -m app.seeds.run

# --- Testing Commands ---

test: ## Jalankan semua unit tests
	pytest tests/ -v --tb=short

test-unit: ## Jalankan hanya unit tests
	pytest tests/unit/ -v --tb=short

test-integration: ## Jalankan hanya integration tests
	pytest tests/integration/ -v --tb=short

test-coverage: ## Jalankan tests dengan coverage report
	pytest tests/ -v --tb=short --cov=services --cov-report=html --cov-report=term-missing

test-vclaim: ## Jalankan tests untuk Mock VClaim
	pytest tests/unit/test_mock_vclaim/ -v --tb=short

# --- Linting & Formatting ---

lint: ## Jalankan linter (flake8)
	flake8 services/ tests/ --max-line-length=120

format: ## Format kode (black + isort)
	black services/ tests/
	isort services/ tests/

format-check: ## Cek format tanpa mengubah file
	black --check services/ tests/
	isort --check services/ tests/

# --- Utility Commands ---

clean: ## Bersihkan file cache dan temporary
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cache dibersihkan!"

shell-api: ## Buka shell di container API Gateway
	docker compose exec api-gateway bash

shell-db: ## Buka psql shell ke database
	docker compose exec postgres psql -U $${POSTGRES_USER:-pramana_user} -d $${POSTGRES_DB:-pramana_dev}

shell-redis: ## Buka redis-cli
	docker compose exec redis redis-cli

health: ## Cek health semua services
	@echo "Checking services..."
	@curl -s http://localhost:8000/health | python -m json.tool 2>/dev/null || echo "❌ API Gateway not responding"
	@curl -s http://localhost:8001/health | python -m json.tool 2>/dev/null || echo "❌ Mock VClaim not responding"
	@curl -s http://localhost:8002/health | python -m json.tool 2>/dev/null || echo "❌ NLP Engine not responding"
	@curl -s http://localhost:8003/health | python -m json.tool 2>/dev/null || echo "❌ ML Engine not responding"
	@curl -s http://localhost:8004/health | python -m json.tool 2>/dev/null || echo "❌ Auth Service not responding"
