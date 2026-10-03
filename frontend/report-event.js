/* =========================================================
   WEATHER XPOSE - REPORT EVENT JS
   ========================================================= */


/* =========================================================
   1. THEME
   ========================================================= */

const themeToggle = document.getElementById("themeToggle");


function updateThemeIcon(isDark) {

    if (!themeToggle) return;

    const icon = themeToggle.querySelector("i");

    if (!icon) return;

    if (isDark) {

        icon.className = "fa-solid fa-sun";

    } else {

        icon.className = "fa-solid fa-moon";
    }
}


const savedTheme =
    localStorage.getItem("weatherxpose-theme");


if (savedTheme === "dark") {

    document.body.classList.add("dark-mode");

    updateThemeIcon(true);

} else {

    updateThemeIcon(false);
}


if (themeToggle) {

    themeToggle.addEventListener("click", () => {

        document.body.classList.toggle("dark-mode");

        const isDark =
            document.body.classList.contains("dark-mode");

        localStorage.setItem(
            "weatherxpose-theme",
            isDark ? "dark" : "light"
        );

        updateThemeIcon(isDark);

    });
}



/* =========================================================
   2. ELEMENTS
   ========================================================= */

const citySelect =
    document.getElementById("city");

const stateInput =
    document.getElementById("state");

const latitudeInput =
    document.getElementById("latitude");

const longitudeInput =
    document.getElementById("longitude");

const localityInput =
    document.getElementById("locality");

const currentLocationBtn =
    document.getElementById("currentLocationBtn");

const centerMarkerBtn =
    document.getElementById("centerMarkerBtn");



/* =========================================================
   3. CITY COORDINATES & STATES
   ========================================================= */

const cityCoordinates = {

    Kolkata: {
        lat: 22.5726,
        lng: 88.3639,
        state: "West Bengal"
    },

    Mumbai: {
        lat: 19.0760,
        lng: 72.8777,
        state: "Maharashtra"
    },

    Delhi: {
        lat: 28.6139,
        lng: 77.2090,
        state: "Delhi"
    },

    Ahmedabad: {
        lat: 23.0225,
        lng: 72.5714,
        state: "Gujarat"
    },

    Jaipur: {
        lat: 26.9124,
        lng: 75.7873,
        state: "Rajasthan"
    },

    Lucknow: {
        lat: 26.8467,
        lng: 80.9462,
        state: "Uttar Pradesh"
    },

    Patna: {
        lat: 25.5941,
        lng: 85.1376,
        state: "Bihar"
    },

    Bhubaneswar: {
        lat: 20.2961,
        lng: 85.8245,
        state: "Odisha"
    },

    Guwahati: {
        lat: 26.1445,
        lng: 91.7362,
        state: "Assam"
    },

    Chennai: {
        lat: 13.0827,
        lng: 80.2707,
        state: "Tamil Nadu"
    },

    Bengaluru: {
        lat: 12.9716,
        lng: 77.5946,
        state: "Karnataka"
    },

    Hyderabad: {
        lat: 17.3850,
        lng: 78.4867,
        state: "Telangana"
    }
};



/* =========================================================
   4. MAP
   ========================================================= */

const reportMap =
    L.map("reportMap", {

        zoomControl: true,

        minZoom: 4,

        maxZoom: 18

    });


reportMap.setView(
    [22.5726, 88.3639],
    11
);


L.tileLayer(
    "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    {
        attribution:
            "&copy; OpenStreetMap contributors",

        maxZoom: 19
    }
).addTo(reportMap);



/* =========================================================
   5. MARKER
   ========================================================= */

let reportMarker = null;


function createReportMarker(lat, lng) {

    if (reportMarker) {

        reportMap.removeLayer(reportMarker);
    }


    reportMarker =
        L.marker([lat, lng], {

            draggable: true

        }).addTo(reportMap);


    reportMarker.bindPopup(
        "<strong>Reported Incident Location</strong>"
    );


    reportMarker.on("dragend", function () {

        const position =
            reportMarker.getLatLng();

        latitudeInput.value =
            position.lat.toFixed(4);

        longitudeInput.value =
            position.lng.toFixed(4);

    });

}



