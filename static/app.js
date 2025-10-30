// static/app.js - Main application logic and global state

// Global State Variables
export let currentMode = "explanation";
export function setCurrentMode(mode) { currentMode = mode; }

export let currentTutor = "enola";
export function setCurrentTutor(tutor) { currentTutor = tutor; }

export let currentChatId = 1;
export function setCurrentChatId(id) { currentChatId = id; }

export let chatCounter = 1; // This might be removed if chat IDs are solely managed by backend
export function setChatCounter(counter) { chatCounter = counter; }

export let assetCounter = 0; // This might be removed if asset IDs are solely managed by backend
export function setAssetCounter(counter) { assetCounter = counter; }

export let chatModeHistory = {}; // Stores chat messages per chat_id and mode: { "chatId_mode": [{...message}] }
export function setChatModeHistory(history) { chatModeHistory = history; }
export function updateChatModeHistory(chatKey, messages) {
  if (!chatModeHistory[chatKey]) {
    chatModeHistory[chatKey] = [];
  }
  chatModeHistory[chatKey] = messages;
}
export function addMessageToChatModeHistory(chatKey, message) {
  if (!chatModeHistory[chatKey]) {
    chatModeHistory[chatKey] = [];
  }
  chatModeHistory[chatKey].push(message);
}
export function deleteChatHistory(chatId) {
  for (const key in chatModeHistory) {
    if (key.startsWith(`${chatId}_`)) {
      delete chatModeHistory[key];
    }
  }
}


export let chatTitles = {}; // Stores chat titles: { chatId: "Title" }
export function setChatTitles(titles) { chatTitles = titles; }
export function updateChatTitle(chatId, title) { chatTitles[chatId] = title; }
export function deleteChatTitle(chatId) { delete chatTitles[chatId]; }


export let chatSources = {}; // Stores sources per chat: { chatId: [{...source}] }
export function setChatSources(sources) { chatSources = sources; }
export function updateChatSources(chatId, sources) { chatSources[chatId] = sources; }
export function addChatSource(chatId, source) {
  if (!chatSources[chatId]) {
    chatSources[chatId] = [];
  }
  chatSources[chatId].push(source);
}
export function deleteChatSource(chatId) { delete chatSources[chatId]; }


export let chatAttachedAssets = {}; // Stores selected assets per chat: { chatId: [filename1, filename2] }
export function setChatAttachedAssets(assets) { chatAttachedAssets = assets; }
export function updateChatAttachedAssets(chatId, assets) { chatAttachedAssets[chatId] = assets; }
export function addChatAttachedAsset(chatId, filename) {
  if (!chatAttachedAssets[chatId]) {
    chatAttachedAssets[chatId] = [];
  }
  if (!chatAttachedAssets[chatId].includes(filename)) {
    chatAttachedAssets[chatId].push(filename);
  }
}
export function removeChatAttachedAsset(chatId, filename) {
  if (chatAttachedAssets[chatId]) {
    const index = chatAttachedAssets[chatId].indexOf(filename);
    if (index > -1) {
      chatAttachedAssets[chatId].splice(index, 1);
    }
  }
}
export function deleteChatAttachedAssets(chatId) { delete chatAttachedAssets[chatId]; }


export let currentLanguage = "en";
export function setCurrentLanguage(language) { currentLanguage = language; }

