// Function to get current position
function getCurrentPosition() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            function(position) {
                // Send position to server
                updateLocation(position.coords.latitude, position.coords.longitude);
            },
            function(error) {
                console.error("Error getting location:", error);
            },
            {
                enableHighAccuracy: true,
                timeout: 5000,
                maximumAge: 0
            }
        );
    } else {
        console.error("Geolocation is not supported by this browser.");
    }
}

// Function to update location on server
function updateLocation(latitude, longitude) {
    fetch('/location/update-location/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            latitude: latitude,
            longitude: longitude
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            console.log('Location updated successfully');
        } else {
            console.error('Error updating location:', data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

// Function to get CSRF token
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

// Update location every 5 minutes
setInterval(getCurrentPosition, 300000);

// Initial location update
getCurrentPosition(); 