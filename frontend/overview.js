/* =========================================================
   WEATHER XPOSE - OVERVIEW CONTROLLER (API CONNECTED)
   ========================================================= */

// --- Marker colors based on truth score ---
const markerColors = {
    verified: "#10b981",
    review: "#f59e0b",
    suspicious: "#ef4444"
};

let activeMarkers = [];

/* =========================================================
   1. MAP INITIALIZATION
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

indiaMap.setView([22.5, 79], 5);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap contributors",
    maxZoom: 19
}).addTo(indiaMap);

function createMarkerIcon(status, score) {
    const color = markerColors[status] || "#10b981";
    const displayScore = Math.round(Number(score) || 0);

    return L.divIcon({
        className: "weather-marker",
        html: `
            <div style="
                width: 30px;
                height: 30px;
                background: ${color};
                border: 3px solid white;
                border-radius: 50%;
                box-shadow: 0 3px 10px rgba(0,0,0,0.25), 0 0 0 4px ${color}33;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 10px;
                font-weight: 800;
            ">
                ${displayScore}
            </div>
        `,
        iconSize: [30, 30],
        iconAnchor: [15, 15],
        popupAnchor: [0, -16]
    });
}

/* =========================================================
   2. LOAD LIVE INCIDENT MARKERS FROM API
   ========================================================= */

async function loadMapIncidents() {
    try {
        const geojson = await apiFetch("/api/map/active-incidents");
        const features = geojson.features || [];

        // Clear existing markers
        activeMarkers.forEach(m => indiaMap.removeLayer(m));
        activeMarkers = [];

        features.forEach(feat => {
            const props = feat.properties || {};
            const coords = feat.geometry?.coordinates || [];
            const lng = coords[0];
            const lat = coords[1];

            if (!lat || !lng) return;

            const score = Number(props.verification_score) || 0;
            let status = "verified";
            let statusText = "VERIFIED";

            if (props.verification_status === "Underprocess" || (score >= 27 && score <= 60)) {
                status = "review";
                statusText = "UNDER REVIEW";
            } else if (props.verification_status === "Fake" || score < 27) {
                status = "suspicious";
                statusText = "SUSPICIOUS";
            }

            const marker = L.marker([lat, lng], {
                icon: createMarkerIcon(status, score)
            }).addTo(indiaMap);

            marker.bindPopup(`
                <div style="min-width: 210px; font-family: Inter, Arial, sans-serif;">
                    <div style="font-size: 14px; font-weight: 800; color: #0b1f3a; margin-bottom: 4px;">
                        ${props.event_type || 'Weather Incident'}
                    </div>
                    <div style="font-size: 12px; color: #64748b; margin-bottom: 10px;">
                        <i class="fa-solid fa-location-dot"></i>
                        ${props.city || 'Location'}${props.state ? ', ' + props.state : ''}
                    </div>
                    <div style="font-size: 11px; color: #475569; margin-bottom: 10px; line-height: 1.4;">
                        ${props.report || 'Incident verified through multi-source radar and citizen telemetry.'}
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-top: 1px solid #e5e7eb;">
                        <span style="font-size: 11px; color: #64748b;">Trust Score</span>
                        <strong style="font-size: 15px; color: ${markerColors[status]};">
                            ${Math.round(score)}/100
                        </strong>
                    </div>
                    <div style="display: flex; justify-content: space-between; padding-top: 4px; font-size: 10px; font-weight: 700; color: ${markerColors[status]};">
                        <span>${statusText}</span>
                        <span>#${props.id || ''}</span>
                    </div>
                </div>
            `);

            activeMarkers.push(marker);
        });

        console.log(`Live incidents plotted on map: ${activeMarkers.length}`);
    } catch (err) {
        console.warn("Could not load live map incidents from API:", err);
    }
}

setTimeout(() => {
    indiaMap.invalidateSize();
}, 300);

/* =========================================================
   3. THEME TOGGLE
   ========================================================= */

const themeToggle = document.getElementById("themeToggle");

function updateThemeIcon(isDark) {
    if (!themeToggle) return;
    const icon = themeToggle.querySelector("i");
    if (!icon) return;
    icon.className = isDark ? "fa-solid fa-sun" : "fa-solid fa-moon";
}

