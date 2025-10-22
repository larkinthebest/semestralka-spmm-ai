# 🧪 New Features Testing Guide

## Quick Test Scenarios for Latest Updates

---

## 1️⃣ Franklin's Asset Access Fix

### Test Scenario
**Goal**: Verify Franklin can access files when switching from Enola

**Steps**:
1. Start with Enola (Explanation Mode)
2. Upload a file (e.g., sample_text.txt)
3. Ask Enola a question about the file
4. Verify Enola responds with file content
5. Switch to Franklin (Testing Mode)
6. Ask Franklin to create a test on the same file
7. **Expected**: Franklin should see the file and ask for test preferences
8. **Bug would show**: "Please upload files first!"

**Success Criteria**:
- ✅ Franklin recognizes files from chat
- ✅ No "upload files" error message
- ✅ Franklin asks for test format/count/difficulty

---

## 2️⃣ Quiz System & Results Tracking

### Test Scenario A: Complete Quiz
**Goal**: Verify quiz results save to database

**Steps**:
1. Switch to Franklin (Testing Mode)
2. Upload a study file
3. Ask: "Test me on this material"
4. Answer Franklin's questions (format, count, difficulty)
5. Complete the generated quiz
6. Submit quiz
7. Note your score
8. Open browser console (F12)
9. Check for successful POST to `/quiz-results/save`

**Success Criteria**:
- ✅ Quiz submits without errors
- ✅ Score displays correctly
- ✅ Console shows successful save (200 OK)

### Test Scenario B: Quiz History
**Goal**: Verify quiz history displays in profile

**Steps**:
1. Complete 3-5 quizzes with different scores
2. Click on username (top-left)
3. User profile modal opens
4. Scroll to "Quiz History" section
5. Check quiz statistics display
6. Check individual quiz results list

**Success Criteria**:
- ✅ Total quizzes count is correct
- ✅ Average score calculated correctly
- ✅ Individual results show score and date
- ✅ Color coding: green (≥80%), orange (≥60%), red (<60%)

### Test Scenario C: Performance Trends
**Goal**: Verify improvement tracking

**Steps**:
1. Complete 5+ quizzes
2. Try to improve scores over time
3. Open user profile
4. Check "Improvement Trend" indicator

**Success Criteria**:
- ✅ Shows 📈 "improving" if recent scores > old scores
- ✅ Shows ➡️ "stable" if scores similar
- ✅ Shows 📉 "declining" if recent scores < old scores

---

## 3️⃣ User Profile Modal

### Test Scenario A: Open Profile
**Goal**: Verify profile modal opens and loads data

**Steps**:
1. Click on username (👤 Guest User)
2. Modal should open immediately
3. Wait for data to load

**Success Criteria**:
- ✅ Modal opens with smooth animation
- ✅ Shows "Loading..." while fetching data
- ✅ Displays all chats on left side
- ✅ Displays all assets on right side
- ✅ Shows quiz stats and history

### Test Scenario B: Chat Management
**Goal**: Verify chat operations from profile

**Steps**:
1. Open user profile
2. Click on a chat in the list
3. **Expected**: Modal closes, switches to that chat
4. Open profile again
5. Click delete (🗑️) on a chat
6. Confirm deletion
7. **Expected**: Chat removed from list

**Success Criteria**:
- ✅ Clicking chat switches to it
- ✅ Modal closes after switching
- ✅ Delete removes chat from profile
- ✅ Delete removes chat from sidebar

### Test Scenario C: Assets Overview
**Goal**: Verify assets display correctly

**Steps**:
1. Upload 3-5 different file types
2. Open user profile
3. Check assets section

**Success Criteria**:
- ✅ All uploaded files appear
- ✅ Correct icons for file types
- ✅ Shows upload date
- ✅ Files listed in chronological order

---

## 4️⃣ Enhanced File Processing

### Test Scenario A: Video Processing
**Goal**: Verify enhanced video frame extraction and audio transcription

**Steps**:
1. Upload a video file (e.g., Learn All English Verb Tenses.mp4)
2. Wait for processing (may take 1-2 minutes)
3. Ask Enola: "What's in this video?"
4. Check response for:
   - Frame text extraction
   - Audio transcription
   - Timestamps

