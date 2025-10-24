# AI Multimedia Tutor

This project is an AI-powered multimedia tutor.

## Local Development Setup

To get the AI Multimedia Tutor running on your local machine, we recommend using the provided `Makefile` for a streamlined setup.

### Prerequisites

*   **Python 3.13** (for local development without Docker)
*   **Docker Desktop** (for Docker-based setup)
*   **Git** (to clone the repository)

### Getting Started with the Makefile

The `Makefile` in the project root simplifies common tasks. You can see all available commands by running:

```bash
make help
```

### Option 1: Using a Python Virtual Environment (Recommended for local development)

This option sets up the project using a Python virtual environment, which is ideal for local development and debugging.

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/larkinthebest/semestralka-spmm-ai.git
    cd semestralka-spmm-ai
    ```

2.  **Install Python Dependencies:**
    Use the `Makefile` to create a virtual environment and install all Python packages:
    ```bash
    make install
    ```
    This command will:
    *   Create a Python virtual environment (`.venv`).
    *   Install all Python dependencies from `requirements.txt`.
    *   Run the database migration script (`migrate_database.py`) to set up the necessary tables.
    *   **Note:** The `make run` command automatically uses this virtual environment. If you need to manually activate it for other commands, run `source .venv/bin/activate` (on Windows, use `.\.venv\Scripts\activate`).

3.  **Install System Dependencies (if not using Docker):**
    Some Python packages (like `pytesseract` and `opencv-python`) require system-level dependencies. These are *not* installed by `make install` and need to be handled manually based on your operating system.

    *   **For Debian/Ubuntu-based systems:**
        ```bash
        sudo apt-get update
        sudo apt-get install -y tesseract-ocr tesseract-ocr-eng libgl1-mesa-glx libsm6 libxext6
        ```
    *   **For macOS (using Homebrew):**
        ```bash
        brew install tesseract
        ```
    *   **For Windows:**
        *   Install [Tesseract OCR](https://tesseract-ocr.github.io/tessdoc/Installation.html). Make sure to add it to your system PATH.
        *   OpenCV usually handles its dependencies better on Windows, but if you encounter issues, you might need to install Visual C++ Redistributable.

4.  **Download AI Models (Crucial Step!):**
    The application relies on large AI models for its functionality (e.g., GPT4All, OpenAI Whisper). These are *not* automatically downloaded with `pip install` or `make install`. You must download them manually.

    *   **GPT4All Models:** Download a compatible model (e.g., `ggml-mpt-7b-chat.bin`) from the [GPT4All website](https://gpt4all.io/index.html) and place it in the `models/` directory at the root of this project.
        Example download using `curl`:
        ```bash
        mkdir -p models
        curl -L https://gpt4all.io/models/ggml-mpt-7b-chat.bin -o models/ggml-mpt-7b-chat.bin
        ```
    *   **OpenAI Whisper Models:** Whisper models are typically downloaded on first use by the `openai-whisper` library. However, if you encounter issues, you might need to manually download a model (e.g., `tiny.en`, `base.en`, `small.en`) and configure the `llm_service.py` to point to its path, or ensure your environment has sufficient internet access and permissions for automatic download.

    **Ensure all required AI model files are present in the `models/` directory before running the application.**

5.  **Run the Application:**
    After completing the `make install` step and downloading the AI models, you can start the application:
    ```bash
    make run
    ```
    This command will clear the terminal and start the FastAPI application, automatically using the virtual environment created by `make install`.

7.  **Access the Application:**
    Open your web browser and go to:
    ```
    http://localhost:8002
    ```

### Option 2: Using Docker (Containerized Setup)

This option provides a consistent environment across different machines using Docker.

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/larkinthebest/semestralka-spmm-ai.git
    cd semestralka-spmm-ai
    ```

2.  **Download AI Models (Crucial Step!):**
    Even with Docker, you need to download the large AI models locally first. Place them in the `models/` directory at the project root. The Docker setup will then mount this directory into the container. Refer to step 4 in "Option 1: Using a Python Virtual Environment" for detailed model download instructions.

3.  **Build and Run with Docker Compose:**
    Navigate to the project root directory in your terminal and run:
    ```bash
    docker-compose up --build
    ```
    This command will:
    *   Build the Docker image for the `ai-tutor` service (if not already built or if changes were made to the `Dockerfile`).
    *   Start the container, mounting your local `models/` directory.

    Alternatively, you can use the `Makefile` for individual steps:
    ```bash
    make build-docker
    make run-docker
    ```

4.  **Initialize the Database:**
    ```bash
    docker-compose exec ai-tutor python migrate_database.py
    ```
    This command runs the `migrate_database.py` script inside the running Docker container to set up the database.

5.  **Access the Application:**
    Once the container is running, the models are downloaded, and the database is initialized, open your web browser and go to:
    ```
    http://localhost:8002
    ```

## Project Structure

*   `src/`: Contains the main application source code.
    *   `api/`: FastAPI endpoints.
    *   `core/`: Core logic, authentication, database models, schemas.
    *   `processors/`: Document and multimedia processing logic.
    *   `services/`: LLM and quiz generation services.
*   `static/`: Static files (CSS, HTML, images).
*   `models/`: Directory for GPT4All models.
*   `data/`: Placeholder for data files.
*   `samples/`: Sample multimedia files.
*   `tests/`: Unit and integration tests.
*   `requirements.txt`: Python dependencies.
*   `run.py`: Entry point for the application.
*   `Dockerfile`: Docker configuration for containerized deployment.
*   `docker-compose.yml`: Docker Compose configuration for multi-service deployment.

## Deployment Options

### 1. GitHub Pages (for static frontend)

If your application has a purely static frontend (HTML, CSS, JavaScript) that communicates with a separate backend API, you could potentially deploy the frontend part to GitHub Pages. However, since this project appears to be a full-stack application with a Python backend, GitHub Pages alone would not be sufficient for the entire application.

### 2. Cloud Platforms (e.g., Render, Heroku, AWS, Google Cloud, Azure)

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

### 3. Self-Hosting (e.g., on a VPS)

You can deploy the Dockerized application on a Virtual Private Server (VPS) using tools like `nginx` for a reverse proxy and `systemd` for process management.

---

This `README.md` provides comprehensive instructions for both local setup and deployment, addressing the issues your teammates faced and offering solutions for simplified setup and easier access.
