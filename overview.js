/* =========================================================
   1. WEATHER INCIDENT DATA
========================================================= */

const incidentData = [

    {
        city: "Mumbai",
        state: "Maharashtra",
        lat: 19.0760,
        lng: 72.8777,
        event: "Heavy Rainfall",
        score: 92,
        status: "verified",
        reports: 5
    },

    {
        city: "Ahmedabad",
        state: "Gujarat",
        lat: 23.0225,
        lng: 72.5714,
        event: "Thunderstorm",
        score: 81,
        status: "verified",
        reports: 3
    },

    {
        city: "Jaipur",
        state: "Rajasthan",
        lat: 26.9124,
        lng: 75.7873,
        event: "Heatwave",
        score: 88,
        status: "verified",
        reports: 1
    },

    {
        city: "Delhi",
        state: "Delhi",
        lat: 28.6139,
        lng: 77.2090,
        event: "Fog",
        score: 63,
        status: "review",
        reports: 1
    },

    {
        city: "Lucknow",
        state: "Uttar Pradesh",
        lat: 26.8467,
        lng: 80.9462,
        event: "Heavy Rainfall",
        score: 78,
        status: "verified",
        reports: 5
    },

    {
        city: "Patna",
        state: "Bihar",
        lat: 25.5941,
        lng: 85.1376,
        event: "Flood",
        score: 55,
        status: "review",
        reports: 2
    },

    {
        city: "Kolkata",
        state: "West Bengal",
        lat: 22.5726,
        lng: 88.3639,
        event: "Heavy Rainfall",
        score: 94,
        status: "verified",
        reports: 5
    },

    {
        city: "Bhubaneswar",
        state: "Odisha",
        lat: 20.2961,
        lng: 85.8245,
        event: "Cyclone",
        score: 89,
        status: "verified",
        reports: 4
    },

    {
        city: "Guwahati",
        state: "Assam",
        lat: 26.1445,
        lng: 91.7362,
        event: "Flood",
        score: 48,
        status: "review",
        reports: 2
    },

    {
        city: "Chennai",
        state: "Tamil Nadu",
        lat: 13.0827,
        lng: 80.2707,
        event: "Heavy Rainfall",
        score: 91,
        status: "verified",
        reports: 5
    },

    {
        city: "Bengaluru",
        state: "Karnataka",
        lat: 12.9716,
        lng: 77.5946,
        event: "Thunderstorm",
        score: 73,
        status: "review",
        reports: 3
    },

    {
        city: "Hyderabad",
        state: "Telangana",
        lat: 17.3850,
        lng: 78.4867,
        event: "Thunderstorm",
        score: 84,
        status: "verified",
        reports: 3
    },

    {
        city: "Kochi",
        state: "Kerala",
        lat: 9.9312,
        lng: 76.2673,
        event: "Heavy Rainfall",
        score: 31,
        status: "suspicious",
        reports: 1
    },

    {
        city: "Srinagar",
        state: "Jammu & Kashmir",
        lat: 34.0837,
        lng: 74.7973,
        event: "Heavy Snowfall",
        score: 27,
        status: "suspicious",
        reports: 1
    },

    {
        city: "Nagpur",
        state: "Maharashtra",
        lat: 21.1458,
        lng: 79.0882,
        event: "Heatwave",
        score: 76,
        status: "verified",
        reports: 1
    }

];


/* =========================================================
   2. MAP
========================================================= */

const indiaMap = L.map("indiaMap", {

    zoomControl: true,

    minZoom: 4,

    maxZoom: 8,

    maxBounds: [
        [5, 67],
        [38, 100]
    ],

    maxBoundsViscosity: 1.0

});


indiaMap.setView(
    [22.5, 79],
    5
);


/* Map tiles */

L.tileLayer(
    "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    {
        attribution: "&copy; OpenStreetMap contributors",

        maxZoom: 19
    }
).addTo(indiaMap);


/* =========================================================
   3. MARKER COLORS
========================================================= */

const markerColors = {

    verified: "#10b981",

    review: "#f59e0b",

    suspicious: "#ef4444"

};


/* =========================================================
   4. MARKER ICON
========================================================= */

function createMarkerIcon(status, score) {

    const color =
        markerColors[status];


    return L.divIcon({

        className: "weather-marker",

        html: `

            <div style="
                width: 30px;
                height: 30px;
                background: ${color};
                border: 3px solid white;
                border-radius: 50%;
                box-shadow:
                    0 3px 10px rgba(0,0,0,0.25),
                    0 0 0 4px ${color}33;

                display:flex;
                align-items:center;
                justify-content:center;

                color:white;
                font-size:10px;
                font-weight:800;
            ">
                ${score}
            </div>

        `,

        iconSize: [30, 30],

        iconAnchor: [15, 15],

        popupAnchor: [0, -16]

    });

}


