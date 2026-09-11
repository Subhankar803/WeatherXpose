/* =========================================================
   WEATHER360 - ADMIN REPORTS CONTROLLER (API CONNECTED)
   ========================================================= */

// --- Global Data Store ---
let reports = [];
let selectedReport = null;
let currentStatus = "all";

// --- DOM Elements ---
const reportsTable = document.getElementById("reportsTableBody") || document.getElementById("reportsTable");
const emptyState = document.getElementById("emptyState");
const searchInput = document.getElementById("searchInput");
const filterButtons = document.querySelectorAll(".filter-btn");
const locationFilter = document.getElementById("locationFilter");
const resetFilters = document.getElementById("resetFilters");

const totalCount = document.getElementById("totalReports");
const verifiedCount = document.getElementById("verifiedReports");
const reviewCount = document.getElementById("reviewReports");
const unverifiedCount = document.getElementById("unverifiedReports");

const detailCard = document.getElementById("reportDetailCard") || document.getElementById("detailCard");
const adminActions = document.getElementById("adminActions");
const verifyReportBtn = document.getElementById("verifyReportBtn");
const fraudReportBtn = document.getElementById("fraudReportBtn");
const triggerIngestionBtn = document.getElementById("triggerIngestionBtn");
const exportBtn = document.getElementById("exportBtn");
const themeToggle = document.getElementById("themeToggle");

let detailMap = null;
let detailMarker = null;

/* =========================================================
   1. AUTHENTICATION & ROLE ACCESS
   ========================================================= */

const loggedInRole = localStorage.getItem("weather360-user-role");
const adminName = localStorage.getItem("weather360-admin-name") || "Administrator";
const adminPermission = localStorage.getItem("weather360-admin-permission") || "Admin";

const userReportsNav = document.querySelector('a[href="user-reports.html"]');
const adminReportsNav = document.querySelector('a[href="admin-reports.html"]');
const topProfileName = document.querySelector(".top-profile span");
const topProfileAvatar = document.querySelector(".profile-avatar");
const sidebarAdminName = document.querySelector(".admin-info strong");
const sidebarAdminRole = document.querySelector(".admin-info span");
const sidebarAdminAvatar = document.querySelector(".admin-avatar");

if (loggedInRole === "user") {
    // Citizen user should not stay on admin dashboard
    if (userReportsNav) userReportsNav.style.display = "flex";
    if (adminReportsNav) adminReportsNav.style.display = "none";
    window.location.href = "user-reports.html";
} else {
    if (userReportsNav) userReportsNav.style.display = "none";
    if (adminReportsNav) adminReportsNav.style.display = "flex";

    const initials = adminName.split(" ").map(w => w[0]).join("").substring(0, 2).toUpperCase() || "AD";
    if (topProfileName) topProfileName.textContent = adminName;
    if (topProfileAvatar) topProfileAvatar.textContent = initials;
    if (sidebarAdminName) sidebarAdminName.textContent = adminName;
    if (sidebarAdminRole) sidebarAdminRole.textContent = adminPermission;
    if (sidebarAdminAvatar) sidebarAdminAvatar.textContent = initials;
}

/* =========================================================
   2. LIVE DATE & TIME
   ========================================================= */

function updateTime() {
    const now = new Date();
    const time = now.toLocaleTimeString("en-IN", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit"
    });
    const lastUpdatedEl = document.getElementById("lastUpdated");
    if (lastUpdatedEl) {
        lastUpdatedEl.textContent = `Live · ${time}`;
    }
}
setInterval(updateTime, 1000);
updateTime();

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
   3. THEME TOGGLE
   ========================================================= */

function applyTheme() {
    const savedTheme = localStorage.getItem("weather360-theme");
    if (savedTheme === "light") {
        document.body.classList.add("light");
        if (themeToggle) themeToggle.innerHTML = '<i class="fa-solid fa-sun"></i>';
    } else {
        document.body.classList.remove("light");
        if (themeToggle) themeToggle.innerHTML = '<i class="fa-solid fa-moon"></i>';
    }
}
applyTheme();

