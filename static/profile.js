// static/profile.js

import { showNotification, getFileIcon, previewFile } from "./ui.js";
import { fetchChatDetailsApi, loadChatsFromDatabaseApi, fetchAssetsApi, fetchQuizHistoryApi, fetchQuizStatsApi } from "./api.js";
import { deleteChat, switchToChat } from "./chat.js";
import { currentLanguage, translations, chatTitles, chatModeHistory, chatAttachedAssets, chatSources, setCurrentLanguage, setChatTitles, updateChatTitle, deleteChatTitle, setChatModeHistory, updateChatModeHistory, addMessageToChatModeHistory, deleteChatHistory, setChatAttachedAssets, updateChatAttachedAssets, addChatAttachedAsset, removeChatAttachedAsset, deleteChatAttachedAssets, setChatSources, updateChatSources, addChatSource, deleteChatSource } from "./app.js"; // Import necessary globals from app.js

/**
 * Opens the user profile modal and loads all user-specific data (chats, assets, quiz history).
 * @returns {Promise<void>}
 */
async function openUserProfile() {
  console.log("DEBUG: openUserProfile function called.");
  const modal = document.getElementById("userProfileModal");
  if (modal) {
    console.log("DEBUG: userProfileModal found. Adding 'show' class.");
    modal.classList.add("show");
    // Ensure display is block if it was none
    modal.style.display = "flex";
  } else {
    console.error("DEBUG: userProfileModal not found!");
  }

  try {
    console.log("DEBUG: Calling loadProfileChats...");
    await loadProfileChats();
    console.log("DEBUG: loadProfileChats completed.");

    console.log("DEBUG: Calling loadProfileAssets...");
    await loadProfileAssets();
    console.log("DEBUG: loadProfileAssets completed.");

    console.log("DEBUG: Calling loadProfileQuizHistory...");
    await loadProfileQuizHistory();
    console.log("DEBUG: loadProfileQuizHistory completed.");
  } catch (error) {
    console.error("DEBUG: Error during profile data loading:", error);
    showNotification(`Error loading profile data: ${error.message}`, "error");
  }
  console.log("DEBUG: openUserProfile function finished.");
}

window.openUserProfile = openUserProfile; // Directly expose to window

/**
 * Loads and displays the user's chat list in the profile modal.
 * @returns {Promise<void>}
 */
export async function loadProfileChats() {
  const container = document.getElementById("profileChatList");
  if (!container) {
    console.error("Profile chat list container not found!");
    return;
  }
  container.innerHTML =
    '<div class="profile-loading-message">Loading...</div>';

  const accessToken = localStorage.getItem("access_token");
  if (!accessToken) {
    container.innerHTML =
      '<div class="profile-empty-message">Sign in to view chats.</div>';
    showNotification("Please sign in to view your chats.", "warning");
    return;
  }

  try {
    const data = await loadChatsFromDatabaseApi(); // Use correct API function

    if (data.length > 0) {
      container.innerHTML = "";
      data.forEach((chat) => {
        const chatDiv = document.createElement("div");
        chatDiv.className = "profile-list-item";
        chatDiv.innerHTML = `
          <div onclick="switchToChatFromProfile(${
            chat.chat_id
          })" class="profile-list-item-content">
            <div class="profile-list-item-title">${chat.title}</div>
            <div class="profile-list-item-meta">
              ${
                chat.tutor === "enola" ? "👩 Enola" : "👨 Franklin"
              } • ${chat.updated_at ? new Date(chat.updated_at).toLocaleDateString() : 'N/A'}
            </div>
          </div>
          <button onclick="event.stopPropagation(); deleteChat(${
            chat.chat_id
          }); setTimeout(loadProfileChats, 500);" 
                  class="action-btn">🗑️</button>
        `;
        container.appendChild(chatDiv);
      });
    } else {
      container.innerHTML =
        '<div class="profile-empty-message">No chats yet</div>';
    }
  } catch (error) {
    console.error("Error loading profile chats:", error);
    container.innerHTML =
      '<div class="profile-error-message">Error loading chats</div>';
    showNotification(`Error loading chats: ${error.message}`, "error");
  }
}

