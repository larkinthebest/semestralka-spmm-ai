.PHONY: install run build-docker run-docker clean help

# Define Python executable and virtual environment directory
PYTHON := python3
VENV_DIR := .venv

# Default target
all: help

# Install Python dependencies in a virtual environment, set up the database, and configure API key
install: setup migrate-db configure-api-key
	@echo "Setup complete. LLM API keys configured."

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

# Internal target for configuring LLM API keys
configure-api-key:
	@echo "Configuring LLM API keys in .env file..."
	@if [ ! -f .env ]; then \
		echo "Creating .env file..."; \
		touch .env; \
		echo ".env file created. Remember to keep this file out of version control."; \
	fi
	@if ! grep -q "GEMINI_API_KEY" .env || grep -q "GEMINI_API_KEY=\"YOUR_GEMINI_API_KEY\"" .env; then \
		read -p "Enter your Google Gemini API Key (leave blank to skip): " GEMINI_API_KEY_INPUT; \
		if [ -n "$$GEMINI_API_KEY_INPUT" ]; then \
			sed -i '' '/^GEMINI_API_KEY=/d' .env; \
			echo "GEMINI_API_KEY=\"$$GEMINI_API_KEY_INPUT\"" >> .env; \
			echo "Gemini API Key configured."; \
		else \
			echo "Skipping Gemini API Key configuration."; \
		fi; \
	else \
		echo "Gemini API Key already configured."; \
	fi
	@if ! grep -q "OPENAI_API_KEY" .env || grep -q "OPENAI_API_KEY=\"YOUR_OPENAI_API_KEY\"" .env; then \
		read -p "Enter your OpenAI API Key (leave blank to skip): " OPENAI_API_KEY_INPUT; \
		if [ -n "$$OPENAI_API_KEY_INPUT" ]; then \
			sed -i '' '/^OPENAI_API_KEY=/d' .env; \
			echo "OPENAI_API_KEY=\"$$OPENAI_API_KEY_INPUT\"" >> .env; \
			echo "OpenAI API Key configured."; \
		else \
			echo "Skipping OpenAI API Key configuration."; \
		fi; \
	else \
		echo "OpenAI API Key already configured."; \
	fi
	@if ! grep -q "OPENROUTER_API_KEY" .env || grep -q "OPENROUTER_API_KEY=\"YOUR_OPENROUTER_API_KEY\"" .env; then \
		read -p "Enter your OpenRouter API Key (leave blank to skip): " OPENROUTER_API_KEY_INPUT; \
		if [ -n "$$OPENROUTER_API_KEY_INPUT" ]; then \
			sed -i '' '/^OPENROUTER_API_KEY=/d' .env; \
			echo "OPENROUTER_API_KEY=\"$$OPENROUTER_API_KEY_INPUT\"" >> .env; \
			echo "OpenRouter API Key configured."; \
		else \
			echo "Skipping OpenRouter API Key configuration."; \
		fi; \
	else \
		echo "OpenRouter API Key already configured."; \
	fi
	@echo "Ollama (local models) is prioritized. Ensure Ollama is running and OLLAMA_BASE_URL/OLLAMA_MODEL_NAME are set in .env if you wish to use it."
	@echo "LLM_PROVIDERS_ORDER is set to 'ollama,openrouter,gemini,openai' in .env to prioritize local models."

# Run the FastAPI application
run:
	@echo "Starting AI Multimedia Tutor..."
	@clear # Clear terminal for a clean start
	./$(VENV_DIR)/bin/$(PYTHON) run.py

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
	@echo "  make install        - Set up virtual environment, install Python dependencies, migrate database, and configure Gemini API key."
	@echo "  make run            - Run the FastAPI application locally (automatically uses virtual environment)."
	@echo "  make build-docker   - Build the Docker image for the application."
	@echo "  make run-docker     - Run the application in a Docker container."
	@echo "  make clean          - Remove virtual environment and Python cache files."
	@echo "  make help           - Display this help message."
	@echo ""
	@echo "Note: To manually activate the virtual environment for other commands, run: source $(VENV_DIR)/bin/activate"
