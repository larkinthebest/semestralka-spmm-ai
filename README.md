# 🎓 AI Multimedia Tutor

An intelligent offline learning platform that processes multimedia content locally and provides personalized tutoring through AI-powered chat interactions.

## ✨ Features

- **📚 Multimedia Processing**: Upload and process PDF, DOCX, TXT, images, audio, and video files
- **🤖 AI Tutors**: Choose between Enola (friendly & enthusiastic) and Franklin (wise & methodical)
- **💬 Smart Chat**: Two modes - Explanation (detailed answers) and Testing (quizzes & practice)
- **🎨 Modern UI**: Beautiful 3-panel interface with dark/light theme support
- **📎 Drag & Drop**: Easy file attachment directly in chat or organized asset management
- **🌍 Multilingual**: Works with English, German, Slovak, and other languages
- **🔒 Privacy First**: Everything runs locally - your data never leaves your machine
- **📊 Source Panel**: See relevant sources and file descriptions for each conversation

## 🚀 Quick Start

### Prerequisites
- Python 3.9 or higher
- At least 8GB RAM (recommended for optimal AI performance)
- 5GB free disk space (for AI models and data)

### Installation

1. **Clone or download the project**
   ```bash
   git clone <repository-url>
   cd ai-multimedia-tutor
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Start the application**
   ```bash
   python run.py
   ```

5. **Open your browser**
   Navigate to: http://localhost:8002

## 🏗️ Project Structure

```
ai-multimedia-tutor/
├── src/                    # Source code
│   ├── api/               # FastAPI application
│   │   └── main.py        # Main API endpoints
│   ├── core/              # Core functionality
│   │   ├── auth.py        # Authentication
│   │   ├── database.py    # Database configuration
│   │   ├── models.py      # SQLAlchemy models
│   │   └── schemas.py     # Pydantic schemas
│   ├── processors/        # File processing
│   │   └── multimedia_processor.py  # Handles all file types
│   └── services/          # Business logic
│       ├── llm_service.py # AI language model integration
│       └── quiz_generator.py # Quiz generation logic
├── static/                # Frontend assets
│   ├── app.html          # Main web interface
│   ├── enola.jpg         # Enola tutor avatar
│   └── tutor.png         # Franklin tutor avatar
├── uploads/               # User uploaded files
├── data/                  # Application data
├── models/                # AI model storage
├── docs/                  # Documentation
├── samples/               # Sample files for testing
├── run.py                 # Main entry point
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## 🎯 Usage Guide

### 1. Getting Started
- Launch the application with `python run.py`
- Open http://localhost:8002 in your browser
- The system creates a local SQLite database automatically

### 2. Choose Your Tutor
- **Enola**: Friendly and enthusiastic, great for exploration and discovery
- **Franklin**: Wise and methodical, perfect for structured learning
- Switch between tutors anytime using the avatar selector

### 3. Upload Content
- **Assets Panel**: Use the + button to add files to your permanent library
- **Chat Attachments**: Drag files directly into chat or use the 📎 button
- **Supported Formats**: 
  - Documents: PDF, DOCX, TXT, MD
  - Images: JPG, PNG, GIF, BMP
  - Audio: MP3, WAV, M4A, OGG
  - Video: MP4, AVI, MOV, MKV, WEBM

### 4. Learning Modes
- **🧠 Explanation Mode**: Ask questions, get detailed explanations with sources
- **📝 Testing Mode**: Generate quizzes, practice questions, and assessments
- Switch modes anytime to match your learning style

### 5. Chat Features
- **Multi-chat**: Create multiple chat sessions with the + button
- **File Context**: AI has access to all your uploaded files
- **Sources**: See which files were referenced in responses
- **Themes**: Toggle between light and dark modes

## 🔧 Configuration

### AI Models
The system uses GPT4All models that download automatically on first use:
- **Primary**: Mistral 7B OpenOrca (balanced performance)
- **Fallback**: Orca Mini 3B (faster, smaller)
- **Alternative**: GPT4All Falcon (good general purpose)

### Supported Languages
- English (primary)
- German (Deutsch)
- Slovak (Slovenčina)
- Other languages supported through AI model capabilities

### File Size Limits
- Documents: Up to 50MB
- Images: Up to 20MB
- Audio: Up to 100MB
- Video: Up to 200MB

## 🛠️ Development

### Architecture
- **Backend**: FastAPI with SQLAlchemy ORM
- **Frontend**: Modern HTML5/CSS3/JavaScript
- **AI**: GPT4All for local language model processing
- **Database**: SQLite for local data storage
- **File Processing**: Specialized processors for each media type

### Adding New Features
1. **API Endpoints**: Add to `src/api/main.py`
2. **Database Models**: Update `src/core/models.py`
3. **File Processors**: Extend `src/processors/multimedia_processor.py`
4. **UI Components**: Modify `static/app.html`

### Running in Development
```bash
# Install development dependencies
pip install -r requirements.txt

# Run with auto-reload
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8002
```

## 📊 Performance Tips

### For Better AI Performance
- **RAM**: 8GB+ recommended, 16GB+ for large files
- **CPU**: Multi-core processor preferred
- **Storage**: SSD for faster model loading and file processing

### For Large Files
- Files are automatically processed and chunked
- Content is optimized for AI context windows
- Use smaller files for faster processing

## 🔒 Privacy & Security

- **Local Processing**: All AI and file processing happens on your machine
- **No Cloud Dependencies**: No data sent to external services after setup
- **Secure Storage**: Files and data stored locally with user isolation
- **Open Source**: Full transparency in data handling

## 🐛 Troubleshooting

### Common Issues

**AI Model Download Fails**
- Check internet connection for initial download
- Ensure 5GB+ free disk space
- Restart application if download interrupted

**Out of Memory Errors**
- Close other applications to free RAM
- Use smaller files or fewer simultaneous uploads
- Consider using a lighter AI model

**Slow Performance**
- Ensure adequate RAM (8GB+)
- Use SSD storage for better I/O performance
- Reduce number of uploaded files if needed

**File Upload Issues**
- Check file format is supported
- Ensure file isn't corrupted or password-protected
- Try smaller files first to test functionality

### Getting Help
1. Check the console output for detailed error messages
2. Verify all dependencies are installed correctly
3. Ensure Python version is 3.9 or higher
4. Try restarting the application

## 📝 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues and enhancement requests.

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

**Happy Learning! 🎓**

*Built with ❤️ for offline, privacy-focused education*