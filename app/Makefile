.PHONY: devb clean force-build rm-containers rm-images nuclear start

# Development build and run
devb:
	docker compose -f docker-compose.dev.yml build --parallel && docker compose -f docker-compose.dev.yml up

# Force rebuild with no cache
force-build:
	docker compose -f docker-compose.dev.yml build --no-cache --pull

# Remove all containers
rm-containers:
	docker stop $$(docker ps -aq) 2>/dev/null; docker rm $$(docker ps -aq) 2>/dev/null

# Remove all unused images
rm-images:
	docker image prune -a -f

# Nuclear option: remove everything and rebuild (without starting)
nuclear: rm-containers rm-images
	docker system prune -a -f --volumes
	docker compose -f docker-compose.dev.yml build --no-cache --pull

# Start containers after nuclear rebuild
start:
	docker compose -f docker-compose.dev.yml up

# Clean up resources
clean:
	./cleanup.sh 