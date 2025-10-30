// static/api.js

const API_BASE_URL = ""; // Assuming API is on the same host

export async function fetchApi(endpoint, options = {}) {
  const token = localStorage.getItem("access_token");
  const headers = {
    "Content-Type": "application/json",
    ...(token && { Authorization: `Bearer ${token}` }),
    ...options.headers,
  };

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    if (response.status === 401) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("user");
      window.location.href = "/auth"; // Redirect to login page
      throw new Error("Unauthorized: Session expired. Please log in again.");
    }
    let errorDetail = `API call to ${endpoint} failed with status ${response.status}.`;
    try {
      const errorData = await response.json();
      if (errorData.detail) {
        if (Array.isArray(errorData.detail)) {
          // FastAPI validation errors often come as an array of objects
          errorDetail = errorData.detail.map(err => `${err.loc.join('.')} - ${err.msg}`).join('; ');
        } else if (typeof errorData.detail === 'string') {
          errorDetail = errorData.detail;
        }
      }
    } catch (e) {
      // If response is not JSON, use status text
      errorDetail = response.statusText || errorDetail;
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

export async function addNewChatApi() {
  return fetchApi("/chats/new", { method: "POST" });
}

export async function renameChatApi(chatId, newTitle) {
  return fetchApi(`/chats/${chatId}/rename`, {
    method: "PATCH",
    body: JSON.stringify({ new_title: newTitle }),
  });
}

export async function deleteChatApi(chatId) {
  return fetchApi(`/chats/${chatId}`, { method: "DELETE" });
}

export async function fetchChatDetailsApi(chatId) {
  return fetchApi(`/chats/${chatId}`);
}

export async function saveChatToDatabaseApi(chatData) {
  return fetchApi("/chats/save", {
    method: "POST",
    body: JSON.stringify(chatData),
  });
}

export async function loadChatsFromDatabaseApi() {
  return fetchApi("/chats/list");
}

export async function uploadFileApi(file) {
  const formData = new FormData();
  formData.append("file", file);
  console.log("DEBUG: In uploadFileApi, FormData prepared for upload. Appending file:", file.name);
  // Attempt to log FormData entries (note: this might consume the FormData object in some browsers/environments)
  for (let pair of formData.entries()) {
      console.log(`DEBUG: FormData entry - Key: ${pair[0]}, Value: ${pair[1]}`);
  }

  const token = localStorage.getItem("access_token");
  const headers = {};
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  // When using FormData, the browser automatically sets the 'Content-Type' header
  // with the correct 'multipart/form-data' and boundary.
  // Manually setting 'Content-Type': 'application/json' or similar will break it.
  // So, we only pass the Authorization header if it exists.

  return fetch(`${API_BASE_URL}/documents/upload`, {
    method: "POST",
    body: formData,
    headers: headers, // Pass headers object directly
  }).then(async response => {
    if (!response.ok) {
      if (response.status === 401) {
        localStorage.removeItem("access_token");
        localStorage.removeItem("user");
        window.location.href = "/auth"; // Redirect to login page
        throw new Error("Unauthorized: Session expired. Please log in again.");
      }
      let errorDetail = `API call to /documents/upload failed with status ${response.status}.`;
      try {
        const errorData = await response.json();
        if (errorData.detail) {
          if (Array.isArray(errorData.detail)) {
            errorDetail = errorData.detail.map(err => `${err.loc.join('.')} - ${err.msg}`).join('; ');
          } else if (typeof errorData.detail === 'string') {
            errorDetail = errorData.detail;
          }
        }
      } catch (e) {
        errorDetail = response.statusText || errorDetail;
      }
      throw new Error(errorDetail);
    }
    return response.json();
  });
}

export async function renameAssetApi(assetId, newFilename) {
  return fetchApi(`/assets/${assetId}/rename`, {
    method: "PATCH",
    body: JSON.stringify({ new_filename: newFilename }),
  });
}

export async function deleteAssetApi(assetId) {
  return fetchApi(`/assets/${assetId}`, { method: "DELETE" });
}

export async function fetchAssetsApi() {
  return fetchApi("/assets");
}

export async function generateQuizApi(quizRequestData) {
  return fetchApi("/quizzes/generate", {
    method: "POST",
    body: JSON.stringify(quizRequestData),
  });
}

export async function submitQuizApi(quizSubmissionData) {
  return fetchApi("/quizzes/submit", {
    method: "POST",
    body: JSON.stringify(quizSubmissionData),
  });
}

export async function fetchQuizHistoryApi() {
  return fetchApi("/quiz-results/history");
}

export async function fetchQuizStatsApi() {
  return fetchApi("/quiz-results/stats");
}

export async function simpleChatApi(chatRequestData) {
  return fetchApi("/simple-chat", {
    method: "POST",
    body: JSON.stringify(chatRequestData),
  });
}
