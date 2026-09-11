/* =========================================================
   WEATHER360 - OVERVIEW
   ========================================================= */


/* =========================================================
   1. USER LOCATION
   ========================================================= */

const DEFAULT_LOCATION = "Kolkata";

let userLocation =
    localStorage.getItem("userLocation") ||
    localStorage.getItem("weather360-location") ||
    DEFAULT_LOCATION;


/*
    Keep location clean.
    Example:
    "Kolkata, West Bengal" -> "Kolkata"
*/

function getCityName(location) {

    if (!location) return DEFAULT_LOCATION;

    return location
        .split(",")[0]
        .trim();

}


userLocation = getCityName(userLocation);


/* =========================================================
   2. LOCATION DATA
   ========================================================= */

const locationData = {

    Kolkata: {
        lat: 22.5726,
        lng: 88.3639,
        temperature: 31,
        feelsLike: 34,
        humidity: 78,
        wind: 14,
        rainfall: 2.4,
        visibility: 8,
        condition: "Partly Cloudy",
        icon: "fa-cloud-sun"
    },

    Mumbai: {
        lat: 19.0760,
        lng: 72.8777,
        temperature: 29,
        feelsLike: 32,
        humidity: 84,
        wind: 18,
        rainfall: 6.8,
        visibility: 7,
        condition: "Light Rain",
        icon: "fa-cloud-rain"
    },

    Delhi: {
        lat: 28.6139,
        lng: 77.2090,
        temperature: 35,
        feelsLike: 38,
        humidity: 52,
        wind: 11,
        rainfall: 0,
        visibility: 6,
        condition: "Sunny",
        icon: "fa-sun"
    },

    Bengaluru: {
        lat: 12.9716,
        lng: 77.5946,
        temperature: 25,
        feelsLike: 26,
        humidity: 68,
        wind: 12,
        rainfall: 1.2,
        visibility: 9,
        condition: "Cloudy",
        icon: "fa-cloud"
    },

    Hyderabad: {
        lat: 17.3850,
        lng: 78.4867,
        temperature: 30,
        feelsLike: 32,
        humidity: 61,
        wind: 15,
        rainfall: 0.8,
        visibility: 8,
        condition: "Partly Cloudy",
        icon: "fa-cloud-sun"
    },

    Chennai: {
        lat: 13.0827,
        lng: 80.2707,
        temperature: 32,
        feelsLike: 37,
        humidity: 76,
        wind: 19,
        rainfall: 3.1,
        visibility: 7,
        condition: "Cloudy",
        icon: "fa-cloud"
    },

    Jaipur: {
        lat: 26.9124,
        lng: 75.7873,
        temperature: 37,
        feelsLike: 40,
        humidity: 38,
        wind: 13,
        rainfall: 0,
        visibility: 9,
        condition: "Sunny",
        icon: "fa-sun"
    },

    Lucknow: {
        lat: 26.8467,
        lng: 80.9462,
        temperature: 33,
        feelsLike: 36,
        humidity: 58,
        wind: 10,
        rainfall: 1.5,
        visibility: 8,
        condition: "Cloudy",
        icon: "fa-cloud"
    },

    Patna: {
        lat: 25.5941,
        lng: 85.1376,
        temperature: 32,
        feelsLike: 35,
        humidity: 70,
        wind: 9,
        rainfall: 4.2,
        visibility: 7,
        condition: "Light Rain",
        icon: "fa-cloud-rain"
    },

    Guwahati: {
        lat: 26.1445,
        lng: 91.7362,
        temperature: 28,
        feelsLike: 31,
        humidity: 82,
        wind: 8,
        rainfall: 7.4,
        visibility: 6,
        condition: "Rainy",
        icon: "fa-cloud-showers-heavy"
    },

    Bhubaneswar: {
        lat: 20.2961,
        lng: 85.8245,
        temperature: 30,
        feelsLike: 34,
        humidity: 79,
        wind: 17,
        rainfall: 5.5,
        visibility: 8,
        condition: "Light Rain",
        icon: "fa-cloud-rain"
    },

    Kochi: {
        lat: 9.9312,
        lng: 76.2673,
        temperature: 28,
        feelsLike: 32,
        humidity: 86,
        wind: 15,
        rainfall: 8.2,
        visibility: 6,
        condition: "Rainy",
        icon: "fa-cloud-showers-heavy"
    },

    Srinagar: {
        lat: 34.0837,
        lng: 74.7973,
        temperature: 18,
        feelsLike: 17,
        humidity: 64,
        wind: 7,
        rainfall: 0.6,
        visibility: 9,
        condition: "Cloudy",
        icon: "fa-cloud"
    }

};


