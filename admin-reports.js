/* ================= REPORT DATA ================= */

const reports = [

    {
        id: "WR-1001",
        event: "Heavy Rainfall",
        location: "Mumbai, Maharashtra",
        city: "Mumbai",
        source: "User Report",
        account: "verified",
        accountName: "Verified Account",
        score: 92,
        status: "verified",
        time: "2 min ago",

        description:
            "Heavy rainfall has caused waterlogging near the reported area. Traffic movement is becoming difficult.",

        reporter: "Anonymous Reporter",
        avatar: "AR",

        submitted:
            "Submitted today at 18:33 IST · 19.0404° N, 72.8610° E",

        hashtags: [
            "#rain",
            "#mumbai",
            "#waterlogging"
        ],

        latitude: 19.0404,
        longitude: 72.8610,

        attachment: "IMG_1001.jpg",

        windy: 15,
        imd: 30,
        local: 20,
        accountScore: 10,
        news: 10,

        match: 96,
        locationMatch: 97,
        imageIntegrity: 92,
        sourceAgreement: 94,
        confidence: "0.94",

        officialTitle: "IMD Supporting Data",
        officialText:
            "Official weather information supports heavy rainfall conditions in the reported area.",

        reason:
            "The reported location, timestamp and rainfall conditions are consistent with supporting independent sources.",

        aiStatus: "No issue detected"
    },


    {
        id: "WR-1002",
        event: "Flood",
        location: "Patna, Bihar",
        city: "Patna",
        source: "User Report",
        account: "new",
        accountName: "New Account",
        score: 57,
        status: "review",
        time: "5 min ago",

        description:
            "Flood water has entered the residential area and local movement is being affected.",

        reporter: "New Reporter",
        avatar: "NR",

        submitted:
            "Submitted today at 18:30 IST · 25.5941° N, 85.1376° E",

        hashtags: [
            "#flood",
            "#patna",
            "#rain"
        ],

        latitude: 25.5941,
        longitude: 85.1376,

        attachment: "PATNA_FLOOD_01.jpg",

        windy: 15,
        imd: -10,
        local: 20,
        accountScore: 2,
        news: 10,

        match: 72,
        locationMatch: 79,
        imageIntegrity: 88,
        sourceAgreement: 65,
        confidence: "0.76",

        officialTitle: "Limited Official Support",
        officialText:
            "Official data does not fully confirm the reported severity.",

        reason:
            "Some independent signals support the report, but official evidence is insufficient. Manual admin verification is required.",

        aiStatus: "No issue detected"
    },


    {
        id: "WR-1003",
        event: "Thunderstorm",
        location: "Hyderabad, Telangana",
        city: "Hyderabad",
        source: "Social Media",
        account: "verified",
        accountName: "Verified Account",
        score: 84,
        status: "verified",
        time: "8 min ago",

        description:
            "Strong thunderstorm activity and heavy winds have been reported across the local area.",

        reporter: "Social Media Source",
        avatar: "SM",

        submitted:
            "Collected today at 18:27 IST · 17.3850° N, 78.4867° E",

        hashtags: [
            "#thunderstorm",
            "#hyderabad",
            "#weather"
        ],

        latitude: 17.3850,
        longitude: 78.4867,

        attachment: "STORM_VIDEO.mp4",

        windy: 15,
        imd: 30,
        local: 20,
        accountScore: 10,
        news: 10,

        match: 91,
        locationMatch: 93,
        imageIntegrity: 90,
        sourceAgreement: 88,
        confidence: "0.91",

        officialTitle: "IMD Weather Report",
        officialText:
            "Weather conditions reported by the official source support thunderstorm activity.",

        reason:
            "The social report matches official weather conditions and independent local signals.",

        aiStatus: "No manipulation detected"
    },


    {
        id: "WR-1004",
        event: "Heavy Rainfall",
        location: "Kolkata, West Bengal",
        city: "Kolkata",
        source: "IMD + Local",
        account: "verified",
        accountName: "Verified Account",
        score: 94,
        status: "verified",
        time: "12 min ago",

        description:
            "Heavy rainfall is being reported across multiple locations in Kolkata.",

        reporter: "Weather Source",
        avatar: "WS",

        submitted:
            "Collected today at 18:23 IST · 22.5726° N, 88.3639° E",

        hashtags: [
            "#rain",
            "#kolkata",
            "#monsoon"
        ],

        latitude: 22.5726,
        longitude: 88.3639,

        attachment: "KOLKATA_RAIN.jpg",

        windy: 15,
        imd: 30,
        local: 20,
        accountScore: 10,
        news: 10,

        match: 98,
        locationMatch: 98,
        imageIntegrity: 95,
        sourceAgreement: 97,
        confidence: "0.97",

        officialTitle: "IMD + Local Reports",
        officialText:
            "Official weather information and multiple local reports support the event.",

        reason:
            "Multiple independent signals strongly agree with the reported weather event.",

        aiStatus: "No issue detected"
    },


    {
        id: "WR-1005",
        event: "Fog",
        location: "Delhi, Delhi",
        city: "Delhi",
        source: "User Report",
        account: "new",
        accountName: "New Account",
        score: 52,
        status: "review",
        time: "15 min ago",

        description:
            "Dense fog is reducing visibility on the reported road section.",

        reporter: "New Reporter",
        avatar: "NR",

        submitted:
            "Submitted today at 18:20 IST · 28.6139° N, 77.2090° E",

        hashtags: [
            "#fog",
            "#delhi",
            "#visibility"
        ],

        latitude: 28.6139,
        longitude: 77.2090,

        attachment: "DELHI_FOG.jpg",

        windy: 0,
        imd: 30,
        local: 20,
        accountScore: 2,
        news: 0,

        match: 75,
        locationMatch: 83,
        imageIntegrity: 81,
        sourceAgreement: 69,
        confidence: "0.74",

        officialTitle: "IMD Visibility Data",
        officialText:
            "Official visibility conditions partially support the report.",

        reason:
            "The event has supporting evidence, but additional verification is required.",

        aiStatus: "No issue detected"
    },


    {
        id: "WR-1006",
        event: "Cyclone",
        location: "Bhubaneswar, Odisha",
        city: "Bhubaneswar",
        source: "Social Media",
        account: "verified",
        accountName: "Verified Account",
        score: 89,
        status: "verified",
        time: "18 min ago",

        description:
            "Cyclonic weather conditions and strong winds are being reported in the region.",

        reporter: "Verified Source",
        avatar: "VS",

        submitted:
            "Collected today at 18:17 IST · 20.2961° N, 85.8245° E",

        hashtags: [
            "#cyclone",
            "#odisha",
            "#weather"
        ],

        latitude: 20.2961,
        longitude: 85.8245,

        attachment: "CYCLONE_REPORT.jpg",

        windy: 15,
        imd: 30,
        local: 20,
        accountScore: 10,
        news: 10,

        match: 94,
        locationMatch: 95,
        imageIntegrity: 91,
        sourceAgreement: 92,
        confidence: "0.93",

        officialTitle: "IMD Cyclone Data",
        officialText:
            "Official weather information supports cyclonic conditions.",

        reason:
            "Strong agreement between official weather data, source evidence and local reports.",

        aiStatus: "No issue detected"
    },


    {
        id: "WR-1007",
        event: "Heatwave",
        location: "Jaipur, Rajasthan",
        city: "Jaipur",
        source: "IMD",
        account: "verified",
        accountName: "Verified Account",
        score: 88,
        status: "verified",
        time: "24 min ago",

        description:
            "Extreme heat conditions have been reported in the area.",

        reporter: "Official Source",
        avatar: "IM",

        submitted:
            "Collected today at 18:11 IST · 26.9124° N, 75.7873° E",

        hashtags: [
            "#heatwave",
            "#jaipur",
            "#temperature"
        ],

        latitude: 26.9124,
        longitude: 75.7873,

        attachment: "HEATWAVE.jpg",

        windy: 15,
        imd: 30,
        local: 20,
        accountScore: 10,
        news: 10,

        match: 95,
        locationMatch: 96,
        imageIntegrity: 90,
        sourceAgreement: 94,
        confidence: "0.95",

        officialTitle: "IMD Official Report",
        officialText:
            "Official weather data confirms severe heat conditions.",

        reason:
            "The report is supported by official weather data and multiple signals.",

        aiStatus: "No issue detected"
    },


    {
        id: "WR-1008",
        event: "Heavy Rainfall",
        location: "Kochi, Kerala",
        city: "Kochi",
        source: "Social Media",
        account: "new",
        accountName: "New Account",
        score: 32,
        status: "unverified",
        time: "29 min ago",

        description:
            "Heavy rainfall is claimed in the reported area, but independent evidence is limited.",

        reporter: "New Social Account",
        avatar: "NS",

        submitted:
            "Collected today at 18:06 IST · 9.9312° N, 76.2673° E",

        hashtags: [
            "#rain",
            "#kochi"
        ],

        latitude: 9.9312,
        longitude: 76.2673,

        attachment: "KOCHI_RAIN.jpg",

        windy: 0,
        imd: -10,
        local: 0,
        accountScore: 2,
        news: 0,

        match: 42,
        locationMatch: 58,
        imageIntegrity: 62,
        sourceAgreement: 31,
        confidence: "0.55",

        officialTitle: "No Strong Official Support",
        officialText:
            "Available independent weather data does not sufficiently support the claim.",

        reason:
            "Insufficient supporting signals were found. The report is marked unverified.",

        aiStatus: "Needs further inspection"
    },


    {
        id: "WR-1009",
        event: "Flood",
        location: "Guwahati, Assam",
        city: "Guwahati",
        source: "User Report",
        account: "new",
        accountName: "New Account",
        score: 52,
        status: "review",
        time: "34 min ago",

        description:
            "Flooding has been reported around low-lying areas of the city.",

        reporter: "Local Reporter",
        avatar: "LR",

        submitted:
            "Submitted today at 18:01 IST · 26.1445° N, 91.7362° E",

        hashtags: [
            "#flood",
            "#guwahati",
            "#assam"
        ],

        latitude: 26.1445,
        longitude: 91.7362,

        attachment: "GUWAHATI_FLOOD.jpg",

        windy: 15,
        imd: -10,
        local: 20,
        accountScore: 2,
        news: 10,

        match: 73,
        locationMatch: 78,
        imageIntegrity: 86,
        sourceAgreement: 67,
        confidence: "0.72",

        officialTitle: "Mixed Weather Evidence",
        officialText:
            "Local reports support the event while official confirmation remains limited.",

        reason:
            "Conflicting signals require manual verification by the administrator.",

        aiStatus: "No issue detected"
    },


    {
        id: "WR-1010",
        event: "Heavy Snowfall",
        location: "Srinagar, Jammu & Kashmir",
        city: "Srinagar",
        source: "Social Media",
        account: "fraud",
        accountName: "Fraud Account",
        score: 27,
        status: "suspicious",
        time: "41 min ago",

        description:
            "A social media account has reported extreme snowfall in the area.",

        reporter: "Flagged Account",
        avatar: "FA",

        submitted:
            "Collected today at 17:54 IST · 34.0837° N, 74.7973° E",

        hashtags: [
            "#snowfall",
            "#srinagar",
            "#weather"
        ],

        latitude: 34.0837,
        longitude: 74.7973,

        attachment: "SNOWFALL.jpg",

        windy: 0,
        imd: -10,
        local: 0,
        accountScore: 0,
        news: 0,

        match: 28,
        locationMatch: 35,
        imageIntegrity: 39,
        sourceAgreement: 21,
        confidence: "0.41",

        officialTitle: "Conflicting Data",
        officialText:
            "Available evidence does not sufficiently support the reported event.",

        reason:
            "The report has weak supporting evidence and originates from a flagged account.",

        aiStatus: "Potentially manipulated"
    }

];


