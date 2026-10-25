.PHONY: postman postman-check newman newman-docker mock-api fixtures
UV ?= uv run --python 3.13
ENV ?= local
BASE_URL ?= http://localhost:8000

postman:            ## regenerate the Postman collection from openapi.yaml and postman/flows
	$(UV) python scripts/postman_collection.py

postman-check:      ## fail when the committed collection is stale (also run by pre-commit and CI)
	$(UV) python scripts/postman_collection.py --check

newman:             ## run the collection with Newman (needs Node): make newman ENV=docker-compose
	cd postman && npx --yes newman run voice-assistant.postman_collection.json \
		-e environments/$(ENV).postman_environment.json --env-var baseUrl=$(BASE_URL) --working-dir .

newman-docker:      ## same without Node: uses the official Newman image
	docker run --rm --add-host host.docker.internal:host-gateway -v "$$PWD/postman":/etc/newman -w /etc/newman \
		postman/newman:alpine run voice-assistant.postman_collection.json \
		-e environments/$(ENV).postman_environment.json --env-var baseUrl=$(subst localhost,host.docker.internal,$(BASE_URL))

mock-api:           ## Prism mock server on :4010
	docker compose -f deploy/docker/docker-compose.mock.yml up

fixtures:           ## regenerate postman/fixtures
	./scripts/make_audio_fixtures.sh
