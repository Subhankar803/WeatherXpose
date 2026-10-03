/* =========================================================
   WEATHER XPOSE - LOGIN CONTROLLER (API CONNECTED)
   ========================================================= */

// --- DOM Elements ---
const userTab = document.getElementById("userTab");
const adminTab = document.getElementById("adminTab");

const loginTitle = document.getElementById("loginTitle");
const loginSubtitle = document.getElementById("loginSubtitle");

const roleIcon = document.getElementById("roleIcon");
const roleName = document.getElementById("roleName");
const roleDescription = document.getElementById("roleDescription");

const loginForm = document.getElementById("loginForm");
const loginEmail = document.getElementById("loginEmail");
const loginPassword = document.getElementById("loginPassword");
const passwordToggle = document.getElementById("passwordToggle");
const loginBtn = document.getElementById("loginBtn");
const rememberMe = document.getElementById("rememberMe");

const themeToggle = document.getElementById("themeToggle");
const forgotPassword = document.getElementById("forgotPassword");

const adminFields = document.getElementById("adminFields");
const adminRole = document.getElementById("adminRole");
const permissionLevel = document.getElementById("permissionLevel");

// Forgot Password Modal Elements
const forgotPasswordModal = document.getElementById("forgotPasswordModal");
const closeForgotModal = document.getElementById("closeForgotModal");
const forgotPasswordForm = document.getElementById("forgotPasswordForm");
const forgotEmail = document.getElementById("forgotEmail");
const sendForgotOtpBtn = document.getElementById("sendForgotOtpBtn");
const forgotOtp = document.getElementById("forgotOtp");
const forgotNewPassword = document.getElementById("forgotNewPassword");
const forgotConfirmPassword = document.getElementById("forgotConfirmPassword");
const forgotStatusMsg = document.getElementById("forgotStatusMsg");
const resetPasswordBtn = document.getElementById("resetPasswordBtn");

/* ================= CURRENT ROLE ================= */
let currentRole = "user";

/* ================= USER / ADMIN SWITCH ================= */

function setLoginRole(role) {
    currentRole = role;

    if (role === "admin") {
        userTab.classList.remove("active");
        adminTab.classList.add("active");

        loginTitle.textContent = "Admin Login";
        loginSubtitle.textContent = "Sign in to access the Weather Xpose administration panel.";

        roleIcon.className = "fas fa-shield-halved";
        roleName.textContent = "Admin Account";
        roleDescription.textContent = "Review and manage weather reports";

        adminFields.classList.add("show");

        loginBtn.innerHTML = `
            <i class="fas fa-shield-halved"></i>
            <span>Login as Admin</span>
        `;

        const savedAdminEmail = localStorage.getItem("weatherxpose-admin-email");
        if (savedAdminEmail) {
            loginEmail.value = savedAdminEmail;
        }
    } else {
        adminTab.classList.remove("active");
        userTab.classList.add("active");

        loginTitle.textContent = "User Login";
        loginSubtitle.textContent = "Sign in to access your Weather Xpose reports.";

        roleIcon.className = "fas fa-user";
        roleName.textContent = "User Account";
        roleDescription.textContent = "Access your reports and submissions";

        adminFields.classList.remove("show");

        loginBtn.innerHTML = `
            <i class="fas fa-user"></i>
            <span>Login as User</span>
        `;

        const savedUserEmail = localStorage.getItem("weatherxpose-user-email");
        if (savedUserEmail) {
            loginEmail.value = savedUserEmail;
        }
    }
}

userTab.addEventListener("click", () => setLoginRole("user"));
adminTab.addEventListener("click", () => setLoginRole("admin"));

// Sync adminRole select with permissionLevel select
if (adminRole && permissionLevel) {
    adminRole.addEventListener("change", () => {
        permissionLevel.value = adminRole.value;
    });
    permissionLevel.addEventListener("change", () => {
        adminRole.value = permissionLevel.value;
    });
}

/* ================= PASSWORD SHOW / HIDE ================= */

passwordToggle.addEventListener("click", function () {
    if (loginPassword.type === "password") {
        loginPassword.type = "text";
        passwordToggle.innerHTML = '<i class="fas fa-eye-slash"></i>';
    } else {
        loginPassword.type = "password";
        passwordToggle.innerHTML = '<i class="fas fa-eye"></i>';
    }
});