/* ================= DOM ================= */

const tableBody = document.getElementById("reportsTableBody");
const emptyState = document.getElementById("emptyState");

const searchInput = document.getElementById("searchInput");
const filterButtons = document.querySelectorAll(".filter-btn");

const locationFilter = document.getElementById("locationFilter");
const resetFilters = document.getElementById("resetFilters");

const totalReports = document.getElementById("totalReports");
const verifiedReports = document.getElementById("verifiedReports");
const reviewReports = document.getElementById("reviewReports");
const unverifiedReports = document.getElementById("unverifiedReports");

const detailCard = document.getElementById("reportDetailCard");
const adminActions = document.getElementById("adminActions");

let currentStatus = "all";
let selectedReport = null;

let detailMap = null;
let detailMarker = null;


/* ================= HELPERS ================= */

function getScoreClass(score) {

    if (score >= 75) return "good";
    if (score >= 35) return "review";

    return "bad";
}


function getStatusLabel(status) {

    if (status === "verified") return "Verified";
    if (status === "review") return "Admin Review";
    if (status === "unverified") return "Unverified";

    return "Suspicious";
}


function getAccountLabel(account) {

    if (account === "verified") return "Verified";
    if (account === "new") return "New Account";

    return "Fraud";
}


/* ================= SUMMARY ================= */

