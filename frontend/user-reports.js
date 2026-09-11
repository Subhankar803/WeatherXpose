/* =========================================================
   WEATHER360 - USER REPORTS CONTROLLER (API CONNECTED)
   ========================================================= */

// --- 1. USER LOCATION & AUTH RESOLUTION ---
const DEFAULT_LOCATION = "Kolkata";
let userLocation = localStorage.getItem("weather360-location") || localStorage.getItem("userLocation") || DEFAULT_LOCATION;

function getCleanCityName(loc) {
    if (!loc) return DEFAULT_LOCATION;
    return loc.split(",")[0].trim();
}
userLocation = getCleanCityName(userLocation);

// --- 2. DOM ELEMENTS ---
const currentWeatherLocation = document.getElementById("currentWeatherLocation");
const weatherActivityLocation = document.getElementById("weatherActivityLocation");
const mapLocationText = document.getElementById("mapLocationText");
const currentTemperature = document.getElementById("currentTemperature");
const currentCondition = document.getElementById("currentCondition");
const feelsLike = document.getElementById("feelsLike");
const currentHumidity = document.getElementById("currentHumidity");
const currentWind = document.getElementById("currentWind");
const currentRainfall = document.getElementById("currentRainfall");
const currentVisibility = document.getElementById("visibility") || document.getElementById("currentVisibility");
const currentWeatherIcon = document.getElementById("currentWeatherIcon");
const weatherUpdated = document.getElementById("weatherUpdated");
const liveDateTime = document.getElementById("liveDateTime");
const themeToggle = document.getElementById("themeToggle");

const sidebarUserName = document.getElementById("sidebarUserName");
const sidebarUserRole = document.getElementById("sidebarUserRole");
const sidebarAvatar = document.getElementById("sidebarAvatar");
const headerUserName = document.getElementById("headerUserName");
const headerUserRole = document.getElementById("headerUserRole");
const headerUserAvatar = document.getElementById("headerUserAvatar");
const userReportsNav = document.querySelector('a[href="user-reports.html"]');
const adminReportsNav = document.querySelector('a[href="admin-reports.html"]');

/* =========================================================
   3. ROLE ACCESS ENFORCEMENT
   ========================================================= */

const loggedInRole = localStorage.getItem("weather360-user-role");
if (loggedInRole === "admin") {
    // If admin enters user portal, make admin nav available and redirect
    if (adminReportsNav) adminReportsNav.style.display = "flex";
    if (userReportsNav) userReportsNav.style.display = "none";
    window.location.href = "admin-reports.html";
} else {
    if (adminReportsNav) adminReportsNav.style.display = "none";
    if (userReportsNav) userReportsNav.style.display = "flex";
}

/* =========================================================
   4. USER PROFILE & TRUST ACCOUNTING
   ========================================================= */

async function loadUserProfile() {
    try {
        const token = getAuthToken();
        if (token) {
            const profile = await apiFetch("/api/auth/user/me");
            const name = profile.name || "Citizen User";
            const role = `Citizen (${profile.trust_status || 'GREY'} List)`;

            if (sidebarUserName) sidebarUserName.textContent = name;
            if (sidebarUserRole) sidebarUserRole.textContent = role;
            if (headerUserName) headerUserName.textContent = name;
            if (headerUserRole) headerUserRole.textContent = role;

            const initials = name.split(" ").map(w => w[0]).join("").substring(0, 2).toUpperCase();
            if (sidebarAvatar) sidebarAvatar.textContent = initials;
            if (headerUserAvatar) headerUserAvatar.textContent = initials;

            if (profile.location) {
                userLocation = getCleanCityName(profile.location);
            }
        } else {
            const savedName = localStorage.getItem("weather360-user-name") || "Citizen User";
            if (sidebarUserName) sidebarUserName.textContent = savedName;
            if (headerUserName) headerUserName.textContent = savedName;
        }
    } catch (err) {
        console.warn("Could not fetch user profile:", err);
    }
}

/* =========================================================
   5. LIVE DATE & TIME
   ========================================================= */

function updateDateTime() {
    if (!liveDateTime) return;
    const now = new Date();
    const date = now.toLocaleDateString("en-IN", {
        day: "2-digit",
        month: "short",
        year: "numeric"
    });
    const time = now.toLocaleTimeString("en-IN", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit"
    });
    liveDateTime.innerHTML = `${date} <span>${time}</span>`;
}
updateDateTime();
setInterval(updateDateTime, 1000);

/* =========================================================
   6. THEME TOGGLE
   ========================================================= */

function updateThemeIcon(isDark) {
    if (!themeToggle) return;
    const icon = themeToggle.querySelector("i");
    if (!icon) return;
    icon.className = isDark ? "fa-solid fa-sun" : "fa-solid fa-moon";
}

