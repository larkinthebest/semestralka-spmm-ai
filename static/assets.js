// static/assets.js

import { showNotification, getFileIcon, showDeleteConfirm, previewFile } from "./ui.js";
import { uploadFileApi, renameAssetApi, deleteAssetApi, fetchAssetsApi } from "./api.js";
import { currentChatId, chatAttachedAssets, chatSources, translations, currentLanguage, setCurrentChatId, setChatAttachedAssets, updateChatAttachedAssets, addChatAttachedAsset, removeChatAttachedAsset, deleteChatAttachedAssets, setChatSources, updateChatSources, addChatSource, deleteChatSource, setCurrentLanguage } from "./app.js"; // Import necessary globals from app.js
import { saveChatToDatabase } from "./chat.js"; // Import saveChatToDatabase from chat.js

let attachedFiles = []; // Files attached to the current message input

/**
 * Returns the array of files currently attached to the message input.
 * @returns {Array<File>} An array of File objects.
 */
export function getAttachedFiles() {
  return attachedFiles;
}

/**
 * Sets up drag and drop functionality for attaching files to the chat.
 * Allows dragging existing assets from the asset list or dropping new files from the system.
 */
export function setupDragAndDrop() {
  const middlePanel = document.getElementById("middlePanel");
  const dropOverlay = document.getElementById("dropOverlay");

  if (!middlePanel || !dropOverlay) {
    console.error("Drag and drop elements not found!");
    return;
  }

  let dragCounter = 0;

  console.log("DEBUG: setupDragAndDrop called.");

  // Add event listeners to the middlePanel to cover the entire chat area
  middlePanel.addEventListener("dragenter", (e) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter++;
    dropOverlay.classList.add("show");
    console.log("DEBUG: dragenter event. dragCounter:", dragCounter, "types:", e.dataTransfer.types, "items:", e.dataTransfer.items);
  });

  middlePanel.addEventListener("dragleave", (e) => {
    e.stopPropagation();
    dragCounter--;
    if (dragCounter === 0) {
      dropOverlay.classList.remove("show");
      console.log("DEBUG: dragleave event. dropOverlay hidden.");
    }
    console.log("DEBUG: dragleave event. dragCounter:", dragCounter);
  });

  middlePanel.addEventListener("dragover", (e) => {
    e.preventDefault();
    e.stopPropagation();
    e.dataTransfer.dropEffect = "copy";
    // console.log("DEBUG: middlePanel dragover event. types:", e.dataTransfer.types, "items:", e.dataTransfer.items); // Too verbose, uncomment if needed
  });

  // Add dragover listener to dropOverlay as well
  dropOverlay.addEventListener("dragover", (e) => {
    e.preventDefault();
    e.stopPropagation();
    e.dataTransfer.dropEffect = "copy";
    // console.log("DEBUG: dropOverlay dragover event. types:", e.dataTransfer.types, "items:", e.dataTransfer.items); // Too verbose, uncomment if needed
  });

  // Move the drop event listener to the dropOverlay
  dropOverlay.addEventListener("drop", async (e) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter = 0;
    dropOverlay.classList.remove("show");
    console.log("DEBUG: drop event on dropOverlay. dropOverlay hidden.");

    // Check for custom asset filename first
    if (e.dataTransfer.types.includes("text/x-asset-filename")) {
      const filename = e.dataTransfer.getData("text/x-asset-filename");
      if (filename) {
        console.log("DEBUG: Attaching existing asset by filename:", filename);
        addChatAttachedAsset(currentChatId, filename);
        updateAssetSelectionUI(); // Update checkboxes in the asset list
        // Also add to attachedFiles for display in the message input
        // For simplicity, we'll create a dummy File object for display purposes
        // This might need refinement if full File object properties are critical
        const dummyFile = { name: filename, type: "application/octet-stream", size: 0 };
        attachFileToMessage(dummyFile);
        saveChatToDatabase(); // Save the updated chat with new attached assets
      }
    } else {
      // Fallback to handling actual file drops
      const files = e.dataTransfer.files;
      console.log("DEBUG: Files dropped on overlay:", files, "types:", e.dataTransfer.types, "items:", e.dataTransfer.items);
      if (files.length > 0) {
        Array.from(files).forEach(file => {
          console.log("DEBUG: Attaching file to message from overlay (e.dataTransfer.files):", file.name);
          attachFileToMessage(file);
        });
      } else {
        console.log("DEBUG: No files directly in e.dataTransfer.files. Attempting fallback with dataTransfer.items.");
        if (e.dataTransfer.items) {
          for (let i = 0; i < e.dataTransfer.items.length; i++) {
            const item = e.dataTransfer.items[i];
            console.log(`DEBUG: dataTransfer.items[${i}] - kind: ${item.kind}, type: ${item.type}`);
            if (item.kind === 'file') {
              const file = item.getAsFile();
              if (file) {
                console.log("DEBUG: Attaching file from dataTransfer.items:", file.name);
                attachFileToMessage(file);
              } else {
                console.log("DEBUG: item.getAsFile() returned null for a file item.");
              }
            }
          }
        } else {
          console.log("DEBUG: e.dataTransfer.items is also not available.");
        }
      }
    }
  });
}

