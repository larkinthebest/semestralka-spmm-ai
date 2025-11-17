
AI Multimedia Tutor: An Intelligent Learning Assistant

Brusniak Yehor, Dymshakov Kirill, Yakovliev Denys, Rud Roman

1 Affiliation (Institution) of the First Author, Postal Address, Country

2 Affiliation (Institution) of the Second Author, Postal Address, Country

3 Affiliation (Institution) of the Third Author, Postal Address, Country

E-mail address of the corresponding author

Abstract - This paper presents the AI Multimedia Tutor, an intelligent, AI-powered platform designed to enhance personalized learning and content comprehension through interactive engagement with diverse multimedia educational materials. The system addresses challenges in traditional learning by offering dynamic explanation and assessment capabilities. Leveraging a robust backend built with FastAPI and Python, the tutor integrates multimodal Large Language Models (LLMs) such as Ollama (specifically LLaVA) and GPT44All to process and understand various content formats, including documents, images, audio, and video. Key features include an Explanation Mode (Enola) for detailed content inquiries, a Testing Mode (Franklin) for generating customizable quizzes (multiple-choice, true/false, fill-in-the-blank, short answer), and comprehensive asset management. The platform also supports LaTeX rendering for mathematical content and provides user-specific chat history and quiz statistics. The AI Multimedia Tutor aims to provide an adaptive and engaging learning environment, demonstrating the practical application of advanced AI in educational technology.

Keywords - AI Tutor; Multimedia Learning; Large Language Models; Personalized Education; FastAPI; Ollama; Quiz Generation

Introduction (Heading 1)
The rapid evolution of artificial intelligence (AI) and multimedia technologies presents unprecedented opportunities to transform educational paradigms. In recent years, AI has shown immense potential in personalizing learning experiences, automating content analysis, and generating adaptive assessments. Traditional learning environments often struggle with providing personalized, interactive, and adaptive content tailored to individual student needs, particularly when dealing with a wide array of digital multimedia. This paper introduces the AI Multimedia Tutor, an innovative platform designed to bridge this gap by leveraging advanced AI capabilities to facilitate comprehensive learning from diverse digital content. The tutor acts as a personal learning companion, offering both in-depth explanations and dynamic assessment tools based on user-uploaded materials. It aims to enhance student engagement, improve comprehension, and provide flexible learning pathways in an increasingly digital educational landscape.

System Overview and Key Features (Heading 1)
The AI Multimedia Tutor is a full-stack web application providing an intuitive user interface for interacting with AI-powered learning tools. The system is designed to handle various multimedia inputs and offer two primary modes of operation: Explanation and Testing.

Ease of Use (Heading 2)
The application prioritizes user experience, offering a streamlined workflow for content upload, interaction, and management. Users can easily upload documents, images, audio, and video files, which form the basis of their learning sessions. The intuitive chat interface allows for natural language interaction with the AI tutors.

Explanation Mode (Enola) (Heading 3)
In Explanation Mode, the "Enola" tutor specializes in providing detailed explanations and insights from uploaded documents. Users can ask specific questions about their content, and Enola will break down complex topics, offer examples, and clarify concepts, making learning more accessible and enjoyable.

Testing Mode (Franklin) (Heading 3)
The "Franklin" tutor, operating in Testing Mode, focuses on assessment and knowledge reinforcement. It can generate various types of quizzes, including multiple-choice, true/false, fill-in-the-blank, and short-answer questions, based on the uploaded learning materials. This mode allows students to practice and test their understanding effectively.

Asset Management (Heading 3)
The platform includes robust asset management capabilities, allowing users to upload files via a dedicated button or drag-and-drop functionality. Uploaded assets can be selected or deselected to define the context for the current chat session, ensuring relevant AI responses.

Chat Management and User Profile (Heading 3)
Users can create, rename, and delete chat sessions, maintaining an organized learning history. A dedicated user profile provides access to chat history, uploaded assets, and comprehensive quiz statistics, offering insights into learning progress and performance.

LaTeX Rendering (Heading 3)
A notable feature for STEM education, the AI Multimedia Tutor seamlessly renders mathematical formulas written in LaTeX format directly within the chat interface, ensuring clear and accurate display of complex equations.

Technical Architecture and Implementation (Heading 1)
The AI Multimedia Tutor is built upon a modern, scalable architecture comprising a FastAPI backend and a responsive JavaScript frontend.

Frontend (Heading 2)
The user interface is developed using standard web technologies (HTML, CSS, JavaScript) and organized into modular components (`static/api.js`, `static/ui.js`, `static/chat.js`, `static/assets.js`, `static/quiz.js`, `static/profile.js`, `static/app.js`). It handles user interactions, displays chat messages, manages asset lists, and presents interactive quizzes. The `static/app.css` defines the visual styling, supporting both light and dark themes.

Backend (Heading 2)
The backend, implemented with FastAPI in Python (`src/api/main.py`), provides RESTful API endpoints for all core functionalities, including user authentication, chat management, asset handling, LLM interaction, and quiz generation. The `run.py` script serves as the application's entry point using Uvicorn.