function updateSummary() {

    totalReports.textContent = reports.length;

    verifiedReports.textContent =
        reports.filter(r => r.status === "verified").length;

    reviewReports.textContent =
        reports.filter(r => r.status === "review").length;

    unverifiedReports.textContent =
        reports.filter(
            r => r.status === "unverified" || r.status === "suspicious"
        ).length;
}


/* ================= TABLE ================= */

function renderReports() {

    const searchValue =
        searchInput.value.toLowerCase().trim();

    const selectedLocation =
        locationFilter.value;


    const filtered = reports.filter(report => {

        const matchesStatus =
            currentStatus === "all" ||
            report.status === currentStatus;


        const searchableText = `
            ${report.id}
            ${report.event}
            ${report.location}
            ${report.source}
            ${report.accountName}
        `.toLowerCase();

        const matchesSearch =
            searchableText.includes(searchValue);


        const matchesLocation =
            selectedLocation === "all" ||
            report.city === selectedLocation;


        return (
            matchesStatus &&
            matchesSearch &&
            matchesLocation
        );

    });


    tableBody.innerHTML = "";


    if (filtered.length === 0) {

        emptyState.style.display = "block";

        return;
    }


    emptyState.style.display = "none";


    filtered.forEach(report => {

        const row = document.createElement("tr");

        row.innerHTML = `

            <td>
                <span class="report-id">
                    ${report.id}
                </span>
            </td>


            <td>
                <span class="event-name">
                    ${report.event}
                </span>
            </td>


            <td>
                <span class="location-cell">
                    <i class="fa-solid fa-location-dot"></i>
                    ${report.city}
                </span>
            </td>


            <td>
                <span class="source-cell">
                    ${report.source}
                </span>
            </td>


            <td>
                <span class="account-badge ${report.account}">
                    ${getAccountLabel(report.account)}
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
            </td>


            <td>
                ${report.time}
            </td>

        `;


        row.addEventListener("click", () => {

            openReportDetail(report);

        });


        tableBody.appendChild(row);

    });

}


