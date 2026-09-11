/* =========================================================
   WEATHER360 - REGISTRATION CONTROLLER (API CONNECTED)
   ========================================================= */

// --- DOM Elements ---
const userTab = document.getElementById("userTab");
const adminTab = document.getElementById("adminTab");

const userForm = document.getElementById("userForm");
const adminForm = document.getElementById("adminForm");

const themeToggle = document.getElementById("themeToggle");

const getLocationBtn = document.getElementById("getLocation");
const userLocation = document.getElementById("userLocation");

const userRegisterForm = document.getElementById("userRegisterForm");
const adminRegisterForm = document.getElementById("adminRegisterForm");

const userSendOtpBtn = document.getElementById("userSendOtpBtn");
const userVerifyOtp = document.getElementById("userVerifyOtp");
const adminSendOtpBtn = document.getElementById("adminSendOtpBtn");
const adminVerifyOtp = document.getElementById("adminVerifyOtp");

const userOtpMessage = document.getElementById("userOtpMessage");
const adminOtpMessage = document.getElementById("adminOtpMessage");

// GPS cache
let resolvedLatitude = null;
let resolvedLongitude = null;

// OTP verification state tracking
let isUserOtpVerified = false;
let isAdminOtpVerified = false;
let userCooldownTimer = null;
let adminCooldownTimer = null;

/* ================= ACCOUNT TYPE SWITCHING ================= */

userTab.addEventListener("click", function () {
    userTab.classList.add("active");
    adminTab.classList.remove("active");
    userForm.classList.remove("hidden");
    adminForm.classList.add("hidden");
});

adminTab.addEventListener("click", function () {
    adminTab.classList.add("active");
    userTab.classList.remove("active");
    adminForm.classList.remove("hidden");
    userForm.classList.add("hidden");
});

/* ================= THEME TOGGLE ================= */

function applyTheme() {
    const savedTheme = localStorage.getItem("weather360-theme");
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
        localStorage.setItem("weather360-theme", isLight ? "light" : "dark");
        applyTheme();
    });
}
applyTheme();

/* ================= PASSWORD VISIBILITY ================= */

document.querySelectorAll(".password-toggle").forEach(function (button) {
    button.addEventListener("click", function () {
        const targetId = button.dataset.target;
        const input = document.getElementById(targetId);
        const icon = button.querySelector("i");

        if (input.type === "password") {
            input.type = "text";
            icon.classList.remove("fa-eye");
            icon.classList.add("fa-eye-slash");
        } else {
            input.type = "password";
            icon.classList.remove("fa-eye-slash");
            icon.classList.add("fa-eye");
        }
    });
});

/* ================= GPS LOCATION RESOLVER ================= */

if (getLocationBtn) {
    getLocationBtn.addEventListener("click", function () {
        if (!navigator.geolocation) {
            showNotice("Geolocation is not supported by your browser.", "warning");
            return;
        }

        getLocationBtn.disabled = true;
        getLocationBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Locating...';

        navigator.geolocation.getCurrentPosition(
            async function (position) {
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;
                resolvedLatitude = lat;
                resolvedLongitude = lon;

                try {
                    // Call backend OSM reverse geocoder
                    const geo = await AuthAPI.resolveLocation(lat, lon);
                    userLocation.value = geo.formatted_location || `${geo.city}, ${geo.state}`;
                    getLocationBtn.innerHTML = '<i class="fas fa-check"></i> Located';
                    showNotice(`Location resolved: ${userLocation.value}`, "success");
                } catch (err) {
                    console.warn("Backend reverse geocode fallback:", err);
                    userLocation.value = `${lat.toFixed(4)}, ${lon.toFixed(4)}`;
                    getLocationBtn.innerHTML = '<i class="fas fa-check"></i> Located';
                } finally {
                    getLocationBtn.disabled = false;
                }
            },
            function (err) {
                console.warn("Geolocation permission error:", err);
                getLocationBtn.disabled = false;
                getLocationBtn.innerHTML = '<i class="fas fa-crosshairs"></i> Current';
                showNotice("Location access denied. Please enter your city manually.", "warning");
            },
            { timeout: 10000, enableHighAccuracy: true }
        );
    });
}

/* ================= OTP COOLDOWN HELPER ================= */

function startOtpCooldown(buttonElement, durationSeconds = 30) {
    let remaining = durationSeconds;
    buttonElement.disabled = true;

    const originalHtml = buttonElement.innerHTML;
    const interval = setInterval(() => {
        buttonElement.innerHTML = `<i class="fas fa-clock"></i> ${remaining}s`;
        remaining--;

        if (remaining < 0) {
            clearInterval(interval);
            buttonElement.disabled = false;
            buttonElement.innerHTML = originalHtml;
        }
    }, 1000);

    return interval;
}

/* ================= USER OTP DISPATCH & VERIFY ================= */