/* Fallback for unknown city */

const weather =
    locationData[userLocation] ||
    locationData.Kolkata;


/* =========================================================
   3. LOCATION TEXT
   ========================================================= */

const currentWeatherLocation =
    document.getElementById(
        "currentWeatherLocation"
    );

const weatherActivityLocation =
    document.getElementById(
        "weatherActivityLocation"
    );

const mapLocationText =
    document.getElementById(
        "mapLocationText"
    );


if (currentWeatherLocation) {

    currentWeatherLocation.textContent =
        userLocation;

}


if (weatherActivityLocation) {

    weatherActivityLocation.textContent =
        userLocation;

}


if (mapLocationText) {

    mapLocationText.textContent =
        `Weather incidents around ${userLocation}`;

}


/* =========================================================
   4. CURRENT WEATHER
   ========================================================= */

const currentTemperature =
    document.getElementById(
        "currentTemperature"
    );

const currentCondition =
    document.getElementById(
        "currentCondition"
    );

const feelsLike =
    document.getElementById(
        "feelsLike"
    );

const currentHumidity =
    document.getElementById(
        "currentHumidity"
    );

const currentWind =
    document.getElementById(
        "currentWind"
    );

const currentRainfall =
    document.getElementById(
        "currentRainfall"
    );

const currentVisibility =
    document.getElementById(
        "currentVisibility"
    );

const currentWeatherIcon =
    document.getElementById(
        "currentWeatherIcon"
    );


if (currentTemperature) {

    currentTemperature.textContent =
        weather.temperature + "°";

}


if (currentCondition) {

    currentCondition.textContent =
        weather.condition;

}


if (feelsLike) {

    feelsLike.textContent =
        `Feels like ${weather.feelsLike}°C`;

}


if (currentHumidity) {

    currentHumidity.textContent =
        weather.humidity + "%";

}


if (currentWind) {

    currentWind.textContent =
        weather.wind + " km/h";

}


if (currentRainfall) {

    currentRainfall.textContent =
        weather.rainfall + " mm";

}


if (currentVisibility) {

    currentVisibility.textContent =
        weather.visibility + " km";

}


if (currentWeatherIcon) {

    currentWeatherIcon.className =
        `fa-solid ${weather.icon}`;

}


const weatherUpdated =
    document.getElementById(
        "weatherUpdated"
    );


if (weatherUpdated) {

    weatherUpdated.textContent =
        "just now";

}


/* =========================================================
   5. MAP INITIALIZATION
   ========================================================= */

const indiaMap =
    L.map("indiaMap", {

        zoomControl: true,

        minZoom: 4,

        maxZoom: 8,

        maxBounds: [
            [5, 67],
            [38, 100]
        ],

        maxBoundsViscosity: 1.0

    });


/* Map tiles */

L.tileLayer(

    "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",

    {

        attribution:
            "&copy; OpenStreetMap contributors",

        maxZoom: 19

    }

).addTo(indiaMap);


/*
    Center map on user's location.
*/

indiaMap.setView(
    [weather.lat, weather.lng],
    7
);


/* =========================================================
   6. INCIDENT DATA
   ========================================================= */