/* =========================================================
   5. ADD MARKERS
========================================================= */

incidentData.forEach((incident) => {


    let statusText;


    if (incident.status === "verified") {

        statusText = "VERIFIED";

    }
    else if (incident.status === "review") {

        statusText = "UNDER REVIEW";

    }
    else {

        statusText = "SUSPICIOUS";

    }


    const marker =
        L.marker(
            [incident.lat, incident.lng],
            {
                icon:
                    createMarkerIcon(
                        incident.status,
                        incident.score
                    )
            }
        ).addTo(indiaMap);


    marker.bindPopup(`

        <div style="
            min-width:210px;
            font-family:Inter,Arial,sans-serif;
        ">

            <div style="
                font-size:15px;
                font-weight:800;
                color:#0b1f3a;
                margin-bottom:5px;
            ">
                ${incident.event}
            </div>


            <div style="
                font-size:12px;
                color:#64748b;
                margin-bottom:11px;
            ">
                <i class="fa-solid fa-location-dot"></i>
                ${incident.city}, ${incident.state}
            </div>


            <div style="
                display:flex;
                justify-content:space-between;
                align-items:center;
                padding:9px 0;
                border-top:1px solid #e5e7eb;
            ">

                <span style="
                    font-size:11px;
                    color:#64748b;
                ">
                    Trust Score
                </span>


                <strong style="
                    font-size:16px;
                    color:${markerColors[incident.status]};
                ">
                    ${incident.score}/100
                </strong>

            </div>


            <div style="
                display:flex;
                justify-content:space-between;
                padding-top:4px;
                font-size:10px;
                font-weight:700;
                color:${markerColors[incident.status]};
            ">

                <span>
                    ${statusText}
                </span>

                <span>
                    ${incident.reports} Report(s)
                </span>

            </div>

        </div>

    `);

});


/* Fix map size */

setTimeout(() => {

    indiaMap.invalidateSize();

}, 300);


/* =========================================================
   6. THEME TOGGLE
========================================================= */

const themeToggle =
    document.getElementById(
        "themeToggle"
    );


function updateThemeIcon(isDark) {

    if (!themeToggle) return;


    const icon =
        themeToggle.querySelector("i");


    if (!icon) return;


    icon.className =
        isDark
            ? "fa-solid fa-sun"
            : "fa-solid fa-moon";

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


            updateThemeIcon(isDark);


            updateChartTheme();

        }
    );

}





/* =========================================================
   8. INCIDENT ACTIVITY CHART
========================================================= */

const chartCanvas =
    document.getElementById(
        "weatherActivityChart"
    );


let weatherChart = null;


if (chartCanvas) {


    const ctx =
        chartCanvas.getContext("2d");


    weatherChart =
        new Chart(
            ctx,
            {

                type: "line",


                data: {

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


                    datasets: [

                        {
                            label:
                                "Verified Reports",

                            data: [
                                3,
                                4,
                                2,
                                7,
                                12,
                                18,
                                14,
                                8
                            ],

                            borderColor:
                                "#10b981",

                            backgroundColor:
                                "rgba(16,185,129,0.12)",

                            borderWidth: 2,

                            pointRadius: 3,

                            pointHoverRadius: 5,

                            fill: true,

                            tension: 0.35
                        },


                        {
                            label:
                                "Review Queue",

                            data: [
                                1,
                                2,
                                1,
                                3,
                                5,
                                8,
                                6,
                                4
                            ],

                            borderColor:
                                "#f59e0b",

                            backgroundColor:
                                "rgba(245,158,11,0.04)",

                            borderWidth: 2,

                            borderDash: [4, 4],

                            pointRadius: 2,

                            pointHoverRadius: 4,

                            fill: false,

                            tension: 0.35
                        }

                    ]

                },


                options: {

                    responsive: true,

                    maintainAspectRatio: false,


                    interaction: {

                        intersect: false,

                        mode: "index"

                    },


                    plugins: {

                        legend: {

                            display: true,

                            position: "top",

                            align: "center",

                            labels: {

                                boxWidth: 11,

                                boxHeight: 7,

                                padding: 16,

                                font: {
                                    size: 11,
                                    weight: "600"
                                }

                            }

                        },


                        tooltip: {

                            backgroundColor:
                                "#0b1f3a",

                            titleFont: {
                                size: 12
                            },

                            bodyFont: {
                                size: 11
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
                                    size: 10
                                },

                                color: "#64748b"

                            }

                        },


                        y: {

                            beginAtZero: true,

                            max: 20,

                            ticks: {

                                stepSize: 4,

                                font: {
                                    size: 10
                                },

                                color: "#64748b"

                            },

                            grid: {

                                color:
                                    "rgba(100,116,139,0.12)"

                            }

                        }

                    }

                }

            }
        );

}


