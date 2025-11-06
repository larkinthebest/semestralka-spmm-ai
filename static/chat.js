// static/chat.js

import {
  addNewChatApi,
  renameChatApi,
  deleteChatApi,
  fetchChatDetailsApi,
  saveChatToDatabaseApi,
  loadChatsFromDatabaseApi,
  simpleChatApi,
  uploadFileApi
} from "./api.js";
import {
  showNotification,
  showLoadingMessage,
  removeLoadingMessage,
  formatMessageText,
  addMessage,
  updateSources,
  getFileIcon,
  showDeleteConfirm,
  closeModal,
  previewFile
} from "./ui.js";
import { updateAssetSelectionUI, updateAttachedFilesDisplay, removeAttachedFile, addFilesToAssets, dragAsset, toggleChatAssetSelection, getAttachedFiles, setupDragAndDrop, loadAssetsIntoMainframe } from "./assets.js"; // Import setupDragAndDrop and loadAssetsIntoMainframe
import { displayQuiz, hideQuiz, generateQuiz } from "./quiz.js";
import { updateTutorDisplay, updateModeDisplay, translations, currentLanguage, currentTutor, currentMode, currentChatId, chatModeHistory, chatTitles, chatSources, chatAttachedAssets, setCurrentMode, setCurrentTutor, setCurrentChatId, setChatModeHistory, updateChatModeHistory, addMessageToChatModeHistory, deleteChatHistory, setChatTitles, updateChatTitle, deleteChatTitle, setChatSources, updateChatSources, addChatSource, deleteChatSource, setChatAttachedAssets, updateChatAttachedAssets, addChatAttachedAsset, removeChatAttachedAsset, deleteChatAttachedAssets, setCurrentLanguage } from "./app.js"; // Import necessary globals from app.js

/**
 * Creates a new chat session, updates the UI, and saves the new chat to the database.
 * @returns {Promise<void>}
 */
export async function addNewChat() {
  try {
    const newChatData = await addNewChatApi();
    const chatList = document.getElementById("chatList");

    if (!chatList) {
      console.error("Chat list element not found!");
      showNotification("Failed to update chat list.", "error");
      return;
    }

    document.querySelectorAll(".chat-item").forEach((item) => {
      item.classList.remove("active");
    });

    const chatItem = document.createElement("div");
    chatItem.className = "chat-item active";
    chatItem.setAttribute("data-chat-id", newChatData.chat_id);
    chatItem.setAttribute(
      "onclick",
      `window.switchToChat(${newChatData.chat_id})`
    ); // Use window. for global access
    chatItem.innerHTML = `
      <span>${newChatData.title}</span>
      <div class="item-actions">
        <button class="action-btn" onclick="event.stopPropagation(); window.renameChat(${newChatData.chat_id})">✏️</button>
        <button class="action-btn" onclick="event.stopPropagation(); window.deleteChat(${newChatData.chat_id})">🗑️</button>
      </div>
    `;
    chatList.prepend(chatItem);

    setCurrentChatId(newChatData.chat_id);
    setCurrentMode(newChatData.current_mode);
    setCurrentTutor(newChatData.current_tutor);

    updateChatTitle(newChatData.chat_id, newChatData.title); // Use newChatData.chat_id
    updateChatAttachedAssets(newChatData.chat_id, []); // Use newChatData.chat_id
    updateChatSources(newChatData.chat_id, []); // Use newChatData.chat_id

    updateTutorDisplay();
    updateModeDisplay();
    loadModeHistory();
    showNotification("New chat created!", "success");
  } catch (error) {
    console.error("Error creating new chat:", error);
    showNotification("Error creating new chat. Please try again.", "error");
  }
}

/**
 * Opens a modal to rename an existing chat.
 * @param {number} chatId - The ID of the chat to rename.
 * @returns {Promise<void>}
 */