const savedTheme = localStorage.getItem("weather360-theme");
if (savedTheme === "dark") {
    document.body.classList.add("dark-mode");
    updateThemeIcon(true);
} else {
    updateThemeIcon(false);
}

if (themeToggle) {
    themeToggle.addEventListener("click", () => {
        document.body.classList.toggle("dark-mode");
        const isDark = document.body.classList.contains("dark-mode");
        localStorage.setItem("weather360-theme", isDark ? "dark" : "light");
        updateThemeIcon(isDark);
        updateChartTheme(isDark);
    });
}

/* =========================================================
   7. MAP INITIALIZATION & INCIDENTS
   ========================================================= */

const markerColors = {
    verified: "#10b981",
    review: "#f59e0b",
    suspicious: "#ef4444"
};

const indiaMap = L.map("indiaMap", {
    zoomControl: true,
    minZoom: 4,
    maxZoom: 9
}).setView([22.5, 79], 5);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap contributors",
    maxZoom: 19
}).addTo(indiaMap);

let mapMarkers = [];

function createCustomMarker(status, score) {
    const color = markerColors[status] || "#10b981";
    return L.divIcon({
        className: "weather-marker",
        html: `
            <div style="
                width: 28px;
                height: 28px;
                background: ${color};
                border: 2px solid white;
                border-radius: 50%;
                box-shadow: 0 2px 8px rgba(0,0,0,0.3);
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 10px;
                font-weight: 800;
            ">
                ${Math.round(score || 0)}
            </div>
        `,
        iconSize: [28, 28],
        iconAnchor: [14, 14]
    });
}

async function loadMapFeed() {
    try {
        const res = await apiFetch("/api/map/active-incidents");
        const features = res.features || [];

        mapMarkers.forEach(m => indiaMap.removeLayer(m));
        mapMarkers = [];

        features.forEach(f => {
            const props = f.properties || {};
            const coords = f.geometry?.coordinates || [];
            const lng = coords[0];
            const lat = coords[1];
            if (!lat || !lng) return;

            const score = Number(props.verification_score) || 0;
            let status = "verified";
            if (props.verification_status === "Underprocess" || (score >= 27 && score <= 60)) {
                status = "review";
            } else if (props.verification_status === "Fake" || score < 27) {
                status = "suspicious";
            }

            const marker = L.marker([lat, lng], {
                icon: createCustomMarker(status, score)
            }).addTo(indiaMap);

            const cState = (props.state && props.state.toLowerCase() !== "india") ? props.state : "";
            const displayLoc = cState ? `${props.city}, ${cState}` : (props.city || "Incident Location");

            marker.bindPopup(`
                <strong>${props.event_type || 'Weather Event'}</strong><br>
                ${displayLoc}<br>
                <small>Trust Score: <strong>${Math.round(score)}/100</strong> (${status.toUpperCase()})</small><br>
                <span style="font-size: 10px; color: #64748b;">${props.report || ''}</span>
            `);

            mapMarkers.push(marker);
        });
    } catch (err) {
        console.warn("Could not load map incidents:", err);
    }
}

/* =========================================================
   8. WEATHER ACTIVITY CHART
   ========================================================= */

const chartCanvas = document.getElementById("weatherActivityChart");
let weatherChart = null;

const chartData = {
    "24h": {
        labels: ["00:00", "03:00", "06:00", "09:00", "12:00", "15:00", "18:00", "21:00"],
        data: [420, 610, 530, 890, 1250, 1090, 1480, 1320]
    },
    "7d": {
        labels: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        data: [3200, 4100, 3700, 5200, 6100, 5700, 6800]
    }
};

if (chartCanvas) {
    const ctx = chartCanvas.getContext("2d");
    weatherChart = new Chart(ctx, {
        type: "line",
        data: {
            labels: chartData["24h"].labels,
            datasets: [{
                label: `${userLocation} Weather Events`,
                data: chartData["24h"].data,
                borderColor: "#2563eb",
                backgroundColor: "rgba(37,99,235,0.10)",
                borderWidth: 2,
                pointRadius: 3,
                pointHoverRadius: 5,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: "index"
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: "#0b1f3a",
                    titleFont: { size: 11 },
                    bodyFont: { size: 10 },
                    padding: 10,
                    cornerRadius: 7
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { font: { size: 9 }, color: "#64748b" }
                },
                y: {
                    beginAtZero: true,
                    grid: { color: "rgba(100,116,139,0.10)" },
                    ticks: { font: { size: 9 }, color: "#64748b" }
                }
            }
        }
    });
}

const chartButtons = document.querySelectorAll(".chart-range");
chartButtons.forEach((button) => {
    button.addEventListener("click", () => {
        chartButtons.forEach((btn) => btn.classList.remove("active"));
        button.classList.add("active");

        if (!weatherChart) return;
        const range = button.dataset.range;
        const selected = chartData[range] || chartData["24h"];
        weatherChart.data.labels = selected.labels;
        weatherChart.data.datasets[0].data = selected.data;
        weatherChart.data.datasets[0].label = `${userLocation} Weather Events`;
        weatherChart.update();
    });
});

