.PHONY: devb clean

devb:
	docker compose -f docker-compose.dev.yml build --parallel && docker compose -f docker-compose.dev.yml up

clean:
	./cleanup.sh 