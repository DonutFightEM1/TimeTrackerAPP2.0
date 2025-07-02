// GPS and Location Management for TimeTracker Pro

let watchId = null;
let currentPosition = null;
let locationStatus = 'unknown'; // 'unknown', 'getting', 'success', 'error', 'denied'

function initGPS() {
    console.log('Initializing GPS...');
    
    // Check if geolocation is supported
    if (!navigator.geolocation) {
        updateLocationStatus('Geolocation not supported by this browser', 'error');
        return;
    }
    
    // Start watching position
    getCurrentLocation();
    
    // Set up form submission handlers
    setupClockForms();
}

function getCurrentLocation() {
    updateLocationStatus('Getting your location...', 'getting');
    
    const options = {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 60000 // Cache for 1 minute
    };
    
    navigator.geolocation.getCurrentPosition(
        onLocationSuccess,
        onLocationError,
        options
    );
}

function onLocationSuccess(position) {
    currentPosition = {
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
        accuracy: position.coords.accuracy,
        timestamp: position.timestamp
    };
    
    console.log('Location obtained:', currentPosition);
    
    // Get human-readable address
    reverseGeocode(currentPosition.latitude, currentPosition.longitude);
    
    // Update form fields
    updateLocationFields();
    
    // Enable clock buttons
    enableClockButtons();
    
    // Start watching for location changes
    watchLocation();
}

function onLocationError(error) {
    console.error('Location error:', error);
    
    let message = 'Unable to get your location';
    let status = 'error';
    
    switch (error.code) {
        case error.PERMISSION_DENIED:
            message = 'Location access denied. Please enable location services.';
            status = 'denied';
            break;
        case error.POSITION_UNAVAILABLE:
            message = 'Location information unavailable.';
            break;
        case error.TIMEOUT:
            message = 'Location request timed out. Please try again.';
            break;
        default:
            message = 'An unknown error occurred while retrieving location.';
            break;
    }
    
    updateLocationStatus(message, status);
    disableClockButtons();
}

function reverseGeocode(lat, lng) {
    // Using a simple approximation for location description
    // In a real app, you might use a geocoding service like Google Maps API
    const locationText = `${lat.toFixed(4)}, ${lng.toFixed(4)}`;
    
    // Update location display
    updateLocationStatus(`Location: ${locationText}`, 'success');
    
    // Store formatted location
    currentPosition.locationText = locationText;
}

function updateLocationStatus(message, status) {
    const statusElement = document.getElementById('location-status');
    if (!statusElement) return;
    
    locationStatus = status;
    
    let iconClass = 'fas fa-spinner fa-spin';
    let textClass = 'text-muted';
    
    switch (status) {
        case 'getting':
            iconClass = 'fas fa-spinner fa-spin';
            textClass = 'text-info';
            break;
        case 'success':
            iconClass = 'fas fa-map-marker-alt';
            textClass = 'text-success';
            break;
        case 'error':
        case 'denied':
            iconClass = 'fas fa-exclamation-triangle';
            textClass = 'text-danger';
            break;
    }
    
    statusElement.innerHTML = `
        <div class="d-flex align-items-center ${textClass}">
            <i class="${iconClass} me-2"></i>
            <span>${message}</span>
        </div>
    `;
}

function updateLocationFields() {
    // Update clock-in form fields
    const inLatField = document.getElementById('in-latitude');
    const inLngField = document.getElementById('in-longitude');
    const inLocationField = document.getElementById('in-location');
    
    if (currentPosition) {
        if (inLatField) inLatField.value = currentPosition.latitude;
        if (inLngField) inLngField.value = currentPosition.longitude;
        if (inLocationField) inLocationField.value = currentPosition.locationText || 'Unknown Location';
    } else {
        // Set empty values when location is unavailable
        if (inLatField) inLatField.value = '';
        if (inLngField) inLngField.value = '';
        if (inLocationField) inLocationField.value = 'Location unavailable';
    }
    
    // Update clock-out form fields
    const outLatField = document.getElementById('out-latitude');
    const outLngField = document.getElementById('out-longitude');
    const outLocationField = document.getElementById('out-location');
    
    if (currentPosition) {
        if (outLatField) outLatField.value = currentPosition.latitude;
        if (outLngField) outLngField.value = currentPosition.longitude;
        if (outLocationField) outLocationField.value = currentPosition.locationText || 'Unknown Location';
    } else {
        // Set empty values when location is unavailable
        if (outLatField) outLatField.value = '';
        if (outLngField) outLngField.value = '';
        if (outLocationField) outLocationField.value = 'Location unavailable';
    }
}

