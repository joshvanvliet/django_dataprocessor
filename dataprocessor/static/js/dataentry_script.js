(() => {
    const NOTIFICATION_DURATION = 2500;
    const copyNotification = document.getElementById("copyNotification");
    const tableCells = document.querySelectorAll("tbody td");

    const showNotification = () => {
        copyNotification.style.display = "block";
        copyNotification.style.animation = "none";
        void copyNotification.offsetWidth; // Trigger reflow
        copyNotification.style.animation = "fadeInOut 2.5s ease";

        setTimeout(() => {
            copyNotification.style.display = "none";
        }, NOTIFICATION_DURATION);
    };

    const handleCellClick = (event, cell) => {
        if (event.target.tagName === "A") return;

        const textToCopy = cell.title || cell.textContent;
        navigator.clipboard.writeText(textToCopy)
            .then(showNotification)
            .catch(err => console.error("Failed to copy text:", err));
    };

    const initializeEventListeners = () => {
        for (const cell of tableCells) {
            cell.addEventListener("click", (event) => handleCellClick(event, cell));
        }
    };

    document.addEventListener("DOMContentLoaded", initializeEventListeners);
})();