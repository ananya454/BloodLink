/**
 * BloodLink - Frontend helper
 * Connects search button directly to Flask /availability route
 */
function findBlood() {
    let bloodGroupSelect = document.getElementById("bloodGroup");
    if (!bloodGroupSelect) {
        window.location.href = "/availability";
        return;
    }

    let bloodGroup = bloodGroupSelect.value;
    if (!bloodGroup || bloodGroup === "" || bloodGroup === "-1") {
        alert("Please select a blood group to check availability.");
        return;
    }

    window.location.href = "/availability?blood_group=" + encodeURIComponent(bloodGroup);
}