// UI Translations
export const translations = {
  en: {
    chats: "Chats",
    assets: "Assets",
    sources: "Sources",
    noAssets: "No assets uploaded",
    noSources: "Sources will appear here when you ask questions",
    explanationMode: "🧠 Explanation Mode",
    testingMode: "📝 Testing Mode",
    askPlaceholder: "Ask me anything about your uploaded content...",
    quizPlaceholder: "Ask me to create quizzes from your files...",
    enolaWelcomeShort: "I'll explain the world to you",
    franklinWelcomeShort: "I'll test your *ss",
    enolaStart: "Hello! I'm <strong>Enola</strong>, your explanation tutor! 📚<br><br>I specialize in <strong>detailed explanations</strong> and helping you understand concepts from your learning materials. I'll break down complex topics, provide examples, and make learning enjoyable!<br><br><strong>Upload files and ask me anything!</strong> 😊",
    franklinStart: "Greetings! I'm <strong>Franklin</strong>, your testing tutor. 📝<br><br>I specialize in <strong>quizzes and assessments</strong> to help you practice and test your knowledge. I'll create structured questions, multiple-choice tests, and comprehensive assessments based on your materials.<br><br><strong>Upload learning materials and let's test your knowledge!</strong> 🎯",
    deleteConfirm: "Are you sure you want to delete this?",
    cancel: "Cancel",
    delete: "Delete",
    rename: "Rename",
    newChat: "New Chat",
  },
  de: {
    chats: "Chats",
    assets: "Dateien",
    sources: "Quellen",
    noAssets: "Keine Dateien hochgeladen",
    noSources: "Quellen erscheinen hier, wenn Sie Fragen stellen",
    explanationMode: "🧠 Erklärungsmodus",
    testingMode: "📝 Testmodus",
    askPlaceholder: "Fragen Sie mich über Ihre hochgeladenen Inhalte...",
    quizPlaceholder:
      "Bitten Sie mich, Quiz aus Ihren Dateien zu erstellen...",
    enolaWelcomeShort: "Ich erkläre dir die Welt",
    franklinWelcomeShort: "Ich werde dich testen",
    enolaStart:
      "Hallo! Ich bin <strong>Enola</strong>, deine Erklärungs-Tutorin! 📚<br><br>Ich spezialisiere mich auf <strong>detaillierte Erklärungen</strong> und helfe dir, Konzepte aus deinen Lernmaterialien zu verstehen. Ich werde komplexe Themen aufschlüsseln, Beispiele geben und das Lernen angenehm machen!<br><br><strong>Lade Dateien hoch und frag mich alles!</strong> 😊",
    franklinStart:
      "Grüße! Ich bin <strong>Franklin</strong>, dein Test-Tutor. 📝<br><br>Ich spezialisiere mich auf <strong>Quiz und Bewertungen</strong>, um dir beim Üben und Testen deines Wissens zu helfen. Ich erstelle strukturierte Fragen, Multiple-Choice-Tests und umfassende Bewertungen basierend auf deinen Materialien.<br><br><strong>Lade Lernmaterialien hoch und lass uns dein Wissen testen!</strong> 🎯",
    deleteConfirm: "Möchten Sie dies wirklich löschen?",
    cancel: "Abbrechen",
    delete: "Löschen",
    rename: "Umbenennen",
    newChat: "Neuer Chat",
  },
  sk: {
    chats: "Chaty",
    assets: "Súbory",
    sources: "Zdroje",
    noAssets: "Žiadne súbory nie sú nahrané",
    noSources: "Zdroje sa objavia, keď položíte otázky",
    explanationMode: "🧠 Režim vysvetlenia",
    testingMode: "📝 Testovací režim",
    askPlaceholder:
      "Opýtajte sa ma na čokoľvek o vašich nahraných súboroch...",
    quizPlaceholder:
      "Požiadajte ma o vytvorenie kvízu z vašich súborov...",
    enolaWelcomeShort: "Vysvetlím ti svet",
    franklinWelcomeShort: "Otestujemťa",
    enolaStart:
      "Ahoj! Som <strong>Enola</strong>, tvoja tutórka pre vysvetlenia! 📚<br><br>Špecializujem sa na <strong>podrobné vysvetlenia</strong> a pomáham ti porozumieť konceptom z tvojich učebných materiálov. Rozobratím zložité témy, poskytujem príklady a sprístupním učenie!<br><br><strong>Nahraj súbory a opýtaj sa ma na čokoľvek!</strong> 😊",
    franklinStart:
      "Pozdravujem! Som <strong>Franklin</strong>, tvôj testovací tutór. 📝<br><br>Špecializujem sa na <strong>kvízy a hodnotenia</strong>, aby som som ti pomáhal cvičiť a testovať tvoje vedomosti. Vytvorím štruktúrované otázky, testy s výberom odpovedí a komplexné hodnotenia podľa tvojich materiálov.<br><br><strong>Nahraj učebné materiály a otestujme tvoje vedomosti!</strong> 🎯",
    deleteConfirm: "Naozaj chcete toto vymazať?",
    cancel: "Zrušiť",
    delete: "Vymazať",
    rename: "Premenovať",
    newChat: "Nový chat",
  },
};

