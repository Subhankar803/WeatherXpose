/**
 * Weather Xpose - Centralized API Service Client
 * Connects frontend interfaces to the FastAPI backend at http://127.0.0.1:8000.
 *
 * Provides:
 * - Unified base URL management
 * - JWT authentication token persistence
 * - Standardized apiFetch() with error handling
 * - Clean method wrappers for Auth, Reports, Map, Weather & Admin APIs
 */

function getApiBaseUrl() {
    // 1. Explicit override via query parameter (?api_base=https://... or ?backend=https://...)
    try {
        const params = new URLSearchParams(window.location.search);
        const queryBase = params.get("api_base") || params.get("backend");
        if (queryBase) {
            const clean = queryBase.replace(/\/$/, "");
            localStorage.setItem("weatherxpose-api-base", clean);
            return clean;
        }
    } catch (e) {}

    // 2. Explicit override saved in localStorage
    const saved = localStorage.getItem("weatherxpose-api-base");
    if (saved) return saved.replace(/\/$/, "");

    // 3. Global window config if set by page
    if (window.API_BASE_URL && window.API_BASE_URL !== "http://127.0.0.1:8000") {
        return window.API_BASE_URL.replace(/\/$/, "");
    }

    // 4. Remote / ngrok / HTTPS environments:
    // Remote users and HTTPS pages must use same-origin (window.location.origin)
    // so requests route through serve_frontend.py reverse proxy, eliminating
    // Mixed-Content (HTTPS -> HTTP) blocks and localhost lookup failures.
    const isLocalhost = window.location.hostname === "127.0.0.1" || window.location.hostname === "localhost";
    if (!isLocalhost || window.location.protocol === "https:") {
        return window.location.origin;
    }

    // 5. Default local dev fallback (backend on 8000)
    return "http://127.0.0.1:8000";
}

// Global accessor for current API base
const API_BASE_URL = getApiBaseUrl();

// Automatically migrate legacy session keys to Weather Xpose
try {
    const legacyPrefix = ["weather", "360", "-"].join("");
    for (let i = localStorage.length - 1; i >= 0; i--) {
        const k = localStorage.key(i);
        if (k && k.startsWith(legacyPrefix)) {
            const newKey = "weatherxpose-" + k.slice(legacyPrefix.length);
            if (!localStorage.getItem(newKey)) {
                localStorage.setItem(newKey, localStorage.getItem(k));
            }
            localStorage.removeItem(k);
        }
    }
} catch (_) {}

// --- Token Management Helpers ---
function getAuthToken() {
    return localStorage.getItem("weatherxpose-auth-token") || localStorage.getItem("weatherxpose-token") || "";
}

function setAuthToken(token) {
    if (token) {
        localStorage.setItem("weatherxpose-auth-token", token);
        localStorage.setItem("weatherxpose-token", token);
    }
}

function clearAuth() {
    [
        "weatherxpose-auth-token", "weatherxpose-token", "weatherxpose-login-status",
        "weatherxpose-user-role", "weatherxpose-user-name", "weatherxpose-user-email",
        "weatherxpose-admin-email", "weatherxpose-admin-role", "weatherxpose-admin-permission",
        "weatherxpose-admin-name", "weatherxpose-location"
    ].forEach(k => localStorage.removeItem(k));
    sessionStorage.clear();
}

function getUserRole() {
    return localStorage.getItem("weatherxpose-user-role") || "guest";
}

function isLoggedIn() {
    return (localStorage.getItem("weatherxpose-login-status") === "logged-in") || !!getAuthToken();
}

async function logout() {
    try {
        if (typeof apiFetch === "function") {
            await apiFetch("/api/auth/logout", { method: "POST" });
        }
    } catch {
        // Continue logout even if offline or network error
    }
    clearAuth();
    if (typeof showNotice === "function") {
        showNotice("Logged out successfully.", "info", 1500);
    }
    setTimeout(() => {
        window.location.href = "login.html";
    }, 350);
}

