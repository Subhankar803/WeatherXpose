/* =========================================================
   WEATHER360 HOME PAGE
========================================================= */


/* =========================================================
   THEME TOGGLE
========================================================= */

const themeToggle =
    document.getElementById("themeToggle");

const savedTheme =
    localStorage.getItem("weather360-theme");


if (savedTheme === "dark") {

    document.body.classList.add("dark");

    themeToggle.innerHTML =
        '<i class="fas fa-sun"></i>';

}


/* Toggle */

themeToggle.addEventListener("click", function () {

    document.body.classList.toggle("dark");

    const darkMode =
        document.body.classList.contains("dark");


    localStorage.setItem(
        "weather360-theme",
        darkMode ? "dark" : "light"
    );


    if (darkMode) {

        themeToggle.innerHTML =
            '<i class="fas fa-sun"></i>';

    } else {

        themeToggle.innerHTML =
            '<i class="fas fa-moon"></i>';

    }

});



/* =========================================================
   NAVIGATION ACTIVE STATE
========================================================= */

const navLinks =
    document.querySelectorAll(".main-nav a");


navLinks.forEach(function (link) {

    link.addEventListener("click", function () {

        navLinks.forEach(function (item) {

            item.classList.remove("active");

        });


        this.classList.add("active");

    });

});



/* =========================================================
   ACTIVE NAVIGATION WHILE SCROLLING
========================================================= */

const sections =
    document.querySelectorAll("section[id]");


window.addEventListener("scroll", function () {

    let currentSection = "";


    sections.forEach(function (section) {

        const sectionTop =
            section.offsetTop - 130;


        if (window.scrollY >= sectionTop) {

            currentSection =
                section.getAttribute("id");

        }

    });


    navLinks.forEach(function (link) {

        link.classList.remove("active");

        const href =
            link.getAttribute("href");


        if (href === "#" + currentSection) {

            link.classList.add("active");

        }

    });

});



/* =========================================================
   SIMPLE CARD REVEAL ANIMATION
========================================================= */

const revealElements =
    document.querySelectorAll(
        ".feature-card, .event-card, .role-card"
    );


const revealObserver =
    new IntersectionObserver(
        function (entries) {

            entries.forEach(function (entry) {

                if (entry.isIntersecting) {

                    entry.target.classList.add("visible");

                    revealObserver.unobserve(
                        entry.target
                    );

                }

            });

        },
        {
            threshold: 0.12
        }
    );


revealElements.forEach(function (element) {

    element.style.opacity = "0";

    element.style.transform =
        "translateY(20px)";

    element.style.transition =
        "opacity .5s ease, transform .5s ease";

    revealObserver.observe(element);

});


/* =========================================================
   ADD VISIBLE STATE
========================================================= */

const style =
    document.createElement("style");

style.innerHTML = `

    .feature-card.visible,
    .event-card.visible,
    .role-card.visible {

        opacity: 1 !important;

        transform: translateY(0) !important;

    }

`;

document.head.appendChild(style);