/* ================= REPORT DETAIL ================= */

function openReportDetail(report) {

    selectedReport = report;

    detailCard.classList.add("show");


    /* HEADER */

    document.getElementById("detailTitle").textContent =
        `${report.event} — ${report.city}`;

    document.getElementById("detailSubtitle").textContent =
        `${report.id} · Incoming weather report`;

    document.getElementById("detailSource").textContent =
        report.source;


    /* ORIGINAL REPORT */

    document.getElementById("detailDescription").textContent =
        `"${report.description}"`;

    document.getElementById("detailReporter").textContent =
        report.reporter;

    document.getElementById("reporterAvatar").textContent =
        report.avatar;

    document.getElementById("detailSubmitted").textContent =
        report.submitted;


    const hashtags =
        document.getElementById("detailHashtags");

    hashtags.innerHTML = "";

    report.hashtags.forEach(tag => {

        const span = document.createElement("span");

        span.className = "hashtag";
        span.textContent = tag;

        hashtags.appendChild(span);

    });


    /* CROSS REFERENCE */

    document.getElementById("crossCitizen").textContent =
        report.event;

    document.getElementById("crossCitizenText").textContent =
        report.description;

    document.getElementById("crossOfficial").textContent =
        report.officialTitle;

    document.getElementById("crossOfficialText").textContent =
        report.officialText;

    document.getElementById("matchBadge").textContent =
        `${report.match}% Match`;


    /* REASONING */

    document.getElementById("locationMatch").textContent =
        report.locationMatch;

    document.getElementById("imageIntegrity").textContent =
        report.imageIntegrity;

    document.getElementById("sourceAgreement").textContent =
        report.sourceAgreement;

    document.getElementById("modelConfidence").textContent =
        report.confidence;


    document.getElementById("locationProgress").style.width =
        `${report.locationMatch}%`;

    document.getElementById("imageProgress").style.width =
        `${report.imageIntegrity}%`;

    document.getElementById("sourceProgress").style.width =
        `${report.sourceAgreement}%`;

    document.getElementById("reasonText").textContent =
        report.reason;


    /* SIGNAL BREAKDOWN */

    document.getElementById("windyScore").textContent =
        formatScore(report.windy);

    document.getElementById("imdScore").textContent =
        formatScore(report.imd);

    document.getElementById("localScore").textContent =
        formatScore(report.local);

    document.getElementById("accountSignalScore").textContent =
        formatScore(report.accountScore);

    document.getElementById("newsScore").textContent =
        formatScore(report.news);


    document.getElementById("accountSignalText").textContent =
        getAccountSignalText(report.account);


    document.getElementById("detailScore").textContent =
        report.score;


    document.getElementById("detailScoreBar").style.width =
        `${Math.min(report.score, 100)}%`;


    /* LOCATION */

    document.getElementById("detailLocation").textContent =
        report.location;

    document.getElementById("detailCoordinates").textContent =
        `${report.latitude.toFixed(4)}° N, ${report.longitude.toFixed(4)}° E`;


    /* ATTACHMENT */

    document.getElementById("attachmentName").textContent =
        report.attachment;

    document.getElementById("gpsStatus").textContent =
        "Available";

    document.getElementById("metadataTime").textContent =
        "Available";

    document.getElementById("aiStatus").textContent =
        report.aiStatus;


    /* ACCOUNT */

    const accountDot =
        document.getElementById("accountStatusDot");

    accountDot.className =
        `account-status-dot ${report.account}`;

    document.getElementById("detailAccountStatus").textContent =
        report.accountName;

    document.getElementById("accountStatusDescription").textContent =
        getAccountDescription(report.account);


    /* FINAL DECISION */


const detailDecision = document.getElementById("detailDecision");
const decisionText = document.getElementById("decisionText");
const decisionDescription = document.getElementById("decisionDescription");

detailDecision.className = `detail-status ${report.status}`;
detailDecision.textContent = getStatusLabel(report.status).toUpperCase();
decisionText.textContent = getStatusLabel(report.status).toUpperCase();

if (report.status === "verified") {

    decisionDescription.textContent =
        "Report has been verified by the administrator and can be shown on the platform.";

    adminActions.classList.remove("show");

} else if (report.status === "review") {

    decisionDescription.textContent =
        "Report requires manual administrator verification before final publication.";

    adminActions.classList.add("show");

} else if (report.status === "suspicious") {

    decisionDescription.textContent =
        "Report has been flagged as suspicious by the administrator and should not be shown.";

    adminActions.classList.remove("show");

} else {

    decisionDescription.textContent =
        "Report does not meet the verification threshold and should not be shown.";

    adminActions.classList.remove("show");
}


    /* MAP */

    initializeDetailMap(
        report.latitude,
        report.longitude,
        report.city
    );


    /* SCROLL */

    setTimeout(() => {

        detailCard.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });

    }, 100);

}

