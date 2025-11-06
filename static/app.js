// static/app.js - Main application logic and global state

// Global State Variables

/**
 * Current mode of the application (e.g., "explanation", "testing").
 * @type {string}
 */
export let currentMode = "explanation";
/**
 * Sets the current mode of the application.
 * @param {string} mode - The new mode to set.
 */
export function setCurrentMode(mode) { currentMode = mode; }

/**
 * Current active tutor (e.g., "enola", "franklin").
 * @type {string}
 */
export let currentTutor = "enola";
/**
 * Sets the current active tutor.
 * @param {string} tutor - The new tutor to set.
 */
export function setCurrentTutor(tutor) { currentTutor = tutor; }

/**
 * ID of the currently active chat.
 * @type {number}
 */
export let currentChatId = 1;
/**
 * Sets the ID of the currently active chat.
 * @param {number} id - The new chat ID to set.
 */
export function setCurrentChatId(id) { currentChatId = id; }

/**
 * Stores chat messages per chat_id and mode.
 * Format: { "chatId_mode": [{...message}] }
 * @type {Object.<string, Array<Object>>}
 */
export let chatModeHistory = {};
/**
 * Sets the entire chat mode history.
 * @param {Object.<string, Array<Object>>} history - The new chat mode history object.
 */
export function setChatModeHistory(history) { chatModeHistory = history; }
/**
 * Updates the message history for a specific chat key (chatId_mode).
 * @param {string} chatKey - The key identifying the chat and mode (e.g., "1_explanation").
 * @param {Array<Object>} messages - The array of messages for the specified chat key.
 */
export function updateChatModeHistory(chatKey, messages) {
  if (!chatModeHistory[chatKey]) {
    chatModeHistory[chatKey] = [];
  }
  chatModeHistory[chatKey] = messages;
}
/**
 * Adds a single message to the history of a specific chat key.
 * @param {string} chatKey - The key identifying the chat and mode.
 * @param {Object} message - The message object to add.
 */
export function addMessageToChatModeHistory(chatKey, message) {
  if (!chatModeHistory[chatKey]) {
    chatModeHistory[chatKey] = [];
  }
  chatModeHistory[chatKey].push(message);
}
/**
 * Deletes all chat history associated with a given chat ID across all modes.
 * @param {number} chatId - The ID of the chat to delete history for.
 */
export function deleteChatHistory(chatId) {
  for (const key in chatModeHistory) {
    if (key.startsWith(`${chatId}_`)) {
      delete chatModeHistory[key];
    }
  }
}


/**
 * Stores chat titles.
 * Format: { chatId: "Title" }
 * @type {Object.<number, string>}
 */
export let chatTitles = {};
/**
 * Sets the entire chat titles object.
 * @param {Object.<number, string>} titles - The new chat titles object.
 */
export function setChatTitles(titles) { chatTitles = titles; }
/**
 * Updates the title for a specific chat ID.
 * @param {number} chatId - The ID of the chat to update.
 * @param {string} title - The new title for the chat.
 */
export function updateChatTitle(chatId, title) { chatTitles[chatId] = title; }
/**
 * Deletes the title for a specific chat ID.
 * @param {number} chatId - The ID of the chat to delete the title for.
 */
export function deleteChatTitle(chatId) { delete chatTitles[chatId]; }


/**
 * Stores sources per chat.
 * Format: { chatId: [{...source}] }
 * @type {Object.<number, Array<Object>>}
 */
export let chatSources = {};
/**
 * Sets the entire chat sources object.
 * @param {Object.<number, Array<Object>>} sources - The new chat sources object.
 */
export function setChatSources(sources) { chatSources = sources; }
/**
 * Updates the sources for a specific chat ID.
 * @param {number} chatId - The ID of the chat to update.
 * @param {Array<Object>} sources - The array of source objects for the specified chat.
 */