const incidentData = [

    {
        city: "Mumbai",
        state: "Maharashtra",
        lat: 19.0760,
        lng: 72.8777,
        event: "Heavy Rainfall",
        score: 92,
        status: "verified"
    },

    {
        city: "Ahmedabad",
        state: "Gujarat",
        lat: 23.0225,
        lng: 72.5714,
        event: "Thunderstorm",
        score: 81,
        status: "verified"
    },

    {
        city: "Jaipur",
        state: "Rajasthan",
        lat: 26.9124,
        lng: 75.7873,
        event: "Heatwave",
        score: 88,
        status: "verified"
    },

    {
        city: "Delhi",
        state: "Delhi",
        lat: 28.6139,
        lng: 77.2090,
        event: "Fog",
        score: 63,
        status: "review"
    },

    {
        city: "Lucknow",
        state: "Uttar Pradesh",
        lat: 26.8467,
        lng: 80.9462,
        event: "Heavy Rainfall",
        score: 78,
        status: "verified"
    },

    {
        city: "Patna",
        state: "Bihar",
        lat: 25.5941,
        lng: 85.1376,
        event: "Flood",
        score: 55,
        status: "review"
    },

    {
        city: "Kolkata",
        state: "West Bengal",
        lat: 22.5726,
        lng: 88.3639,
        event: "Heavy Rainfall",
        score: 94,
        status: "verified"
    },

    {
        city: "Bhubaneswar",
        state: "Odisha",
        lat: 20.2961,
        lng: 85.8245,
        event: "Cyclone",
        score: 89,
        status: "verified"
    },

    {
        city: "Guwahati",
        state: "Assam",
        lat: 26.1445,
        lng: 91.7362,
        event: "Flood",
        score: 48,
        status: "review"
    },

    {
        city: "Chennai",
        state: "Tamil Nadu",
        lat: 13.0827,
        lng: 80.2707,
        event: "Heavy Rainfall",
        score: 91,
        status: "verified"
    },

    {
        city: "Bengaluru",
        state: "Karnataka",
        lat: 12.9716,
        lng: 77.5946,
        event: "Thunderstorm",
        score: 73,
        status: "review"
    },

    {
        city: "Hyderabad",
        state: "Telangana",
        lat: 17.3850,
        lng: 78.4867,
        event: "Thunderstorm",
        score: 84,
        status: "verified"
    },

    {
        city: "Kochi",
        state: "Kerala",
        lat: 9.9312,
        lng: 76.2673,
        event: "Heavy Rainfall",
        score: 31,
        status: "suspicious"
    },

    {
        city: "Srinagar",
        state: "Jammu & Kashmir",
        lat: 34.0837,
        lng: 74.7973,
        event: "Heavy Snowfall",
        score: 27,
        status: "suspicious"
    },

    {
        city: "Nagpur",
        state: "Maharashtra",
        lat: 21.1458,
        lng: 79.0882,
        event: "Heatwave",
        score: 76,
        status: "verified"
    }

];


/* =========================================================
   7. MARKER COLORS
   ========================================================= */

const markerColors = {

    verified: "#16a34a",

    review: "#eab308",

    suspicious: "#dc2626"

};


/* =========================================================
   8. MARKER ICON
   ========================================================= */

function createMarkerIcon(status) {

    const color =
        markerColors[status];

    return L.divIcon({

        className:
            "weather-marker",

        html: `
            <div style="
                width:15px;
                height:15px;
                background:${color};
                border:3px solid white;
                border-radius:50%;
                box-shadow:
                    0 2px 8px rgba(0,0,0,0.35),
                    0 0 0 4px ${color}33;
            "></div>
        `,

        iconSize: [15, 15],

        iconAnchor: [7.5, 7.5],

        popupAnchor: [0, -8]

    });

}


/* =========================================================
   9. ADD INCIDENT MARKERS
   ========================================================= */