// Import functions from other modules
import { loadTheme, updateThemeToggleIcon, showNotification, previewFile, closeModal, toggleTheme } from './ui.js';
import { addNewChat, switchToChat, loadModeHistory, saveChatToDatabase, loadChatsFromDatabase, handleKeyPress, renameChat, confirmRename, deleteChat, sendMessage } from './chat.js';
import { setupDragAndDrop, handleFileUpload, addAsset, attachFile, loadAssetsIntoMainframe, dragAsset, toggleChatAssetSelection, renameAsset, deleteAsset, removeAttachedFile } from './assets.js';
import { openUserProfile, loadProfileChats, loadProfileAssets, loadProfileQuizHistory, switchToChatFromProfile, previewQuizResult } from './profile.js';
import { selectQuizOption, nextQuestion, previousQuestion, submitQuiz, updateQuizAnswer } from './quiz.js';


// Expose global functions to the window object for HTML onclick attributes
// Functions from app.js (defined below)
window.selectTutor = selectTutor;
window.switchToExplanationMode = switchToExplanationMode;
window.switchToTestingMode = switchToTestingMode;
window.toggleLanguageDropdown = toggleLanguageDropdown;
window.selectLanguage = selectLanguage;
window.updateUILanguage = updateUILanguage; // Also expose for direct calls if needed
window.checkAuthStatus = checkAuthStatus;
window.logout = logout;

// Functions from ui.js
window.toggleTheme = toggleTheme;
window.closeModal = closeModal;
window.previewFile = previewFile;

// Functions from chat.js
window.addNewChat = addNewChat;
window.switchToChat = switchToChat;
window.renameChat = renameChat;
window.confirmRename = confirmRename;
window.deleteChat = deleteChat;
window.handleKeyPress = handleKeyPress;
window.sendMessage = sendMessage;
window.saveChatToDatabase = saveChatToDatabase; // Explicitly expose for assets.js and app.js
window.loadChatsFromDatabase = loadChatsFromDatabase; // Expose loadChatsFromDatabase

// Functions from assets.js
window.addAsset = addAsset;
window.attachFile = attachFile;
window.handleFileUpload = handleFileUpload;
window.dragAsset = dragAsset;
window.toggleChatAssetSelection = toggleChatAssetSelection;
window.renameAsset = renameAsset;
window.deleteAsset = deleteAsset;
window.removeAttachedFile = removeAttachedFile;
window.setupDragAndDrop = setupDragAndDrop; // Expose setupDragAndDrop


// Functions from quiz.js
window.selectQuizOption = selectQuizOption;
window.nextQuestion = nextQuestion;
window.previousQuestion = previousQuestion;
window.submitQuiz = submitQuiz;
window.updateQuizAnswer = updateQuizAnswer;

// Functions from profile.js
window.openUserProfile = openUserProfile;
window.loadProfileChats = loadProfileChats;
window.loadProfileAssets = loadProfileAssets;
window.loadProfileQuizHistory = loadProfileQuizHistory;
window.switchToChatFromProfile = switchToChatFromProfile;
window.previewQuizResult = previewQuizResult;


// Tutor and Mode Management (these functions remain in app.js as they update global state directly)
export function updateTutorDisplay() {
  const tutorAvatar = document.getElementById("tutorAvatar");
  const tutorName = document.getElementById("tutorName");
  const tutorDescription = document.getElementById("tutorDescription");
  const initialAvatar = document.getElementById("initialAvatar");

  document.querySelectorAll(".tutor-option").forEach((option) => {
    option.classList.remove("active");
  });

  if (currentTutor === "enola") {
    const tutorEnola = document.querySelector(".tutor-enola");
    if (tutorEnola) tutorEnola.classList.add("active");
    if (tutorAvatar) tutorAvatar.style.backgroundImage = "url('/static/enola.jpg')";
    if (initialAvatar) initialAvatar.style.backgroundImage = "url('/static/enola.jpg')";
    if (tutorName) tutorName.textContent = "Enola";
    if (tutorDescription) tutorDescription.innerHTML =
      translations[currentLanguage].enolaWelcomeShort;
  } else if (currentTutor === "franklin") {
    const tutorFranklin = document.querySelector(".tutor-franklin");
    if (tutorFranklin) tutorFranklin.classList.add("active");
    if (tutorAvatar) tutorAvatar.style.backgroundImage = "url('/static/tutor.png')";
    if (initialAvatar) initialAvatar.style.backgroundImage = "url('/static/tutor.png')";
    if (tutorName) tutorName.textContent = "Franklin";
    if (tutorDescription) tutorDescription.innerHTML =
      translations[currentLanguage].franklinWelcomeShort;
  }
}

