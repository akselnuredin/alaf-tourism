document.addEventListener('DOMContentLoaded', function() {
    // Display Hijri Date
    function displayHijriDate() {
        const hijriDate = document.getElementById('hijriDate');
        if (hijriDate) {
            try {
                const today = new Date();

                // Get ordinal suffix for day
                function getOrdinalSuffix(day) {
                    const j = day % 10;
                    const k = day % 100;
                    if (j === 1 && k !== 11) return day + 'st';
                    if (j === 2 && k !== 12) return day + 'nd';
                    if (j === 3 && k !== 13) return day + 'rd';
                    return day + 'th';
                }

                // Using Intl API to get Hijri date
                const hijriFormatter = new Intl.DateTimeFormat('en-u-ca-islamic', {
                    day: 'numeric',
                    month: 'long',
                    year: 'numeric'
                });

                const hijriParts = hijriFormatter.formatToParts(today);
                const day = parseInt(hijriParts.find(part => part.type === 'day').value);
                const month = hijriParts.find(part => part.type === 'month').value;
                const year = hijriParts.find(part => part.type === 'year').value;

                // Get weekday name
                const weekdayFormatter = new Intl.DateTimeFormat('en', { weekday: 'long' });
                const weekday = weekdayFormatter.format(today);

                // Format: "21st Jumada Al-Akhirah, 1447h" + "Friday"
                const dayWithSuffix = getOrdinalSuffix(day);
                const dateString = `${dayWithSuffix} ${month}, ${year}h`;

                // Display the date (two lines)
                hijriDate.querySelector('.hijri-day').textContent = dateString;
                hijriDate.querySelector('.hijri-full').textContent = weekday;
            } catch (error) {
                console.error('Error displaying Hijri date:', error);
                hijriDate.querySelector('.hijri-day').textContent = 'Islamic Calendar';
                hijriDate.querySelector('.hijri-full').textContent = '';
            }
        }
    }

    // Initialize Hijri date
    displayHijriDate();

    const loginForm = document.getElementById('loginForm');
    const messageDiv = document.getElementById('message');
    const btnLogin = document.querySelector('.btn-login');
    const btnText = document.querySelector('.btn-text');
    const btnLoader = document.querySelector('.btn-loader');

    // Function to show message
    function showMessage(message, type) {
        messageDiv.textContent = message;
        messageDiv.className = 'message ' + type;
        messageDiv.style.display = 'block';

        // Auto hide after 5 seconds
        setTimeout(() => {
            messageDiv.style.display = 'none';
        }, 5000);
    }

    // Function to get CSRF token from cookies
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Handle form submission
    loginForm.addEventListener('submit', function(e) {
        e.preventDefault();

        // Get form data
        const username = document.getElementById('username').value.trim();
        const password = document.getElementById('password').value;
        const remember = document.getElementById('remember').checked;

        // Validation
        if (!username || !password) {
            showMessage('Please fill in all fields', 'error');
            return;
        }

        // Show loader
        btnText.style.display = 'none';
        btnLoader.style.display = 'inline-block';
        btnLogin.disabled = true;

        // Prepare form data
        const formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);
        formData.append('remember', remember);

        // Get CSRF token
        const csrftoken = getCookie('csrftoken');

        // AJAX request
        fetch('/accounts/login/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Hide loader
            btnText.style.display = 'inline-block';
            btnLoader.style.display = 'none';
            btnLogin.disabled = false;

            if (data.success) {
                showMessage(data.message || 'Login successful! Redirecting...', 'success');

                // Redirect after successful login
                setTimeout(() => {
                    window.location.href = data.redirect_url || '/admin/dashboard/';
                }, 1500);
            } else {
                showMessage(data.message || 'Invalid username or password', 'error');
            }
        })
        .catch(error => {
            // Hide loader
            btnText.style.display = 'inline-block';
            btnLoader.style.display = 'none';
            btnLogin.disabled = false;

            console.error('Error:', error);
            showMessage('An error occurred. Please try again.', 'error');
        });
    });

    // Add input focus animations
    const inputs = document.querySelectorAll('.input-wrapper input');
    inputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.parentElement.style.transform = 'scale(1.02)';
        });

        input.addEventListener('blur', function() {
            this.parentElement.style.transform = 'scale(1)';
        });
    });

    // Handle "Forgot password" click (you can customize this)
    const forgotPassword = document.querySelector('.forgot-password');
    if (forgotPassword) {
        forgotPassword.addEventListener('click', function(e) {
            e.preventDefault();
            showMessage('Password reset feature will be implemented soon', 'error');
        });
    }
});