incidentData.forEach(
    (incident) => {

        const marker =
            L.marker(

                [
                    incident.lat,
                    incident.lng
                ],

                {
                    icon:
                        createMarkerIcon(
                            incident.status
                        )
                }

            ).addTo(indiaMap);


        let statusText;


        if (
            incident.status ===
            "verified"
        ) {

            statusText =
                "VERIFIED";

        }

        else if (
            incident.status ===
            "review"
        ) {

            statusText =
                "UNDER REVIEW";

        }

        else {

            statusText =
                "SUSPICIOUS";

        }


        marker.bindPopup(`

            <div style="
                min-width:190px;
                font-family:Inter,Arial,sans-serif;
            ">

                <div style="
                    font-size:14px;
                    font-weight:700;
                    color:#0b1f3a;
                    margin-bottom:5px;
                ">
                    ${incident.event}
                </div>


                <div style="
                    font-size:11px;
                    color:#64748b;
                    margin-bottom:10px;
                ">

                    <i class="fa-solid fa-location-dot"></i>

                    ${incident.city},
                    ${incident.state}

                </div>


                <div style="
                    display:flex;
                    justify-content:space-between;
                    align-items:center;
                    padding:8px 0;
                    border-top:1px solid #e5e7eb;
                ">

                    <span style="
                        font-size:10px;
                        color:#64748b;
                    ">
                        Trust Score
                    </span>


                    <strong style="
                        font-size:15px;
                        color:${markerColors[incident.status]};
                    ">
                        ${incident.score}
                    </strong>

                </div>


                <div style="
                    font-size:9px;
                    font-weight:700;
                    color:${markerColors[incident.status]};
                    margin-top:3px;
                ">
                    ${statusText}
                </div>

            </div>

        `);

    }
);


/* =========================================================
   10. HIGHLIGHT USER LOCATION
   ========================================================= */

const userLocationMarker =
    L.marker(

        [
            weather.lat,
            weather.lng
        ],

        {

            icon: L.divIcon({

                className:
                    "user-location-marker",

                html: `
                    <div style="
                        width:18px;
                        height:18px;
                        background:#2563eb;
                        border:4px solid white;
                        border-radius:50%;
                        box-shadow:
                            0 0 0 6px rgba(37,99,235,0.18),
                            0 3px 10px rgba(0,0,0,0.3);
                    "></div>
                `,

                iconSize: [18,18],

                iconAnchor: [9,9]

            })

        }

    ).addTo(indiaMap);


userLocationMarker.bindPopup(`

    <strong>
        Your Location
    </strong>

    <br>

    ${userLocation}

    <br>

    <small>
        Current weather is shown below.
    </small>

`);


/* =========================================================
   11. MAP RESIZE
   ========================================================= */

setTimeout(() => {

    indiaMap.invalidateSize();

}, 300);


/* =========================================================
   12. LIVE DATE & TIME
   ========================================================= */

const liveDateTime =
    document.getElementById(
        "liveDateTime"
    );


function updateDateTime() {

    if (!liveDateTime) return;


    const now =
        new Date();


    const date =
        now.toLocaleDateString(
            "en-IN",
            {
                day: "2-digit",
                month: "short",
                year: "numeric"
            }
        );


    const time =
        now.toLocaleTimeString(
            "en-IN",
            {
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit"
            }
        );


    liveDateTime.innerHTML = `

        ${date}

        <span>
            ${time}
        </span>

    `;

}


updateDateTime();


setInterval(
    updateDateTime,
    1000
);


/* =========================================================
   13. THEME TOGGLE
   ========================================================= */

const themeToggle =
    document.getElementById(
        "themeToggle"
    );


function updateThemeIcon(
    isDark
) {

    if (!themeToggle) return;


    const icon =
        themeToggle.querySelector(
            "i"
        );


    if (!icon) return;


    icon.className =
        isDark
            ? "fa-solid fa-sun"
            : "fa-solid fa-moon";

}


if (themeToggle) {

    themeToggle.addEventListener(
        "click",
        () => {

            document.body.classList.toggle(
                "dark-mode"
            );


            const isDark =
                document.body.classList.contains(
                    "dark-mode"
                );


            localStorage.setItem(
                "weather360-theme",
                isDark
                    ? "dark"
                    : "light"
            );


            updateThemeIcon(
                isDark
            );


            updateChartTheme(
                isDark
            );

        }
    );

}