if (userSendOtpBtn) {
    userSendOtpBtn.addEventListener("click", async function () {
        const email = document.getElementById("userEmail").value.trim().toLowerCase();
        if (!email || !email.includes("@")) {
            userOtpMessage.textContent = "Please enter a valid email address first.";
            userOtpMessage.style.color = "#fb7185";
            return;
        }

        userSendOtpBtn.disabled = true;
        userSendOtpBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';
        userOtpMessage.textContent = "Sending verification code...";
        userOtpMessage.style.color = "#94a3b8";

        try {
            const res = await AuthAPI.sendEmailOtp(email);
            userOtpMessage.textContent = `Verification code sent to ${email} (valid 10 mins).`;
            userOtpMessage.style.color = "#34d399";
            showNotice(`OTP dispatched to ${email}`, "success");
            userCooldownTimer = startOtpCooldown(userSendOtpBtn, res.cooldown_seconds || 30);
        } catch (err) {
            userSendOtpBtn.disabled = false;
            userSendOtpBtn.innerHTML = '<i class="fas fa-paper-plane"></i> Send OTP';
            userOtpMessage.textContent = err.message || "Failed to send OTP.";
            userOtpMessage.style.color = "#fb7185";
            showNotice(err.message || "Failed to send OTP", "error");
        }
    });
}

if (userVerifyOtp) {
    userVerifyOtp.addEventListener("click", async function () {
        const email = document.getElementById("userEmail").value.trim().toLowerCase();
        const otp = document.getElementById("userOtp").value.trim();

        if (!email || !email.includes("@")) {
            userOtpMessage.textContent = "Please enter your email.";
            userOtpMessage.style.color = "#fb7185";
            return;
        }

        if (otp.length !== 6) {
            userOtpMessage.textContent = "Please enter a valid 6-digit OTP.";
            userOtpMessage.style.color = "#fb7185";
            return;
        }

        userVerifyOtp.disabled = true;
        userVerifyOtp.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Checking...';

        try {
            await AuthAPI.verifyOtp(email, otp);
            isUserOtpVerified = true;
            userOtpMessage.textContent = "Email OTP verified successfully!";
            userOtpMessage.style.color = "#34d399";
            userVerifyOtp.innerHTML = '<i class="fas fa-check-circle"></i> Verified';
            userVerifyOtp.style.background = "#065f46";
            userVerifyOtp.style.borderColor = "#10b981";
            userVerifyOtp.style.color = "#ffffff";
            showNotice("Email verified successfully!", "success");
        } catch (err) {
            isUserOtpVerified = false;
            userVerifyOtp.disabled = false;
            userVerifyOtp.innerHTML = '<i class="fas fa-check"></i> Verify';
            userOtpMessage.textContent = err.message || "Invalid or expired OTP.";
            userOtpMessage.style.color = "#fb7185";
            showNotice(err.message || "Invalid OTP code", "error");
        }
    });
}

/* ================= ADMIN OTP DISPATCH & VERIFY ================= */

if (adminSendOtpBtn) {
    adminSendOtpBtn.addEventListener("click", async function () {
        const email = document.getElementById("adminEmail").value.trim().toLowerCase();
        if (!email || !email.includes("@")) {
            adminOtpMessage.textContent = "Please enter a valid email address first.";
            adminOtpMessage.style.color = "#fb7185";
            return;
        }

        adminSendOtpBtn.disabled = true;
        adminSendOtpBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';
        adminOtpMessage.textContent = "Sending verification code...";
        adminOtpMessage.style.color = "#94a3b8";

        try {
            const res = await AuthAPI.sendEmailOtp(email);
            adminOtpMessage.textContent = `Verification code sent to ${email} (valid 10 mins).`;
            adminOtpMessage.style.color = "#34d399";
            showNotice(`OTP dispatched to ${email}`, "success");
            adminCooldownTimer = startOtpCooldown(adminSendOtpBtn, res.cooldown_seconds || 30);
        } catch (err) {
            adminSendOtpBtn.disabled = false;
            adminSendOtpBtn.innerHTML = '<i class="fas fa-paper-plane"></i> Send OTP';
            adminOtpMessage.textContent = err.message || "Failed to send OTP.";
            adminOtpMessage.style.color = "#fb7185";
            showNotice(err.message || "Failed to send OTP", "error");
        }
    });
}

if (adminVerifyOtp) {
    adminVerifyOtp.addEventListener("click", async function () {
        const email = document.getElementById("adminEmail").value.trim().toLowerCase();
        const otp = document.getElementById("adminOtp").value.trim();

        if (!email || !email.includes("@")) {
            adminOtpMessage.textContent = "Please enter your email.";
            adminOtpMessage.style.color = "#fb7185";
            return;
        }

        if (otp.length !== 6) {
            adminOtpMessage.textContent = "Please enter a valid 6-digit OTP.";
            adminOtpMessage.style.color = "#fb7185";
            return;
        }

        adminVerifyOtp.disabled = true;
        adminVerifyOtp.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Checking...';

        try {
            await AuthAPI.verifyOtp(email, otp);
            isAdminOtpVerified = true;
            adminOtpMessage.textContent = "Email OTP verified successfully!";
            adminOtpMessage.style.color = "#34d399";
            adminVerifyOtp.innerHTML = '<i class="fas fa-check-circle"></i> Verified';
            adminVerifyOtp.style.background = "#065f46";
            adminVerifyOtp.style.borderColor = "#10b981";
            adminVerifyOtp.style.color = "#ffffff";
            showNotice("Email verified successfully!", "success");
        } catch (err) {
            isAdminOtpVerified = false;
            adminVerifyOtp.disabled = false;
            adminVerifyOtp.innerHTML = '<i class="fas fa-check"></i> Verify';
            adminOtpMessage.textContent = err.message || "Invalid or expired OTP.";
            adminOtpMessage.style.color = "#fb7185";
            showNotice(err.message || "Invalid OTP code", "error");
        }
    });
}