const savedTheme = localStorage.getItem("weatherxpose-theme");
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
        localStorage.setItem("weatherxpose-theme", isDark ? "dark" : "light");
        updateThemeIcon(isDark);
        updateChartTheme();
    });
}

/* =========================================================
   4. INCIDENT ACTIVITY CHART
   ========================================================= */

const chartCanvas = document.getElementById("weatherActivityChart");
let weatherChart = null;

if (chartCanvas) {
    const ctx = chartCanvas.getContext("2d");
    weatherChart = new Chart(ctx, {
        type: "line",
        data: {
            labels: ["00:00", "03:00", "06:00", "09:00", "12:00", "15:00", "18:00", "21:00"],
            datasets: [
                {
                    label: "Verified Reports",
                    data: [4, 6, 3, 9, 15, 22, 18, 12],
                    borderColor: "#10b981",
                    backgroundColor: "rgba(16,185,129,0.12)",
                    borderWidth: 2,
                    pointRadius: 3,
                    pointHoverRadius: 5,
                    fill: true,
                    tension: 0.35
                },
                {
                    label: "Review Queue",
                    data: [1, 2, 1, 4, 6, 9, 7, 5],
                    borderColor: "#f59e0b",
                    backgroundColor: "rgba(245,158,11,0.04)",
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
                        font: { size: 11, weight: "600" }
                    }
                },
                tooltip: {
                    backgroundColor: "#0b1f3a",
                    titleFont: { size: 12 },
                    bodyFont: { size: 11 },
                    padding: 10,
                    cornerRadius: 7
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { font: { size: 10 }, color: "#64748b" }
                },
                y: {
                    beginAtZero: true,
                    ticks: { stepSize: 4, font: { size: 10 }, color: "#64748b" },
                    grid: { color: "rgba(100,116,139,0.12)" }
                }
            }
        }
    });
}

function updateChartTheme() {
    if (!weatherChart) return;
    const isDark = document.body.classList.contains("dark-mode");
    const textColor = isDark ? "#a8b9ce" : "#64748b";
    const gridColor = isDark ? "rgba(148,163,184,0.12)" : "rgba(100,116,139,0.12)";

    weatherChart.options.scales.x.ticks.color = textColor;
    weatherChart.options.scales.y.ticks.color = textColor;
    weatherChart.options.scales.y.grid.color = gridColor;
    weatherChart.options.plugins.legend.labels.color = textColor;
    weatherChart.update();
}
updateChartTheme();

/* =========================================================
   5. LOAD REAL DASHBOARD STATS & TOP EVENTS
   ========================================================= */

async function loadDashboardStats() {
    try {
        const stats = await apiFetch("/api/stats/dashboard");

        // Update Top Events list if container exists
        const eventsList = document.querySelector(".events-list");
        if (eventsList && stats.event_distribution) {
            const evDist = stats.event_distribution;
            const entries = Object.entries(evDist);

            if (entries.length > 0) {
                eventsList.innerHTML = entries.map(([name, count]) => {
                    let icon = "fa-cloud-showers-heavy";
                    let iconClass = "rain";
                    const lower = name.toLowerCase();

                    if (lower.includes("thunder") || lower.includes("storm") || lower.includes("lightning")) {
                        icon = "fa-bolt";
                        iconClass = "storm";
                    } else if (lower.includes("flood")) {
                        icon = "fa-water";
                        iconClass = "flood";
                    } else if (lower.includes("heat") || lower.includes("sun")) {
                        icon = "fa-sun";
                        iconClass = "heat";
                    } else if (lower.includes("fog") || lower.includes("snow")) {
                        icon = "fa-smog";
                        iconClass = "fog";
                    }

                    return `
                        <div class="event-item">
                            <div class="event-left">
                                <div class="event-icon ${iconClass}">
                                    <i class="fa-solid ${icon}"></i>
                                </div>
                                <strong>${name}</strong>
                            </div>
                            <span class="event-count green">
                                ${count} Event${count > 1 ? 's' : ''}
                            </span>
                        </div>
                    `;
                }).join("");
            }
        }
    } catch (err) {
        console.warn("Could not load stats dashboard:", err);
    }
}

/* =========================================================
   6. LOCATION WEATHER TELEMETRY & ML EVALUATION
   ========================================================= */