export function updateChatSources(chatId, sources) { chatSources[chatId] = sources; }
/**
 * Adds a single source to a specific chat.
 * @param {number} chatId - The ID of the chat to add the source to.
 * @param {Object} source - The source object to add.
 */
export function addChatSource(chatId, source) {
  if (!chatSources[chatId]) {
    chatSources[chatId] = [];
  }
  chatSources[chatId].push(source);
}
/**
 * Deletes all sources for a specific chat ID.
 * @param {number} chatId - The ID of the chat to delete sources for.
 */
export function deleteChatSource(chatId) { delete chatSources[chatId]; }


/**
 * Stores selected assets per chat.
 * Format: { chatId: [filename1, filename2] }
 * @type {Object.<number, Array<string>>}
 */
export let chatAttachedAssets = {};
/**
 * Sets the entire chat attached assets object.
 * @param {Object.<number, Array<string>>} assets - The new chat attached assets object.
 */
export function setChatAttachedAssets(assets) { chatAttachedAssets = assets; }

/**
 * Stores the total number of chats.
 * @type {number}
 */
export let chatCounter = 0;
/**
 * Sets the total number of chats.
 * @param {number} count - The new chat count.
 */
export function setChatCounter(count) { chatCounter = count; }
/**
 * Updates the attached assets for a specific chat ID.
 * @param {number} chatId - The ID of the chat to update.
 * @param {Array<string>} assets - The array of filenames for the attached assets.
 */
export function updateChatAttachedAssets(chatId, assets) { chatAttachedAssets[chatId] = assets; }
/**
 * Adds a filename to the attached assets for a specific chat.
 * @param {number} chatId - The ID of the chat to add the asset to.
 * @param {string} filename - The filename of the asset to add.
 */
export function addChatAttachedAsset(chatId, filename) {
  if (!chatAttachedAssets[chatId]) {
    chatAttachedAssets[chatId] = [];
  }
  if (!chatAttachedAssets[chatId].includes(filename)) {
    chatAttachedAssets[chatId].push(filename);
  }
}
/**
 * Removes a filename from the attached assets for a specific chat.
 * @param {number} chatId - The ID of the chat to remove the asset from.
 * @param {string} filename - The filename of the asset to remove.
 */
export function removeChatAttachedAsset(chatId, filename) {
  if (chatAttachedAssets[chatId]) {
    const index = chatAttachedAssets[chatId].indexOf(filename);
    if (index > -1) {
      chatAttachedAssets[chatId].splice(index, 1);
    }
  }
}
/**
 * Deletes all attached assets for a specific chat ID.
 * @param {number} chatId - The ID of the chat to delete attached assets for.
 */
export function deleteChatAttachedAssets(chatId) { delete chatAttachedAssets[chatId]; }


/**
 * Current language code (e.g., "en", "de", "sk").
 * @type {string}
 */
export let currentLanguage = "en";
/**
 * Sets the current language code.
 * @param {string} language - The new language code to set.
 */
export function setCurrentLanguage(language) { currentLanguage = language; }

/**
 * UI Translations object, containing localized strings for different languages.
 * @type {Object.<string, Object.<string, string>>}
 */
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
window.setChatCounter = setChatCounter; // Expose setChatCounter

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


/**
 * Updates the display of the current tutor (avatar, name, description, mode descriptions).
 */
export function updateTutorDisplay() {
  const tutorAvatar = document.getElementById("tutorAvatar");
  const tutorName = document.getElementById("tutorName");
  const tutorDescription = document.getElementById("tutorDescription");
  const initialAvatar = document.getElementById("initialAvatar");
  const enolaModeDescription = document.getElementById("enolaModeDescription");
  const franklinModeDescription = document.getElementById("franklinModeDescription");

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
    if (enolaModeDescription) enolaModeDescription.style.display = "block";
    if (franklinModeDescription) franklinModeDescription.style.display = "none";
  } else if (currentTutor === "franklin") {
    const tutorFranklin = document.querySelector(".tutor-franklin");
    if (tutorFranklin) tutorFranklin.classList.add("active");
    if (tutorAvatar) tutorAvatar.style.backgroundImage = "url('/static/tutor.png')";
    if (initialAvatar) initialAvatar.style.backgroundImage = "url('/static/tutor.png')";
    if (tutorName) tutorName.textContent = "Franklin";
    if (tutorDescription) tutorDescription.innerHTML =
      translations[currentLanguage].franklinWelcomeShort;
    if (enolaModeDescription) enolaModeDescription.style.display = "none";
    if (franklinModeDescription) franklinModeDescription.style.display = "block";
  }
}