LLM Integration (Heading 3)
The system integrates multimodal Large Language Models (LLMs) for its core AI capabilities, chosen for their ability to operate locally and handle diverse data types. Ollama, specifically with the LLaVA model, is utilized for local multimodal processing, enabling the tutor to understand and generate responses based on diverse inputs (text, images, etc.). This choice prioritizes privacy and reduces reliance on external API calls. GPT4All serves as a robust fallback LLM provider, ensuring continuous functionality even if the primary Ollama service is unavailable or for specific tasks where its models might be more suitable. The `src/services/llm_service.py` module orchestrates interactions with these LLMs, managing model loading, context window, and response generation.

Multimedia Processing (Heading 3)
The `src/processors/` directory houses specialized modules responsible for handling various content types, transforming raw multimedia into AI-digestible formats:
*   `document_processor.py`: Manages efficient text extraction from various document formats, including PDF (`pypdf`) and DOCX (`python-docx`). This involves parsing document structures and extracting textual content for LLM processing.
*   `multimedia_processor.py`: Provides general utilities for multimedia handling, acting as a central point for dispatching tasks to more specialized processors.
*   `video_audio_processor.py`: Dedicated to processing audio and video files. For video, this includes frame extraction at key intervals, which are then processed as images. For both audio and video, transcription is performed using advanced speech-to-text models (e.g., `openai-whisper`) to convert spoken content into text.
Optical Character Recognition (OCR) via `pytesseract` is extensively employed for extracting text from image-based content, including scanned documents and images embedded within other files. This ensures that visual information containing text is also made available to the LLMs.

Quiz Generation Service (Heading 3)
The `src/services/quiz_generator.py` module is dedicated to dynamically creating quizzes based on the processed content and user-defined parameters (type, number of questions, difficulty).

Database (Heading 3)
SQLAlchemy is used for database interactions, managing user data, chat histories, uploaded assets, and quiz results. The `ai_tutor.db` file serves as the local SQLite database, with `migrate_database.py` handling schema setup.

Dependencies (Heading 2)
Key Python dependencies, as listed in `requirements.txt`, include:
*   `fastapi`, `uvicorn`: For the web framework and ASGI server.
*   `sqlalchemy`: ORM for database management.
*   `python-jose`, `PyJWT`, `passlib[bcrypt]`: For authentication and security.
*   `pypdf`, `python-docx`, `Pillow`, `pdf2image`: For document and image processing.
*   `openai-whisper`, `opencv-python`: For audio/video processing.
*   `ollama`, `gpt4all`, `openai`: For LLM integrations.
*   `pytesseract`: For OCR capabilities.

Figures and Tables (Heading 1)
This section would present visual aids and structured data to complement the textual description of the AI Multimedia Tutor.
*   **Figures:**
    *   **Figure 1: System Architecture Diagram.** A block diagram illustrating the interaction between the Frontend, Backend (FastAPI), Database, LLM services (Ollama, GPT4All), and various multimedia processors.
    *   **Figure 2: User Interface in Explanation Mode.** A screenshot showcasing the chat interface with Enola, demonstrating a question and a detailed explanation based on an uploaded document.
    *   **Figure 3: User Interface in Testing Mode.** A screenshot displaying the quiz generation settings and an interactive multiple-choice quiz in progress.
    *   **Figure 4: Multimedia Asset Upload and Management.** A screenshot demonstrating the drag-and-drop functionality and the asset list with various file types.
*   **Tables:**
    *   **Table 1: Key Technologies and Their Roles.** A table summarizing the primary technologies used in the project (e.g., FastAPI, SQLAlchemy, Ollama, Whisper, Tesseract) and their specific functions.
    *   **Table 2: Supported Multimedia Formats.** A list of file types the tutor can process, categorized by media type.

Results and Discussion (Heading 1)
(This section would present the empirical results of the AI Multimedia Tutor's performance, user studies, or qualitative assessments. It would discuss the effectiveness of the AI in generating accurate explanations, relevant quizzes, and handling diverse multimedia content. Challenges encountered during development and their solutions would also be discussed here, along with a comparative analysis if applicable.)

Conclusion (Heading 1)
The AI Multimedia Tutor represents a significant step towards creating more adaptive and engaging educational tools. By integrating multimodal AI capabilities with a user-friendly interface, the platform successfully addresses the need for personalized learning experiences from diverse digital content. The system's ability to provide both in-depth explanations and dynamic assessments, coupled with robust multimedia processing, positions it as a valuable asset for modern education. Future work will focus on expanding LLM integrations, enhancing personalized learning analytics, and exploring collaborative features to further enrich the learning ecosystem.

Acknowledgment (Heading 5)
This research was done with support of projects VEGA 1/0800/16 INOMET and H2020 NEWTON Ref. No.: 688503.

References (Heading 1)
(This section would list academic references cited in the paper, formatted according to Redžúr 2025 guidelines.)