/* ================= LOGIN FORM SUBMISSION ================= */

loginForm.addEventListener("submit", async function (event) {
    event.preventDefault();

    const email = loginEmail.value.trim().toLowerCase();
    const password = loginPassword.value;

    if (!email || !password) {
        showNotice("Please enter your email and password.", "warning");
        return;
    }

    loginBtn.disabled = true;
    loginBtn.innerHTML = `
        <i class="fas fa-spinner fa-spin"></i>
        <span>Signing In...</span>
    `;

    try {
        if (currentRole === "admin") {
            // Selected role/permission
            const selectedRaw = (adminRole && adminRole.value) || (permissionLevel && permissionLevel.value) || "reviewer";
            const selectedRole = selectedRaw === "super-admin" ? "Super Admin" : "Reviewer";

            const result = await AuthAPI.loginAdmin({
                email,
                password,
                role: selectedRole,
            });

            // Store JWT access token & admin details
            setAuthToken(result.access_token);
            localStorage.setItem("weatherxpose-login-status", "logged-in");
            localStorage.setItem("weatherxpose-user-role", "admin");
            localStorage.setItem("weatherxpose-admin-email", email);
            localStorage.setItem("weatherxpose-admin-role", selectedRaw);
            localStorage.setItem("weatherxpose-admin-permission", result.account_info?.permission_level || selectedRole);
            localStorage.setItem("weatherxpose-user-name", result.account_info?.name || "Admin");
            localStorage.setItem("weatherxpose-admin-name", result.account_info?.name || "Admin");

            showNotice(`Welcome back, ${result.account_info?.name || 'Administrator'}!`, "success");

            loginBtn.innerHTML = '<i class="fas fa-check"></i><span>Redirecting...</span>';
            setTimeout(() => {
                window.location.href = "admin-reports.html";
            }, 600);
        } else {
            const result = await AuthAPI.loginUser({
                email,
                password,
            });

            // Store JWT access token & user details
            setAuthToken(result.access_token);
            localStorage.setItem("weatherxpose-login-status", "logged-in");
            localStorage.setItem("weatherxpose-user-role", "user");
            localStorage.setItem("weatherxpose-user-email", email);
            localStorage.setItem("weatherxpose-user-name", result.account_info?.name || "User");
            if (result.account_info?.location) {
                localStorage.setItem("weatherxpose-location", result.account_info.location);
            }

            showNotice(`Welcome back, ${result.account_info?.name || 'Citizen'}!`, "success");

            loginBtn.innerHTML = '<i class="fas fa-check"></i><span>Redirecting...</span>';
            setTimeout(() => {
                window.location.href = "user-reports.html";
            }, 600);
        }
    } catch (err) {
        loginBtn.disabled = false;
        loginBtn.innerHTML = currentRole === "admin"
            ? '<i class="fas fa-shield-halved"></i><span>Login as Admin</span>'
            : '<i class="fas fa-user"></i><span>Login as User</span>';

        showNotice(err.message || "Invalid credentials. Please try again.", "error");
    }
});

/* ================= FORGOT PASSWORD FLOW ================= */

if (forgotPassword) {
    forgotPassword.addEventListener("click", function (event) {
        event.preventDefault();
        if (loginEmail.value) {
            forgotEmail.value = loginEmail.value.trim();
        }
        forgotPasswordModal.classList.add("show");
        forgotStatusMsg.textContent = "";
    });
}

if (closeForgotModal) {
    closeForgotModal.addEventListener("click", function () {
        forgotPasswordModal.classList.remove("show");
    });
}

// Close modal when clicking on overlay background
if (forgotPasswordModal) {
    forgotPasswordModal.addEventListener("click", function (e) {
        if (e.target === forgotPasswordModal) {
            forgotPasswordModal.classList.remove("show");
        }
    });
}