if (themeToggle) {
    themeToggle.addEventListener("click", () => {
        document.body.classList.toggle("light");
        const isLight = document.body.classList.contains("light");
        localStorage.setItem("weather360-theme", isLight ? "light" : "dark");
        themeToggle.innerHTML = isLight ? '<i class="fa-solid fa-sun"></i>' : '<i class="fa-solid fa-moon"></i>';
    });
}

/* =========================================================
   4. DATA INGESTION TRIGGER (BACKEND API)
   ========================================================= */

if (triggerIngestionBtn) {
    triggerIngestionBtn.addEventListener("click", async () => {
        triggerIngestionBtn.disabled = true;
        triggerIngestionBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Ingesting...';

        try {
            const res = await apiFetch("/api/admin/trigger-ingestion", { method: "POST" });
            showNotice(`Ingestion completed! Collected ${res.collected_events_count} events, verified ${res.verified_and_stored_count}.`, "success");
            await loadAllReports();
            await updateSummaryStats();
        } catch (err) {
            showNotice(err.message || "Failed to trigger ingestion pipeline.", "error");
        } finally {
            triggerIngestionBtn.disabled = false;
            triggerIngestionBtn.innerHTML = '<i class="fa-solid fa-satellite-dish"></i> Trigger Ingestion';
        }
    });
}

/* =========================================================
   5. LOAD REPORTS FROM BACKEND API
   ========================================================= */