/**
 * Loads and displays the user's uploaded assets in the profile modal.
 * @returns {Promise<void>}
 */
export async function loadProfileAssets() {
  const container = document.getElementById("profileAssetList");
  if (!container) {
    console.error("Profile asset list container not found!");
    return;
  }
  container.innerHTML =
    '<div class="profile-loading-message">Loading...</div>';

  const accessToken = localStorage.getItem("access_token");
  if (!accessToken) {
    container.innerHTML =
      '<div class="profile-empty-message">Sign in to view assets.</div>';
    showNotification("Please sign in to view your assets.", "warning");
    return;
  }

  try {
    const data = await fetchAssetsApi(); // Use correct API function

    if (data && data.length > 0) {
      container.innerHTML = "";
      data.forEach((asset) => {
        const assetDiv = document.createElement("div");
        assetDiv.className = "profile-list-item";
        const icon = getFileIcon(asset.filename);
        const extension = (asset.filename && typeof asset.filename === 'string') ? asset.filename.split('.').pop().toLowerCase() : '';
        assetDiv.innerHTML = `
          <div class="profile-list-item-content" onclick="window.previewFile('${encodeURIComponent(asset.filename)}', '${extension}')">
            <div class="profile-list-item-title">${icon} ${asset.filename}</div>
            <div class="profile-list-item-meta">
              ${asset.created_at && typeof asset.created_at === 'string' ? new Date(asset.created_at).toLocaleDateString() : 'N/A'}
            </div>
          </div>
        `;
        container.appendChild(assetDiv);
      });
    } else {
      container.innerHTML =
        '<div class="profile-empty-message">No assets uploaded</div>';
    }
  } catch (error) {
    console.error("Error loading profile assets:", error);
    container.innerHTML =
      '<div class="profile-error-message">Error loading assets</div>';
    showNotification(`Error loading assets: ${error.message}`, "error");
  }
}

/**
 * Loads and displays the user's quiz history and statistics in the profile modal.
 * @returns {Promise<void>}
 */
export async function loadProfileQuizHistory() {
  const container = document.getElementById("profileQuizHistory");
  if (!container) {
    console.error("Profile quiz history container not found!");
    return;
  }
  container.innerHTML =
    '<div class="profile-loading-message">Loading history...</div>';

  const accessToken = localStorage.getItem("access_token");
  if (!accessToken) {
    container.innerHTML =
      '<div class="profile-empty-message">Sign in to view quiz history.</div>';
    showNotification("Please sign in to view your quiz history.", "warning");
    return;
  }

  try {
    const data = await fetchQuizHistoryApi(); // Use correct API function
    const quizResults = data; // Backend now returns a list directly

    const quizStatsContainer = document.getElementById("profileQuizStats");
    if (quizStatsContainer) {
      quizStatsContainer.innerHTML =
        '<div class="profile-loading-message">Loading stats...</div>';
    }

    const statsData = await fetchQuizStatsApi(); // Use correct API function

    if (quizStatsContainer) {
      quizStatsContainer.innerHTML = `
        <h4 class="profile-section-title">📊 Quiz Stats</h4>
        <div class="profile-quiz-stats-content">
          <div class="profile-quiz-stats-grid">
            <div>
              <div class="profile-quiz-stats-value">${statsData.total_quizzes}</div>
              <div class="profile-quiz-stats-label">Total Quizzes</div>
            </div>
            <div>
              <div class="profile-quiz-stats-value">${statsData.average_score}%</div>
              <div class="profile-quiz-stats-label">Avg. Score</div>
            </div>
            <div>
              <div class="profile-quiz-stats-value">
                <span class="profile-quiz-stats-trend-icon">📈</span>
              </div>
              <div class="profile-quiz-stats-trend-label">${statsData.improvement_trend}</div>
            </div>
          </div>
        </div>
      `;
    }

    if (quizResults && quizResults.length > 0) {
      container.innerHTML = "";
      quizResults.forEach((result) => {
        const quizHistoryDiv = document.createElement("div");
        quizHistoryDiv.className = "profile-quiz-history-item";
        quizHistoryDiv.setAttribute("data-quiz-result-id", result.id);
        // Pass the entire result object directly, no need for JSON.parse(JSON.stringify)
        quizHistoryDiv.onclick = () => window.previewQuizResult(result);
        quizHistoryDiv.innerHTML = `
          <div class="profile-quiz-history-item-header">
            <div class="profile-list-item-title">${result.quiz_title || 'Untitled Quiz'}</div>
            <div class="profile-quiz-history-score" style="color: ${result.percentage >= 70 ? '#4caf50' : '#f44336'};">
              ${result.percentage}%
            </div>
          </div>
          <div class="profile-list-item-meta">
            ${result.asset_filename ? `📚 ${result.asset_filename} • ` : ''}
            Score: ${result.score}/${result.total_questions} • 
            ${new Date(result.completed_at).toLocaleDateString()}
          </div>
        `;
        container.appendChild(quizHistoryDiv);
      });
    } else {
      container.innerHTML =
        '<div class="profile-empty-message">No quiz history yet</div>';
    }
  } catch (error) {
    console.error("Error loading profile quiz history:", error);
    container.innerHTML =
      '<div class="profile-error-message">Error loading quiz history</div>';
    showNotification(`Error loading quiz history: ${error.message}`, "error");
  }
}