function updateChartTheme(isDark) {
    if (!weatherChart) return;
    const color = isDark ? "#8fa1b7" : "#64748b";
    const grid = isDark ? "rgba(148,163,184,0.12)" : "rgba(100,116,139,0.10)";
    weatherChart.options.scales.x.ticks.color = color;
    weatherChart.options.scales.y.ticks.color = color;
    weatherChart.options.scales.y.grid.color = grid;
    weatherChart.update();
}

/* =========================================================
   9. LOAD CURRENT LOCATION WEATHER TELEMETRY
   ========================================================= */

function getWeatherIconClass(code) {
    if (code === 0) return "fa-solid fa-sun";
    if ([1, 2, 3].includes(code)) return "fa-solid fa-cloud-sun";
    if ([45, 48].includes(code)) return "fa-solid fa-smog";
    if ([51, 53, 55, 61, 63, 65, 80, 81, 82].includes(code)) return "fa-solid fa-cloud-rain";
    if ([71, 73, 75].includes(code)) return "fa-solid fa-snowflake";
    if ([95, 96, 99].includes(code)) return "fa-solid fa-cloud-bolt";
    return "fa-solid fa-cloud";
}

async function loadUserCityWeather() {
    if (currentWeatherLocation) currentWeatherLocation.textContent = userLocation;
    if (weatherActivityLocation) weatherActivityLocation.textContent = userLocation;
    if (mapLocationText) mapLocationText.textContent = `Weather incidents around ${userLocation}`;

    try {
        const evalData = await apiFetch(`/api/evaluate/${encodeURIComponent(userLocation)}`);
        const telem = evalData.live_telemetry || {};

        if (currentTemperature) currentTemperature.textContent = `${Math.round(telem.temperature || 30)}°`;
        if (currentCondition) currentCondition.textContent = telem.condition || "Partly Cloudy";
        if (feelsLike) feelsLike.textContent = `Feels like ${Math.round(telem.apparent_temperature || telem.temperature || 32)}°C`;
        if (currentHumidity) currentHumidity.textContent = `${Math.round(telem.humidity || 75)}%`;
        if (currentWind) currentWind.textContent = `${Math.round(telem.wind_speed_kmh || 14)} km/h`;
        if (currentRainfall) currentRainfall.textContent = `${Number(telem.precipitation_mm || 0).toFixed(1)} mm`;
        if (currentVisibility) currentVisibility.textContent = `${Number(telem.visibility_km || 8).toFixed(1)} km`;
        if (currentWeatherIcon) currentWeatherIcon.className = getWeatherIconClass(telem.weather_code || 2);
        if (weatherUpdated) weatherUpdated.textContent = "Live · just now";
    } catch (err) {
        console.warn("Telemetry endpoint fallback:", err);
    }
}

/* =========================================================
   10. TOP EVENTS DISTRIBUTION FROM DATABASE
   ========================================================= */

async function loadEventDistribution() {
    try {
        const stats = await apiFetch("/api/stats/dashboard");
        const evDist = stats.event_distribution || {};
        const eventsList = document.querySelector(".top-events-card .events-list");

        if (eventsList && Object.keys(evDist).length > 0) {
            eventsList.innerHTML = Object.entries(evDist).slice(0, 5).map(([name, count]) => {
                let iconClass = "rainfall";
                let icon = "fa-cloud-showers-heavy";
                const lower = name.toLowerCase();

                if (lower.includes("flood")) {
                    iconClass = "flood";
                    icon = "fa-water";
                } else if (lower.includes("thunder") || lower.includes("storm")) {
                    iconClass = "storm";
                    icon = "fa-bolt";
                } else if (lower.includes("heat")) {
                    iconClass = "heatwave";
                    icon = "fa-temperature-high";
                } else if (lower.includes("fog")) {
                    iconClass = "fog";
                    icon = "fa-smog";
                }

                return `
                    <div class="event-item">
                        <div class="event-icon ${iconClass}">
                            <i class="fa-solid ${icon}"></i>
                        </div>
                        <div class="event-info">
                            <strong>${name}</strong>
                            <span>Real-time platform signals</span>
                        </div>
                        <div class="event-count">${count}</div>
                    </div>
                `;
            }).join("");
        }
    } catch (err) {
        console.warn("Could not load event distribution:", err);
    }
}

/* =========================================================
   11. INITIALIZATION
   ========================================================= */

loadUserProfile();
loadUserCityWeather();
loadMapFeed();
loadEventDistribution();

setTimeout(() => {
    indiaMap.invalidateSize();
}, 300);

console.log("Weather360 User Reports portal initialized.");