const locationInput = document.getElementById("locationInput");
const searchLocationBtn = document.getElementById("searchLocationBtn");
const weatherLocation = document.getElementById("weatherLocation");
const temperature = document.getElementById("temperature");
const weatherCondition = document.getElementById("weatherCondition");
const feelsLike = document.getElementById("feelsLike");
const humidity = document.getElementById("humidity");
const windSpeed = document.getElementById("windSpeed");
const rainfall = document.getElementById("rainfall");
const visibility = document.getElementById("visibility");
const weatherIcon = document.getElementById("weatherIcon");
const locationEvent = document.getElementById("locationEvent");
const locationReports = document.getElementById("locationReports");
const locationScore = document.getElementById("locationScore");
const locationStatus = document.getElementById("locationStatus");

function getWeatherCondition(code) {
    if (code === 0) return "Clear Sky";
    if ([1, 2, 3].includes(code)) return "Partly Cloudy";
    if ([45, 48].includes(code)) return "Fog";
    if ([51, 53, 55, 56, 57].includes(code)) return "Drizzle";
    if ([61, 63, 65, 66, 67, 80, 81, 82].includes(code)) return "Rain Showers";
    if ([71, 73, 75, 77].includes(code)) return "Snowfall";
    if ([95, 96, 99].includes(code)) return "Thunderstorm";
    return "Weather Available";
}

function getWeatherIcon(code) {
    if (code === 0) return "fa-solid fa-sun";
    if ([1, 2, 3].includes(code)) return "fa-solid fa-cloud-sun";
    if ([45, 48].includes(code)) return "fa-solid fa-smog";
    if ([51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82].includes(code)) return "fa-solid fa-cloud-rain";
    if ([71, 73, 75, 77].includes(code)) return "fa-solid fa-snowflake";
    if ([95, 96, 99].includes(code)) return "fa-solid fa-cloud-bolt";
    return "fa-solid fa-cloud";
}

async function searchWeather() {
    const query = (locationInput.value || "Kolkata").trim();
    if (!query) return;

    if (searchLocationBtn) {
        searchLocationBtn.disabled = true;
        searchLocationBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Searching...';
    }

    try {
        // 1. First attempt backend ML evaluate endpoint
        let evalData = null;
        try {
            evalData = await apiFetch(`/api/evaluate/${encodeURIComponent(query)}`);
        } catch {
            evalData = null;
        }

        // 2. Fetch reports for this city from backend
        let cityReports = [];
        try {
            const reportsRes = await apiFetch(`/api/reports?city=${encodeURIComponent(query)}&limit=10`);
            cityReports = reportsRes.data || [];
        } catch {
            cityReports = [];
        }

        // If backend returned telemetry
        if (evalData && evalData.live_telemetry) {
            const telem = evalData.live_telemetry;
            const ml = evalData.ml_inference || {};

            weatherLocation.textContent = `${evalData.city}, India`;
            temperature.textContent = Math.round(telem.temperature || 28);
            feelsLike.textContent = Math.round(telem.apparent_temperature || telem.temperature || 28);
            weatherCondition.textContent = telem.condition || (ml.overall_alert ? `${ml.overall_alert} Alert` : "Normal Conditions");
            weatherIcon.className = getWeatherIcon(telem.weather_code || 2);
            humidity.textContent = `${Math.round(telem.humidity || 70)}%`;
            windSpeed.textContent = `${Math.round(telem.wind_speed_kmh || 12)} km/h`;
            rainfall.textContent = `${Number(telem.precipitation_mm || 0).toFixed(1)} mm`;
            visibility.textContent = `${Number(telem.visibility_km || 8).toFixed(1)} km`;
        } else {
            // Geocoding fallback to Open-Meteo
            const geoRes = await fetch(`https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(query)}&count=1&language=en&format=json`);
            const geoData = await geoRes.json();

            if (geoData.results && geoData.results[0]) {
                const place = geoData.results[0];
                const weatherRes = await fetch(`https://api.open-meteo.com/v1/forecast?latitude=${place.latitude}&longitude=${place.longitude}&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m&hourly=visibility&timezone=auto`);
                const weatherData = await weatherRes.json();
                const current = weatherData.current;

                weatherLocation.textContent = `${place.name}, ${place.country || "India"}`;
                temperature.textContent = Math.round(current.temperature_2m);
                feelsLike.textContent = Math.round(current.apparent_temperature);
                weatherCondition.textContent = getWeatherCondition(current.weather_code);
                weatherIcon.className = getWeatherIcon(current.weather_code);
                humidity.textContent = `${current.relative_humidity_2m}%`;
                windSpeed.textContent = `${Math.round(current.wind_speed_10m)} km/h`;
                rainfall.textContent = `${Number(current.precipitation || 0).toFixed(1)} mm`;

                let vis = 8.0;
                if (weatherData.hourly?.visibility?.length) {
                    vis = (weatherData.hourly.visibility[0] / 1000).toFixed(1);
                }
                visibility.textContent = `${vis} km`;

                indiaMap.setView([place.latitude, place.longitude], 6);
            }
        }

        // 3. Update Incident Box with real database records
        if (cityReports.length > 0) {
            const latest = cityReports[0];
            const score = Math.round(Number(latest.verification_score) || 0);

            locationEvent.textContent = latest.event_type || "Weather Event";
            locationReports.textContent = `${cityReports.length}`;
            locationScore.textContent = `${score}/100`;

            if (latest.verification_status === "Othentic") {
                locationStatus.textContent = "Verified";
                locationStatus.style.color = "#10b981";
            } else if (latest.verification_status === "Underprocess") {
                locationStatus.textContent = "Under Review";
                locationStatus.style.color = "#f59e0b";
            } else {
                locationStatus.textContent = "Suspicious";
                locationStatus.style.color = "#ef4444";
            }

            if (latest.latitude && latest.longitude) {
                indiaMap.setView([latest.latitude, latest.longitude], 6);
            }
        } else {
            locationEvent.textContent = "No active critical alert";
            locationReports.textContent = "0";
            locationScore.textContent = "N/A";
            locationStatus.textContent = "Normal";
            locationStatus.style.color = "#64748b";
        }
    } catch (err) {
        console.error("Search weather error:", err);
    } finally {
        if (searchLocationBtn) {
            searchLocationBtn.disabled = false;
            searchLocationBtn.innerHTML = '<i class="fa-solid fa-magnifying-glass"></i> Search';
        }
    }
}

