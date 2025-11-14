# AI Multimedia Tutor

This project is an AI-powered multimedia tutor.

## Local Development Setup

To get the AI Multimedia Tutor running on your local machine, we recommend using the provided `Makefile` for a streamlined setup.

### Prerequisites

*   **Python 3.10 or higher** (for local development without Docker)
*   **Git** (to clone the repository)
*   **Ollama** (for local multimodal LLM capabilities) - Download from [ollama.com](https://ollama.com/)

### Getting Started with the Makefile

The `Makefile` in the project root simplifies common tasks. You can see all available commands by running:

```bash
make help
```

### Option 1: Using a Python Virtual Environment (Recommended for local development)

This option sets up the project using a Python virtual environment, which is ideal for local development and debugging.

1.  **Clone the Repository:**
    To clone the repository into your *current directory* (without creating an extra folder), use:
    ```bash
    git clone https://github.com/larkinthebest/semestralka-spmm-ai.git .
    ```
    (Note the `.` at the end of the command.)

2.  **Install Dependencies and Setup:**
    Use the `Makefile` to perform a complete setup, including virtual environment creation, dependency installation, and database migration:
    ```bash
    make install
    ```
    This single command will:
    *   Create a Python virtual environment (`.venv`).
    *   Install all Python dependencies from `requirements.txt`.
    *   Run the database migration script (`migrate_database.py`) to set up the necessary tables.
    *   Download configured LLM models (GPT4All and Ollama).

    **Note:** The `make run` command automatically uses this virtual environment. If you need to manually activate it for other commands, run `source .venv/bin/activate` (on Windows, use `.\.venv\Scripts\activate`).

3.  **Install System Dependencies (if not using Docker):**
    Some Python packages (like `pytesseract`, `opencv-python`, `whisper`, and `pdf2image`) require system-level dependencies. These are *not* installed by `make install` and need to be handled manually based on your operating system.

    *   **For Debian/Ubuntu-based systems:**
        ```bash
        sudo apt-get update
        sudo apt-get install -y tesseract-ocr tesseract-ocr-eng libgl1-mesa-glx libsm6 libxext6 ffmpeg poppler-utils
        ```
    *   **For macOS (using Homebrew):**
        ```bash
        brew install tesseract ffmpeg poppler
        ```
    *   **For Windows:**
        *   Install [Tesseract OCR](https://tesseract-ocr.github.io/tessdoc/Installation.html). Make sure to add it to your system PATH.
        *   Install [FFmpeg](https://ffmpeg.org/download.html). Make sure to add it to your system PATH.
        *   Install [Poppler](https://poppler.freedesktop.org/). You might need to find a pre-compiled binary for Windows, e.g., from [here](https://github.com/oschwartz10612/poppler-windows/releases). Add its `bin` directory to your system PATH.

4.  **Run the Application:**
    After completing the `make install` step and ensuring system dependencies are met, you can start the application:
    ```bash
    make run
    ```
    This command will clear the terminal and start the FastAPI application, automatically using the virtual environment created by `make install`.

5.  **Access the Application:**
    Open your web browser and go to:
    ```
    http://localhost:8002
    ```

### LLM Configuration (Ollama and GPT4All)

The application is configured to use Ollama (with a multimodal model like LLaVA) as the primary LLM provider, with GPT4All as a fallback.

1.  **Install Ollama and Download Model:**
    *   If you haven't already, download and install Ollama from [ollama.com](https://ollama.com/).
    *   Once installed, open your terminal and pull the `llava` model:
        ```bash
        ollama pull llava
        ```

2.  **Set LLM Provider Order:**
    The application uses an environment variable `LLM_PROVIDERS_ORDER` to determine which LLM providers to use and in what order.

    **Recommended for Local Development (.env file):**
    *   Ensure your `.env` file in the project root contains:
        ```
        OLLAMA_BASE_URL="http://localhost:11434"
        OLLAMA_MODEL_NAME="llava"
        GPT4ALL_MODEL_NAME="Meta-Llama-3-8B-Instruct.Q4_0.gguf"
        LLM_PROVIDERS_ORDER="ollama,gpt4all"
        ```
    *   This prioritizes Ollama. If Ollama is not running or the `llava` model is not available, it will fall back to GPT4All.

3.  **Restart the Application:**
    After configuring your `.env` file and ensuring Ollama is running with the `llava` model, restart the application (e.g., `make run`) to ensure the new environment variables are loaded.

### Usage Guide

*   **Explanation Mode (Enola)**: Ask questions about your uploaded documents to get detailed explanations.
*   **Testing Mode (Franklin)**: Generate quizzes (multiple choice, true/false, fill-in-the-blank, short answer) based on your content.
*   **Asset Management**: Upload files using the '+' button in the Assets section or by dragging and dropping them into the chat area. Select/deselect assets to include them in the current chat's context.
*   **Chat Management**: Create new chats, rename existing ones, and delete chats from the left panel.
*   **User Profile**: Access your chat history, uploaded assets, and quiz statistics from the user profile modal.
*   **LaTeX Rendering**: Mathematical formulas written in LaTeX format (e.g., `$E=mc^2$` or `\[ \int_a^b f(x) dx \]`) will be rendered beautifully in the chat.

## Video Demo

Watch a video demonstration of the application's features:

https://www.youtube.com/watch?v=eGbgwIOLzic

### Troubleshooting

*   **"Tesseract not found" / OCR errors**:
    *   Ensure `pytesseract` is installed (included in `requirements.txt`).
    *   Verify that Tesseract OCR is installed on your system and its executable is in your system's PATH (see "Install System Dependencies" above).
*   **"OpenCV errors" / Video processing issues**:
    *   Ensure `opencv-python` is installed (included in `requirements.txt`).
    *   Ensure `ffmpeg` is installed on your system, as it's often a dependency for video processing.
*   **"Whisper errors" / Audio transcription issues**:
    *   Ensure `whisper` is installed (included in `requirements.txt`).
    *   Ensure `ffmpeg` is installed on your system, as it's often a dependency for audio processing.
*   **Ollama model not found**:
    *   Ensure Ollama is running (`ollama serve` in a separate terminal if not running as a service).
    *   Verify you have pulled the correct model (e.g., `ollama pull llava`).
    *   Check `OLLAMA_MODEL_NAME` in your `.env` file.
*   **Database issues**:
    *   Ensure `make install` completed the `migrate-db` step. If not, run `make migrate-db` manually.
    *   If you encounter `sqlite3.OperationalError: database is locked`, try restarting the application.

## Project Structure

*   `src/`: Contains the main application source code.
    *   `api/`: FastAPI endpoints.
    *   `core/`: Core logic, authentication, database models, schemas.
    *   `processors/`: Document and multimedia processing logic (including LaTeX detection).
    *   `services/`: LLM and quiz generation services.
*   `static/`: Static files (CSS, HTML, JavaScript).
*   `models/`: (No longer used for GPT4All models, but kept for potential future local LLMs)
*   `data/`: Placeholder for data files.
*   `samples/`: Sample multimedia files.
*   `tests/`: Unit and integration tests.
*   `requirements.txt`: Python dependencies.
*   `run.py`: Entry point for the application.
*   `Dockerfile`: Docker configuration for containerized deployment.
*   `docker-compose.yml`: Docker Compose configuration for multi-service deployment.

## Deployment Options

### 1. Cloud Platforms (e.g., Render, Heroku, AWS, Google Cloud, Azure)

For a full-stack Python application like this, cloud platforms are the most suitable deployment option. They offer various services for deploying web applications, databases, and other necessary components.

*   **Render.com:** A popular choice for deploying web services, databases, and static sites. It's relatively easy to set up and supports Docker.
*   **Heroku:** Another platform-as-a-service (PaaS) that simplifies deployment.
*   **AWS Elastic Beanstalk / EC2:** More control and flexibility, but also more complex to set up.
*   **Google Cloud Run / App Engine:** Serverless options that scale automatically.
*   **Azure App Service:** Microsoft's PaaS offering.

**General Steps for Cloud Deployment:**

1.  **Choose a Platform:** Select a cloud provider that best fits your needs and budget.
2.  **Containerize (if not already):** Ensure your application is containerized using Docker (which we've already done).
3.  **Database Setup:** Configure a production-ready database (e.g., PostgreSQL, MySQL) on your chosen platform.
4.  **Environment Variables:** Set up environment variables for sensitive information (e.g., API keys, database credentials).
5.  **Deployment:** Follow the platform-specific instructions to deploy your Docker image.

### 2. Self-Hosting (e.g., on a VPS)

You can deploy the Dockerized application on a Virtual Private Server (VPS) using tools like `nginx` for a reverse proxy and `systemd` for process management.