async function loadAllReports() {
    try {
        const res = await apiFetch("/api/reports?limit=150");
        const apiData = res.data || [];

        reports = apiData.map(item => {
            const score = Math.round(Number(item.verification_score) || 0);
            let uiStatus = "verified";

            if (item.verification_status === "Underprocess" || item.review_action === "On hold") {
                uiStatus = "review";
            } else if (item.verification_status === "Fake" || item.review_action === "Rejected") {
                uiStatus = "unverified";
            } else if (item.verification_status === "Othentic" || item.review_action === "Approved") {
                uiStatus = "verified";
            } else if (score < 27) {
                uiStatus = "suspicious";
            }

            // Extract hints
            const hints = item.hint_breakdown || [];
            const windyObj = hints.find(h => (h.source || h.signal || '').toLowerCase().includes("windy"));
            const imdObj = hints.find(h => (h.source || h.signal || '').toLowerCase().includes("imd"));
            const localObj = hints.find(h => (h.source || h.signal || '').toLowerCase().includes("local") || (h.source || h.signal || '').toLowerCase().includes("cluster"));
            const accObj = hints.find(h => (h.source || h.signal || '').toLowerCase().includes("account") || (h.source || h.signal || '').toLowerCase().includes("trust"));
            const newsObj = hints.find(h => (h.source || h.signal || '').toLowerCase().includes("news"));

            const formattedTime = item.timestamp
                ? new Date(item.timestamp).toLocaleString("en-IN", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" })
                : "Recent";

            // Clean up state if it was stored as "India" or generic
            let cleanState = item.state;
            if (!cleanState || cleanState.toLowerCase() === "india" || cleanState.toLowerCase() === "unknown") {
                const CITY_STATE_JS = {
                    "kolkata": "West Bengal", "mumbai": "Maharashtra", "delhi": "Delhi",
                    "new delhi": "Delhi", "chennai": "Tamil Nadu", "bengaluru": "Karnataka",
                    "bangalore": "Karnataka", "hyderabad": "Telangana", "ahmedabad": "Gujarat",
                    "pune": "Maharashtra", "jaipur": "Rajasthan", "lucknow": "Uttar Pradesh",
                    "patna": "Bihar", "guwahati": "Assam", "bhubaneswar": "Odisha", "malda": "West Bengal",
                    "alipurduar": "West Bengal", "durg": "Chhattisgarh", "ballia": "Uttar Pradesh", "raisen": "Madhya Pradesh"
                };
                const cLower = (item.city || "").toLowerCase().trim();
                cleanState = CITY_STATE_JS[cLower] || "";
            }

            const displayLocation = cleanState
                ? `${item.city || 'Location'}, ${cleanState}`
                : (item.city || "India");

            return {
                id: `WR-${item.id}`,
                rawId: item.id,
                event: item.event_type || "Weather Incident",
                location: displayLocation,
                city: item.city || "India",
                source: item.reviewed_by ? `Reviewed (${item.reviewed_by})` : "Citizen Report",
                account: "verified",
                accountName: item.reviewed_by ? "Audited Report" : "Citizen Submitter",
                score: score,
                status: uiStatus,
                backendStatus: item.verification_status,
                time: formattedTime,
                description: item.report_text || "Weather incident report stored in Truth Verification Engine.",
                reporter: item.reviewed_by || "Citizen User",
                avatar: (item.city ? item.city[0] : "W").toUpperCase(),
                submitted: `Submitted: ${formattedTime} · ${Number(item.latitude || 22.5).toFixed(4)}° N, ${Number(item.longitude || 88.3).toFixed(4)}° E`,
                hashtags: [`#${(item.event_type || 'weather').toLowerCase().replace(/\s+/g, '')}`, `#${(item.city || 'india').toLowerCase()}`],
                latitude: Number(item.latitude) || 22.5726,
                longitude: Number(item.longitude) || 88.3639,
                attachment: item.media_url ? item.media_url.split("/").pop() : "No attachment",
                mediaUrl: item.media_url,
                windy: windyObj ? (windyObj.points !== undefined ? windyObj.points : (windyObj.passed ? 15 : 5)) : 15,
                windyStatus: windyObj ? (windyObj.status || (windyObj.passed ? "Telemetry corroborated" : "Telemetry inconclusive")) : "Strong supporting signal",
                imd: imdObj ? (imdObj.points !== undefined ? imdObj.points : (imdObj.passed ? 30 : -10)) : 30,
                imdStatus: imdObj ? (imdObj.status || (imdObj.passed ? "Corroborated by official IMD alert" : "No active IMD warning bulletin")) : "Supporting official report",
                local: localObj ? (localObj.points !== undefined ? localObj.points : (localObj.passed ? 20 : 0)) : 20,
                localStatus: localObj ? (localObj.status || "Local reports analysis") : "5+ supporting reports",
                accountScore: accObj ? (accObj.points !== undefined ? accObj.points : 0) : 10,
                accountSignalText: accObj ? (accObj.status || "Account trust standing") : "Verified account",
                news: newsObj ? (newsObj.points !== undefined ? newsObj.points : 0) : 10,
                newsStatus: newsObj ? (newsObj.status || "News media coverage") : "Multiple news confirmations",
                match: Math.min(100, score + 4),
                locationMatch: Math.min(100, score + 5),
                imageIntegrity: item.is_ai_generated ? 15 : 92,
                sourceAgreement: Math.max(20, score - 2),
                confidence: (score / 100).toFixed(2),
                officialTitle: "IMD & Radar Corroboration",
                officialText: (imdObj && imdObj.status) ? imdObj.status : (item.admin_comment || "Automated corroboration across IMD, Windy & forensic telemetry."),
                reason: item.admin_comment || (score > 60 ? "Highly corroborated by official bulletins and ground sensors." : "Ambiguous signals requiring administrative verification."),
                isAi: !!item.is_ai_generated,
                aiStatus: item.is_ai_generated ? "AI Deepfake Detected" : "Integrity Passed"
            };
        });

        console.log(`[Weather360 Admin] Successfully loaded ${reports.length} reports from database.`);
        renderReports();
        updateLocationFilterOptions();
    } catch (err) {
        console.error("[Weather360 Admin] Error loading reports from API:", err);
        showNotice("Could not load reports: " + (err.message || err), "error");
    }
}

/* =========================================================
   6. SUMMARY STATS (BACKEND API)
   ========================================================= */

async function updateSummaryStats() {
    try {
        const stats = await apiFetch("/api/stats/dashboard");
        if (totalCount) totalCount.textContent = stats.total_claims_processed || reports.length;
        if (verifiedCount) verifiedCount.textContent = stats.verified_authentic_claims || reports.filter(r => r.status === "verified").length;
        if (reviewCount) reviewCount.textContent = stats.pending_review_queue || reports.filter(r => r.status === "review").length;
        if (unverifiedCount) unverifiedCount.textContent = stats.disinformation_fake_claims || reports.filter(r => r.status === "unverified" || r.status === "suspicious").length;
    } catch {
        if (totalCount) totalCount.textContent = reports.length;
        if (verifiedCount) verifiedCount.textContent = reports.filter(r => r.status === "verified").length;
        if (reviewCount) reviewCount.textContent = reports.filter(r => r.status === "review").length;
        if (unverifiedCount) unverifiedCount.textContent = reports.filter(r => r.status === "unverified" || r.status === "suspicious").length;
    }
}

/* =========================================================
   7. POPULATE LOCATION FILTER DROPDOWN
   ========================================================= */

function updateLocationFilterOptions() {
    if (!locationFilter) return;
    const cities = Array.from(new Set(reports.map(r => r.city).filter(Boolean))).sort();
    const currentVal = locationFilter.value;

    locationFilter.innerHTML = '<option value="all">All Locations</option>' +
        cities.map(c => `<option value="${c}">${c}</option>`).join("");

    if (cities.includes(currentVal)) {
        locationFilter.value = currentVal;
    }
}

/* =========================================================
   8. STATUS HELPERS
   ========================================================= */

function getStatusLabel(status) {
    if (status === "verified") return "Verified";
    if (status === "review") return "Under Review";
    if (status === "suspicious") return "Suspicious";
    return "Unverified";
}

function getScoreClass(score) {
    if (score > 60) return "green";
    if (score >= 27) return "orange";
    return "red";
}

function getEventIcon(event) {
    const ev = (event || "").toLowerCase();
    if (ev.includes("rain")) return "fa-cloud-showers-heavy";
    if (ev.includes("flood")) return "fa-water";
    if (ev.includes("storm") || ev.includes("thunder")) return "fa-bolt";
    if (ev.includes("heat")) return "fa-temperature-high";
    if (ev.includes("cyclone")) return "fa-tornado";
    return "fa-triangle-exclamation";
}

/* =========================================================
   9. RENDER REPORTS TABLE
   ========================================================= */

function renderReports() {
    if (!reportsTable) return;
    reportsTable.innerHTML = "";

    const query = (searchInput ? searchInput.value : "").toLowerCase().trim();
    const location = locationFilter ? locationFilter.value : "all";

    const filtered = reports.filter(report => {
        const matchesStatus =
            currentStatus === "all" ||
            report.status === currentStatus ||
            (currentStatus === "unverified" && (report.status === "unverified" || report.status === "suspicious"));

        const matchesSearch =
            report.id.toLowerCase().includes(query) ||
            report.event.toLowerCase().includes(query) ||
            report.location.toLowerCase().includes(query) ||
            report.source.toLowerCase().includes(query);

        const matchesLocation =
            location === "all" || report.city === location;

        return matchesStatus && matchesSearch && matchesLocation;
    });

    if (filtered.length === 0) {
        if (emptyState) emptyState.style.display = "flex";
        reportsTable.innerHTML = `
            <tr>
                <td colspan="8" style="text-align: center; padding: 30px; color: var(--muted);">
                    <i class="fa-solid fa-inbox" style="font-size: 24px; margin-bottom: 8px; display: block;"></i>
                    No reports match the selected filters.
                </td>
            </tr>
        `;
        return;
    }

    if (emptyState) emptyState.style.display = "none";

    filtered.forEach(report => {
        const tr = document.createElement("tr");
        tr.style.cursor = "pointer";

        tr.innerHTML = `
            <td class="report-id">${report.id}</td>
            <td>
                <div class="event-name">
                    <i class="fa-solid ${getEventIcon(report.event)}"></i>
                    <span>${report.event}</span>
                </div>
            </td>
            <td class="location-cell"><i class="fa-solid fa-location-dot"></i> ${report.location}</td>
            <td class="source-cell">${report.source}</td>
            <td>
                <span class="account-badge ${report.account}">
                    ${report.accountName}
                </span>
            </td>
            <td>
                <span class="score ${getScoreClass(report.score)}">
                    ${report.score}
                </span>
            </td>
            <td>
                <span class="status-badge ${report.status}">
                    ${getStatusLabel(report.status)}
                </span>
                ${report.isAi ? '<span class="status-badge" style="background:#ef4444; color:#fff; font-size:10px; padding:2px 5px; border-radius:4px; margin-left:4px;"><i class="fa-solid fa-robot"></i> AI Fake</span>' : ''}
            </td>
            <td>${report.time}</td>
        `;

        tr.addEventListener("click", () => {
            openReportDetail(report);
        });

        reportsTable.appendChild(tr);
    });
}

/* =========================================================
   10. OPEN DETAILED REPORT PANEL
   ========================================================= */

function openReportDetail(report) {
    selectedReport = report;
    if (detailCard) detailCard.classList.add("show");

    const detailTitle = document.getElementById("detailTitle");
    if (detailTitle) detailTitle.textContent = `${report.event} (${report.id})`;

    const detailSubtitle = document.getElementById("detailSubtitle");
    if (detailSubtitle) detailSubtitle.textContent = `Report #${report.rawId} · ${report.location} · ${report.submitted}`;

    const detailDecision = document.getElementById("detailDecision");
    if (detailDecision) {
        detailDecision.textContent = getStatusLabel(report.status).toUpperCase();
        detailDecision.className = `detail-status ${report.status}`;
    }

    const detailSource = document.getElementById("detailSource");
    if (detailSource) detailSource.textContent = report.source;

    const detailDescription = document.getElementById("detailDescription");
    if (detailDescription) detailDescription.textContent = report.description;

    const hashtags = document.getElementById("detailHashtags");
    if (hashtags) {
        hashtags.innerHTML = "";
        report.hashtags.forEach(tag => {
            const span = document.createElement("span");
            span.className = "hashtag";
            span.textContent = tag;
            hashtags.appendChild(span);
        });
    }

    const reporterAvatar = document.getElementById("reporterAvatar") || document.getElementById("detailAvatar");
    if (reporterAvatar) reporterAvatar.textContent = report.avatar;

    const detailReporter = document.getElementById("detailReporter");
    if (detailReporter) detailReporter.textContent = report.reporter;

    const detailSubmitted = document.getElementById("detailSubmitted");
    if (detailSubmitted) detailSubmitted.textContent = report.submitted;

    // Cross reference & reasoning
    const crossCitizen = document.getElementById("crossCitizen");
    if (crossCitizen) crossCitizen.textContent = report.event;

    const crossCitizenText = document.getElementById("crossCitizenText");
    if (crossCitizenText) crossCitizenText.textContent = report.description;

    const crossOfficial = document.getElementById("crossOfficial");
    if (crossOfficial) crossOfficial.textContent = report.officialTitle;

    const crossOfficialText = document.getElementById("crossOfficialText");
    if (crossOfficialText) crossOfficialText.textContent = report.officialText;

    const matchBadge = document.getElementById("matchBadge");
    if (matchBadge) matchBadge.textContent = `${report.match}% Match`;

    const locMatch = document.getElementById("locationMatch");
    if (locMatch) locMatch.textContent = report.locationMatch;

    const imgInteg = document.getElementById("imageIntegrity");
    if (imgInteg) imgInteg.textContent = report.imageIntegrity;

    const srcAgree = document.getElementById("sourceAgreement");
    if (srcAgree) srcAgree.textContent = report.sourceAgreement;

    const modConf = document.getElementById("modelConfidence");
    if (modConf) modConf.textContent = report.confidence;

    const locProg = document.getElementById("locationProgress");
    if (locProg) locProg.style.width = `${report.locationMatch}%`;

    const imgProg = document.getElementById("imageProgress");
    if (imgProg) imgProg.style.width = `${report.imageIntegrity}%`;

    const srcProg = document.getElementById("sourceProgress");
    if (srcProg) srcProg.style.width = `${report.sourceAgreement}%`;

    const reasonText = document.getElementById("reasonText");
    if (reasonText) reasonText.textContent = report.reason;

    // Signal breakdown
    const windyScore = document.getElementById("windyScore");
    if (windyScore) windyScore.textContent = formatScore(report.windy);
    const windyText = document.getElementById("windyText");
    if (windyText && report.windyStatus) windyText.textContent = report.windyStatus;

    const imdScore = document.getElementById("imdScore");
    if (imdScore) {
        imdScore.textContent = formatScore(report.imd);
        imdScore.style.color = report.imd > 0 ? "#10b981" : "#ef4444";
    }
    const imdText = document.getElementById("imdText");
    if (imdText && report.imdStatus) imdText.textContent = report.imdStatus;

    const localScore = document.getElementById("localScore");
    if (localScore) localScore.textContent = formatScore(report.local);
    const localText = document.getElementById("localText");
    if (localText && report.localStatus) localText.textContent = report.localStatus;

    const accSignal = document.getElementById("accountSignalScore");
    if (accSignal) accSignal.textContent = formatScore(report.accountScore);
    const accSignalText = document.getElementById("accountSignalText");
    if (accSignalText && report.accountSignalText) accSignalText.textContent = report.accountSignalText;

    const newsScore = document.getElementById("newsScore");
    if (newsScore) newsScore.textContent = formatScore(report.news);
    const newsText = document.getElementById("newsText");
    if (newsText && report.newsStatus) newsText.textContent = report.newsStatus;

    const detailScore = document.getElementById("detailScore");
    if (detailScore) detailScore.textContent = report.score;

    const detailScoreBar = document.getElementById("detailScoreBar");
    if (detailScoreBar) detailScoreBar.style.width = `${Math.min(report.score, 100)}%`;

    const detailLocation = document.getElementById("detailLocation");
    if (detailLocation) detailLocation.textContent = report.location;

    const detailCoordinates = document.getElementById("detailCoordinates");
    if (detailCoordinates) detailCoordinates.textContent = `${report.latitude.toFixed(4)}° N, ${report.longitude.toFixed(4)}° E`;

    const attachmentName = document.getElementById("attachmentName");
    if (attachmentName) attachmentName.textContent = report.attachment;

    const aiStatus = document.getElementById("aiStatus");
    if (aiStatus) aiStatus.textContent = report.aiStatus;

    const accountDot = document.getElementById("accountStatusDot");
    if (accountDot) accountDot.className = `account-status-dot ${report.account}`;

    const detAccStatus = document.getElementById("detailAccountStatus");
    if (detAccStatus) detAccStatus.textContent = report.accountName;

    const decisionText = document.getElementById("decisionText");
    if (decisionText) decisionText.textContent = getStatusLabel(report.status).toUpperCase();

    const decisionDescription = document.getElementById("decisionDescription");
    if (report.status === "verified") {
        if (decisionDescription) decisionDescription.textContent = "Report has been verified by the administrator and is published on the national map.";
        if (adminActions) adminActions.classList.remove("show");
    } else if (report.status === "review") {
        if (decisionDescription) decisionDescription.textContent = "Report requires human administrator verification before final publication.";
        if (adminActions) adminActions.classList.add("show");
    } else {
        if (decisionDescription) decisionDescription.textContent = "Report flagged as suspicious/disinformation. It is withheld from public feeds.";
        if (adminActions) adminActions.classList.remove("show");
    }

    initializeDetailMap(report.latitude, report.longitude, report.city);

    setTimeout(() => {
        if (detailCard) detailCard.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 100);
}

function formatScore(val) {
    const num = Number(val) || 0;
    return num > 0 ? `+${num}` : `${num}`;
}

/* =========================================================
   11. MINI DETAIL MAP
   ========================================================= */

function initializeDetailMap(lat, lng, city) {
    if (!detailMap) {
        detailMap = L.map("detailMap", { zoomControl: true }).setView([lat, lng], 11);
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            attribution: "&copy; OpenStreetMap contributors"
        }).addTo(detailMap);
        detailMarker = L.marker([lat, lng]).addTo(detailMap);
    } else {
        detailMap.setView([lat, lng], 11);
        detailMarker.setLatLng([lat, lng]);
    }

    detailMarker.bindPopup(`<strong>${city}</strong><br>${lat.toFixed(4)}° N, ${lng.toFixed(4)}° E`).openPopup();
    setTimeout(() => detailMap.invalidateSize(), 200);
}