if (searchLocationBtn) {
    searchLocationBtn.addEventListener("click", searchWeather);
}
if (locationInput) {
    locationInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") searchWeather();
    });
}

/* =========================================================
   7. SIDEBAR LIVE DATE / TIME
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

/* =========================================================
   8. ROLE-BASED ACCESS & USER BADGES
   ========================================================= */

const loggedInRole = localStorage.getItem("weatherxpose-user-role");
const loggedInUserName = localStorage.getItem("weatherxpose-user-name");

const userReportsNav = document.querySelector('a[href="user-reports.html"]');
const adminReportsNav = document.querySelector('a[href="admin-reports.html"]');
const headerUserName = document.getElementById("headerUserName");
const headerUserRole = document.querySelector(".header-user small");
const sidebarUserName = document.getElementById("sidebarUserName");
const sidebarUserRole = document.getElementById("sidebarUserRole");
const sidebarAvatar = document.getElementById("sidebarAvatar");

if (loggedInRole === "admin") {
    if (userReportsNav) userReportsNav.style.display = "none";
    if (adminReportsNav) adminReportsNav.style.display = "flex";

    const adminName = localStorage.getItem("weatherxpose-admin-name") || "Admin";
    if (headerUserName) headerUserName.textContent = adminName;
    if (headerUserRole) headerUserRole.textContent = "Administrator";
    if (sidebarUserName) sidebarUserName.textContent = adminName;
    if (sidebarUserRole) sidebarUserRole.textContent = "Administrator";
    if (sidebarAvatar) sidebarAvatar.textContent = adminName.substring(0, 2).toUpperCase();
} else {
    if (adminReportsNav) adminReportsNav.style.display = "none";
    if (userReportsNav) userReportsNav.style.display = "flex";

    const displayName = loggedInUserName || "User";
    if (headerUserName) headerUserName.textContent = displayName;
    if (headerUserRole) headerUserRole.textContent = "Citizen Member";
    if (sidebarUserName) sidebarUserName.textContent = displayName;
    if (sidebarUserRole) sidebarUserRole.textContent = "Citizen Member";
    if (sidebarAvatar) sidebarAvatar.textContent = displayName.substring(0, 2).toUpperCase();
}

/* =========================================================
   9. INITIAL LOAD
   ========================================================= */

loadMapIncidents();
loadDashboardStats();
searchWeather();