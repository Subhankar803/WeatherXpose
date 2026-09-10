/* ================= ELEMENTS ================= */

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

const passwordToggle =
    document.getElementById("passwordToggle");

const loginBtn =
    document.getElementById("loginBtn");

const themeToggle =
    document.getElementById("themeToggle");

const forgotPassword =
    document.getElementById("forgotPassword");

const adminFields =
    document.getElementById("adminFields");

const adminRole =
    document.getElementById("adminRole");

const permissionLevel =
    document.getElementById("permissionLevel");


/* ================= CURRENT ROLE ================= */

let currentRole = "user";


/* ================= USER / ADMIN SWITCH ================= */

function setLoginRole(role) {

    currentRole = role;


    /* =================================================
       ADMIN LOGIN
       ================================================= */

    if (role === "admin") {

        /* Active tab */

        userTab.classList.remove("active");
        adminTab.classList.add("active");


        /* Heading */

        loginTitle.textContent =
            "Admin Login";

        loginSubtitle.textContent =
            "Sign in to access the Weather360 administration panel.";


        /* Role information */

        roleIcon.className =
            "fas fa-shield-halved";

        roleName.textContent =
            "Admin Account";

        roleDescription.textContent =
            "Review and manage weather reports";


        /* Show admin fields */

        adminFields.classList.add("show");


        /* Login button */

        loginBtn.innerHTML = `
            <i class="fas fa-shield-halved"></i>
            <span>Login as Admin</span>
        `;


        /* Load previously registered admin email */

        const savedAdminEmail =
            localStorage.getItem(
                "weather360-admin-email"
            );

        if (savedAdminEmail) {

            loginEmail.value =
                savedAdminEmail;

        }

    }


    /* =================================================
       USER LOGIN
       ================================================= */

    else {

        /* Active tab */

        adminTab.classList.remove("active");
        userTab.classList.add("active");


        /* Heading */

        loginTitle.textContent =
            "User Login";

        loginSubtitle.textContent =
            "Sign in to access your Weather360 reports.";


        /* Role information */

        roleIcon.className =
            "fas fa-user";

        roleName.textContent =
            "User Account";

        roleDescription.textContent =
            "Access your reports and submissions";


        /* Hide admin fields */

        adminFields.classList.remove("show");


        /* Login button */

        loginBtn.innerHTML = `
            <i class="fas fa-user"></i>
            <span>Login as User</span>
        `;


        /* Load previously registered user email */

        const savedUserEmail =
            localStorage.getItem(
                "weather360-user-email"
            );

        if (savedUserEmail) {

            loginEmail.value =
                savedUserEmail;

        }

    }

}


/* ================= TAB CLICK ================= */


/* User */

userTab.addEventListener("click", function () {

    setLoginRole("user");

});


/* Admin */

adminTab.addEventListener("click", function () {

    setLoginRole("admin");

});


/* ================= PASSWORD SHOW / HIDE ================= */

passwordToggle.addEventListener(
    "click",
    function () {

        if (loginPassword.type === "password") {

            loginPassword.type = "text";

            passwordToggle.innerHTML = `
                <i class="fas fa-eye-slash"></i>
            `;

        }

        else {

            loginPassword.type = "password";

            passwordToggle.innerHTML = `
                <i class="fas fa-eye"></i>
            `;

        }

    }
);


/* ================= FORGOT PASSWORD ================= */

forgotPassword.addEventListener(
    "click",
    function (event) {

        event.preventDefault();

        alert(
            "Password recovery will be available after backend integration."
        );

    }
);


/* ================= LOGIN ================= */

loginForm.addEventListener(
    "submit",
    function (event) {

        event.preventDefault();


        /* Get email and password */

        const email =
            loginEmail.value.trim();

        const password =
            loginPassword.value;


        /* Basic validation */

        if (!email || !password) {

            alert(
                "Please enter your email and password."
            );

            return;

        }


        /* =================================================
           ADMIN LOGIN
           ================================================= */

        if (currentRole === "admin") {

            const selectedRole =
                adminRole.value;

            const selectedPermission =
                permissionLevel.value;


            /* Save admin login information */

            localStorage.setItem(
                "weather360-admin-role",
                selectedRole
            );

            localStorage.setItem(
                "weather360-admin-permission",
                selectedPermission
            );

            localStorage.setItem(
                "weather360-admin-email",
                email
            );

        }


        /* =================================================
           USER LOGIN
           ================================================= */

        else {

            localStorage.setItem(
                "weather360-user-email",
                email
            );

        }


        /* Save login status */

localStorage.setItem(
    "weather360-login-status",
    "logged-in"
);

localStorage.setItem(
    "weather360-user-role",
    currentRole
);


/* Save logged-in user's name */

if (currentRole === "admin") {

    const adminName =
        localStorage.getItem("weather360-admin-name");

    localStorage.setItem(
        "weather360-user-name",
        adminName || "Admin"
    );

} else {

    const userName =
        localStorage.getItem("weather360-user-name");

    localStorage.setItem(
        "weather360-user-name",
        userName || "User"
    );

}
    

        /* Loading */

        loginBtn.disabled = true;

        loginBtn.innerHTML = `
            <i class="fas fa-spinner fa-spin"></i>
            <span>Signing In...</span>
        `;


        /* =================================================
           REDIRECT
           ================================================= */

        setTimeout(function () {

            /* ADMIN */

            if (currentRole === "admin") {

                window.location.href =
                    "admin-reports.html";

            }


            /* USER */

            else {

                window.location.href =
                    "user-reports.html";

            }

        }, 700);

    }
);


/* ================= THEME ================= */

function applyTheme() {

    const savedTheme =
        localStorage.getItem(
            "weather360-theme"
        );


    if (savedTheme === "light") {

        document.body.classList.add("light");

        themeToggle.innerHTML = `
            <i class="fas fa-sun"></i>
            <span>Light</span>
        `;

    }

    else {

        document.body.classList.remove("light");

        themeToggle.innerHTML = `
            <i class="fas fa-moon"></i>
            <span>Dark</span>
        `;

    }

}


themeToggle.addEventListener(
    "click",
    function () {

        document.body.classList.toggle("light");


        const isLight =
            document.body.classList.contains(
                "light"
            );


        localStorage.setItem(
            "weather360-theme",
            isLight ? "light" : "dark"
        );


        applyTheme();

    }
);


/* ================= INITIAL SETUP ================= */

/*
   Default login type = USER
*/

setLoginRole("user");

applyTheme();