/* =========================================================
   12. ADMIN DECISION ACTIONS (BACKEND API INTEGRATION)
   ========================================================= */

// Action: Approve / Verify Report
if (verifyReportBtn) {
    verifyReportBtn.onclick = async function () {
        if (!selectedReport) return;

        verifyReportBtn.disabled = true;
        verifyReportBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Approving...';

        try {
            const res = await apiFetch(`/api/admin/review/${selectedReport.rawId}`, {
                method: "POST",
                body: {
                    action: "Approved",
                    verification_status: "Othentic",
                    comment: `Report verified and published by ${adminName}.`
                }
            });

            selectedReport.status = "verified";
            selectedReport.backendStatus = "Othentic";
            selectedReport.score = Math.max(selectedReport.score, 85);

            showNotice(`Report #${selectedReport.rawId} approved and published!`, "success");
            await loadAllReports();
            await updateSummaryStats();
            openReportDetail(selectedReport);
        } catch (err) {
            showNotice(err.message || "Failed to submit review decision.", "error");
        } finally {
            verifyReportBtn.disabled = false;
            verifyReportBtn.innerHTML = '<i class="fa-solid fa-check"></i> Verify Report';
        }
    };
}

// Action: Reject / Mark as Fraud
if (fraudReportBtn) {
    fraudReportBtn.onclick = async function () {
        if (!selectedReport) return;

        fraudReportBtn.disabled = true;
        fraudReportBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Rejecting...';

        try {
            const res = await apiFetch(`/api/admin/review/${selectedReport.rawId}`, {
                method: "POST",
                body: {
                    action: "Rejected",
                    verification_status: "Fake",
                    comment: `Disinformation identified. Marked as fake by ${adminName}.`
                }
            });

            selectedReport.status = "unverified";
            selectedReport.backendStatus = "Fake";
            selectedReport.score = Math.min(selectedReport.score, 25);

            showNotice(`Report #${selectedReport.rawId} flagged as fraud. User penalized.`, "warning");
            await loadAllReports();
            await updateSummaryStats();
            openReportDetail(selectedReport);
        } catch (err) {
            showNotice(err.message || "Failed to mark as fraud.", "error");
        } finally {
            fraudReportBtn.disabled = false;
            fraudReportBtn.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i> Mark as Fraud';
        }
    };
}