/* ================= USER REGISTRATION SUBMIT ================= */

userRegisterForm.addEventListener("submit", async function (event) {
    event.preventDefault();

    const name = document.getElementById("userName").value.trim();
    const email = document.getElementById("userEmail").value.trim().toLowerCase();
    const password = document.getElementById("userPassword").value;
    const confirmPassword = document.getElementById("userConfirmPassword").value;
    const otp = document.getElementById("userOtp").value.trim();
    const location = userLocation.value.trim();

    if (!name || !email || !password) {
        showNotice("Please fill in all required fields.", "warning");
        return;
    }

    if (password.length < 6) {
        showNotice("Password must be at least 6 characters long.", "warning");
        return;
    }

    if (password !== confirmPassword) {
        showNotice("Passwords do not match.", "error");
        return;
    }

    if (!otp || otp.length !== 6) {
        showNotice("Please enter the 6-digit email OTP.", "warning");
        return;
    }

    const submitBtn = userRegisterForm.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating Account...';

    try {
        const payload = {
            name,
            email,
            password,
            email_otp: otp,
            location: location || "India",
            latitude: resolvedLatitude,
            longitude: resolvedLongitude,
        };

        const result = await AuthAPI.registerUser(payload);

        // Store JWT token and session details
        setAuthToken(result.access_token);
        localStorage.setItem("weather360-login-status", "logged-in");
        localStorage.setItem("weather360-user-role", "user");
        localStorage.setItem("weather360-user-email", email);
        localStorage.setItem("weather360-user-name", name);
        localStorage.setItem("weather360-location", location || "India");

        showNotice("User account registered successfully!", "success");

        submitBtn.innerHTML = '<i class="fas fa-check"></i> Registered!';
        setTimeout(() => {
            window.location.href = "user-reports.html";
        }, 1000);
    } catch (err) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fas fa-user-plus"></i> Create User Account';
        showNotice(err.message || "Registration failed. Please try again.", "error");
    }
});

/* ================= ADMIN REGISTRATION SUBMIT ================= */

adminRegisterForm.addEventListener("submit", async function (event) {
    event.preventDefault();

    const name = document.getElementById("adminName").value.trim();
    const email = document.getElementById("adminEmail").value.trim().toLowerCase();
    const password = document.getElementById("adminPassword").value;
    const confirmPassword = document.getElementById("adminConfirmPassword").value;
    const authorizedCode = document.getElementById("authorizedCode").value.trim();
    const otp = document.getElementById("adminOtp").value.trim();
    const permissionRaw = document.getElementById("permissionLevel").value;

    if (!name || !email || !password || !authorizedCode) {
        showNotice("Please fill in all required fields.", "warning");
        return;
    }

    if (password.length < 6) {
        showNotice("Password must be at least 6 characters long.", "warning");
        return;
    }

    if (password !== confirmPassword) {
        showNotice("Passwords do not match.", "error");
        return;
    }

    if (!otp || otp.length !== 6) {
        showNotice("Please enter the 6-digit email OTP.", "warning");
        return;
    }

    if (!permissionRaw) {
        showNotice("Please select an administrator permission level.", "warning");
        return;
    }

    // Normalize role string to backend enum ("Reviewer" or "Super Admin")
    const permission = permissionRaw === "super-admin" ? "Super Admin" : "Reviewer";

    const submitBtn = adminRegisterForm.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating Admin Account...';

    try {
        const payload = {
            name,
            email,
            password,
            admin_auth_code: authorizedCode,
            email_otp: otp,
            permission_level: permission,
        };

        const result = await AuthAPI.registerAdmin(payload);

        // Store JWT token and session details
        setAuthToken(result.access_token);
        localStorage.setItem("weather360-login-status", "logged-in");
        localStorage.setItem("weather360-user-role", "admin");
        localStorage.setItem("weather360-admin-email", email);
        localStorage.setItem("weather360-admin-name", name);
        localStorage.setItem("weather360-admin-role", permissionRaw);
        localStorage.setItem("weather360-admin-permission", permission);

        showNotice("Admin account registered successfully!", "success");

        submitBtn.innerHTML = '<i class="fas fa-check"></i> Registered!';
        setTimeout(() => {
            window.location.href = "admin-reports.html";
        }, 1000);
    } catch (err) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fas fa-shield-halved"></i> Create Admin Account';
        showNotice(err.message || "Admin registration failed. Please verify the authorized code.", "error");
    }
});