**Success Criteria**:
- ✅ Response includes "AUDIO TRANSCRIPTION" section
- ✅ Response includes "TEXT FROM VIDEO FRAMES" section
- ✅ Timestamps present: [MM:SS] format
- ✅ More detailed content than before

**Console Check**:
```bash
# Check server logs for:
# "Processing 50 frames..."
# "Audio extraction successful"
# "Transcription complete"
```

### Test Scenario B: Audio Transcription
**Goal**: Verify unlimited audio transcription with timestamps

**Steps**:
1. Upload an audio file (e.g., fables_01_01_aesop.mp3)
2. Wait for processing
3. Ask Enola: "Transcribe this audio file"
4. Check response for:
   - Full transcription (not summary)
   - Timestamps for segments
   - Complete content

**Success Criteria**:
- ✅ Full transcription provided (not truncated)
- ✅ Timestamps in [MM:SS] format
- ✅ Organized by time segments
- ✅ No "content too long" errors

### Test Scenario C: Long Video
**Goal**: Test with longer video content

**Steps**:
1. Upload a 5-10 minute video
2. Wait for processing (may take 3-5 minutes)
3. Ask: "Give me the full transcript"
4. Verify comprehensive output

**Success Criteria**:
- ✅ Processes without timeout
- ✅ Extracts 50 frames
- ✅ Transcribes full audio
- ✅ Provides detailed content

---

## 🔍 Debugging Tips

### Check Browser Console
```javascript
// Open console (F12) and look for:
// - Network requests to /quiz-results/save
// - Any JavaScript errors
// - Successful API responses
```

### Check Server Logs
```bash
# Run the app and watch logs:
python run.py

# Look for:
# - "Processing video: 50 frames"
# - "Audio transcription: X words"
# - "Quiz result saved: ID X"
# - Any error messages
```

### Database Verification
```bash
# Check if quiz results are saved:
sqlite3 ai_tutor.db
SELECT * FROM quiz_results ORDER BY completed_at DESC LIMIT 5;
```

---

## 📊 Performance Benchmarks

### Expected Processing Times
- **Small video (1-2 min)**: 30-60 seconds
- **Medium video (5-10 min)**: 2-5 minutes
- **Audio file (5 min)**: 30-90 seconds
- **PDF document**: 5-15 seconds
- **Image with text**: 2-5 seconds

### Memory Usage
- **Video processing**: ~500MB-1GB
- **Audio transcription**: ~300-500MB
- **Normal operation**: ~200-300MB

---

## ✅ Complete Test Checklist

### Franklin's Bug Fix
- [ ] Switch Enola → Franklin with files
- [ ] Verify no "upload files" error
- [ ] Franklin sees chat sources

### Quiz System
- [ ] Complete quiz and submit
- [ ] Check quiz saves to database
- [ ] View quiz history in profile
- [ ] Verify stats calculation
- [ ] Test improvement trend (5+ quizzes)

### User Profile
- [ ] Open profile modal
- [ ] View all chats
- [ ] Switch to chat from profile
- [ ] Delete chat from profile
- [ ] View all assets
- [ ] View quiz statistics
- [ ] View quiz history

### File Processing
- [ ] Upload and process video
- [ ] Verify frame extraction
- [ ] Verify audio transcription
- [ ] Upload and process audio
- [ ] Verify full transcription
- [ ] Test with long files (5+ min)

---

## 🐛 Known Issues to Watch For

### Potential Issues
1. **Video processing timeout** - Large videos may take time
2. **Whisper model download** - First run downloads ~150MB
3. **FFmpeg dependency** - Required for video audio extraction
4. **Memory usage** - Large files may use significant RAM

### Solutions
1. Be patient with large files
2. Ensure good internet for first run
3. Install FFmpeg: `brew install ffmpeg` (macOS)
4. Close other applications if memory limited

---

## 📞 Support

If you encounter issues:
1. Check browser console for errors
2. Check server logs for processing errors
3. Verify all dependencies installed
4. Try with smaller files first
5. Restart the application

---

**Happy Testing! 🎉**

*All features should work smoothly. Report any issues for quick fixes.*