export async function renameChat(chatId) {
  const modal = document.getElementById("renameModal");
  const input = document.getElementById("renameInput");
  const chatItem = document.querySelector(
    `[data-chat-id="${chatId}"] span`
  );

  if (input && modal && chatItem) {
    input.value = chatTitles[chatId] || chatItem.textContent; // Use chatTitles for current name
    modal.style.display = "block";
    modal.setAttribute("data-chat-id", chatId);
  }
}

/**
 * Confirms the chat rename operation and sends the new title to the backend.
 * @returns {Promise<void>}
 */
export async function confirmRename() {
  const modal = document.getElementById("renameModal");
  const chatId = modal ? parseInt(modal.getAttribute("data-chat-id")) : null;
  const newName = document.getElementById("renameInput") ? document.getElementById("renameInput").value : "";

  if (newName.trim() && chatId) {
    try {
      await renameChatApi(chatId, newName);
      const chatItem = document.querySelector(
        `[data-chat-id="${chatId}"] span`
      );
      if (chatItem) {
        chatItem.textContent = newName;
        updateChatTitle(chatId, newName);
        showNotification("Chat renamed successfully!", "success");
      }
    } catch (error) {
      console.error("Error renaming chat:", error);
      showNotification(error.message || "Failed to rename chat.", "error");
    }
  }
  closeModal("renameModal");
}

/**
 * Deletes a chat after user confirmation.
 * @param {number} chatId - The ID of the chat to delete.
 * @returns {Promise<void>}
 */
export async function deleteChat(chatId) {
  const confirmed = await showDeleteConfirm(
    translations[currentLanguage].deleteConfirm
  );
  if (confirmed) {
    try {
      await deleteChatApi(chatId);
      const chatItem = document.querySelector(`[data-chat-id="${chatId}"]`);
      if (chatItem) chatItem.remove();
      deleteChatTitle(chatId);
      deleteChatAttachedAssets(chatId);
      deleteChatSource(chatId);
      deleteChatHistory(chatId);
      setChatModeHistory(JSON.parse(JSON.stringify(chatModeHistory))); // Trigger reactivity for chatModeHistory

      if (currentChatId === chatId) {
        const remainingChats = document.querySelectorAll(".chat-item");
        if (remainingChats.length > 0) {
          const firstChatId = parseInt(remainingChats[0].getAttribute("data-chat-id"));
          await switchToChat(firstChatId);
        } else {
          await addNewChat();
        }
      }
      showNotification("Chat deleted successfully!", "success");
    } catch (error) {
      console.error("Error deleting chat:", error);
      showNotification(error.message || "Failed to delete chat.", "error");
    }
  }
}

/**
 * Switches the current view to a specified chat.
 * Saves the current chat's state before switching.
 * @param {number} chatId - The ID of the chat to switch to.
 * @returns {Promise<void>}
 */
export async function switchToChat(chatId) {
  await saveChatToDatabase();

  setCurrentChatId(chatId);

  document.querySelectorAll(".chat-item").forEach((item) => {
    item.classList.remove("active");
  });

  const clickedChat = document.querySelector(`[data-chat-id="${chatId}"]`);
  if (clickedChat) {
    clickedChat.classList.add("active");
  }

  try {
    const chatData = await fetchChatDetailsApi(chatId);
    setCurrentTutor(chatData.current_tutor || "enola");
    setCurrentMode(chatData.current_mode || "explanation");
  } catch (error) {
    console.error(`Failed to load chat details for chat ID ${chatId}:`, error);
    setCurrentTutor("enola");
    setCurrentMode("explanation");
  }

  updateTutorDisplay();
  updateModeDisplay();
  loadModeHistory();
  hideQuiz(); // Hide quiz panel when switching chats
}

/**
 * Loads and displays the chat history for the current chat ID and mode.
 * If no history exists, displays a welcome message.
 */
