// static/ui.js

import { translations, currentLanguage } from './app.js'; // Assuming app.js will export these

/**
 * Checks if a string contains basic HTML tags.
 * This is a simple heuristic and might not catch all cases,
 * but should be sufficient for distinguishing pre-formatted HTML from markdown.
 * @param {string} text - The string to check.
 * @returns {boolean} True if the string appears to contain HTML, false otherwise.
 */
function containsHtml(text) {
  // Regex to detect common HTML tags (e.g., <div, <p, <span, <br, <h1-h6, <ul, <ol, <li, <strong, <em, <code>)
  // This is a simplified check and might not cover all edge cases, but should be sufficient for our purpose.
  return /<[a-z][\s\S]*?>/i.test(text);
}

/**
 * Displays a notification message to the user.
 * @param {string} message - The message to display.
 * @param {"info" | "success" | "warning" | "error"} [type="info"] - The type of notification, affecting its styling.
 */
export function showNotification(message, type = "info") {
  const notificationContainer =
    document.getElementById("notificationContainer");
  if (!notificationContainer) {
    console.error("Notification container not found!");
    return;
  }

  const notification = document.createElement("div");
  notification.className = `notification ${type}`;
  notification.innerHTML = `
    <span class="notification-icon">${getNotificationIcon(type)}</span>
    <span class="notification-message">${message}</span>
  `;

  notificationContainer.appendChild(notification);

  // Animate in
  setTimeout(() => {
    notification.classList.add("show");
  }, 10);

  // Animate out and remove
  setTimeout(() => {
    notification.classList.remove("show");
    notification.classList.add("hide");
    notification.addEventListener("transitionend", () => {
      notification.remove();
    });
  }, 3000); // Notifications disappear after 3 seconds
}

function getNotificationIcon(type) {
  switch (type) {
    case "success":
      return "✅";
    case "warning":
      return "⚠️";
    case "error":
      return "❌";
    case "info":
    default:
      return "ℹ️";
  }
}

/**
 * Updates the icon of the theme toggle button based on the current theme.
 */
export function updateThemeToggleIcon() {
  const themeToggleBtn = document.getElementById("themeToggle");
  if (themeToggleBtn) {
    if (document.documentElement.getAttribute("data-theme") === "dark") {
      themeToggleBtn.textContent = "☀️"; // Sun icon for dark theme
    } else {
      themeToggleBtn.textContent = "🌙"; // Moon icon for light theme
    }
  }
}

/**
 * Loads the user's preferred theme from local storage or sets a default, then updates the UI.
 */
export function loadTheme() {
  const savedTheme = localStorage.getItem("theme");
  if (savedTheme) {
    document.documentElement.setAttribute("data-theme", savedTheme);
  } else {
    document.documentElement.setAttribute("data-theme", "light"); // Default theme
  }
  updateThemeToggleIcon();
}

/**
 * Toggles the application's theme between 'light' and 'dark'.
 */
export function toggleTheme() {
  const currentTheme = document.documentElement.getAttribute("data-theme");
  const newTheme = currentTheme === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", newTheme);
  localStorage.setItem("theme", newTheme);
  updateThemeToggleIcon();
}

/**
 * Closes a modal by setting its display style to 'none'.
 * @param {string} modalId - The ID of the modal element to close.
 */
export function closeModal(modalId) {
  console.log(`DEBUG: closeModal called for modalId: ${modalId}`);
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove("show"); // Remove 'show' class for CSS transition
    // Use a timeout to set display: none after the transition
    setTimeout(() => {
      if (modal) modal.style.display = "none";
    }, 300); // Match CSS transition duration
  }
}

/**
 * Returns a Unicode emoji icon based on the file's extension.
 * @param {string} filename - The name of the file.
 * @returns {string} An emoji representing the file type.
 */