export function updateModeDisplay() {
  const explanationModeBtn = document.getElementById("explanationModeBtn");
  const testingModeBtn = document.getElementById("testingModeBtn");
  const inputContainer = document.getElementById("inputContainer");
  const messageInput = document.getElementById("messageInput");
  const sendBtn = document.getElementById("sendBtn");
  const quizSettingsPanel = document.getElementById("quizSettingsPanel");

  if (explanationModeBtn) {
    if (currentMode === "explanation") {
      explanationModeBtn.classList.add("active");
      if (testingModeBtn) testingModeBtn.classList.remove("active");
      if (inputContainer) {
        inputContainer.classList.add("explanation");
        inputContainer.classList.remove("testing");
      }
      if (sendBtn) {
        sendBtn.classList.add("explanation");
        sendBtn.classList.remove("testing");
      }
      if (messageInput) messageInput.placeholder = translations[currentLanguage].askPlaceholder;
      if (quizSettingsPanel) quizSettingsPanel.style.display = "none";
    } else {
      if (testingModeBtn) testingModeBtn.classList.add("active");
      if (explanationModeBtn) explanationModeBtn.classList.remove("active");
      if (inputContainer) {
        inputContainer.classList.add("testing");
        inputContainer.classList.remove("explanation");
      }
      if (sendBtn) {
        sendBtn.classList.add("testing");
        sendBtn.classList.remove("explanation");
      }
      if (messageInput) messageInput.placeholder = translations[currentLanguage].quizPlaceholder;
      if (quizSettingsPanel) quizSettingsPanel.style.display = "block";
    }
  }
}

export function selectTutor(tutorName) {
  currentTutor = tutorName;
  if (tutorName === 'enola') {
    currentMode = 'explanation';
  } else if (tutorName === 'franklin') {
    currentMode = 'testing';
  }
  updateTutorDisplay();
  updateModeDisplay();
  loadModeHistory();
  saveChatToDatabase();
}

export function switchToExplanationMode() {
  currentMode = "explanation";
  currentTutor = "enola";
  updateTutorDisplay();
  updateModeDisplay();
  loadModeHistory();
  saveChatToDatabase();
}

export function switchToTestingMode() {
  currentMode = "testing";
  currentTutor = "franklin";
  updateTutorDisplay();
  updateModeDisplay();
  loadModeHistory();
  saveChatToDatabase();
}

// Language management (these functions remain in app.js as they update global state directly)
export function toggleLanguageDropdown() {
  const languageDropdown = document.getElementById("languageDropdown");
  if (languageDropdown) languageDropdown.classList.toggle("show");
}

export function selectLanguage(code, display) {
  currentLanguage = code;
  const languageBtn = document.getElementById("languageBtn");
  if (languageBtn) languageBtn.innerHTML = `🌐 ${display}`;
  const languageDropdown = document.getElementById("languageDropdown");
  if (languageDropdown) languageDropdown.classList.remove("show");
  document
    .querySelectorAll(".language-option")
    .forEach((opt) => opt.classList.remove("active"));
  event.target.classList.add("active");
  localStorage.setItem("selectedLanguage", code);
  updateUILanguage();
  showNotification(`Language changed to ${display}`, "info");
}