/* =========================================================
   13. FILTERS & EVENT LISTENERS
   ========================================================= */

filterButtons.forEach(button => {
    button.addEventListener("click", () => {
        filterButtons.forEach(btn => btn.classList.remove("active"));
        button.classList.add("active");
        currentStatus = button.dataset.status;
        renderReports();
    });
});

if (searchInput) searchInput.addEventListener("input", renderReports);
if (locationFilter) locationFilter.addEventListener("change", renderReports);

if (resetFilters) {
    resetFilters.addEventListener("click", () => {
        searchInput.value = "";
        if (locationFilter) locationFilter.value = "all";
        currentStatus = "all";
        filterButtons.forEach(btn => btn.classList.remove("active"));
        const allBtn = document.querySelector('[data-status="all"]');
        if (allBtn) allBtn.classList.add("active");
        renderReports();
    });
}

const closeDetailBtn = document.getElementById("closeDetail");
if (closeDetailBtn) {
    closeDetailBtn.addEventListener("click", () => {
        detailCard.classList.remove("show");
        selectedReport = null;
    });
}

// Open OSM External Map
const openMapBtn = document.getElementById("openMapBtn");
if (openMapBtn) {
    openMapBtn.addEventListener("click", () => {
        if (!selectedReport) return;
        const { latitude, longitude } = selectedReport;
        window.open(`https://www.openstreetmap.org/?mlat=${latitude}&mlon=${longitude}#map=14/${latitude}/${longitude}`, "_blank");
    });
}

// Export CSV
if (exportBtn) {
    exportBtn.addEventListener("click", () => {
        let csv = "Report ID,Event,Location,Source,Score,Status,Time\n";
        reports.forEach(r => {
            csv += [
                r.id,
                `"${r.event}"`,
                `"${r.location}"`,
                `"${r.source}"`,
                r.score,
                getStatusLabel(r.status),
                `"${r.time}"`
            ].join(",") + "\n";
        });

        const blob = new Blob([csv], { type: "text/csv" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = "national-weather-reports.csv";
        link.click();
        URL.revokeObjectURL(url);
    });
}

/* =========================================================
   14. INITIAL LOAD
   ========================================================= */

window.loadAllReports = loadAllReports;
window.renderReports = renderReports;

loadAllReports();
updateSummaryStats();
console.log("Weather360 Admin Reports control room active.");