# Run your local app
run:
	uvicorn src.main:app --reload

build:
	docker build -t lia:latest .

# Start the production environment using Docker Compose
prod:
	echo "Starting production Docker containers"
	docker compose up

# Tear down the production Docker environment, removing orphan containers
prod-down:
	echo "Stopping and removing production containers"
	docker compose down --remove-orphans
	echo "To remove all containers, volumes, and networks, use --volumes"

# Start the development environment using the dev Docker Compose file
dev:
	echo "Starting development environment"
	docker compose -f docker-compose.dev.yml up

# Tear down the development environment, removing orphan containers
dev-down:
	echo "Stopping and removing development containers"
	docker compose -f docker-compose.dev.yml down --remove-orphans
	echo "To remove all containers, volumes, and networks, use --volumes"

# Pass extra pytest flags like: make test ARGS='-k "test_start_real_workflow" -s --log-cli-level=DEBUG'
ARGS ?=

# Bring up infra deps (postgres, etcd, minio, milvus) in the background
test-up:
	docker compose -f docker-compose.dev.yml up -d postgres etcd minio milvus

# Run tests inside the lia image as a one-off (no uvicorn/streamlit)
test:
	$(MAKE) test-up
	docker compose -f docker-compose.dev.yml run --rm --no-deps -e PYTHONUNBUFFERED=1 lia \
		bash -lc "pytest $(ARGS)"
	# clean the ephemeral 'lia' container created by `run`
	docker compose -f docker-compose.dev.yml rm -fsv lia >/dev/null 2>&1 || true

# Run a specific test file or function quickly
test-full:
	$(MAKE) test ARGS='tests/test_full_conversation.py::test_start_real_workflow -s'

# If the `lia` service is already up and you want to exec into it instead of run:
test-exec:
	docker compose -f docker-compose.dev.yml exec -T lia bash -lc "pytest $(ARGS)"

# Stop infra (keeps volumes)
test-down:
	docker compose -f docker-compose.dev.yml down --remove-orphans