/* =========================================================
   9. CHART DARK MODE
========================================================= */

function updateChartTheme() {

    if (!weatherChart) return;


    const isDark =
        document.body.classList.contains(
            "dark-mode"
        );


    const textColor =
        isDark
            ? "#a8b9ce"
            : "#64748b";


    const gridColor =
        isDark
            ? "rgba(148,163,184,0.12)"
            : "rgba(100,116,139,0.12)";


    weatherChart.options.scales.x.ticks.color =
        textColor;


    weatherChart.options.scales.y.ticks.color =
        textColor;


    weatherChart.options.scales.y.grid.color =
        gridColor;


    weatherChart.options.plugins.legend.labels.color =
        textColor;


    weatherChart.update();

}


updateChartTheme();


/* =========================================================
   10. LOCATION WEATHER
========================================================= */

const locationInput =
    document.getElementById(
        "locationInput"
    );


const searchLocationBtn =
    document.getElementById(
        "searchLocationBtn"
    );


const weatherLocation =
    document.getElementById(
        "weatherLocation"
    );


const temperature =
    document.getElementById(
        "temperature"
    );


const weatherCondition =
    document.getElementById(
        "weatherCondition"
    );


const feelsLike =
    document.getElementById(
        "feelsLike"
    );


const humidity =
    document.getElementById(
        "humidity"
    );


const windSpeed =
    document.getElementById(
        "windSpeed"
    );


const rainfall =
    document.getElementById(
        "rainfall"
    );


const visibility =
    document.getElementById(
        "visibility"
    );


const weatherIcon =
    document.getElementById(
        "weatherIcon"
    );


const locationEvent =
    document.getElementById(
        "locationEvent"
    );


const locationReports =
    document.getElementById(
        "locationReports"
    );


const locationScore =
    document.getElementById(
        "locationScore"
    );


const locationStatus =
    document.getElementById(
        "locationStatus"
    );


/* =========================================================
   11. WEATHER CODE
========================================================= */

function getWeatherCondition(code) {

    if (code === 0)
        return "Clear Sky";


    if ([1, 2, 3].includes(code))
        return "Partly Cloudy";


    if ([45, 48].includes(code))
        return "Fog";


    if (
        [51, 53, 55, 56, 57].includes(code)
    )
        return "Drizzle";


    if (
        [61, 63, 65, 66, 67].includes(code)
    )
        return "Rain";


    if (
        [71, 73, 75, 77].includes(code)
    )
        return "Snow";


    if (
        [80, 81, 82].includes(code)
    )
        return "Rain Showers";


    if (
        [95, 96, 99].includes(code)
    )
        return "Thunderstorm";


    return "Weather Data Available";

}


/* =========================================================
   12. WEATHER ICON
========================================================= */

function getWeatherIcon(code) {

    if (code === 0)
        return "fa-solid fa-sun";


    if ([1, 2, 3].includes(code))
        return "fa-solid fa-cloud-sun";


    if ([45, 48].includes(code))
        return "fa-solid fa-smog";


    if (
        [51, 53, 55, 56, 57,
         61, 63, 65, 66, 67,
         80, 81, 82].includes(code)
    )
        return "fa-solid fa-cloud-rain";


    if (
        [71, 73, 75, 77].includes(code)
    )
        return "fa-solid fa-snowflake";


    if (
        [95, 96, 99].includes(code)
    )
        return "fa-solid fa-cloud-bolt";


    return "fa-solid fa-cloud";

}


/* =========================================================
   13. FIND INCIDENT
========================================================= */

function findIncident(cityName) {

    const city =
        cityName
            .toLowerCase()
            .trim();


    return incidentData.find(
        incident =>
            incident.city
                .toLowerCase()
                === city
    );

}


/* =========================================================
   14. SEARCH WEATHER
========================================================= */