export function loadModeHistory() {
  const chatArea = document.getElementById("chatArea");
  if (!chatArea) {
    console.error("Chat area element not found!");
    return;
  }
  chatArea.innerHTML = "";

  // Setup drag and drop for the chat area
  setupDragAndDrop();

  const chatKey = `${currentChatId}_${currentMode}`;
  const history = chatModeHistory[chatKey];

  if (history && history.length > 0) {
    history.forEach((msg) => {
      addMessage(msg.content, msg.type, currentTutor, msg.attachments || "");
      if (msg.quizData) {
        displayQuiz(msg.quizData);
      }
    });
  } else {
    const welcomeMessage =
      currentTutor === "enola"
        ? translations[currentLanguage].enolaStart
        : translations[currentLanguage].franklinStart;
    addMessage(welcomeMessage, "bot", currentTutor);
    // Only add the welcome message to history if it's a new chat session
    // and not just a mode switch within an existing empty chat.
    // The backend will handle persisting the initial message for new chats.
    // For existing chats, if history is empty, it means it's a mode switch
    // and the welcome message is purely for display.
    if (!chatModeHistory[chatKey] || chatModeHistory[chatKey].length === 0) {
      updateChatModeHistory(chatKey, [{
        type: "bot",
        content: welcomeMessage,
        attachments: "",
      }]);
    }
  }
  loadChatSources(currentChatId);
  updateAssetSelectionUI();
}

/**
 * Loads and updates the display of sources for a given chat ID.
 * @param {number} chatId - The ID of the chat to load sources for.
 */
export function loadChatSources(chatId) {
  const sources = chatSources[chatId] || [];
  updateSources(sources);
}

/**
 * Handles key press events in the message input, specifically for sending messages on Enter.
 * @param {KeyboardEvent} event - The keyboard event.
 */
export function handleKeyPress(event) {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault(); // Prevent default to avoid adding a newline in the input field
    sendMessage();
  }
  // If Shift + Enter, allow default behavior (which is usually a newline)
}

/**
 * Sends a message to the backend, handling file uploads, chat modes, and displaying responses.
 * @returns {Promise<void>}
 */