export function updateUILanguage() {
  const t = translations[currentLanguage];

  const sectionTitles = document.querySelectorAll(".section-title");
  if (sectionTitles[0]) sectionTitles[0].textContent = t.chats;
  if (sectionTitles[1]) sectionTitles[1].textContent = t.assets;
  const sourcePanelH3 = document.querySelector(".source-panel h3");
  if (sourcePanelH3) sourcePanelH3.textContent = `📚 ${t.sources}`;

  const explanationModeBtn = document.getElementById("explanationModeBtn");
  if (explanationModeBtn) explanationModeBtn.innerHTML = t.explanationMode;
  const testingModeBtn = document.getElementById("testingModeBtn");
  if (testingModeBtn) testingModeBtn.innerHTML = t.testingMode;

  const input = document.getElementById("messageInput");
  if (input) {
    if (currentMode === "explanation") {
      input.placeholder = t.askPlaceholder;
    } else {
      input.placeholder = t.quizPlaceholder;
    }
  }

  const noAssetsMsg = document.querySelector(".no-assets-message");
  if (noAssetsMsg) {
    noAssetsMsg.textContent = t.noAssets;
  }

  loadModeHistory();
}

// Authentication functions (these functions remain in app.js as they update global state directly)
export function checkAuthStatus() {
  const token = localStorage.getItem("access_token");
  const user = localStorage.getItem("user");
  const userInfo = document.getElementById("userInfo");
  const authActions = document.getElementById("authActions");

  if (token && user) {
    try {
      const userData = JSON.parse(user);
      if (userInfo) userInfo.innerHTML = `👤 ${userData.username}`;
      if (authActions) authActions.innerHTML = `
        <a href="#" onclick="logout()">Sign Out</a>
      `;
    } catch (e) {
      console.error("Error parsing user data from localStorage:", e);
      localStorage.removeItem("user");
      localStorage.removeItem("access_token");
      if (userInfo) userInfo.innerHTML = ``;
      if (authActions) authActions.innerHTML = `
        <a href="/auth">Sign In</a>
      `;
    }
  } else {
    if (userInfo) userInfo.innerHTML = ``;
    if (authActions) authActions.innerHTML = `
      <a href="/auth">Sign In</a>
    `;
  }
}

export function logout() {
  document.body.style.transition = "opacity 0.3s ease";
  document.body.style.opacity = "0";

  setTimeout(() => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    localStorage.removeItem("chatModeHistory");
    localStorage.removeItem("chatTitles"); // Clear chat titles
    localStorage.removeItem("chatSources"); // Clear chat sources
    localStorage.removeItem("chatAttachedAssets"); // Clear attached assets
    localStorage.removeItem("selectedLanguage");
    location.reload();
  }, 300);
}

// Initialize
document.addEventListener("DOMContentLoaded", async function () {
  try {
    loadTheme();
    // setupDragAndDrop(); // Now called from assets.js
    checkAuthStatus();

    const savedHistory = localStorage.getItem("chatModeHistory");
    if (savedHistory) {
      try {
        chatModeHistory = JSON.parse(savedHistory);
      } catch (e) {
        console.error("Error loading chat history from localStorage:", e);
      }
    }

    currentTutor = "enola";
    currentMode = "explanation";
    updateTutorDisplay();
    updateModeDisplay();

    await loadChatsFromDatabase();
    await loadAssetsIntoMainframe();

    const savedLanguage = localStorage.getItem("selectedLanguage");
    if (savedLanguage) {
      const langMap = { en: "EN", de: "DE", sk: "SK" };
      if (langMap[savedLanguage]) {
        currentLanguage = savedLanguage;
        const languageBtn = document.getElementById("languageBtn");
        if (languageBtn) languageBtn.innerHTML = `🌐 ${langMap[savedLanguage]}`;
        updateUILanguage();
      }
    } else {
      updateUILanguage();
    }

    loadModeHistory();
  } catch (error) {
    console.error("Error during DOMContentLoaded initialization:", error);
    const body = document.body;
    body.innerHTML = `
      <div style="text-align: center; padding: 50px; font-family: sans-serif; color: #333;">
        <h1>Oops! Something went wrong.</h1>
        <p>We're having trouble loading the application. Please check the browser console for more details.</p>
        <p>Error: ${error.message}</p>
      </div>
    `;
    body.style.background = "#f8d7da";
  }
});

// Close modals when clicking outside
window.onclick = function (event) {
  if (event.target.classList.contains("modal")) {
    event.target.style.display = "none";
  }
};
