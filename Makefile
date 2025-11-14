.PHONY: install run build-docker run-docker clean help

# Define Python executable and virtual environment directory
PYTHON := python3
VENV_DIR := .venv

# Default target
all: help

# Install Python dependencies in a virtual environment, set up the database, and configure API key
install: setup migrate-db download-gpt4all-model download-ollama-model
	@echo "Setup complete. LLM models configured."

# Internal target for setting up virtual environment and installing dependencies
setup:
	@echo "Setting up Python virtual environment..."
	$(PYTHON) -m venv $(VENV_DIR)
	@echo "Activating virtual environment and installing dependencies..."
	./$(VENV_DIR)/bin/pip install --upgrade pip
	./$(VENV_DIR)/bin/pip install -r requirements.txt

# Internal target for migrating the database
migrate-db:
	@echo "Migrating database..."
	./$(VENV_DIR)/bin/$(PYTHON) migrate_database.py

# Target for downloading GPT4All model
download-gpt4all-model:
	@echo "Checking for GPT4All model..."
	@mkdir -p models
	@MODEL_NAME=$$(grep -E '^GPT4ALL_MODEL_NAME=' .env | cut -d'=' -f2 | tr -d '"'); \
	if [ -z "$$MODEL_NAME" ]; then \
		echo "GPT4ALL_MODEL_NAME not found in .env. Skipping GPT4All model download."; \
	else \
		MODEL_PATH="models/$$MODEL_NAME"; \
		if [ ! -f "$$MODEL_PATH" ]; then \
			echo "GPT4ALL model '$$MODEL_NAME' not found in 'models/' directory. Attempting to download..."; \
			./$(VENV_DIR)/bin/$(PYTHON) -c "from gpt4all import GPT4All; GPT4All('$$MODEL_NAME', model_path='models/')" || { echo "Failed to download GPT4All model. Please check the model name and your internet connection."; exit 1; }; \
			echo "GPT4ALL model '$$MODEL_NAME' downloaded to 'models/'."; \
		else \
			echo "GPT4ALL model '$$MODEL_NAME' already exists in 'models/'."; \
		fi; \
	fi

# New target for downloading Ollama model
download-ollama-model:
	@echo "Checking for Ollama model..."
	@OLLAMA_MODEL_NAME=$$(grep -E '^OLLAMA_MODEL_NAME=' .env | cut -d'=' -f2 | tr -d '"'); \
	if [ -z "$$OLLAMA_MODEL_NAME" ]; then \
		echo "OLLAMA_MODEL_NAME not found in .env. Skipping Ollama model download."; \
	else \
		if command -v ollama &> /dev/null; then \
			echo "Ollama is installed. Attempting to pull '$$OLLAMA_MODEL_NAME'..."; \
			ollama pull "$$OLLAMA_MODEL_NAME" || { echo "Failed to pull Ollama model. Please check the model name and your internet connection."; exit 1; }; \
			echo "Ollama model '$$OLLAMA_MODEL_NAME' pulled successfully."; \
		else \
			echo "Ollama is not installed. Please install Ollama from ollama.com to use '$$OLLAMA_MODEL_NAME'. Skipping Ollama model download."; \
		fi; \
	fi

# Run the FastAPI application
run:
	@echo "Starting AI Multimedia Tutor..."
	@clear # Clear terminal for a clean start
	PYTHONPATH=$(shell pwd) ./$(VENV_DIR)/bin/$(PYTHON) run.py

# Run tests
test:
	@echo "Running tests..."
	PYTHONPATH=$(shell pwd) ./$(VENV_DIR)/bin/pytest tests/

# Build the Docker image
build-docker:
	@echo "Building Docker image..."
	docker build -t ai-tutor .
	@echo "Docker image 'ai-tutor' built successfully."

# Run the Docker container
run-docker:
	@echo "Running Docker container..."
	@echo "Ensure AI models are mounted or downloaded inside the container."
	docker run -p 8002:8002 -v $(shell pwd)/models:/app/models ai-tutor
	@echo "AI Multimedia Tutor running in Docker at http://localhost:8002"

# Clean up build artifacts and virtual environment
clean:
	@echo "Cleaning up virtual environment and __pycache__ directories..."
	rm -rf $(VENV_DIR)
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "Cleanup complete."

# Display help message
help:
	@echo "AI Multimedia Tutor - Makefile Commands"
	@echo "-------------------------------------"
	@echo "  make install        - Set up virtual environment, install Python dependencies, migrate database, and download configured LLM models (GPT4All, Ollama)."
	@echo "  make run            - Run the FastAPI application locally (automatically uses virtual environment)."
	@echo "  make build-docker   - Build the Docker image for the application."
	@echo "  make run-docker     - Run the application in a Docker container."
	@echo "  make clean          - Remove virtual environment and Python cache files."
	@echo "  make help           - Display this help message."
	@echo ""
	@echo "Note: To manually activate the virtual environment for other commands, run: source $(VENV_DIR)/bin/activate"