const savedTheme =
    localStorage.getItem(
        "weather360-theme"
    );


if (savedTheme === "dark") {

    document.body.classList.add(
        "dark-mode"
    );

    updateThemeIcon(true);

}

else {

    updateThemeIcon(false);

}


/* =========================================================
   14. WEATHER ACTIVITY CHART
   ========================================================= */

const chartCanvas =
    document.getElementById(
        "weatherActivityChart"
    );


let weatherChart = null;


const chartData = {

    "24h": {

        labels: [
            "00:00",
            "03:00",
            "06:00",
            "09:00",
            "12:00",
            "15:00",
            "18:00",
            "21:00"
        ],

        data: [
            420,
            610,
            530,
            890,
            1250,
            1090,
            1480,
            1320
        ]

    },

    "7d": {

        labels: [
            "Mon",
            "Tue",
            "Wed",
            "Thu",
            "Fri",
            "Sat",
            "Sun"
        ],

        data: [
            3200,
            4100,
            3700,
            5200,
            6100,
            5700,
            6800
        ]

    }

};


if (chartCanvas) {

    const ctx =
        chartCanvas.getContext(
            "2d"
        );


    weatherChart =
        new Chart(

            ctx,

            {

                type: "line",


                data: {

                    labels:
                        chartData["24h"]
                            .labels,

                    datasets: [

                        {

                            label:
                                `${userLocation} Weather Events`,

                            data:
                                chartData["24h"]
                                    .data,

                            borderColor:
                                "#2563eb",

                            backgroundColor:
                                "rgba(37,99,235,0.10)",

                            borderWidth: 2,

                            pointRadius: 3,

                            pointHoverRadius: 5,

                            fill: true,

                            tension: 0.4

                        }

                    ]

                },


                options: {

                    responsive: true,

                    maintainAspectRatio:
                        false,

                    interaction: {

                        intersect: false,

                        mode: "index"

                    },


                    plugins: {

                        legend: {

                            display: false

                        },


                        tooltip: {

                            backgroundColor:
                                "#0b1f3a",

                            titleFont: {
                                size: 11
                            },

                            bodyFont: {
                                size: 10
                            },

                            padding: 10,

                            cornerRadius: 7

                        }

                    },


                    scales: {

                        x: {

                            grid: {
                                display: false
                            },

                            ticks: {

                                font: {
                                    size: 9
                                },

                                color:
                                    "#64748b"

                            }

                        },


                        y: {

                            beginAtZero: true,

                            grid: {

                                color:
                                    "rgba(100,116,139,0.10)"

                            },

                            ticks: {

                                font: {
                                    size: 9
                                },

                                color:
                                    "#64748b"

                            }

                        }

                    }

                }

            }

        );

}


/* =========================================================
   15. CHART RANGE
   ========================================================= */

const chartButtons =
    document.querySelectorAll(
        ".chart-range"
    );


chartButtons.forEach(
    (button) => {

        button.addEventListener(
            "click",
            () => {

                chartButtons.forEach(
                    (btn) => {

                        btn.classList.remove(
                            "active"
                        );

                    }
                );


                button.classList.add(
                    "active"
                );


                if (!weatherChart)
                    return;


                const range =
                    button.dataset.range;


                const selected =
                    chartData[range] ||
                    chartData["24h"];


                weatherChart.data.labels =
                    selected.labels;


                weatherChart.data.datasets[0]
                    .data =
                    selected.data;


                weatherChart.data.datasets[0]
                    .label =
                    `${userLocation} Weather Events`;


                weatherChart.update();

            }
        );

    }
);


/* =========================================================
   16. UPDATE CHART THEME
   ========================================================= */