/**
 * Closes the user profile modal and switches to a specified chat.
 * @param {number} chatId - The ID of the chat to switch to.
 * @returns {Promise<void>}
 */
export async function switchToChatFromProfile(chatId) {
  const userProfileModal = document.getElementById("userProfileModal");
  if (userProfileModal) userProfileModal.style.display = "none";
  await switchToChat(chatId);
}

/**
 * Displays a detailed preview of a specific quiz result in a modal.
 * @param {Object} quizResult - The quiz result object to display.
 */
export function previewQuizResult(quizResult) {
  const modal = document.createElement("div");
  modal.className = "modal";
  modal.id = "quizResultPreviewModal";
  modal.style.cssText = `
    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    background: rgba(0,0,0,0.8); z-index: 2000; display: flex;
    align-items: center; justify-content: center;
  `;

  const content = document.createElement("div");
  content.className = "modal-content";
  // The styling for centering is now handled by the CSS class #quizResultPreviewModal .modal-content
  // We only need to ensure basic modal-content styles are applied.
  // Removed inline style to allow CSS in app.css to take effect for centering.

  content.innerHTML = `
    <div class="user-profile-header">
      <h3>📝 Quiz Result: ${quizResult.quiz_title || 'Untitled Quiz'}</h3>
      <button onclick="window.closeModal('quizResultPreviewModal')" class="user-profile-close-btn">&times;</button>
    </div>
    <div style="margin-bottom: 15px;">
      <p><strong>Score:</strong> ${quizResult.score}/${quizResult.total_questions} (${quizResult.percentage}%)</p>
      <p><strong>Completed:</strong> ${new Date(quizResult.completed_at).toLocaleDateString()}</p>
      ${quizResult.asset_filename ? `<p><strong>Source:</strong> 📚 ${quizResult.asset_filename}</p>` : ''}
    </div>
    <div class="quiz-result-details" style="flex: 1; overflow-y: auto;">
      ${quizResult.questions && quizResult.questions.length > 0 ? quizResult.questions.map((q, qIndex) => `
        <div style="margin-bottom: 20px; padding: 10px; border: 1px solid var(--border-color); border-radius: 8px;">
          <p><strong>Question ${qIndex + 1}:</strong> ${q.question_text}</p>
          <p><strong>Your Answer:</strong> ${q.user_answer || 'N/A'}</p>
          <p><strong>Correct Answer:</strong> ${q.correct_answer || 'N/A'}</p>
          <p style="color: ${q.is_correct ? '#4caf50' : '#f44336'};"><strong>Status:</strong> ${q.is_correct ? 'Correct' : 'Incorrect'}</p>
          ${q.explanation ? `<p><strong>Explanation:</strong> ${q.explanation}</p>` : ''}
        </div>
      `).join('') : '<p>No question details available for this quiz.</p>'}
    </div>
  `;

  modal.appendChild(content);
  document.body.appendChild(modal);

  modal.addEventListener("click", (e) => {
    if (e.target === modal) modal.remove();
  });
}
