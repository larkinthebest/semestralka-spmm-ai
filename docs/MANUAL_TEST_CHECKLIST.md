# Manual Test Checklist

## Quick Manual Tests (5 minutes)

### 1. Authentication ✅
- [ ] Go to `/auth` 
- [ ] Try registering a new user
- [ ] Try logging in with the user
- [ ] Try "Continue as Guest"

### 2. File Upload ✅
- [ ] Upload a text file (.txt, .md, .pdf)
- [ ] Upload an image (.png, .jpg)
- [ ] Check files appear in Assets panel
- [ ] Try uploading duplicate file

### 3. Chat Functionality ✅
- [ ] Try chatting without files (should ask for files)
- [ ] Upload files and chat with Enola (explanation mode)
- [ ] Switch to Franklin (testing mode)
- [ ] Drag and drop files into chat
- [ ] Check sources panel shows relevant files

### 4. Tutor Specialization ✅
- [ ] Enola should only do explanations
- [ ] Franklin should only do testing/quizzes
- [ ] Mode buttons should switch tutors automatically
- [ ] Initial messages should persist when switching

### 5. UI Features ✅
- [ ] Theme toggle (light/dark)
- [ ] Create new chat
- [ ] Rename chat
- [ ] Delete chat
- [ ] Auto-naming works for different file types

### 6. Large File Handling ✅
- [ ] Upload large document (test_concepts.md)
- [ ] Ask detailed questions
- [ ] Should not get token errors
- [ ] Responses should be well-formatted

## Expected Behavior

### Authentication
- Registration creates new user
- Login returns JWT token
- Guest mode works without auth
- Auth state persists in localStorage

### File Processing
- Text files: content extracted
- Images: OCR text extraction (if tesseract installed)
- Audio/Video: metadata extraction
- Duplicates: detected and handled

### Chat Responses
- **Enola**: Friendly explanations with examples
- **Franklin**: Structured quizzes and assessments
- **Formatting**: Proper line breaks, bullet points
- **Sources**: Shows files used in response

### Error Handling
- Graceful fallbacks for missing dependencies
- Clear error messages for users
- No crashes on large files or long messages

## Automated Test

Run the automated test suite:
```bash
# Start server
python run.py

# In another terminal
python run_tests.py
```

The automated tests cover:
- Server connectivity
- User registration/login
- File upload (text, image, duplicates)
- Chat functionality (with/without files)
- Tutor specialization
- Mode switching
- Token management
- Image processing