function updateChartTheme(
    isDark
) {

    if (!weatherChart)
        return;


    weatherChart.options
        .scales.x.ticks.color =
        isDark
            ? "#8fa1b7"
            : "#64748b";


    weatherChart.options
        .scales.y.ticks.color =
        isDark
            ? "#8fa1b7"
            : "#64748b";


    weatherChart.options
        .scales.y.grid.color =
        isDark
            ? "rgba(148,163,184,0.12)"
            : "rgba(100,116,139,0.10)";


    weatherChart.update();

}


/* =========================================================
   17. MAP FILTER
   ========================================================= */

const mapFilterBtn =
    document.querySelector(
        ".map-filter-btn"
    );


if (mapFilterBtn) {

    mapFilterBtn.addEventListener(
        "click",
        () => {

            alert(
                "Map filters: Verified, Under Review, Suspicious"
            );

        }
    );

}


/* =========================================================
   18. NAVIGATION
   ========================================================= */

const navItems =
    document.querySelectorAll(
        ".nav-item"
    );


navItems.forEach(
    (item) => {

        item.addEventListener(
            "click",
            function (event) {

                const href =
                    this.getAttribute(
                        "href"
                    );


                if (
                    !href ||
                    href === "#"
                ) {

                    event.preventDefault();

                }

            }
        );

    }
);


/* =========================================================
   19. CONSOLE STATUS
   ========================================================= */

console.log(
    "Weather360 Overview loaded successfully."
);

console.log(
    `User location: ${userLocation}`
);

console.log(
    `Live incident markers: ${incidentData.length}`
);
/* =========================================================
   USER ROLE ACCESS
========================================================= */

const loggedInRole =
    localStorage.getItem("weather360-user-role");

const userReportsNav =
    document.querySelector('a[href="user-reports.html"]');

const adminReportsNav =
    document.querySelector('a[href="admin-reports.html"]');


/* ================= ADMIN BLOCK ================= */

if (loggedInRole === "admin") {

    if (userReportsNav) {
        userReportsNav.style.display = "none";
    }

    if (adminReportsNav) {
        adminReportsNav.style.display = "flex";
    }

    /* Admin should not stay on User Reports */

    window.location.href = "admin-reports.html";

}


/* ================= USER ================= */

else if (loggedInRole === "user") {

    if (userReportsNav) {
        userReportsNav.style.display = "flex";
    }

    if (adminReportsNav) {
        adminReportsNav.style.display = "none";
    }

}
/* =========================================================
   ROLE BASED USER NAME + SIDEBAR
========================================================= */


const displayName =
    loggedInRole === "admin"
        ? (localStorage.getItem("weather360-admin-name") || "Admin")
        : (localStorage.getItem("weather360-user-name") || "User");


/* ================= SIDEBAR ================= */

const sidebarUserName =
    document.getElementById("sidebarUserName");

const sidebarUserRole =
    document.getElementById("sidebarUserRole");

const sidebarAvatar =
    document.getElementById("sidebarAvatar");


if (sidebarUserName) {
    sidebarUserName.textContent = displayName;
}

if (sidebarUserRole) {
    sidebarUserRole.textContent =
        loggedInRole === "admin"
            ? "Administrator"
            : "Member";
}

if (sidebarAvatar) {

    sidebarAvatar.textContent =
        displayName
            .split(" ")
            .map(word => word[0])
            .join("")
            .substring(0, 2)
            .toUpperCase();

}


/* ================= TOP HEADER ================= */

const headerUserName =
    document.getElementById("headerUserName");

const headerUserRole =
    document.getElementById("headerUserRole");

const headerUserAvatar =
    document.getElementById("headerUserAvatar");


if (headerUserName) {
    headerUserName.textContent = displayName;
}

if (headerUserRole) {
    headerUserRole.textContent =
        loggedInRole === "admin"
            ? "Administrator"
            : "Member";
}

if (headerUserAvatar) {

    headerUserAvatar.textContent =
        displayName
            .split(" ")
            .map(word => word[0])
            .join("")
            .substring(0, 2)
            .toUpperCase();

}