document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('test-form');
    const timerDisplay = document.getElementById('timer');
    const timeLabel = document.getElementById('timer-display');

    let totalSeconds = 600; // 10 minutes
    const startKey = `${window.location.pathname}-startTime`;

    // Restore start time if exists
    let startTime = localStorage.getItem(startKey);
    if (!startTime) {
        startTime = Date.now();
        localStorage.setItem(startKey, startTime);
    }

    function updateTimer() {
        const now = Date.now();
        const elapsed = Math.floor((now - startTime) / 1000);
        const remaining = Math.max(0, totalSeconds - elapsed);
        const minutes = Math.floor(remaining / 60);
        const seconds = remaining % 60;
        const timeString = `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;

        if (timerDisplay) timerDisplay.textContent = timeString;
        if (timeLabel) timeLabel.textContent = timeString;

        if (remaining <= 60) {
            timerDisplay.style.backgroundColor = '#e74c3c';
        } else if (remaining <= 180) {
            timerDisplay.style.backgroundColor = '#f39c12';
        }

        if (remaining <= 0) {
            clearInterval(timerInterval);
            localStorage.removeItem(startKey);
            alert('Time is up! Your test will be submitted.');
            form.submit();
        }
    }

    const timerInterval = setInterval(updateTimer, 1000);
    updateTimer();

    form.addEventListener('submit', function (e) {
        localStorage.removeItem(startKey);
    });

    window.addEventListener('beforeunload', function () {
        if (Date.now() - startTime < totalSeconds * 1000) {
            localStorage.removeItem(startKey);
        }
    });
});
