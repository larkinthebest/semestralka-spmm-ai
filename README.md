# AI Multimedia Tutor

## Project Description

The AI Multimedia Tutor is an intelligent learning platform designed to enhance educational experiences by leveraging various digital assets. Users can upload diverse content, including videos, images, YouTube links, and documents, which the AI processes to generate personalized explanations and interactive quizzes. The platform aims to provide a comprehensive learning environment, offering detailed feedback on quizzes, suggesting topics for review, and tracking user progress.

## Key Features

*   **Multi-Asset Support:** Upload and process various file types including PDFs, DOCX, TXT, Markdown, images (JPG, PNG, GIF, BMP), audio (MP3, WAV, M4A, OGG), and video (MP4, AVI, MOV, MKV, WEBM).
*   **AI-Powered Explanations:** Get detailed, context-rich explanations from the "Enola" tutor based on your uploaded materials.
*   **Dynamic Quiz Generation:** Generate customizable quizzes (multiple choice, true/false, short answer, mixed) on specific topics from your assets using the "Franklin" tutor.
*   **Intelligent Grading & Feedback:** Quizzes are automatically graded, providing scores, detailed results, and personalized suggestions for topics to revisit.
*   **User Authentication:** Secure user registration and login, including Google OAuth integration.
*   **Chat Interface:** Interact with AI tutors in a conversational manner, referencing uploaded documents.
*   **Progress Tracking:** View quiz history and performance statistics to monitor learning progress.
*   **Conversation Memory:** Chat sessions are saved, allowing users to revisit past discussions and learning paths.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

Ensure you have the following installed:

*   **Python 3.9+**: [Download Python](https://www.python.org/downloads/)
*   **pip**: Python package installer (usually comes with Python)
*   **Git**: For cloning the repository

### Local Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/larkinthebest/semestralka-spmm-ai.git
    cd semestralka-spmm-ai
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    # On Windows:
    # .\venv\Scripts\activate
    # On macOS/Linux:
    # source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Initialize the database:**
    ```bash
    python semestralka-spmm-ai/migrate_database.py
    ```
    This will create the `ai_tutor.db` SQLite database in the project root.

5.  **Run the application:**
    ```bash
    python run.py
    ```
    The application will start on `http://localhost:8002`. Open this URL in your web browser.

## Project Structure

```
.
├── ai_tutor.db             # SQLite database file
├── semestralka-spmm-ai/
│   ├── .gitignore          # Git ignore file
│   ├── migrate_database.py # Script to initialize the database
│   ├── requirements.txt    # Python dependencies
│   ├── run.py              # Main entry point to start the FastAPI app
│   ├── setup.py            # Project setup file
│   ├── data/               # Placeholder for data files
│   ├── docs/               # Project documentation
│   ├── models/             # Placeholder for AI models
│   ├── samples/            # Sample assets for testing
│   ├── src/
│   │   ├── api/            # FastAPI application endpoints
│   │   │   └── main.py     # Main FastAPI application
│   │   ├── core/           # Core functionalities (auth, db, models, schemas)
│   │   ├── processors/     # Data processing (documents, multimedia)
│   │   ├── services/       # AI services (LLM, quiz generation)
│   │   └── __init__.py
│   ├── static/             # Frontend static files (HTML, CSS, JS, images)
│   ├── tests/              # Unit and integration tests
│   └── uploads/            # Directory for user-uploaded files
└── Dockerfile              # Docker configuration for containerization (will be added)
```

## Technologies Used

*   **Backend:** FastAPI, Python
*   **Database:** SQLAlchemy (SQLite)
*   **Authentication:** Authlib, bcrypt, Google OAuth
*   **LLM Integration:** gpt4all, openai-whisper
*   **Document Processing:** PyPDF2, python-docx, pytesseract
*   **Multimedia Processing:** OpenCV, Pillow
*   **Frontend:** HTML, CSS, JavaScript (served statically)

## Docker Setup (Recommended for Cross-Platform Development)

Docker provides a consistent environment for running the application, regardless of your operating system.

### Prerequisites for Docker

*   **Docker Desktop**: [Download Docker Desktop](https://www.docker.com/products/docker-desktop/)

### Building and Running with Docker

1.  **Build the Docker image:**
    ```bash
    docker build -t ai-tutor .
    ```
    This command builds a Docker image named `ai-tutor` from the `Dockerfile` in the current directory.

2.  **Run the Docker container:**
    ```bash
    docker run -p 8002:8002 ai-tutor
    ```
    This command starts a container from the `ai-tutor` image, mapping port 8002 on your host machine to port 8002 inside the container.

3.  **Access the application:**
    Once the container is running, the application will be accessible in your web browser at `http://localhost:8002`.

## Contributing

(Add instructions for contributing if applicable)

## License

(Add license information if applicable)