// --- Unified API Fetch Wrapper ---
async function apiFetch(endpoint, options = {}) {
    const baseUrl = getApiBaseUrl();
    const url = endpoint.startsWith("http") ? endpoint : `${baseUrl}${endpoint}`;

    const headers = {
        "Accept": "application/json",
        ...(options.headers || {}),
    };

    // Attach JWT Bearer Token if available
    const token = getAuthToken();
    if (token && !headers["Authorization"]) {
        headers["Authorization"] = `Bearer ${token}`;
    }

    // Default to JSON body if object provided and Content-Type not set
    if (options.body && typeof options.body === "object" && !(options.body instanceof FormData)) {
        headers["Content-Type"] = "application/json";
        options.body = JSON.stringify(options.body);
    }

    let response;
    try {
        response = await fetch(url, {
            ...options,
            headers,
        });
    } catch (fetchErr) {
        console.error("[Weather Xpose API Connection Error]", fetchErr, "Target URL:", url);
        const isRemote = window.location.hostname.includes("ngrok") || window.location.protocol === "https:";
        let friendlyMsg = fetchErr.message || "Failed to fetch";
        if (friendlyMsg.includes("Failed to fetch") || friendlyMsg.includes("NetworkError")) {
            if (isRemote) {
                friendlyMsg = `Backend unavailable. Ensure frontend is running with 'python serve_frontend.py 3000' or specify ?backend=URL`;
            } else {
                friendlyMsg = `Cannot connect to backend at ${baseUrl}. Please make sure uvicorn is running on port 8000.`;
            }
        }
        const netErr = new Error(friendlyMsg);
        netErr.originalError = fetchErr;
        throw netErr;
    }

    let data;
    const contentType = response.headers.get("content-type");
    if (contentType && contentType.includes("application/json")) {
        data = await response.json();
    } else {
        const text = await response.text();
        try {
            data = JSON.parse(text);
        } catch {
            data = { text };
        }
    }

    if (!response.ok) {
        let errorMsg = "An error occurred";
        if (data && data.detail) {
            if (typeof data.detail === "string") {
                errorMsg = data.detail;
            } else if (Array.isArray(data.detail)) {
                errorMsg = data.detail.map(d => d.msg || JSON.stringify(d)).join(", ");
            }
        } else if (data && data.message) {
            errorMsg = data.message;
        } else if (response.status === 404) {
            errorMsg = "API route not found (404). Start frontend with 'python serve_frontend.py 3000' so /api routes proxy to backend.";
        } else if (response.statusText) {
            errorMsg = `${response.status} ${response.statusText}`;
        }
        const error = new Error(errorMsg);
        error.status = response.status;
        error.data = data;
        throw error;
    }

    return data;
}

// --- Multipart File Upload Wrapper ---
async function apiUpload(endpoint, formData) {
    const baseUrl = getApiBaseUrl();
    const url = endpoint.startsWith("http") ? endpoint : `${baseUrl}${endpoint}`;
    const headers = {
        "Accept": "application/json",
    };

    const token = getAuthToken();
    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }

    let response;
    try {
        response = await fetch(url, {
            method: "POST",
            headers,
            body: formData,
        });
    } catch (fetchErr) {
        console.error("[Weather Xpose Upload Connection Error]", fetchErr, "Target URL:", url);
        const friendlyMsg = `Upload connection error. Target URL: ${url}`;
        const netErr = new Error(friendlyMsg);
        netErr.originalError = fetchErr;
        throw netErr;
    }

    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
        const errorMsg = data.detail || data.message || `Upload failed with status ${response.status}`;
        const error = new Error(errorMsg);
        error.status = response.status;
        error.data = data;
        throw error;
    }

    return data;
}