/* Initial Kolkata marker */

createReportMarker(
    22.5726,
    88.3639
);

if (stateInput && (!stateInput.value || stateInput.value.toLowerCase() === "india")) {
    stateInput.value = "West Bengal";
}



/* =========================================================
   6. CITY CHANGE
   ========================================================= */

if (citySelect) {

    citySelect.addEventListener(
        "change",
        function () {

            const city =
                this.value;

            if (!city) return;


            const coordinates =
                cityCoordinates[city];

            if (!coordinates) return;

            if (stateInput && coordinates.state) {
                stateInput.value = coordinates.state;
            }

            latitudeInput.value =
                coordinates.lat.toFixed(4);

            longitudeInput.value =
                coordinates.lng.toFixed(4);


            reportMap.setView(
                [
                    coordinates.lat,
                    coordinates.lng
                ],
                11
            );


            createReportMarker(
                coordinates.lat,
                coordinates.lng
            );

            runPreChecks();

        }
    );
}



/* =========================================================
   7. CENTER MARKER
   ========================================================= */

if (centerMarkerBtn) {

    centerMarkerBtn.addEventListener(
        "click",
        () => {

            const lat =
                parseFloat(latitudeInput.value);

            const lng =
                parseFloat(longitudeInput.value);


            if (
                Number.isNaN(lat) ||
                Number.isNaN(lng)
            ) {

                alert(
                    "Please enter valid latitude and longitude."
                );

                return;
            }


            reportMap.setView(
                [lat, lng],
                14
            );


            createReportMarker(
                lat,
                lng
            );

        }
    );
}



/* =========================================================
   8. CURRENT LOCATION
   ========================================================= */

if (currentLocationBtn) {

    currentLocationBtn.addEventListener(
        "click",
        () => {

            if (!navigator.geolocation) {

                alert(
                    "Geolocation is not supported by your browser."
                );

                return;
            }


            currentLocationBtn.innerHTML = `
                <i class="fa-solid fa-spinner fa-spin"></i>
                Detecting Location...
            `;


            navigator.geolocation.getCurrentPosition(

                async (position) => {

                    const lat =
                        position.coords.latitude;

                    const lng =
                        position.coords.longitude;


                    latitudeInput.value =
                        lat.toFixed(4);

                    longitudeInput.value =
                        lng.toFixed(4);


                    reportMap.setView(
                        [lat, lng],
                        15
                    );


                    createReportMarker(
                        lat,
                        lng
                    );

                    // Auto-resolve city and state using backend reverse-geocoding
                    try {
                        let res = null;
                        const token = localStorage.getItem("weatherxpose-token") || "";
                        const raw = await fetch("/api/auth/resolve-location", {
                            method: "POST",
                            headers: {
                                "Content-Type": "application/json",
                                ...(token ? { "Authorization": `Bearer ${token}` } : {})
                            },
                            body: JSON.stringify({ latitude: lat, longitude: lng })
                        });
                        if (raw.ok) {
                            res = await raw.json();
                        }

                        if (res) {
                            if (res.state && stateInput) {
                                stateInput.value = res.state;
                            }
                            if (res.city && citySelect) {
                                let matched = false;
                                for (let opt of citySelect.options) {
                                    if (opt.value.toLowerCase() === res.city.toLowerCase() || opt.text.toLowerCase().includes(res.city.toLowerCase())) {
                                        citySelect.value = opt.value;
                                        matched = true;
                                        break;
                                    }
                                }
                                if (!matched) {
                                    const newOpt = document.createElement("option");
                                    newOpt.value = res.city;
                                    newOpt.textContent = `${res.city}, ${res.state || 'India'}`;
                                    newOpt.selected = true;
                                    citySelect.appendChild(newOpt);
                                }
                            }
                            if (localityInput && res.suburb && !localityInput.value.trim()) {
                                localityInput.value = res.suburb;
                            }
                        }
                    } catch (geoErr) {
                        console.warn("[report-event] Auto-resolve location error:", geoErr);
                    }

                    currentLocationBtn.innerHTML = `
                        <i class="fa-solid fa-location-dot"></i>
                        Location Detected
                    `;

                },


                () => {

                    alert(
                        "Unable to access your current location. Please allow location permission or enter the location manually."
                    );


                    currentLocationBtn.innerHTML = `
                        <i class="fa-solid fa-crosshairs"></i>
                        Use My Current Location
                    `;

                },

                {
                    enableHighAccuracy: true,

                    timeout: 10000,

                    maximumAge: 0
                }

            );

        }
    );
}



