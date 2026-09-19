/* ExamCloud AI — Central API Client & Utils */

const API_BASE_URL = window.location.origin.includes("localhost") || window.location.origin.includes("127.0.0.1")
  ? "http://127.0.0.1:8000/api"
  : "/api";

// Toast Notification Engine
function showToast(message, type = "info") {
  let container = document.getElementById("toast-container");
  if (!container) {
    container = document.createElement("div");
    container.id = "toast-container";
    document.body.appendChild(container);
  }

  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// Token Storage Helpers
function getAuthToken() {
  return localStorage.getItem("examcloud_token");
}

function setAuthToken(token) {
  localStorage.setItem("examcloud_token", token);
}

function getUserProfile() {
  const profile = localStorage.getItem("examcloud_user");
  return profile ? JSON.parse(profile) : null;
}

function setUserProfile(user) {
  localStorage.setItem("examcloud_user", JSON.stringify(user));
}

function clearAuth() {
  localStorage.removeItem("examcloud_token");
  localStorage.removeItem("examcloud_user");
}

// Core API Fetch Function
async function apiFetch(endpoint, options = {}) {
  const token = getAuthToken();
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {})
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const config = {
    ...options,
    headers
  };

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
    
    if (response.status === 401) {
      clearAuth();
      if (!window.location.pathname.endsWith("login.html") && !window.location.pathname.endsWith("register.html") && window.location.pathname !== "/") {
        window.location.href = "/static/login.html";
      }
      throw new Error("Session expired. Please log in again.");
    }

    if (response.status === 204) {
      return null;
    }

    const data = await response.json();

    if (!response.ok) {
      const errorMsg = data.detail || "An error occurred during request execution";
      throw new Error(errorMsg);
    }

    return data;
  } catch (err) {
    console.error(`API Error [${endpoint}]:`, err);
    throw err;
  }
}