/**
 * Updates the checked state of asset checkboxes in the asset list
 * based on which assets are currently attached to the active chat.
 */
export function updateAssetSelectionUI() {
  document.querySelectorAll(".asset-checkbox").forEach((checkbox) => {
    const filename = checkbox.getAttribute("data-filename");
    checkbox.checked = (chatAttachedAssets[currentChatId] || []).includes(
      filename
    );
  });
}

/**
 * Attaches a file to the current message input for sending.
 * Prevents duplicate files from being attached.
 * @param {File} file - The File object to attach.
 */
export function attachFileToMessage(file) {
  const isDuplicate = attachedFiles.some(existingFile => existingFile.name === file.name);
  if (!isDuplicate) {
    attachedFiles.push(file);
    updateAttachedFilesDisplay();
  } else {
    console.log(`File "${file.name}" is already attached to the current message.`);
  }
}

/**
 * Updates the display of files currently attached to the message input.
 */
export function updateAttachedFilesDisplay() {
  const attachedFilesDiv = document.getElementById("attachedFiles");
  if (!attachedFilesDiv) return;
  attachedFilesDiv.innerHTML = "";

  if (attachedFiles.length === 0) {
    attachedFilesDiv.style.display = "none";
    return;
  }

  attachedFilesDiv.style.display = "flex";
  attachedFiles.forEach((file, index) => {
    const fileIcon = getFileIcon(file.name);
    const fileElement = document.createElement("div");
    fileElement.className = "attached-file-item";
    fileElement.innerHTML = `
      ${fileIcon} ${file.name}
      <button class="remove-attached-file" onclick="window.removeAttachedFile(${index})">&times;</button>
    `;
    attachedFilesDiv.appendChild(fileElement);
  });
}

/**
 * Removes an attached file from the message input by its index.
 * @param {number} index - The index of the file to remove from the `attachedFiles` array.
 */
export function removeAttachedFile(index) {
  attachedFiles.splice(index, 1);
  updateAttachedFilesDisplay();
}

/**
 * Handles file upload events from hidden input fields.
 * @param {Event} event - The file input change event.
 * @param {"attach" | "asset"} type - The type of upload ("attach" for message, "asset" for asset list).
 * @returns {Promise<void>}
 */
export async function handleFileUpload(event, type) {
  const files = event.target.files;

  if (type === "attach") {
    Array.from(files).forEach((file) => {
      attachFileToMessage(file);
    });
  } else {
    await addFilesToAssets(files);
  }

  event.target.value = "";
}

/**
 * Adds new files to the asset list, uploads them to the backend, and updates the UI.
 * @param {FileList | File[]} files - A FileList or array of File objects to add.
 * @returns {Promise<void>}
 */