if (sendForgotOtpBtn) {
    sendForgotOtpBtn.addEventListener("click", async function () {
        const email = forgotEmail.value.trim().toLowerCase();
        if (!email || !email.includes("@")) {
            forgotStatusMsg.textContent = "Please enter your registered email address.";
            forgotStatusMsg.style.color = "#fb7185";
            return;
        }

        sendForgotOtpBtn.disabled = true;
        sendForgotOtpBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';
        forgotStatusMsg.textContent = "Checking account and sending reset code...";
        forgotStatusMsg.style.color = "#94a3b8";

        try {
            const res = await AuthAPI.forgotPassword(email);
            forgotStatusMsg.textContent = `Reset OTP code sent to ${email} (valid 10 mins).`;
            forgotStatusMsg.style.color = "#34d399";
            showNotice("Password reset code sent to email!", "success");

            // Cooldown timer
            let cd = res.cooldown_seconds || 30;
            const timer = setInterval(() => {
                sendForgotOtpBtn.innerHTML = `<i class="fas fa-clock"></i> ${cd}s`;
                cd--;
                if (cd < 0) {
                    clearInterval(timer);
                    sendForgotOtpBtn.disabled = false;
                    sendForgotOtpBtn.innerHTML = '<i class="fas fa-paper-plane"></i> Send OTP';
                }
            }, 1000);
        } catch (err) {
            sendForgotOtpBtn.disabled = false;
            sendForgotOtpBtn.innerHTML = '<i class="fas fa-paper-plane"></i> Send OTP';
            forgotStatusMsg.textContent = err.message || "Failed to dispatch reset code.";
            forgotStatusMsg.style.color = "#fb7185";
            showNotice(err.message || "Account not found", "error");
        }
    });
}

if (forgotPasswordForm) {
    forgotPasswordForm.addEventListener("submit", async function (event) {
        event.preventDefault();

        const email = forgotEmail.value.trim().toLowerCase();
        const otp = forgotOtp.value.trim();
        const newPassword = forgotNewPassword.value;
        const confirmPassword = forgotConfirmPassword.value;

        if (!email || !otp || !newPassword) {
            forgotStatusMsg.textContent = "Please complete all fields.";
            forgotStatusMsg.style.color = "#fb7185";
            return;
        }

        if (otp.length !== 6) {
            forgotStatusMsg.textContent = "Please enter the 6-digit OTP.";
            forgotStatusMsg.style.color = "#fb7185";
            return;
        }

        if (newPassword.length < 6) {
            forgotStatusMsg.textContent = "New password must be at least 6 characters.";
            forgotStatusMsg.style.color = "#fb7185";
            return;
        }

        if (newPassword !== confirmPassword) {
            forgotStatusMsg.textContent = "Passwords do not match.";
            forgotStatusMsg.style.color = "#fb7185";
            return;
        }

        resetPasswordBtn.disabled = true;
        resetPasswordBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Resetting...';

        try {
            const res = await AuthAPI.resetPassword({
                email,
                otp,
                new_password: newPassword,
            });

            forgotStatusMsg.textContent = "Password updated successfully! You can now log in.";
            forgotStatusMsg.style.color = "#34d399";
            showNotice("Password successfully updated! Please log in.", "success");

            // Pre-fill email into login form and close modal
            loginEmail.value = email;
            loginPassword.value = "";

            setTimeout(() => {
                forgotPasswordModal.classList.remove("show");
                resetPasswordBtn.disabled = false;
                resetPasswordBtn.innerHTML = '<i class="fas fa-check-double"></i><span>Reset Password</span>';
            }, 1500);
        } catch (err) {
            resetPasswordBtn.disabled = false;
            resetPasswordBtn.innerHTML = '<i class="fas fa-check-double"></i><span>Reset Password</span>';
            forgotStatusMsg.textContent = err.message || "Failed to reset password.";
            forgotStatusMsg.style.color = "#fb7185";
            showNotice(err.message || "Failed to reset password", "error");
        }
    });
}

/* ================= THEME ================= */

function applyTheme() {
    const savedTheme = localStorage.getItem("weatherxpose-theme");

    if (savedTheme === "light") {
        document.body.classList.add("light");
        if (themeToggle) {
            themeToggle.innerHTML = '<i class="fas fa-sun"></i><span>Light</span>';
        }
    } else {
        document.body.classList.remove("light");
        if (themeToggle) {
            themeToggle.innerHTML = '<i class="fas fa-moon"></i><span>Dark</span>';
        }
    }
}

if (themeToggle) {
    themeToggle.addEventListener("click", function () {
        document.body.classList.toggle("light");
        const isLight = document.body.classList.contains("light");
        localStorage.setItem("weatherxpose-theme", isLight ? "light" : "dark");
        applyTheme();
    });
}

/* ================= INITIAL SETUP ================= */
setLoginRole("user");
applyTheme();