/* =========================================================
   9. FILE UPLOAD
   ========================================================= */

const mediaFile =
    document.getElementById("mediaFile");

const selectedFile =
    document.getElementById("selectedFile");

const fileName =
    document.getElementById("fileName");

const fileSize =
    document.getElementById("fileSize");

const removeFile =
    document.getElementById("removeFile");

const uploadBox =
    document.getElementById("uploadBox");



function formatFileSize(bytes) {

    if (bytes < 1024) {

        return bytes + " B";
    }


    if (bytes < 1024 * 1024) {

        return (
            (bytes / 1024).toFixed(1)
            + " KB"
        );
    }


    return (
        (bytes / (1024 * 1024)).toFixed(2)
        + " MB"
    );
}



if (mediaFile) {

    mediaFile.addEventListener(
        "change",
        function () {

            const file =
                this.files[0];

            if (!file) return;


            fileName.textContent =
                file.name;

            fileSize.textContent =
                formatFileSize(file.size);


            selectedFile.classList.add(
                "show"
            );


            updateMetadata(file);

            runPreChecks();

        }
    );
}



/* Remove file */

if (removeFile) {

    removeFile.addEventListener(
        "click",
        () => {

            mediaFile.value = "";

            selectedFile.classList.remove(
                "show"
            );


            fileName.textContent =
                "No file selected";

            fileSize.textContent =
                "No evidence attached (Optional)";


            document.getElementById(
                "metadataFile"
            ).textContent =
                "Not available";


            document.getElementById(
                "metadataTime"
            ).textContent =
                "Not available";

            const metadataFingerprintEl = document.getElementById("metadataFingerprint");
            if (metadataFingerprintEl) {
                metadataFingerprintEl.textContent = "Not available";
            }


            setStatus(
                "metadataStatus",
                "OPTIONAL (NO FILE)"
            );

            setStatus(
                "aiStatus",
                "OPTIONAL (NO FILE)"
            );

        }
    );
}



/* =========================================================
   10. METADATA
   ========================================================= */

function updateMetadata(file) {

    const metadataFile =
        document.getElementById(
            "metadataFile"
        );


    const metadataTime =
        document.getElementById(
            "metadataTime"
        );


    const metadataDevice =
        document.getElementById(
            "metadataDevice"
        );


    metadataFile.textContent =
        `${file.type || "Unknown"} · ${formatFileSize(file.size)}`;

    const metadataFingerprintEl = document.getElementById("metadataFingerprint");
    if (metadataFingerprintEl) {
        metadataFingerprintEl.textContent = "Pending submission scan";
    }


    const modified =
        new Date(file.lastModified);


    metadataTime.textContent =
        modified.toLocaleString(
            "en-IN",
            {
                day: "2-digit",
                month: "short",
                year: "numeric",
                hour: "2-digit",
                minute: "2-digit"
            }
        );


    metadataDevice.textContent =
        "Browser upload";


    const lat =
        latitudeInput.value;

    const lng =
        longitudeInput.value;


    if (lat && lng) {

        document.getElementById(
            "metadataGps"
        ).textContent =
            `${lat}° N, ${lng}° E`;

    }

}



/* =========================================================
   11. UPDATE GPS METADATA
   ========================================================= */

function updateGpsMetadata() {

    const lat =
        latitudeInput.value;

    const lng =
        longitudeInput.value;


    const gpsElement =
        document.getElementById(
            "metadataGps"
        );


    if (lat && lng) {

        gpsElement.textContent =
            `${lat}° N, ${lng}° E`;

    } else {

        gpsElement.textContent =
            "Not available";
    }

}