export async function addFilesToAssets(files) {
  const assetList = document.getElementById("assetList");
  if (!assetList) return;

  if (assetList.querySelector(".no-assets-message")) {
    assetList.innerHTML = "";
  }

  for (let file of files) {
    const tempAssetId = `temp-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
    const fileIcon = getFileIcon(file.name);
    const assetItem = document.createElement("div");
    assetItem.className = "asset-item loading";
    assetItem.setAttribute("data-asset-id", tempAssetId);
    assetItem.innerHTML = `
      <div style="display: flex; align-items: center; flex: 1;">
        <div class="loading-spinner" style="margin-right: 8px;"></div>
        <label style="margin-left: 8px;">${fileIcon} ${file.name} (Uploading...)</label>
      </div>
    `;
    assetList.prepend(assetItem);

    try {
      const uploadedAssetData = await uploadFileApi(file);
      if (uploadedAssetData && uploadedAssetData.file_type === "existing") {
        assetItem.remove(); // Remove the temporary loading item
        showNotification(`File "${uploadedAssetData.filename}" already exists.`, "info");
      } else if (uploadedAssetData && uploadedAssetData.id) {
        assetItem.classList.remove("loading");
        assetItem.setAttribute("data-asset-id", uploadedAssetData.id);
        assetItem.setAttribute("draggable", "true");
        assetItem.setAttribute(
          "ondragstart",
          `window.dragAsset(event, '${uploadedAssetData.filename}')`
        );
        const isSelected = (chatAttachedAssets[currentChatId] || []).includes(
          uploadedAssetData.filename
        );
        const extension = (uploadedAssetData.filename && typeof uploadedAssetData.filename === 'string') ? uploadedAssetData.filename.split('.').pop().toLowerCase() : '';
        assetItem.innerHTML = `
          <div style="display: flex; align-items: center; flex: 1; cursor: pointer;" onclick="window.previewFile(JSON.stringify('${uploadedAssetData.filename}'), '${extension}')">
            <input type="checkbox" class="asset-checkbox" 
                   id="asset-checkbox-${uploadedAssetData.id}" 
                   data-filename="${uploadedAssetData.filename}" 
                   ${isSelected ? "checked" : ""} 
                   onclick="event.stopPropagation(); window.toggleChatAssetSelection(JSON.stringify('${
                     uploadedAssetData.filename
                   }'))">
            <label for="asset-checkbox-${uploadedAssetData.id}" style="margin-left: 8px; cursor: pointer;">${fileIcon} ${
            uploadedAssetData.filename
          }</label>
          </div>
          <div class="item-actions">
            <button class="action-btn" onclick="event.stopPropagation(); window.renameAsset(${uploadedAssetData.id})">✏️</button>
            <button class="action-btn" onclick="event.stopPropagation(); window.deleteAsset(${uploadedAssetData.id})">🗑️</button>
          </div>
        `;
        showNotification(`File "${uploadedAssetData.filename}" uploaded successfully!`, "success");

        // Update chatAttachedAssets and chatSources after successful upload
        addChatAttachedAsset(currentChatId, uploadedAssetData.filename);
        addChatSource(currentChatId, { title: uploadedAssetData.filename, type: file.type, created_at: new Date().toISOString() });
        saveChatToDatabase(); // Save the updated chat with new attached assets
      } else {
        assetItem.remove();
        showNotification(`Failed to upload "${file.name}".`, "error");
      }
    } catch (error) {
      console.error("Error during file upload in addFilesToAssets:", error);
      assetItem.remove();
      showNotification(`Error uploading "${file.name}". Please try again.`, "error");
    }
  }
  updateAssetSelectionUI();
}

/**
 * Handles the drag start event for an asset item, setting data for drag and drop.
 * @param {DragEvent} event - The drag event.
 * @param {string} filename - The filename of the asset being dragged.
 */
export function dragAsset(event, filename) {
  event.dataTransfer.setData("text/plain", filename);
  event.dataTransfer.setData("text/x-asset-filename", filename); // Custom data type for existing assets
  event.dataTransfer.effectAllowed = "copy";
}

/**
 * Toggles the selection state of an asset for the current chat.
 * Adds or removes the asset from `chatAttachedAssets` and updates the UI.
 * @param {string} filename - The filename of the asset to toggle.
 */
export function toggleChatAssetSelection(filename) {
  if (!chatAttachedAssets[currentChatId]) {
    updateChatAttachedAssets(currentChatId, []);
  }
  const index = chatAttachedAssets[currentChatId].indexOf(filename);
  if (index > -1) {
    removeChatAttachedAsset(currentChatId, filename);
  } else {
    addChatAttachedAsset(currentChatId, filename);
  }
  updateAssetSelectionUI();
  saveChatToDatabase();
}

/**
 * Renames an asset after prompting the user for a new filename.
 * Updates the backend and frontend UI.
 * @param {number} assetId - The ID of the asset to rename.
 * @returns {Promise<void>}
 */
export async function renameAsset(assetId) {
  const assetItem = document.querySelector(`[data-asset-id="${assetId}"]`);
  if (!assetItem) return;
  const currentFilename = assetItem.querySelector("label").textContent.trim().substring(2).trim();
  
  const newFilename = prompt(`Rename asset "${currentFilename}":`, currentFilename);

  if (newFilename && newFilename.trim() !== currentFilename) {
    try {
      const data = await renameAssetApi(assetId, newFilename);
      const label = assetItem.querySelector("label");
      if (label) label.innerHTML = `${getFileIcon(data.new_filename)} ${data.new_filename}`;
      for (const chatId in chatAttachedAssets) {
        const index = chatAttachedAssets[chatId].indexOf(currentFilename);
        if (index > -1) {
          updateChatAttachedAssets(chatId, chatAttachedAssets[chatId].map(f => f === currentFilename ? data.new_filename : f));
        }
      }
      updateAssetSelectionUI();
      showNotification("Asset renamed successfully!", "success");
    } catch (error) {
      console.error("Error renaming asset:", error);
      showNotification(error.message || "Failed to rename asset.", "error");
    }
  }
}

/**
 * Deletes an asset after user confirmation.
 * Removes the asset from the backend, frontend list, and any associated chats.
 * @param {number} assetId - The ID of the asset to delete.
 * @returns {Promise<void>}
 */
export async function deleteAsset(assetId) {
  const confirmed = await showDeleteConfirm(
    translations[currentLanguage].deleteConfirm
  );
  if (confirmed) {
    const assetItem = document.querySelector(
      `[data-asset-id="${assetId}"]`
    );
    if (!assetItem) return;
    const filename = assetItem
      .querySelector("label")
      .textContent.trim()
      .substring(2)
      .trim();

    try {
      await deleteAssetApi(assetId);
      assetItem.remove();

      for (const chatId in chatAttachedAssets) {
        removeChatAttachedAsset(chatId, filename);
      }
      updateAssetSelectionUI();

      const assetList = document.getElementById("assetList");
      const remainingAssets = assetList ? document.querySelectorAll(".asset-item") : [];
      if (remainingAssets.length === 0) {
        if (assetList) {
          assetList.innerHTML = `
            <div class="no-assets-message">
              No assets uploaded
            </div>
          `;
        }
      }
      showNotification("Asset deleted successfully!", "success");
    } catch (error) {
      console.error("Error deleting asset:", error);
      showNotification(error.message || "Failed to delete asset.", "error");
    }
  }
}

/**
 * Loads all assets for the current user from the backend and displays them in the asset list.
 * @returns {Promise<void>}
 */
export async function loadAssetsIntoMainframe() {
  const assetList = document.getElementById("assetList");
  if (!assetList) {
    console.error("Asset list element not found during loadAssetsIntoMainframe!");
    return;
  }
  assetList.innerHTML = '<div class="no-assets-message">Loading assets...</div>';

  try {
    const data = await fetchAssetsApi();
    assetList.innerHTML = "";

    if (data && data.length > 0) {
      for (const asset of data) {
        const fileIcon = getFileIcon(asset.filename);
        const assetItem = document.createElement("div");
        assetItem.className = "asset-item";
        assetItem.setAttribute("data-asset-id", asset.id);
        assetItem.setAttribute("draggable", "true");
        assetItem.setAttribute(
          "ondragstart",
          `window.dragAsset(event, '${asset.filename}')`
        );
        const isSelected = (chatAttachedAssets[currentChatId] || []).includes(
          asset.filename
        );
        const extension = (asset.filename && typeof asset.filename === 'string') ? asset.filename.split('.').pop().toLowerCase() : '';
        assetItem.innerHTML = `
          <div style="display: flex; align-items: center; flex: 1; cursor: pointer;" onclick="window.previewFile(JSON.stringify('${asset.filename}'), '${extension}')">
            <input type="checkbox" class="asset-checkbox" 
                   id="asset-checkbox-${asset.id}" 
                   data-filename="${asset.filename}" 
                   ${isSelected ? "checked" : ""} 
                   onclick="event.stopPropagation(); window.toggleChatAssetSelection(JSON.stringify('${
                     asset.filename
                   }'))">
            <label for="asset-checkbox-${asset.id}" style="margin-left: 8px; cursor: pointer;">${fileIcon} ${
            asset.filename
          }</label>
          </div>
          <div class="item-actions">
            <button class="action-btn" onclick="event.stopPropagation(); window.renameAsset(${asset.id})">✏️</button>
            <button class="action-btn" onclick="event.stopPropagation(); window.deleteAsset(${asset.id})">🗑️</button>
          </div>
        `;
        assetList.appendChild(assetItem);
      }
      updateAssetSelectionUI();
    } else {
      assetList.innerHTML = `<div class="no-assets-message">${translations[currentLanguage].noAssets}</div>`;
    }
  } catch (error) {
    console.error("Error loading assets into mainframe:", error);
    assetList.innerHTML = `<div class="no-assets-message">Error loading assets.</div>`;
    showNotification(`Error loading assets: ${error.message}`, "error");
  }
}

/**
 * Triggers the hidden file input to open the file selection dialog for adding new assets.
 */
export function addAsset() {
  const fileInput = document.getElementById("fileInput");
  if (fileInput) fileInput.click();
}

/**
 * Triggers the hidden file input to open the file selection dialog for attaching files to the current message.
 */
export function attachFile() {
  const attachInput = document.getElementById("attachInput");
  if (attachInput) attachInput.click();
}