/* ================= SCORE HELPERS ================= */

function formatScore(value) {

    if (value > 0) return `+${value}`;

    return `${value}`;
}


function getAccountSignalText(account) {

    if (account === "verified") {
        return "Verified account";
    }

    if (account === "new") {
        return "New account · first post";
    }

    return "Fraud account";
}


function getAccountDescription(account) {

    if (account === "verified") {
        return "Trusted source";
    }

    if (account === "new") {
        return "New account";
    }

    return "Flagged / fraud source";
}


/* ================= MAP ================= */

function initializeDetailMap(lat, lng, city) {

    if (!detailMap) {

        detailMap = L.map("detailMap", {
            zoomControl: true
        }).setView([lat, lng], 11);


        L.tileLayer(
            "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            {
                attribution: "&copy; OpenStreetMap contributors"
            }
        ).addTo(detailMap);


        detailMarker =
            L.marker([lat, lng])
                .addTo(detailMap);

    }

    else {

        detailMap.setView(
            [lat, lng],
            11
        );

        detailMarker.setLatLng([
            lat,
            lng
        ]);

    }


    detailMarker
        .bindPopup(
            `<strong>${city}</strong><br>
             ${lat.toFixed(4)}° N,
             ${lng.toFixed(4)}° E`
        )
        .openPopup();


    setTimeout(() => {

        detailMap.invalidateSize();

    }, 200);

}


