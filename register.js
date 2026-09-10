/* ================= ELEMENTS ================= */

const userTab = document.getElementById("userTab");
const adminTab = document.getElementById("adminTab");

const userForm = document.getElementById("userForm");
const adminForm = document.getElementById("adminForm");

const themeToggle = document.getElementById("themeToggle");

const getLocationBtn = document.getElementById("getLocation");
const userLocation = document.getElementById("userLocation");

const userRegisterForm = document.getElementById("userRegisterForm");
const adminRegisterForm = document.getElementById("adminRegisterForm");

const userVerifyOtp = document.getElementById("userVerifyOtp");
const adminVerifyOtp = document.getElementById("adminVerifyOtp");

const userOtpMessage = document.getElementById("userOtpMessage");
const adminOtpMessage = document.getElementById("adminOtpMessage");


/* ================= ACCOUNT TYPE ================= */

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


/* ================= THEME ================= */

function applyTheme() {

    const savedTheme = localStorage.getItem("weather360-theme");

    if (savedTheme === "light") {

        document.body.classList.add("light");

        themeToggle.innerHTML = `
            <i class="fas fa-sun"></i>
            <span>Light</span>
        `;

    } else {

        document.body.classList.remove("light");

        themeToggle.innerHTML = `
            <i class="fas fa-moon"></i>
            <span>Dark</span>
        `;
    }
}


themeToggle.addEventListener("click", function () {

    document.body.classList.toggle("light");

    const isLight = document.body.classList.contains("light");

    localStorage.setItem(
        "weather360-theme",
        isLight ? "light" : "dark"
    );

    applyTheme();

});


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


/* ================= CURRENT LOCATION ================= */

getLocationBtn.addEventListener("click", function () {

    if (!navigator.geolocation) {

        alert("Geolocation is not supported by your browser.");
        return;

    }

    getLocationBtn.innerHTML = `
        <i class="fas fa-spinner fa-spin"></i>
        Loading
    `;

    navigator.geolocation.getCurrentPosition(

        function (position) {

            const latitude = position.coords.latitude;
            const longitude = position.coords.longitude;

            /*
             * For now we display coordinates.
             * Backend integration can convert these coordinates
             * into the actual city/location.
             */

            userLocation.value =
                `${latitude.toFixed(5)}, ${longitude.toFixed(5)}`;

            getLocationBtn.innerHTML = `
                <i class="fas fa-check"></i>
                Located
            `;

        },

        function () {

            alert(
                "Unable to access your current location. Please allow location permission."
            );

            getLocationBtn.innerHTML = `
                <i class="fas fa-crosshairs"></i>
                Current
            `;

        }

    );

});


/* ================= OTP DEMO ================= */

userVerifyOtp.addEventListener("click", function () {

    const otp = document.getElementById("userOtp").value.trim();

    if (otp.length !== 6) {

        userOtpMessage.textContent =
            "Please enter a valid 6-digit OTP.";

        userOtpMessage.style.color = "#fb7185";

        return;
    }

    userOtpMessage.textContent =
        "Email verified successfully.";

    userOtpMessage.style.color = "#34d399";

});


adminVerifyOtp.addEventListener("click", function () {

    const otp = document.getElementById("adminOtp").value.trim();

    if (otp.length !== 6) {

        adminOtpMessage.textContent =
            "Please enter a valid 6-digit OTP.";

        adminOtpMessage.style.color = "#fb7185";

        return;
    }

    adminOtpMessage.textContent =
        "Email verified successfully.";

    adminOtpMessage.style.color = "#34d399";

});


/* ================= USER REGISTRATION ================= */

userRegisterForm.addEventListener("submit", function (event) {

    event.preventDefault();

    const name = document.getElementById("userName").value.trim();
    const email = document.getElementById("userEmail").value.trim();

    const password =
        document.getElementById("userPassword").value;

    const confirmPassword =
        document.getElementById("userConfirmPassword").value;

    const otp =
        document.getElementById("userOtp").value.trim();

    const location =
        document.getElementById("userLocation").value.trim();


    if (password !== confirmPassword) {

        alert("Passwords do not match.");
        return;

    }


    if (otp.length !== 6) {

        alert("Please verify your email OTP.");
        return;

    }


    if (!location) {

        alert("Please provide your current location.");
        return;

    }


    /*
     * Temporary frontend registration.
     *
     * Backend integration will replace this section.
     */

    localStorage.setItem(
        "weather360-registration-role",
        "user"
    );

    localStorage.setItem(
        "weather360-user-email",
        email
    );

    localStorage.setItem(
        "weather360-user-name",
        name
    );


    alert("User registration successful!");

    /*
     * Later this will open the User Login page.
     */

    window.location.href = "login.html";

});


/* ================= ADMIN REGISTRATION ================= */

adminRegisterForm.addEventListener("submit", function (event) {

    event.preventDefault();

    const name = document.getElementById("adminName").value.trim();
    const email = document.getElementById("adminEmail").value.trim();

    const password =
        document.getElementById("adminPassword").value;

    const confirmPassword =
        document.getElementById("adminConfirmPassword").value;

    const authorizedCode =
        document.getElementById("authorizedCode").value.trim();

    const otp =
        document.getElementById("adminOtp").value.trim();

    const permission =
        document.getElementById("permissionLevel").value;


    if (password !== confirmPassword) {

        alert("Passwords do not match.");
        return;

    }


    if (!authorizedCode) {

        alert("Please enter the authorized code.");
        return;

    }


    if (otp.length !== 6) {

        alert("Please verify your email OTP.");
        return;

    }


    if (!permission) {

        alert("Please select a permission level.");
        return;

    }


    /*
     * Temporary frontend registration.
     *
     * Backend integration will replace this section.
     */

    localStorage.setItem(
        "weather360-registration-role",
        "admin"
    );

    localStorage.setItem(
        "weather360-admin-email",
        email
    );

    localStorage.setItem(
        "weather360-admin-name",
        name
    );

    localStorage.setItem(
        "weather360-admin-permission",
        permission
    );


    alert("Admin registration successful!");

    /*
     * Later this will open the Admin Login page.
     */

    window.location.href = "login.html";

});