export async function sendMessage() {
  const input = document.getElementById("messageInput");
  const message = input ? input.value.trim() : "";

  if (!message && getAttachedFiles().length === 0) return;

  console.log('sendMessage called. filesToUpload:', getAttachedFiles());
  getAttachedFiles().forEach((file, index) => {
      console.log(`File ${index}:`, file);
      console.log(`File ${index} name:`, file.name);
      console.log(`File ${index} type:`, file.type);
      console.log(`File ${index} size:`, file.size);
  });

  const chatSourceFiles = (chatSources[currentChatId] || []).map(
    (s) => s.title
  );

  const isEnolaFindRequest = currentTutor === "enola" && currentMode === "explanation" && message.toLowerCase().includes("find what i need");

  const existingAssetLabels = document.querySelectorAll(".asset-item label");
  const existingAssetFilenames = Array.from(existingAssetLabels).map((label) => label.textContent.trim().substring(2).trim());

  const filesToUpload = [];
  const attachedFileNames = [];
  for (const file of getAttachedFiles()) {
    attachedFileNames.push(file.name);
    if (!existingAssetFilenames.includes(file.name)) {
      filesToUpload.push(file);
    }
  }

  for (const file of filesToUpload) {
    console.log("DEBUG: Attempting to upload file:", file.name, "type:", file.type, "size:", file.size);
    try {
      await uploadFileApi(file); // Use API function
      console.log("DEBUG: File uploaded successfully:", file.name);
      // After successful upload, refresh the asset list in the mainframe
      await loadAssetsIntoMainframe();
      await updateAssetSelectionUI();
    } catch (uploadError) {
      console.error("ERROR: Failed to upload file:", file.name, uploadError);
      showNotification(`Failed to upload file: ${file.name}. ${uploadError.message}`, "error");
      removeLoadingMessage();
      return; // Stop sending message if file upload fails
    }
  }

  const allAvailableFiles = [
    ...new Set([
      ...(chatAttachedAssets[currentChatId] || []),
      ...attachedFileNames,
      ...chatSourceFiles,
    ]),
  ];

  if (allAvailableFiles.length === 0) {
    showNotification(
      "Please upload files first! Use the + button in Assets or drag files here.",
      "warning"
    );
    return;
  }

  showLoadingMessage(currentTutor);

  let messageContent = message;
  let attachmentHtml = "";

  if (getAttachedFiles().length > 0) {
    attachmentHtml = '<div class="message-attachments">';
    getAttachedFiles().forEach((file) => {
      const fileIcon = getFileIcon(file.name);
      attachmentHtml += `<div class="attachment-preview">${fileIcon} ${file.name}</div>`;
    });
    attachmentHtml += "</div>";
  }

  addMessage(messageContent, "user", currentTutor, attachmentHtml);
  if (input) input.value = "";

  const chatKey = `${currentChatId}_${currentMode}`;
  addMessageToChatModeHistory(chatKey, {
    type: "user",
    content: messageContent,
    attachments: attachmentHtml,
  });

  setChatModeHistory(JSON.parse(JSON.stringify(chatModeHistory))); // Trigger reactivity for chatModeHistory

  let suggestedTitle = null;
  let botResponseContent = "";
  let quizData = null;
  let sourcesData = null;

  try {
    if (currentMode === "testing" && currentTutor === "franklin") {
      const quizResult = await generateQuiz(message, allAvailableFiles); // generateQuiz now returns data
      if (quizResult) {
        quizData = quizResult;
        botResponseContent = `Generated a quiz on ${quizResult.title || message || "general topics"}.`;
        if (quizResult.title) { // Use quizResult.title as suggested_title
          suggestedTitle = quizResult.title;
        }
        if (quizResult.sources) { // If quizResult includes sources, use them
          sourcesData = quizResult.sources;
        }
      }
      // Clear attached files after quiz generation
      getAttachedFiles().length = 0;
      updateAttachedFilesDisplay();
    } else if (isEnolaFindRequest) {
      // Handle "Enola, find what I need" request
      const data = await simpleChatApi({
        message: message,
        mode: currentMode,
        tutor: currentTutor,
        chat_id: currentChatId,
        attached_files: allAvailableFiles,
        language: currentLanguage,
        find_what_i_need: true, // Indicate this is a "find what I need" request
      });

      if (data.requires_files) {
        showNotification("Please upload files first!", "warning");
        removeLoadingMessage();
        return;
      }

      botResponseContent = data.response;
      if (data.suggested_title) {
        suggestedTitle = data.suggested_title;
      }
      if (data.sources) {
        sourcesData = data.sources;
      }
    }
    else {
      const data = await simpleChatApi({
        message: message,
        mode: currentMode,
        tutor: currentTutor,
        chat_id: currentChatId,
        attached_files: allAvailableFiles,
        language: currentLanguage,
      });

      if (data.requires_files) {
        showNotification("Please upload files first!", "warning");
        removeLoadingMessage();
        return;
      }

      botResponseContent = data.response;
      if (data.suggested_title) {
        suggestedTitle = data.suggested_title;
      }
      if (data.sources) {
        sourcesData = data.sources;
      }
    }

    removeLoadingMessage();
    addMessage(botResponseContent, "bot", currentTutor);

    const messageHistoryEntry = {
      type: "bot",
      content: botResponseContent,
    };
    if (quizData) {
      messageHistoryEntry.quizData = quizData;
    }
    addMessageToChatModeHistory(chatKey, messageHistoryEntry);
    setChatModeHistory(JSON.parse(JSON.stringify(chatModeHistory))); // Trigger reactivity for chatModeHistory

    // Apply suggested title if available
    if (suggestedTitle) {
      const chatItem = document.querySelector(
        `[data-chat-id="${currentChatId}"] span`
      );
      if (
        chatItem &&
        (chatItem.textContent === "New Chat" ||
          chatItem.textContent.startsWith("New Chat"))
      ) {
        let uniqueTitle = suggestedTitle;
        let counter = 1;
        while (Object.values(chatTitles).includes(uniqueTitle)) {
          uniqueTitle = `${suggestedTitle} (${counter})`;
          counter++;
        }
        if (chatItem) chatItem.textContent = uniqueTitle;
        updateChatTitle(currentChatId, uniqueTitle);
      }
    }

    if (sourcesData) {
      updateChatSources(currentChatId, sourcesData);
    }

    saveChatToDatabase();
  } catch (error) {
    removeLoadingMessage();
    addMessage("Sorry, I encountered an error. Please try again.", "bot", currentTutor);
    showNotification(error.message || "Error sending message.", "error");
  }
}