export function getFileIcon(filename) {
  if (!filename || typeof filename !== 'string' || filename.trim() === '') {
    return "📎"; // Default icon if filename is undefined, not a string, or empty
  }
  const parts = filename.split(".");
  const extension = parts.length > 1 ? parts.pop().toLowerCase() : '';

  if (["jpg", "jpeg", "png", "gif", "bmp"].includes(extension)) {
    return "🖼️";
  } else if (["mp3", "wav", "m4a", "ogg"].includes(extension)) {
    return "🎵";
  } else if (["mp4", "avi", "mov", "mkv", "webm"].includes(extension)) {
    return "🎬";
  } else if (["pdf"].includes(extension)) {
    return "📕";
  } else if (["docx", "doc"].includes(extension)) {
    return "📘";
  } else if (["txt"].includes(extension)) {
    return "📄";
  } else if (["md"].includes(extension)) {
    return "📝";
  } else if (["ppt", "pptx"].includes(extension)) {
    return "📊";
  } else {
    return "📎";
  }
}

/**
 * Displays a loading message with a spinner in the chat area.
 * @param {string} currentTutor - The name of the current tutor ("enola" or "franklin") to determine the avatar.
 */
export function showLoadingMessage(currentTutor) {
  const chatArea = document.getElementById("chatArea");
  if (!chatArea) return;
  const loadingDiv = document.createElement("div");
  loadingDiv.className = "message loading-message";
  loadingDiv.id = "loadingMessage";

  const avatarUrl =
    currentTutor === "enola" ? "/static/enola.jpg" : "/static/tutor.png";

  loadingDiv.innerHTML = `
    <div class="message-avatar" style="background-image: url('${avatarUrl}')"></div>
    <div class="message-content">
      <div class="loading-spinner"></div>
      Thinking...
    </div>
  `;

  chatArea.appendChild(loadingDiv);
  chatArea.scrollTop = chatArea.scrollHeight;
}

/**
 * Removes the loading message from the chat area.
 */
export function removeLoadingMessage() {
  const loadingMsg = document.getElementById("loadingMessage");
  if (loadingMsg) {
    loadingMsg.remove();
  }
}

/**
 * Formats raw markdown text into HTML with custom styling (Amazon Q-style spacing, LaTeX rendering).
 * @param {string} text - The raw markdown text to format.
 * @returns {string} The formatted HTML string.
 */