latitudeInput.addEventListener(
    "input",
    updateGpsMetadata
);


longitudeInput.addEventListener(
    "input",
    updateGpsMetadata
);



/* =========================================================
   12. VERIFICATION STATUS
   ========================================================= */

function setStatus(id, status) {
    const element = document.getElementById(id);
    if (!element) return;

    element.classList.remove("passed", "failed");
    element.textContent = status;

    if (status === "PASSED" || status === "RESOLVED") {
        element.classList.add("passed");
        element.style.color = "#10b981";
    } else if (status.includes("AI DETECTED") || status.includes("FAIL") || status.includes("REJECTED")) {
        element.classList.add("failed");
        element.style.color = "#ef4444";
        element.style.fontWeight = "bold";
    } else if (status.includes("ANALYZING") || status.includes("SCANNING") || status.includes("CHECKING")) {
        element.style.color = "#3b82f6";
    } else if (status.includes("OPTIONAL") || status.includes("SKIPPED") || status.includes("N/A")) {
        element.style.color = "#94a3b8";
    } else {
        element.style.color = "#f59e0b";
    }
}


/* =========================================================
   13. PRE-CHECK
   ========================================================= */

function runPreChecks() {
    const hasMedia = mediaFile && mediaFile.files && mediaFile.files.length > 0;

    setTimeout(() => {
        if (hasMedia) {
            setStatus("metadataStatus", "FILE LOADED");
        } else {
            setStatus("metadataStatus", "OPTIONAL (NO FILE)");
        }
    }, 300);

    setTimeout(() => {
        const lat = latitudeInput ? latitudeInput.value : "";
        const lng = longitudeInput ? longitudeInput.value : "";
        if (lat && lng) {
            setStatus("locationStatus", "RESOLVED");
        } else {
            setStatus("locationStatus", "PENDING");
        }
    }, 600);

    setTimeout(() => {
        if (hasMedia) {
            setStatus("aiStatus", "READY FOR SCAN");
        } else {
            setStatus("aiStatus", "OPTIONAL (NO FILE)");
        }
    }, 800);
}



/* Auto-detect incident type from description */
const incidentDescEl = document.getElementById("incidentDescription");
const eventTypeEl = document.getElementById("eventType");
if (incidentDescEl && eventTypeEl) {
    incidentDescEl.addEventListener("input", () => {
        const text = incidentDescEl.value.toLowerCase();
        if (text.includes("earthquake") || text.includes("earth quack") || text.includes("tremor") || text.includes("seismic")) {
            eventTypeEl.value = "Earthquake";
        } else if (text.includes("landslide") || text.includes("mudslide")) {
            eventTypeEl.value = "Landslide";
        } else if (text.includes("cyclone") || text.includes("typhoon")) {
            eventTypeEl.value = "Cyclone";
        }
    });
}

/* =========================================================
   14. SUBMIT REPORT
   ========================================================= */

const submitReportBtn =
    document.getElementById(
        "submitReportBtn"
    );