/**
 * Updates the display of the current mode (buttons, input placeholder, quiz settings panel visibility).
 */
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

/**
 * Selects a tutor and updates the UI accordingly.
 * @param {string} tutorName - The name of the tutor to select ("enola" or "franklin").
 */
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

/**
 * Switches the application to explanation mode with Enola as the tutor.
 */
export function switchToExplanationMode() {
  currentMode = "explanation";
  currentTutor = "enola";
  updateTutorDisplay();
  updateModeDisplay();
  loadModeHistory();
  saveChatToDatabase();
}

/**
 * Switches the application to testing mode with Franklin as the tutor.
 */
export function switchToTestingMode() {
  currentMode = "testing";
  currentTutor = "franklin";
  updateTutorDisplay();
  updateModeDisplay();
  loadModeHistory();
  saveChatToDatabase();
}

/**
 * Toggles the visibility of the language selection dropdown.
 */
export function toggleLanguageDropdown() {
  const languageDropdown = document.getElementById("languageDropdown");
  if (languageDropdown) languageDropdown.classList.toggle("show");
}

/**
 * Selects a language and updates the UI accordingly.
 * @param {string} code - The language code (e.g., "en", "de", "sk").
 * @param {string} display - The display text for the language button (e.g., "EN", "DE", "SK").
 */
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

/**
 * Updates all UI elements with the currently selected language.
 */
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

  // Re-render the initial message in the chat area when language changes
  const chatArea = document.getElementById("chatArea");
  if (chatArea) {
    const initialMessageDiv = chatArea.querySelector(".message");
    if (initialMessageDiv && initialMessageDiv.id === "initialWelcomeMessage") {
      const welcomeMessage =
        currentTutor === "enola"
          ? translations[currentLanguage].enolaStart
          : translations[currentLanguage].franklinStart;
      initialMessageDiv.querySelector(".message-content").innerHTML = welcomeMessage;
    }
  }

  loadModeHistory();
}

/**
 * Checks the authentication status of the user and updates the UI accordingly.
 * Displays user info if logged in, otherwise shows sign-in options.
 */
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

/**
 * Logs out the current user, clears local storage, and reloads the page.
 */
export function logout() {
  document.body.style.transition = "opacity 0.3s ease";
  document.body.style.opacity = "0";

  setTimeout(() => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");
    localStorage.removeItem("chatTitles"); // Clear chat titles
    localStorage.removeItem("chatSources"); // Clear chat sources
    localStorage.removeItem("chatAttachedAssets"); // Clear attached assets
    localStorage.removeItem("selectedLanguage");
    location.reload();
  }, 300);
}

/**
 * Initializes the application when the DOM is fully loaded.
 * Sets up theme, authentication, loads chats and assets, and updates UI language.
 */
document.addEventListener("DOMContentLoaded", async function () {
  try {
    loadTheme();
    // setupDragAndDrop(); // Now called from assets.js
    checkAuthStatus();

    currentTutor = "enola";
    currentMode = "explanation";
    updateTutorDisplay();
    updateModeDisplay();

    await loadChatsFromDatabase(); // This will now be the sole source of truth for chatModeHistory
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

/**
 * Global event listener to close modals when clicking outside their content.
 * @param {Event} event - The click event.
 */
window.onclick = function (event) {
  if (event.target.classList.contains("modal")) {
    event.target.style.display = "none";
  }
};