/* ================= OPEN MAP ================= */

document
    .getElementById("openMapBtn")
    .addEventListener("click", () => {

        if (!selectedReport) return;

        const {
            latitude,
            longitude
        } = selectedReport;


        const mapUrl =
            `https://www.openstreetmap.org/?mlat=${latitude}&mlon=${longitude}#map=14/${latitude}/${longitude}`;


        window.open(
            mapUrl,
            "_blank"
        );

    });


/* ================= FILTER ================= */

filterButtons.forEach(button => {

    button.addEventListener("click", () => {

        filterButtons.forEach(btn => {
            btn.classList.remove("active");
        });

        button.classList.add("active");

        currentStatus =
            button.dataset.status;

        renderReports();

    });

});


searchInput.addEventListener(
    "input",
    renderReports
);


locationFilter.addEventListener(
    "change",
    renderReports
);


/* ================= RESET ================= */

resetFilters.addEventListener("click", () => {

    searchInput.value = "";

    locationFilter.value = "all";

    currentStatus = "all";

    filterButtons.forEach(btn => {
        btn.classList.remove("active");
    });

    document
        .querySelector('[data-status="all"]')
        .classList.add("active");

    renderReports();

});


/* ================= CLOSE DETAIL ================= */

document
    .getElementById("closeDetail")
    .addEventListener("click", () => {

        detailCard.classList.remove("show");

        selectedReport = null;

    });


/* ================= EXPORT CSV ================= */

document
    .getElementById("exportBtn")
    .addEventListener("click", () => {

        let csv =
            "Report ID,Event,Location,Source,Account,Score,Status,Time\n";


        reports.forEach(report => {

            csv += [
                report.id,
                `"${report.event}"`,
                `"${report.location}"`,
                `"${report.source}"`,
                report.accountName,
                report.score,
                getStatusLabel(report.status),
                report.time
            ].join(",") + "\n";

        });


        const blob =
            new Blob([csv], {
                type: "text/csv"
            });


        const url =
            URL.createObjectURL(blob);


        const link =
            document.createElement("a");

        link.href = url;
        link.download = "weather-reports.csv";

        link.click();

        URL.revokeObjectURL(url);

    });



/* ================= THEME ================= */

const themeToggle =
    document.getElementById("themeToggle");


function applyTheme() {

    const savedTheme =
        localStorage.getItem("weather360-theme");


    if (savedTheme === "light") {

        document.body.classList.add("light");

        themeToggle.innerHTML =
            '<i class="fa-solid fa-sun"></i>';

    }

    else {

        document.body.classList.remove("light");

        themeToggle.innerHTML =
            '<i class="fa-solid fa-moon"></i>';

    }

}


themeToggle.addEventListener(
    "click",
    () => {

        document.body.classList.toggle("light");


        const isLight =
            document.body.classList.contains("light");


        localStorage.setItem(
            "weather360-theme",
            isLight ? "light" : "dark"
        );


        themeToggle.innerHTML =
            isLight
                ? '<i class="fa-solid fa-sun"></i>'
                : '<i class="fa-solid fa-moon"></i>';

    }
);


/* ================= LIVE TIME ================= */

function updateTime() {

    const now = new Date();

    const time =
        now.toLocaleTimeString(
            "en-IN",
            {
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit"
            }
        );

    document.getElementById(
        "lastUpdated"
    ).textContent =
        `Live · ${time}`;

}


setInterval(
    updateTime,
    1000
);


/* ================= INITIALIZE ================= */

applyTheme();

updateTime();

updateSummary();

renderReports();

/* ================= ADMIN REVIEW ACTIONS ================= */

verifyReportBtn.onclick = function () {

    if (!selectedReport) return;

    if (selectedReport.status !== "review") return;

    selectedReport.status = "verified";

    updateSummary();
    renderReports();
    openReportDetail(selectedReport);
};


fraudReportBtn.onclick = function () {

    if (!selectedReport) return;

    if (selectedReport.status !== "review") return;

    selectedReport.status = "suspicious";

    updateSummary();
    renderReports();
    openReportDetail(selectedReport);
};

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