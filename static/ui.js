// static/ui.js

import { translations, currentLanguage } from './app.js'; // Assuming app.js will export these

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

export function loadTheme() {
  const savedTheme = localStorage.getItem("theme");
  if (savedTheme) {
    document.documentElement.setAttribute("data-theme", savedTheme);
  } else {
    document.documentElement.setAttribute("data-theme", "light"); // Default theme
  }
  updateThemeToggleIcon();
}

export function toggleTheme() {
  const currentTheme = document.documentElement.getAttribute("data-theme");
  const newTheme = currentTheme === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", newTheme);
  localStorage.setItem("theme", newTheme);
  updateThemeToggleIcon();
}

export function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.style.display = "none";
}

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

export function removeLoadingMessage() {
  const loadingMsg = document.getElementById("loadingMessage");
  if (loadingMsg) {
    loadingMsg.remove();
  }
}

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
  if (typeof MathJax !== 'undefined') {
    formatted = formatted.replace(/\\\((.*?)\\\)/g, (match, p1) => {
      return `<span class="math-inline">\\(${p1}\\)</span>`;
    });
    formatted = formatted.replace(/\\\[(.*?)\\\]/g, (match, p1) => {
      return `<div class="math-display">\\[${p1}\\]</div>`;
    });
    // Trigger MathJax rendering for new content
    setTimeout(() => {
      MathJax.typesetPromise();
    }, 0);
  }

  return formatted;
}

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

  // Format text for better display
  const formattedText = formatMessageText(text);

  messageDiv.innerHTML = `
          <div class="message-avatar" style="background-image: url('${avatarUrl}')"></div>
          <div class="message-content" style="white-space: pre-wrap;">${formattedText}${attachmentsHtml}</div>
      `;

  chatArea.appendChild(messageDiv);

  // Animate message appearance
  setTimeout(() => {
    messageDiv.style.opacity = "1";
    messageDiv.style.transform = "translateY(0)";
  }, 50);

  chatArea.scrollTop = chatArea.scrollHeight;
}

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
               onerror="this.style.display='none'">
        </div>`;
    } else if (["mp4", "avi", "mov", "mkv", "webm"].includes(extension)) {
      thumbnailHtml = `
        <div class="source-thumbnail">
          <video style="width: 60px; height: 40px; object-fit: cover; border-radius: 4px; margin-right: 8px;" 
                 muted>
            <source src="/uploads/${encodedFilename}" type="video/${extension}">
          </video>
        </div>`;
    }

    sourceItem.innerHTML = `
      <div style="display: flex; align-items: flex-start; gap: 8px;" onclick="previewFile('${encodedFilename}', '${extension}')" style="cursor: pointer;">
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

export function previewFile(encodedFilename, extension) {
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
  modal.style.cssText = `
    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    background: rgba(0,0,0,0.8); z-index: 2000; display: flex;
    align-items: center; justify-content: center;
  `;
  modal.classList.add("modal"); // Add modal class for global close handler

  const content = document.createElement("div");
  content.style.cssText = `
    background: var(--bg-secondary); border-radius: 8px; padding: 20px;
    max-width: 80%; max-height: 80%; overflow: auto; position: relative;
  `;

  const header = document.createElement("div");
  header.innerHTML = `
    <h3>${filename}</h3>
    <button onclick="this.closest('.modal').remove()" style="
      position: absolute; top: 10px; right: 15px; background: none;
      border: none; font-size: 20px; cursor: pointer;
    ">&times;</button>
  `;

  const body = document.createElement("div");
  body.style.cssText = "max-height: 60vh; overflow-y: auto;"; // Add scroll for content

  if (["jpg", "jpeg", "png", "gif", "bmp"].includes(fileExtension)) {
    body.innerHTML = `<img src="/uploads/${encodedFilename}" style="max-width: 100%; height: auto;" alt="${filename}">`;
  } else if (["mp4", "avi", "mov", "mkv", "webm"].includes(fileExtension)) {
    body.innerHTML = `<video controls style="max-width: 100%; height: auto;"><source src="/uploads/${encodedFilename}" type="video/${fileExtension}"></video>`;
  } else if (["mp3", "wav", "m4a", "ogg"].includes(fileExtension)) {
    body.innerHTML = `<audio controls style="width: 100%;"><source src="/uploads/${encodedFilename}" type="audio/${fileExtension}"></audio>`;
  } else if (["pdf", "docx", "doc", "ppt", "pptx"].includes(fileExtension)) {
    body.innerHTML = `<iframe src="/uploads/${encodedFilename}" style="width: 100%; height: 500px; border: none;"></iframe>`;
  } else if (["md", "txt"].includes(fileExtension)) {
    body.innerHTML = "<div>Loading...</div>";
    fetch(`/uploads/${encodedFilename}`)
      .then((response) => response.text())
      .then((text) => {
        body.innerHTML = `<pre style="white-space: pre-wrap; font-family: monospace; font-size: 14px;">${text}</pre>`;
      })
      .catch(() => {
        body.innerHTML = "<div>Error loading file</div>";
      });
  } else {
    body.innerHTML = "<div>Unsupported file type for preview.</div>";
  }

  content.appendChild(header);
  content.appendChild(body);
  modal.appendChild(content);
  document.body.appendChild(modal);

  modal.addEventListener("click", (e) => {
    if (e.target === modal) modal.remove();
  });
}

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