function enableClockButtons() {
    const clockInBtn = document.getElementById('clock-in-btn');
    const clockOutBtn = document.getElementById('clock-out-btn');
    
    if (clockInBtn) {
        clockInBtn.disabled = false;
        clockInBtn.innerHTML = '<i class="fas fa-sign-in-alt me-2"></i>Clock In';
    }
    
    if (clockOutBtn) {
        clockOutBtn.disabled = false;
        clockOutBtn.innerHTML = '<i class="fas fa-sign-out-alt me-2"></i>Clock Out';
    }
}

function disableClockButtons() {
    // Don't disable buttons - allow clock in/out without GPS
    updateLocationStatus('Location unavailable - will require admin review', 'warning');
}

function watchLocation() {
    if (watchId) {
        navigator.geolocation.clearWatch(watchId);
    }
    
    const options = {
        enableHighAccuracy: true,
        timeout: 15000,
        maximumAge: 30000 // Cache for 30 seconds when watching
    };
    
    watchId = navigator.geolocation.watchPosition(
        (position) => {
            // Update position if significantly different
            const newLat = position.coords.latitude;
            const newLng = position.coords.longitude;
            
            if (!currentPosition || 
                Math.abs(newLat - currentPosition.latitude) > 0.0001 ||
                Math.abs(newLng - currentPosition.longitude) > 0.0001) {
                
                onLocationSuccess(position);
            }
        },
        (error) => {
            console.warn('Watch position error:', error);
            // Don't update UI for watch errors unless it's critical
        },
        options
    );
}

function setupClockForms() {
    const clockInForm = document.getElementById('clock-in-form');
    const clockOutForm = document.getElementById('clock-out-form');
    
    if (clockInForm) {
        clockInForm.addEventListener('submit', function(e) {
            const button = clockInForm.querySelector('button[type="submit"]');
            if (button && !button.disabled) {
                TimeTracker.showLoading(button, 'Clocking In...');
            }
            
            // Update location fields before submission (even if location is unavailable)
            updateLocationFields();
            
            // Show warning if no location is available
            if (!currentPosition) {
                TimeTracker.showToast('Clocking in without location - this will require manager approval', 'warning');
            }
        });
    }
    
    if (clockOutForm) {
        clockOutForm.addEventListener('submit', function(e) {
            // Add confirmation dialog
            if (!confirm('Are you sure you want to clock out?')) {
                e.preventDefault();
                return false;
            }
            
            const button = clockOutForm.querySelector('button[type="submit"]');
            if (button && !button.disabled) {
                TimeTracker.showLoading(button, 'Clocking Out...');
            }
            
            // Update location fields before submission (even if location is unavailable)
            updateLocationFields();
            
            // Show warning if no location is available
            if (!currentPosition) {
                TimeTracker.showToast('Clocking out without location - this will require manager approval', 'warning');
            }
        });
    }
}

function refreshLocation() {
    getCurrentLocation();
}

function calculateDistance(lat1, lng1, lat2, lng2) {
    const R = 6371000; // Earth's radius in meters
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLng = (lng2 - lng1) * Math.PI / 180;
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
              Math.sin(dLng/2) * Math.sin(dLng/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c; // Distance in meters
}

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (watchId) {
        navigator.geolocation.clearWatch(watchId);
    }
});

// Export GPS functions
window.GPS = {
    getCurrentLocation,
    refreshLocation,
    calculateDistance,
    getCurrentPosition: () => currentPosition,
    getLocationStatus: () => locationStatus
};

// Initialize GPS when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initGPS);
} else {
    initGPS();
}
