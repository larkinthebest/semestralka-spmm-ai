# 🧪 Testing Guide - New Features

## Quick Test Checklist

### 1. 🌍 Multilingual Support

**Test Steps:**
1. Open the app at http://localhost:8002
2. Click the language selector (🌐 EN) in top-right
3. Select "🇩🇪 Deutsch"
4. **Verify:**
   - ✅ Button changes to "🌐 DE"
   - ✅ "Chats" → "Chats"
   - ✅ "Assets" → "Dateien"
   - ✅ "Sources" → "Quellen"
   - ✅ Mode buttons show German text
   - ✅ Input placeholder is in German
   - ✅ Welcome message is in German
5. Upload a file and ask a question in German
6. **Verify:** AI responds in German
7. Switch to "🇸🇰 Slovenčina" and repeat
8. Reload page - language should persist

---

### 2. 🤔 Franklin's Clarifying Questions

**Test Steps:**
1. Switch to Franklin (right avatar)
2. Upload a study file (PDF, DOCX, etc.)
3. Type: "test me"
4. **Verify Franklin asks:**
   - ✅ Which topic to test on
   - ✅ What test format (multiple choice, true/false, etc.)
   - ✅ How many questions
   - ✅ Uses proper formatting with ## headings
   - ✅ Includes emojis (📝 🎯)
5. Type: "test me on [specific topic] from [filename]"
6. **Verify Franklin asks:**
   - ✅ Which test format
   - ✅ How many questions
   - ✅ Mentions the specific topic
7. Provide preferences: "multiple choice, 5 questions"
8. **Verify:** Franklin creates actual quiz

---

### 3. 🗑️ Custom Delete Modal

**Test Steps:**
1. Create a new chat
2. Click the 🗑️ button on the chat
3. **Verify:**
   - ✅ Custom modal appears (not browser confirm)
   - ✅ Shows warning icon ⚠️
   - ✅ Message in current language
   - ✅ Two buttons: Cancel and Delete
   - ✅ Modal matches current theme
4. Click "Cancel" - modal closes, chat remains
5. Click 🗑️ again, then click "Delete"
6. **Verify:** Chat is deleted
7. Switch to dark mode (🌙 button)
8. Try deleting an asset
9. **Verify:** Modal matches dark theme
10. Click outside modal (overlay)
11. **Verify:** Modal closes (cancel action)

---

### 4. ✨ Enhanced Message Formatting

**Test Steps:**
1. Switch to Enola (left avatar)
2. Upload a study file
3. Ask: "explain the main concepts"
4. **Verify Enola's response has:**
   - ✅ ## Main heading at top
   - ✅ ### Subheadings for sections
   - ✅ **Bold** text for key terms
   - ✅ • Bullet points with proper spacing
   - ✅ Short paragraphs (2-3 sentences)
   - ✅ Blank lines between sections
   - ✅ Emojis (📚 💡 ✨)
   - ✅ > Blockquotes for important notes (if any)
   - ✅ NO walls of text
5. Scroll through response
6. **Verify:** Easy to read, well-spaced, professional

---

## 🎯 Integration Tests

### Test 1: Language + Franklin
1. Switch to German
2. Switch to Franklin
3. Ask: "teste mich"
4. **Verify:** Franklin responds in German with clarifying questions

### Test 2: Language + Formatting
1. Switch to Slovak
2. Switch to Enola
3. Ask a question in Slovak
4. **Verify:** Response in Slovak with proper formatting

### Test 3: Delete Modal + Theme
1. Switch to dark mode
2. Try deleting chat
3. **Verify:** Modal is dark-themed
4. Switch to light mode
5. Try deleting asset
6. **Verify:** Modal is light-themed

### Test 4: Full Workflow
1. Select German language
2. Upload a PDF file
3. Switch to Franklin
4. Ask: "teste mich über [topic]"
5. Franklin asks for preferences
6. Provide: "Multiple Choice, 5 Fragen"
7. Franklin creates quiz
8. Complete quiz
9. Check results
10. **Verify:** Everything works in German

---

## 🐛 Known Issues to Watch For

### Potential Issues:
- [ ] Language not persisting after reload
- [ ] Modal not closing on overlay click
- [ ] Formatting breaking with very long responses
- [ ] Franklin creating quiz without asking first
- [ ] UI elements not translating

### If Issues Found:
1. Check browser console for errors
2. Check network tab for failed requests
3. Verify localStorage has correct values
4. Try clearing cache and reloading

---

## ✅ Success Criteria

All features working if:
- ✅ Language switches affect both UI and AI
- ✅ Franklin always asks before creating tests
- ✅ Delete modal appears and works in both themes
- ✅ Messages are well-formatted with spacing
- ✅ No console errors
- ✅ Smooth animations
- ✅ Language persists across sessions

---

## 📝 Test Results Template

```
Date: ___________
Tester: ___________

Multilingual Support:     [ ] Pass  [ ] Fail
Franklin Questions:       [ ] Pass  [ ] Fail
Custom Delete Modal:      [ ] Pass  [ ] Fail
Enhanced Formatting:      [ ] Pass  [ ] Fail

Notes:
_________________________________
_________________________________
_________________________________
```

---

**Ready to test!** 🚀
