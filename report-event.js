/* =========================================================
   WEATHER360 - REPORT EVENT JS
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
    localStorage.getItem("weather360-theme");


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
            "weather360-theme",
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
   3. CITY COORDINATES
   ========================================================= */

const cityCoordinates = {

    Kolkata: {
        lat: 22.5726,
        lng: 88.3639
    },

    Mumbai: {
        lat: 19.0760,
        lng: 72.8777
    },

    Delhi: {
        lat: 28.6139,
        lng: 77.2090
    },

    Ahmedabad: {
        lat: 23.0225,
        lng: 72.5714
    },

    Jaipur: {
        lat: 26.9124,
        lng: 75.7873
    },

    Lucknow: {
        lat: 26.8467,
        lng: 80.9462
    },

    Patna: {
        lat: 25.5941,
        lng: 85.1376
    },

    Bhubaneswar: {
        lat: 20.2961,
        lng: 85.8245
    },

    Guwahati: {
        lat: 26.1445,
        lng: 91.7362
    },

    Chennai: {
        lat: 13.0827,
        lng: 80.2707
    },

    Bengaluru: {
        lat: 12.9716,
        lng: 77.5946
    },

    Hyderabad: {
        lat: 17.3850,
        lng: 78.4867
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

                (position) => {

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
                "Upload evidence to continue";


            document.getElementById(
                "metadataFile"
            ).textContent =
                "Not available";


            document.getElementById(
                "metadataTime"
            ).textContent =
                "Not available";


            setStatus(
                "metadataStatus",
                "PENDING"
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

    const element =
        document.getElementById(id);

    if (!element) return;


    element.classList.remove(
        "passed"
    );


    element.textContent =
        status;


    if (status === "PASSED") {

        element.classList.add(
            "passed"
        );
    }
}



/* =========================================================
   13. PRE-CHECK
   ========================================================= */

function runPreChecks() {

    setTimeout(() => {

        if (mediaFile.files.length > 0) {

            setStatus(
                "metadataStatus",
                "PASSED"
            );

        }

    }, 500);


    setTimeout(() => {

        const lat =
            latitudeInput.value;

        const lng =
            longitudeInput.value;


        if (lat && lng) {

            setStatus(
                "locationStatus",
                "PASSED"
            );

        }

    }, 800);


    setTimeout(() => {

        if (mediaFile.files.length > 0) {

            setStatus(
                "aiStatus",
                "PASSED"
            );

        }

    }, 1100);

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

            const eventType =
                document.getElementById(
                    "eventType"
                ).value;


            const description =
                document.getElementById(
                    "incidentDescription"
                ).value.trim();


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


            if (!date || !time) {

                alert(
                    "Please enter the incident date and time."
                );

                return;
            }


            if (!mediaFile.files.length) {

                alert(
                    "Please upload an incident image or video."
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



            /* Loading */

            submitReportBtn.disabled = true;

            submitReportBtn.innerHTML = `
                <i class="fa-solid fa-spinner fa-spin"></i>
                Submitting Report...
            `;



            setTimeout(() => {

                submitReportBtn.disabled = false;

                submitReportBtn.innerHTML = `
                    <i class="fa-solid fa-check"></i>
                    Report Submitted Successfully
                `;


                alert(
                    "Your weather report has been submitted for verification."
                );


                setTimeout(() => {

                    submitReportBtn.innerHTML = `
                        <i class="fa-solid fa-paper-plane"></i>
                        Submit Report for Verification
                    `;

                }, 2500);

            }, 1500);

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
   17. CONSOLE
   ========================================================= */

console.log(
    "Weather360 Report Event page loaded successfully."
);