async function searchWeather() {

    const query =
        locationInput.value.trim();


    if (!query) {

        alert(
            "Please enter a city or location."
        );

        return;

    }


    searchLocationBtn.disabled = true;


    searchLocationBtn.innerHTML = `
        <i class="fa-solid fa-spinner fa-spin"></i>
        Searching...
    `;


    try {

        /* -----------------------------------------
           GEOCODING
        ----------------------------------------- */

        const geoResponse =
            await fetch(
                `https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(query)}&count=1&language=en&format=json`
            );


        const geoData =
            await geoResponse.json();


        if (
            !geoData.results ||
            geoData.results.length === 0
        ) {

            throw new Error(
                "Location not found"
            );

        }


        const place =
            geoData.results[0];


        const latitude =
            place.latitude;


        const longitude =
            place.longitude;


        const cityName =
            place.name;


        const country =
            place.country || "India";


        /* -----------------------------------------
           WEATHER API
        ----------------------------------------- */

        const weatherResponse =
            await fetch(
                `https://api.open-meteo.com/v1/forecast?latitude=${latitude}&longitude=${longitude}&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m&hourly=visibility&timezone=auto`
            );


        const weatherData =
            await weatherResponse.json();


        const current =
            weatherData.current;


        /* -----------------------------------------
           UPDATE LOCATION
        ----------------------------------------- */

        weatherLocation.textContent =
            `${cityName}, ${country}`;


        /* -----------------------------------------
           TEMPERATURE
        ----------------------------------------- */

        temperature.textContent =
            Math.round(
                current.temperature_2m
            );


        feelsLike.textContent =
            Math.round(
                current.apparent_temperature
            );


        /* -----------------------------------------
           CONDITION
        ----------------------------------------- */

        weatherCondition.textContent =
            getWeatherCondition(
                current.weather_code
            );


        weatherIcon.className =
            getWeatherIcon(
                current.weather_code
            );


        /* -----------------------------------------
           STATS
        ----------------------------------------- */

        humidity.textContent =
            `${current.relative_humidity_2m}%`;


        windSpeed.textContent =
            `${Math.round(current.wind_speed_10m)} km/h`;


        rainfall.textContent =
            `${Number(current.precipitation || 0).toFixed(1)} mm`;


        let visibilityValue =
            "--";


        if (
            weatherData.hourly &&
            weatherData.hourly.visibility &&
            weatherData.hourly.visibility.length
        ) {

            visibilityValue =
                (
                    weatherData
                        .hourly
                        .visibility[0] / 1000
                ).toFixed(1);

        }


        visibility.textContent =
            `${visibilityValue} km`;


        /* -----------------------------------------
           INCIDENT INFORMATION
        ----------------------------------------- */

        const incident =
            findIncident(cityName);


        if (incident) {

            locationEvent.textContent =
                incident.event;


            locationReports.textContent =
                `${incident.reports}`;


            locationScore.textContent =
                `${incident.score}/100`;


            if (
                incident.status ===
                "verified"
            ) {

                locationStatus.textContent =
                    "Verified";

                locationStatus.style.color =
                    "#10b981";

            }
            else if (
                incident.status ===
                "review"
            ) {

                locationStatus.textContent =
                    "Under Review";

                locationStatus.style.color =
                    "#f59e0b";

            }
            else {

                locationStatus.textContent =
                    "Suspicious";

                locationStatus.style.color =
                    "#ef4444";

            }


            /* Center map on searched city */

            indiaMap.setView(
                [
                    incident.lat,
                    incident.lng
                ],
                6
            );

        }
        else {

            locationEvent.textContent =
                "No major incident reported";


            locationReports.textContent =
                "0";


            locationScore.textContent =
                "N/A";


            locationStatus.textContent =
                "No Alert";


            locationStatus.style.color =
                "#64748b";


            /* Center map on searched location */

            indiaMap.setView(
                [
                    latitude,
                    longitude
                ],
                6
            );

        }

    }
    catch (error) {

        console.error(error);


        alert(
            "Unable to fetch weather data. Please check the location name or try again."
        );

    }
    finally {

        searchLocationBtn.disabled = false;


        searchLocationBtn.innerHTML = `
            <i class="fa-solid fa-magnifying-glass"></i>
            Search
        `;

    }

}


/* Search button */

searchLocationBtn.addEventListener(
    "click",
    searchWeather
);


/* Enter key */

locationInput.addEventListener(
    "keydown",
    (event) => {

        if (
            event.key === "Enter"
        ) {

            searchWeather();

        }

    }
);


/* =========================================================
   15. DEFAULT LOCATION
========================================================= */

locationInput.value =
    "Kolkata";


searchWeather();


/* =========================================================
   16. NAVIGATION
========================================================= */

document
    .querySelectorAll(".nav-item")
    .forEach((item) => {

        item.addEventListener(
            "click",
            function () {

                const href =
                    this.getAttribute(
                        "href"
                    );


                if (
                    href &&
                    href !== "#"
                ) {

                    window.location.href =
                        href;

                }

            }
        );

    });


/* =========================================================
   17. CONSOLE
========================================================= */

console.log(
    "Weather360 Overview loaded successfully."
);

console.log(
    `Incident markers: ${incidentData.length}`
);
/* =========================================================
   SIDEBAR LIVE DATE / TIME
========================================================= */

function updateSidebarDateTime() {

    const el = document.getElementById("liveDateTime");

    if (!el) return;

    const now = new Date();

    el.textContent = now.toLocaleString("en-IN", {
        weekday: "short",
        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit"
    });
}

updateSidebarDateTime();

setInterval(updateSidebarDateTime, 1000);