if (submitReportBtn) {

    submitReportBtn.addEventListener(
        "click",
        () => {

            let eventType =
                document.getElementById(
                    "eventType"
                ).value;


            const description =
                document.getElementById(
                    "incidentDescription"
                ).value.trim();

            // Override generic/mismatched dropdown if description explicitly describes an earthquake or landslide
            const descLower = description.toLowerCase();
            if (descLower.includes("earthquake") || descLower.includes("earth quack") || descLower.includes("tremor") || descLower.includes("seismic")) {
                eventType = "Earthquake";
                if (eventTypeEl) eventTypeEl.value = "Earthquake";
            } else if (descLower.includes("landslide") || descLower.includes("mudslide")) {
                eventType = "Landslide";
                if (eventTypeEl) eventTypeEl.value = "Landslide";
            }


            const city =
                citySelect.value;


            const date =
                document.getElementById(
                    "incidentDate"
                ).value;


            const time =
                document.getElementById(
                    "incidentTime"
                ).value;


            const platform =
                document.getElementById(
                    "sourcePlatform"
                ).value.trim();


            const userId =
                document.getElementById(
                    "sourceUserId"
                ).value.trim();



            /* Required validation */

            if (!eventType) {

                alert(
                    "Please select an event type."
                );

                return;
            }


            if (!description) {

                alert(
                    "Please enter an incident description."
                );

                return;
            }


            if (!city) {

                alert(
                    "Please select the incident location."
                );

                return;
            }


            if (!date) {

                alert(
                    "Please enter the incident date."
                );

                return;
            }


            if (!platform) {

                alert(
                    "Please enter the source / platform."
                );

                return;
            }


            if (!userId) {

                alert(
                    "Please enter the User ID / username."
                );

                return;
            }



            /* Real Backend API Submission */
            submitReportBtn.disabled = true;
            submitReportBtn.innerHTML = `
                <i class="fa-solid fa-spinner fa-spin"></i>
                Running Truth Verification Engine...
            `;

            // Update pre-checks to running state
            const hasMedia = mediaFile && mediaFile.files && mediaFile.files.length > 0;
            setStatus("metadataStatus", hasMedia ? "ANALYZING" : "SKIPPED (NO FILE)");
            setStatus("locationStatus", "CHECKING");
            setStatus("aiStatus", hasMedia ? "SCANNING" : "SKIPPED (NO FILE)");

            const formData = new FormData();
            formData.append("report_text", description);
            formData.append("city", city);
            const resolvedState = (stateInput && stateInput.value.trim()) ||
                                  (cityCoordinates[city] ? cityCoordinates[city].state : null);
            if (resolvedState && resolvedState.toLowerCase() !== "india") {
                formData.append("state", resolvedState);
            }
            if (latitudeInput && latitudeInput.value.trim()) {
                formData.append("latitude", latitudeInput.value.trim());
            }
            if (longitudeInput && longitudeInput.value.trim()) {
                formData.append("longitude", longitudeInput.value.trim());
            }
            formData.append("event_type", eventType);
            const incidentDateTime = time ? `${date} ${time}` : date;
            formData.append("incident_time", incidentDateTime);
            formData.append("platform", platform || "Citizen");
            formData.append("source_username", userId || "citizen_user");

            if (hasMedia) {
                formData.append("media_file", mediaFile.files[0]);
            }

            apiUpload("/api/citizen-report", formData)
                .then(res => {
                    const data = res.data || {};
                    const score = data.verification_score !== undefined ? Number(data.verification_score).toFixed(1) : "N/A";
                    const statusVal = data.verification_status || "Othentic";
                    const isAi = !!data.is_ai_generated;

                    // Update pre-check boxes
                    setStatus("metadataStatus", hasMedia ? "PASSED" : "N/A (TEXT ONLY)");
                    setStatus("locationStatus", "PASSED");
                    setStatus("aiStatus", hasMedia ? (isAi ? "AI DETECTED" : "PASSED") : "N/A (NO MEDIA)");

                    // Update forensic fingerprint in Section E
                    const metaFp = document.getElementById("metadataFingerprint");
                    if (metaFp) {
                        if (hasMedia) {
                            if (isAi) {
                                metaFp.innerHTML = `<span style="color: #ef4444; font-weight: 700;"><i class="fa-solid fa-triangle-exclamation"></i> AI Synthetic Fingerprint (${Math.round((data.ai_confidence || 0.9) * 100)}%)</span>`;
                                metaFp.title = data.ai_reason || "Synthetic latent grid pattern / canonical dimensions";
                            } else {
                                metaFp.innerHTML = `<span style="color: #10b981; font-weight: 700;"><i class="fa-solid fa-circle-check"></i> Authentic Optical Fingerprint</span>`;
                                metaFp.title = data.ai_reason || "Natural optical sensor noise verified";
                            }
                        } else {
                            metaFp.textContent = "N/A (No Media Attached)";
                        }
                    }

                    // Render Live Verification Card
                    const resultCard = document.getElementById("liveVerificationResult");
                    const statusBadge = document.getElementById("liveResultStatus");
                    const scoreEl = document.getElementById("liveResultScore");
                    const breakdownEl = document.getElementById("liveResultBreakdown");

                    if (resultCard) {
                        resultCard.style.display = "block";
                        scoreEl.textContent = score;

                        if (statusVal === "Othentic" || statusVal === "Approved") {
                            statusBadge.textContent = "VERIFIED (AUTHENTIC)";
                            statusBadge.style.background = "#10b981";
                            scoreEl.style.color = "#10b981";
                        } else if (statusVal === "Underprocess" || statusVal === "On hold") {
                            statusBadge.textContent = "UNDER HUMAN REVIEW";
                            statusBadge.style.background = "#f59e0b";
                            scoreEl.style.color = "#f59e0b";
                        } else {
                            statusBadge.textContent = "DISINFORMATION / FAKE";
                            statusBadge.style.background = "#ef4444";
                            scoreEl.style.color = "#ef4444";
                        }

                        if (data.hint_breakdown && Array.isArray(data.hint_breakdown)) {
                            const pills = data.hint_breakdown.map(h => 
                                `<span style="display:inline-block; margin: 3px 4px 3px 0; padding: 2px 7px; border-radius: 4px; background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.15);">
                                    <strong>${h.source || h.signal || 'Signal'}:</strong> ${h.points || h.score || 0} pts
                                </span>`
                            ).join("");
                            breakdownEl.innerHTML = pills || "Multi-signal evaluation stored in database.";
                        } else {
                            breakdownEl.textContent = data.summary_reason || "Analyzed against IMD, Windy & forensic telemetry.";
                        }
                    }

                    submitReportBtn.disabled = false;
                    submitReportBtn.innerHTML = `
                        <i class="fa-solid fa-check"></i>
                        Report Verified & Submitted!
                    `;

                    showNotice(`Report #${data.report_id || ''} processed! Status: ${statusVal} (${score}/100)`, "success");

                    setTimeout(() => {
                        submitReportBtn.innerHTML = `
                            <i class="fa-solid fa-paper-plane"></i>
                            Submit Another Report
                        `;
                    }, 4000);
                })
                .catch(err => {
                    console.error("Submission error:", err);
                    submitReportBtn.disabled = false;
                    submitReportBtn.innerHTML = `
                        <i class="fa-solid fa-paper-plane"></i>
                        Submit Report for Verification
                    `;
                    showNotice(err.message || "Failed to submit report. Please try again.", "error");
                });

        }
    );
}