// --- Global UI Toast / Alert Notification Helper ---
function showNotice(message, type = "info", duration = 4000) {
    let container = document.getElementById("weatherxpose-toast-container");
    if (!container) {
        container = document.createElement("div");
        container.id = "weatherxpose-toast-container";
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 999999;
            display: flex;
            flex-direction: column;
            gap: 10px;
            max-width: 420px;
            pointer-events: none;
        `;
        document.body.appendChild(container);
    }

    const toast = document.createElement("div");
    toast.style.cssText = `
        pointer-events: auto;
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px 18px;
        border-radius: 10px;
        font-family: 'Inter', sans-serif;
        font-size: 13px;
        font-weight: 500;
        color: #ffffff;
        box-shadow: 0 10px 25px -5px rgba(0,0,0,0.3);
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        opacity: 0;
        transform: translateX(30px);
    `;

    let bgColor = "#1e293b";
    let icon = "fa-circle-info";
    if (type === "success") {
        bgColor = "linear-gradient(135deg, #059669, #10b981)";
        icon = "fa-circle-check";
    } else if (type === "error") {
        bgColor = "linear-gradient(135deg, #dc2626, #ef4444)";
        icon = "fa-circle-exclamation";
    } else if (type === "warning") {
        bgColor = "linear-gradient(135deg, #d97706, #f59e0b)";
        icon = "fa-triangle-exclamation";
    } else {
        bgColor = "linear-gradient(135deg, #2563eb, #3b82f6)";
        icon = "fa-info-circle";
    }
    toast.style.background = bgColor;

    toast.innerHTML = `
        <i class="fa-solid ${icon}" style="font-size: 16px;"></i>
        <div style="flex: 1; line-height: 1.4;">${message}</div>
        <button style="background: none; border: none; color: #fff; cursor: pointer; padding: 2px 4px; opacity: 0.8;" onclick="this.parentElement.remove()">
            <i class="fa-solid fa-xmark"></i>
        </button>
    `;

    container.appendChild(toast);
    requestAnimationFrame(() => {
        toast.style.opacity = "1";
        toast.style.transform = "translateX(0)";
    });

    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateX(30px)";
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// --- Domain API Services ---

const AuthAPI = {
    // 1. OTP Endpoints
    sendEmailOtp: (email) => apiFetch("/api/auth/otp/send-email", {
        method: "POST",
        body: { email }
    }),

    resendEmailOtp: (email) => apiFetch("/api/auth/otp/resend", {
        method: "POST",
        body: { email }
    }),

    verifyOtp: (identifier, otp) => apiFetch("/api/auth/otp/verify", {
        method: "POST",
        body: { identifier, otp }
    }),

    // 2. GPS Pinpoint Reverse Geocoder
    resolveLocation: (latitude, longitude, custom_location = null) => apiFetch("/api/auth/resolve-location", {
        method: "POST",
        body: { latitude, longitude, custom_location }
    }),

    // 3. Citizen Registration & Login
    registerUser: (payload) => apiFetch("/api/auth/user/register", {
        method: "POST",
        body: payload
    }),

    loginUser: (payload) => apiFetch("/api/auth/user/login", {
        method: "POST",
        body: payload
    }),

    // 4. Admin Registration & Login
    registerAdmin: (payload) => apiFetch("/api/auth/admin/register", {
        method: "POST",
        body: payload
    }),

    loginAdmin: (payload) => apiFetch("/api/auth/admin/login", {
        method: "POST",
        body: payload
    }),

    // 5. Profile
    getProfile: () => apiFetch("/api/auth/me"),
    getUserProfile: () => apiFetch("/api/auth/user/me"),
    getAdminProfile: () => apiFetch("/api/auth/admin/me"),

    // 6. Forgot & Reset Password
    forgotPassword: (email) => apiFetch("/api/auth/forgot-password", {
        method: "POST",
        body: { email }
    }),

    resendForgotPasswordOtp: (email) => apiFetch("/api/auth/forgot-password/resend", {
        method: "POST",
        body: { email }
    }),

    resetPassword: (payload) => apiFetch("/api/auth/reset-password", {
        method: "POST",
        body: payload
    }),
};

// Export to window
window.API_BASE_URL = API_BASE_URL;
window.getApiBaseUrl = getApiBaseUrl;
window.setApiBaseUrl = (url) => {
    if (url) {
        localStorage.setItem("weatherxpose-api-base", url.replace(/\/$/, ""));
    } else {
        localStorage.removeItem("weatherxpose-api-base");
    }
};
window.getAuthToken = getAuthToken;
window.setAuthToken = setAuthToken;
window.clearAuth = clearAuth;
window.getUserRole = getUserRole;
window.isLoggedIn = isLoggedIn;
window.logout = logout;
window.apiFetch = apiFetch;
window.apiUpload = apiUpload;
window.showNotice = showNotice;
window.AuthAPI = AuthAPI;
AuthAPI.logout = logout;

// Auto-inject universal styles for Logout Button
(function injectLogoutStyles() {
    if (document.getElementById("weatherxpose-logout-style")) return;
    const style = document.createElement("style");
    style.id = "weatherxpose-logout-style";
    style.textContent = `
        .logout-btn {
            display: inline-flex;
            align-items: center;
            gap: 7px;
            padding: 7px 14px;
            font-size: 12px;
            font-weight: 600;
            color: #f87171 !important;
            background: rgba(239, 68, 68, 0.12) !important;
            border: 1px solid rgba(239, 68, 68, 0.28) !important;
            border-radius: 8px;
            cursor: pointer;
            text-decoration: none;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            line-height: 1;
        }
        .logout-btn i {
            font-size: 12px;
            color: #f87171;
            transition: transform 0.2s ease;
        }
        .logout-btn:hover {
            background: rgba(239, 68, 68, 0.24) !important;
            border-color: rgba(239, 68, 68, 0.5) !important;
            color: #ffffff !important;
            box-shadow: 0 4px 12px rgba(239, 68, 68, 0.25);
            transform: translateY(-1px);
        }
        .logout-btn:hover i {
            color: #ffffff;
            transform: translateX(2px);
        }
        .logout-btn:active {
            transform: translateY(0);
        }
        .sidebar-logout-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 10px 14px;
            margin: 8px 14px;
            border-radius: 8px;
            color: #f87171 !important;
            background: rgba(239, 68, 68, 0.08);
            border: 1px solid rgba(239, 68, 68, 0.18);
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            text-decoration: none;
            transition: all 0.2s ease;
        }
        .sidebar-logout-item:hover {
            background: rgba(239, 68, 68, 0.2);
            border-color: rgba(239, 68, 68, 0.4);
            color: #fff !important;
        }
    `;
    if (document.head) {
        document.head.appendChild(style);
    } else {
        document.addEventListener("DOMContentLoaded", () => document.head.appendChild(style));
    }
})();

// Universal auto-binding for any Logout button across all pages
function bindLogoutButtons() {
    const targets = document.querySelectorAll("#logoutBtn, .logout-btn, [data-action='logout'], #sidebarLogoutBtn");
    targets.forEach(btn => {
        if (!btn.dataset.logoutBound) {
            btn.dataset.logoutBound = "true";
            btn.addEventListener("click", (e) => {
                e.preventDefault();
                logout();
            });
        }
    });
}
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bindLogoutButtons);
} else {
    bindLogoutButtons();
}

