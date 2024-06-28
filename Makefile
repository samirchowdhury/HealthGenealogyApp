# Define the image name and container name
IMAGE_NAME=pothos_agent
CONTAINER_NAME=pothos_dev
# Path to the Dockerfile
DOCKERFILE_PATH=Dockerfile

.PHONY: build dev clean clean-all react-build run

build:
	@docker image inspect $(IMAGE_NAME) > /dev/null 2>&1 || \
		(echo "Building Docker image $(IMAGE_NAME)..." && docker build -t $(IMAGE_NAME) .)

# Build React app
react-build:
	@echo "Building React app..."
	@docker run --rm -v $(shell pwd)/frontend:/app -w /app $(IMAGE_NAME) npm run build

# Start or enter the container
dev: build
	@if [ $$(docker ps -q -f name=$(CONTAINER_NAME)) ]; then \
		echo "Container $(CONTAINER_NAME) is already running, attaching to it..."; \
		docker attach $(CONTAINER_NAME); \
	else \
		echo "Container $(CONTAINER_NAME) is not running, cleaning and restarting..."; \
		$(MAKE) clean; \
		docker run \
			-it \
			--name $(CONTAINER_NAME) \
			-p 5001:5001 \
			-v $(shell pwd):/home/pothos \
			$(IMAGE_NAME); \
	fi

# Run the Flask app with React build
run: build react-build
	@echo "Running Flask app with React build..."
	@docker run -it --rm \
		--name $(CONTAINER_NAME) \
		-p 5001:5001 \
		-v $(shell pwd):/home/pothos \
		$(IMAGE_NAME) \
		python app.py

clean:
	@echo "Stopping and removing container $(CONTAINER_NAME)..."
	-docker stop $(CONTAINER_NAME)
	-docker rm $(CONTAINER_NAME)

clean-all: clean
	@echo "Removing the image $(IMAGE_NAME)"
	-docker rmi $(IMAGE_NAME)

	