/* =========================================================
   15. SET DEFAULT DATE & TIME
   ========================================================= */

const incidentDate =
    document.getElementById(
        "incidentDate"
    );

const incidentTime =
    document.getElementById(
        "incidentTime"
    );


const now =
    new Date();


if (incidentDate) {

    incidentDate.value =
        now.toISOString()
            .split("T")[0];
}


if (incidentTime) {

    const hours =
        String(
            now.getHours()
        ).padStart(2, "0");


    const minutes =
        String(
            now.getMinutes()
        ).padStart(2, "0");


    incidentTime.value =
        `${hours}:${minutes}`;
}



/* =========================================================
   16. MAP RESIZE
   ========================================================= */

setTimeout(() => {

    reportMap.invalidateSize();

}, 300);



/* =========================================================
   17. USER AUTH SESSION AUTO-POPULATION
   ========================================================= */

const loggedInRole = localStorage.getItem("weatherxpose-user-role");
const loggedInUserName = localStorage.getItem("weatherxpose-user-name");
const loggedInUserEmail = localStorage.getItem("weatherxpose-user-email");

const headerUserName = document.getElementById("headerUserName");
const headerAvatar = document.querySelector(".header-avatar");
const sourceUserId = document.getElementById("sourceUserId");

if (loggedInUserName) {
    if (headerUserName) headerUserName.textContent = loggedInUserName;
    if (headerAvatar) headerAvatar.textContent = loggedInUserName.substring(0, 2).toUpperCase();
    if (sourceUserId && !sourceUserId.value) {
        sourceUserId.value = loggedInUserName;
    }
} else if (loggedInUserEmail && sourceUserId) {
    sourceUserId.value = loggedInUserEmail;
}

// Initial pre-check status indicators
runPreChecks();

console.log("Weather Xpose Report Event page loaded successfully.");