export function formatMessageText(text) {
  // Convert comprehensive markdown formatting to HTML with Amazon Q-style spacing
  let formatted = text;

  // Process line by line for better control
  const lines = formatted.split("\n");
  const processedLines = [];
  let inList = false;
  let inCodeBlock = false;

  for (let i = 0; i < lines.length; i++) {
    let line = lines[i];
    const trimmed = line.trim();

    // Handle code blocks
    if (trimmed.startsWith("```")) {
      inCodeBlock = !inCodeBlock;
      processedLines.push(line);
      continue;
    }

    if (inCodeBlock) {
      processedLines.push(line);
      continue;
    }

    // Empty lines
    if (!trimmed) {
      processedLines.push("");
      inList = false;
      continue;
    }

    // Headings with spacing
    if (trimmed.startsWith("### ")) {
      if (
        processedLines.length > 0 &&
        processedLines[processedLines.length - 1] !== ""
      ) {
        processedLines.push(""); // Add space before
      }
      processedLines.push(
        `<h3 style="margin: 12px 0 8px 0; font-size: 16px; font-weight: 600; color: var(--text-primary);">${trimmed.substring(
          4
        )}</h3>`
      );
      inList = false;
    } else if (trimmed.startsWith("## ")) {
      if (
        processedLines.length > 0 &&
        processedLines[processedLines.length - 1] !== ""
      ) {
        processedLines.push(""); // Add space before
      }
      processedLines.push(
        `<h2 style="margin: 16px 0 10px 0; font-size: 18px; font-weight: 700; color: var(--text-primary);">${trimmed.substring(
          3
        )}</h2>`
      );
      inList = false;
    } else if (trimmed.startsWith("# ")) {
      if (
        processedLines.length > 0 &&
        processedLines[processedLines.length - 1] !== ""
      ) {
        processedLines.push("");
      }
      processedLines.push(
        `<h2 style="margin: 16px 0 10px 0; font-size: 18px; font-weight: 700; color: var(--text-primary);">${trimmed.substring(
          2
        )}</h2>`
      );
      inList = false;
    }
    // Bullet points with spacing
    else if (
      trimmed.startsWith("• ") ||
      trimmed.startsWith("- ") ||
      trimmed.startsWith("* ")
    ) {
      if (
        !inList &&
        processedLines.length > 0 &&
        processedLines[processedLines.length - 1] !== ""
      ) {
        processedLines.push(""); // Add space before list
      }
      const content = trimmed.substring(2).trim();
      processedLines.push(
        `<div style="margin: 4px 0; padding-left: 20px; position: relative;"><span style="position: absolute; left: 0;">•</span>${content}</div>`
      );
      inList = true;
    }
    // Numbered lists
    else if (/^\d+\.\s/.test(trimmed)) {
      if (
        !inList &&
        processedLines.length > 0 &&
        processedLines[processedLines.length - 1] !== ""
      ) {
        processedLines.push("");
      }
      processedLines.push(
        `<div style="margin: 4px 0; padding-left: 20px;">${trimmed}</div>`
      );
      inList = true;
    }
    // Blockquotes
    else if (trimmed.startsWith("> ")) {
      if (
        processedLines.length > 0 &&
        processedLines[processedLines.length - 1] !== ""
      ) {
        processedLines.push("");
      }
      processedLines.push(
        `<blockquote style="margin: 12px 0; padding: 10px 15px; border-left: 4px solid #2196f3; background: rgba(33, 150, 243, 0.1); border-radius: 4px;">${trimmed.substring(
          2
        )}</blockquote>`
      );
      if (i < lines.length - 1 && lines[i + 1].trim()) {
        processedLines.push("");
      }
      inList = false;
    }
    // Regular paragraphs
    else {
      if (inList && processedLines.length > 0) {
        processedLines.push(""); // Add space after list
      }
      processedLines.push(line);
      inList = false;
    }
  }

  formatted = processedLines.join("\n");

  // Apply inline formatting
  formatted = formatted
    .replace(
      /\*\*(.*?)\*\*/g,
      '<strong style="font-weight: 600;">$1</strong>'
    ) // Bold
    .replace(/\*(.*?)\*/g, "<em>$1</em>") // Italic
    .replace(
      /`([^`]+)`/g,
      '<code style="background: var(--bg-tertiary); padding: 2px 6px; border-radius: 3px; font-family: monospace; font-size: 0.9em;">$1</code>'
    ) // Inline code
    .replace(/\n\n/g, "<br><br>") // Double line breaks
    .replace(/\n/g, "<br>"); // Single line breaks

  // Render LaTeX using MathJax
  if (typeof MathJax !== 'undefined' && MathJax.typesetPromise) {
    formatted = formatted.replace(/\\\((.*?)\\\)/g, (match, p1) => {
      return `<span class="math-inline">\\(${p1}\\)</span>`;
    });
    formatted = formatted.replace(/\\\[(.*?)\\\]/g, (match, p1) => {
      return `<div class="math-display">\\[${p1}\\]</div>`;
    });
    // Trigger MathJax rendering for new content
    // Use a small delay to ensure elements are in DOM before typesetting
    setTimeout(() => {
      MathJax.typesetPromise();
    }, 100);
  }

  return formatted;
}

/**
 * Adds a new message to the chat area, animating its appearance.
 * @param {string} text - The content of the message (markdown supported).
 * @param {"user" | "bot"} sender - The sender of the message.
 * @param {string} currentTutor - The current active tutor ("enola" or "franklin") to determine bot avatar.
 * @param {string} [attachmentsHtml=""] - Optional HTML string for message attachments.
 */
export function addMessage(text, sender, currentTutor, attachmentsHtml = "") {
  const chatArea = document.getElementById("chatArea");
  if (!chatArea) return;
  const messageDiv = document.createElement("div");
  messageDiv.className = `message ${sender}`;
  messageDiv.style.opacity = "0";
  messageDiv.style.transform = "translateY(20px)";
  messageDiv.style.transition = "all 0.3s ease";

  const avatarUrl =
    sender === "user"
      ? "/static/user.png"
      : currentTutor === "enola"
      ? "/static/enola.jpg"
      : "/static/tutor.png";

  // Determine if the text is already HTML or needs markdown formatting
  const contentToDisplay = containsHtml(text) ? text : formatMessageText(text);

  messageDiv.innerHTML = `
          <div class="message-avatar" style="background-image: url('${avatarUrl}')"></div>
          <div class="message-content" style="white-space: pre-wrap;">${contentToDisplay}${attachmentsHtml}</div>
      `;

  chatArea.appendChild(messageDiv);

  // Animate message appearance
  setTimeout(() => {
    messageDiv.style.opacity = "1";
    messageDiv.style.transform = "translateY(0)";
  }, 50);

  chatArea.scrollTop = chatArea.scrollHeight;
}

/**
 * Updates the display of source files in the source panel.
 * @param {Array<Object>} sources - An array of source objects, each with a `title` and `created_at`.
 */
export function updateSources(sources) {
  const sourceList = document.getElementById("sourceList");
  if (!sourceList) return;
  sourceList.innerHTML = "";

  if (!sources || sources.length === 0) {
    sourceList.innerHTML = `
      <div class="no-sources-message">
        <div style="color: var(--text-secondary); font-size: 14px; text-align: center; padding: 20px;">
          No sources used in current response
        </div>
      </div>`;
    return;
  }

  // Add header for current chat sources
  const headerDiv = document.createElement("div");
  headerDiv.innerHTML = `
    <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 10px; padding: 0 10px; border-bottom: 1px solid var(--border-color); padding-bottom: 8px;">
      📄 Files used in this chat:
    </div>
  `;
  sourceList.appendChild(headerDiv);

  sources.forEach((source) => {
    // Filter out invalid sources
    if (!source || !source.title || typeof source.title !== 'string' || source.title.trim() === '') {
      console.warn("Skipping invalid source entry:", source);
      return;
    }

    const sourceItem = document.createElement("div");
    sourceItem.className = "source-item";

    const fileIcon = getFileIcon(source.title);
    const extension = (source.title.split(".").pop() || '').toLowerCase();
    const encodedFilename = encodeURIComponent(source.title); // URL-encode filename

    // Generate thumbnail for images and videos
    let thumbnailHtml = "";
    if (["jpg", "jpeg", "png", "gif", "bmp"].includes(extension)) {
      thumbnailHtml = `
        <div class="source-thumbnail">
          <img src="/uploads/${encodedFilename}" alt="${source.title}" 
               style="width: 60px; height: 40px; object-fit: cover; border-radius: 4px; margin-right: 8px;" 
               loading="lazy" onerror="this.style.display='none'">
        </div>`;
    } else if (["mp4", "avi", "mov", "mkv", "webm"].includes(extension)) {
      thumbnailHtml = `
        <div class="source-thumbnail">
          <video style="width: 60px; height: 40px; object-fit: cover; border-radius: 4px; margin-right: 8px;" 
                 muted loop playsinline preload="none" poster="/static/tutor.png" loading="lazy">
            <source src="/uploads/${encodedFilename}" type="video/${extension}">
          </video>
        </div>`;
    }

    // Pass the URL-encoded filename and extension directly as string literals
    sourceItem.innerHTML = `
      <div style="display: flex; align-items: flex-start; gap: 8px;" onclick="window.previewFile('${encodedFilename}', '${extension}')" style="cursor: pointer;">
        ${thumbnailHtml}
        <div style="flex: 1;">
          <div class="source-title">${fileIcon} ${source.title}</div>
          <div style="font-size: 11px; color: var(--text-secondary); margin-top: 2px;">
            ${source.created_at && typeof source.created_at === 'string' ? new Date(source.created_at).toLocaleDateString() : 'N/A'}
          </div>
        </div>
      </div>
    `;

    sourceList.appendChild(sourceItem);
  });
}

/**
 * Displays a file preview in a modal. Supports images, videos, audio, PDFs, DOCX, PPTX, MD, and TXT.
 * @param {string} encodedFilename - The URL-encoded filename of the file to preview.
 * @param {string} extension - The file extension (e.g., "pdf", "mp4").
 */
export function previewFile(encodedFilename, extension) {
  console.log("DEBUG: previewFile called with encodedFilename:", encodedFilename, "extension:", extension);
  if (!encodedFilename || typeof encodedFilename !== 'string' || encodedFilename.trim() === '') {
    console.error("Invalid filename provided for previewFile:", encodedFilename);
    showNotification("Cannot preview file: Invalid filename.", "error");
    return;
  }

  const filename = decodeURIComponent(encodedFilename); // URL-decode filename for display and internal logic

  // Determine file extension
  const fileExtension = (extension && typeof extension === 'string') ? extension : (filename.split(".").pop() || '').toLowerCase();

  if (!fileExtension) {
    showNotification("Cannot preview file: Unknown file type.", "error");
    return;
  }

  const modal = document.createElement("div");
  modal.classList.add("modal"); // Add modal class for global close handler
  modal.classList.add("show"); // Add 'show' class to trigger CSS visibility/opacity
  modal.style.cssText = `
    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    background: rgba(0,0,0,0.8); z-index: 2000; display: flex;
    align-items: center; justify-content: center;
  `;

  const modalContent = document.createElement("div");
  modalContent.className = "file-preview-modal-content";

  modalContent.innerHTML = `
    <div class="file-preview-header">
      <h3>${filename}</h3>
      <button class="file-preview-close-btn">&times;</button>
    </div>
    <div class="file-preview-body" id="filePreviewBody">
      <!-- Content will be loaded here -->
    </div>
  `;

  const filePreviewBody = modalContent.querySelector("#filePreviewBody");

  if (["jpg", "jpeg", "png", "gif", "bmp"].includes(fileExtension)) {
    filePreviewBody.innerHTML = `<img src="/uploads/${encodedFilename}" class="file-preview-image" alt="${filename}" loading="lazy">`;
  } else if (["mp4", "avi", "mov", "mkv", "webm"].includes(fileExtension)) {
    filePreviewBody.innerHTML = `<video controls class="file-preview-video" preload="metadata" poster="/static/tutor.png" loading="lazy"><source src="/uploads/${encodedFilename}" type="video/${fileExtension}"></video>`;
  } else if (["mp3", "wav", "m4a", "ogg"].includes(fileExtension)) {
    filePreviewBody.innerHTML = `<audio controls class="file-preview-audio" preload="metadata" loading="lazy"><source src="/uploads/${encodedFilename}" type="audio/${fileExtension}"></audio>`;
  } else if (["pdf", "docx", "doc", "ppt", "pptx"].includes(fileExtension)) {
    filePreviewBody.innerHTML = `<iframe src="/uploads/${encodedFilename}" class="file-preview-iframe" loading="lazy"></iframe>`;
  } else if (["md", "txt", "js", "css", "py", "html", "json", "xml", "yaml", "yml", "c", "cpp", "java", "go", "rb", "php", "ts", "tsx", "jsx"].includes(fileExtension)) {
    filePreviewBody.innerHTML = "<div>Loading...</div>";
    fetch(`/uploads/${encodedFilename}`)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.text();
      })
      .then((text) => {
        // Apply markdown formatting and LaTeX rendering for text-based files
        const formattedText = formatMessageText(text);
        filePreviewBody.innerHTML = `<div class="file-preview-text">${formattedText}</div>`;
      })
      .catch((error) => {
        console.error("Error loading file for preview:", error);
        filePreviewBody.innerHTML = `<div>Error loading file: ${error.message}</div>`;
      });
  } else {
    filePreviewBody.innerHTML = "<div>Unsupported file type for preview.</div>";
  }

  modal.appendChild(modalContent);
  document.body.appendChild(modal);

  // Close modal when clicking outside or on the close button
  modal.addEventListener("click", (e) => {
    if (e.target === modal || e.target.classList.contains("file-preview-close-btn")) {
      modal.remove();
    }
  });
}

/**
 * Displays a custom confirmation modal for delete operations.
 * @param {string} message - The confirmation message to display.
 * @returns {Promise<boolean>} A promise that resolves to `true` if confirmed, `false` if canceled.
 */
export function showDeleteConfirm(message) {
  return new Promise((resolve) => {
    const t = translations[currentLanguage];
    const modal = document.createElement("div");
    modal.className = "custom-modal";
    modal.innerHTML = `
      <div class="custom-modal-overlay"></div>
      <div class="custom-modal-content">
        <div class="custom-modal-icon">⚠️</div>
        <div class="custom-modal-message">${message}</div>
        <div class="custom-modal-buttons">
          <button class="custom-modal-btn cancel" id="cancelBtn">${t.cancel}</button>
          <button class="custom-modal-btn delete" id="deleteBtn">${t.delete}</button>
        </div>
      </div>
    `;

    document.body.appendChild(modal);

    // Animate in
    setTimeout(() => modal.classList.add("show"), 10);

    const cleanup = (result) => {
      modal.classList.remove("show");
      setTimeout(() => {
        if (document.body.contains(modal)) {
          document.body.removeChild(modal);
        }
      }, 300);
      resolve(result);
    };

    modal.querySelector("#cancelBtn").onclick = () => cleanup(false);
    modal.querySelector("#deleteBtn").onclick = () => cleanup(true);
    modal.querySelector(".custom-modal-overlay").onclick = () =>
      cleanup(false);
  });
}

/**
 * Displays a custom prompt modal for rename operations.
 * @param {string} message - The message to display in the prompt.
 * @param {string} defaultValue - The default value for the input field.
 * @returns {Promise<string | null>} A promise that resolves to the new name if confirmed, or `null` if canceled.
 */
export function showRenamePrompt(message, defaultValue = "") {
  return new Promise((resolve) => {
    const t = translations[currentLanguage];
    const modal = document.createElement("div");
    modal.className = "custom-modal";
    modal.innerHTML = `
      <div class="custom-modal-overlay"></div>
      <div class="custom-modal-content">
        <div class="custom-modal-icon">✏️</div>
        <div class="custom-modal-message">${message}</div>
        <input type="text" class="custom-modal-input" id="renamePromptInput" value="${defaultValue}" />
        <div class="custom-modal-buttons">
          <button class="custom-modal-btn secondary" id="cancelRenameBtn">${t.cancel}</button>
          <button class="custom-modal-btn primary" id="confirmRenameBtn">${t.rename}</button>
        </div>
      </div>
    `;

    document.body.appendChild(modal);

    const input = modal.querySelector("#renamePromptInput");
    input.focus();
    input.select();

    // Animate in
    setTimeout(() => modal.classList.add("show"), 10);

    const cleanup = (result) => {
      modal.classList.remove("show");
      setTimeout(() => {
        if (document.body.contains(modal)) {
          document.body.removeChild(modal);
        }
      }, 300);
      resolve(result);
    };

    modal.querySelector("#cancelRenameBtn").onclick = () => cleanup(null);
    modal.querySelector("#confirmRenameBtn").onclick = () => cleanup(input.value.trim());
    modal.querySelector(".custom-modal-overlay").onclick = () => cleanup(null);

    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        cleanup(input.value.trim());
      } else if (e.key === 'Escape') {
        e.preventDefault();
        cleanup(null);
      }
    });
  });
}