/**
 * Loads all chats for the current user from the database and updates the chat list UI.
 * @returns {Promise<void>}
 */
export async function loadChatsFromDatabase() {
  try {
    const data = await loadChatsFromDatabaseApi();
    const chatList = document.getElementById("chatList");

    if (!chatList) {
      console.error("Chat list element not found during loadChatsFromDatabase!");
      return;
    }
    chatList.innerHTML = "";

    if (data.length > 0) {
      data.forEach((chat, index) => {
        const chatItem = document.createElement("div");
        chatItem.className = `chat-item ${index === 0 ? "active" : ""}`;
        chatItem.setAttribute("data-chat-id", chat.chat_id);
        chatItem.setAttribute(
          "onclick",
          `window.switchToChat(${chat.chat_id})`
        );
        chatItem.innerHTML = `
          <span>${chat.title}</span>
          <div class="item-actions">
            <button class="action-btn" onclick="event.stopPropagation(); window.renameChat(${chat.chat_id})">✏️</button>
            <button class="action-btn" onclick="event.stopPropagation(); window.deleteChat(${chat.chat_id})">🗑️</button>
          </div>
        `;
        chatList.prepend(chatItem);

        updateChatTitle(chat.chat_id, chat.title);
        if (chat.messages) {
          const chatKey = `${chat.chat_id}_${chat.mode}`;
          updateChatModeHistory(chatKey, chat.messages);
        }
        if (chat.attached_asset_filenames) {
          updateChatAttachedAssets(chat.chat_id, chat.attached_asset_filenames);
          updateChatSources(chat.chat_id, chat.attached_asset_filenames.map(
            (filename) => ({ title: filename, created_at: chat.updated_at || new Date().toISOString() })
          ));
        }

        if (index === 0) {
          setCurrentChatId(chat.chat_id);
          setCurrentMode(chat.current_mode || "explanation");
          setCurrentTutor(chat.current_tutor || "enola");
        }
      });

      setChatCounter(Math.max(...data.map((c) => c.chat_id)));
    } else {
      await addNewChat();
    }
  } catch (error) {
    console.error("DEBUG: Error loading chats:", error);
    showNotification(`Error loading chats: ${error.message}`, "error");
    await addNewChat();
  }
}

/**
 * Saves the current chat's state (messages, title, mode, attached assets) to the database.
 * @returns {Promise<void>}
 */
export async function saveChatToDatabase() {
  if (!currentChatId) return;

  const chatKey = `${currentChatId}_${currentMode}`;
  const messages = chatModeHistory[chatKey] || [];
  const title = chatTitles[currentChatId] || "New Chat";
  const attachedAssetFilenames = chatAttachedAssets[currentChatId] || [];

  const chatData = {
    chat_id: currentChatId,
    title: title,
    mode: currentMode,
    tutor: currentTutor,
    messages: messages,
    attached_asset_filenames: attachedAssetFilenames,
    current_tutor: currentTutor,
    current_mode: currentMode,
  };

  try {
    await saveChatToDatabaseApi(chatData);
    console.log(`DEBUG: Chat ${currentChatId} saved successfully.`);
  } catch (error) {
    console.error("DEBUG: Error saving chat:", error);
  }
}

// Auto-save chat periodically (reduced frequency)
setInterval(saveChatToDatabase, 120000); // Save every 2 minutes

// Save chat before page unload
window.addEventListener("beforeunload", saveChatToDatabase);
