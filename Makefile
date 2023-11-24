# Variables
IMAGE_NAME = jobs-gpt
ACR_NAME = jobsgpt.azurecr.io
WEBAPP_NAME = jobsgpt-api
RESOURCE_GROUP = incregen
TAG = latest

# Default target
all: build tag push update

# Build the Docker image
build:
	docker build -t $(IMAGE_NAME):$(TAG) .

# Tag the Docker image for Azure Container Registry
tag:
	docker tag $(IMAGE_NAME):$(TAG) $(ACR_NAME)/$(IMAGE_NAME):$(TAG)

# Push the Docker image to Azure Container Registry
push:
	docker push $(ACR_NAME)/$(IMAGE_NAME):$(TAG)

# Update Azure Web App with the new Docker image
update:
	az webapp config container set --name $(WEBAPP_NAME) --resource-group $(RESOURCE_GROUP) --docker-custom-image-name $(ACR_NAME)/$(IMAGE_NAME):$(TAG)

# runs a local version of the docker container
run-local:
	docker run -d -p 8000:8000 jobs-gpt:latest

.PHONY: build tag push update
