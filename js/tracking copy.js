document.addEventListener("DOMContentLoaded", function () {
    const app = document.getElementById("tracking-app");
    if (!app) return;

    const etaElement = document.getElementById("eta-display");
    const statusElement = document.getElementById("status-text");
    const mapStatusElement = document.getElementById("map-status");
    const progressBar = document.getElementById("progress-bar");
    const progressPercent = document.getElementById("progress-percent");
    const routeProgress = document.getElementById("route-progress");
    const riderMarker = document.getElementById("rider-marker");
    const arrivalMessage = document.getElementById("arrival-message");

    const startingEta = Math.max(0, parseInt(app.dataset.etaMinutes || "0", 10));
    let remainingMinutes = startingEta;

    function updateUI() {
        if (remainingMinutes <= 0) {
            etaElement.textContent = "Arrived at Location";
            statusElement.textContent = "Arrived";
            mapStatusElement.textContent = "Arrived";
            progressBar.style.width = "100%";
            routeProgress.style.width = "100%";
            progressPercent.textContent = "100%";
            riderMarker.style.left = "79%";
            arrivalMessage.hidden = false;
            return;
        }

        etaElement.textContent = remainingMinutes + " min away";
        statusElement.textContent = "On the way";
        mapStatusElement.textContent = "On the way";

        const progress = startingEta > 0
            ? Math.min(100, Math.round(((startingEta - remainingMinutes) / startingEta) * 100))
            : 100;

        progressBar.style.width = progress + "%";
        routeProgress.style.width = progress + "%";
        progressPercent.textContent = progress + "%";

        // Move the visual rider marker along the route.
        const leftPosition = 18 + (61 * progress / 100);
        riderMarker.style.left = leftPosition + "%";
    }

    updateUI();

    if (remainingMinutes > 0) {
        const timer = setInterval(function () {
            remainingMinutes -= 1;
            updateUI();

            if (remainingMinutes <= 0) {
                clearInterval(timer);
            }
        }, 60000);
    }
});
