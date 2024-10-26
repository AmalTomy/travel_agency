$(document).ready(function() {
    console.log('Document ready');
    
    var locationsData;
    try {
        locationsData = JSON.parse(document.getElementById('locations-data').textContent);
        console.log('Parsed locations data:', locationsData);
    } catch (error) {
        console.error('Error parsing locations data:', error);
        console.log('Raw locations data:', document.getElementById('locations-data').textContent);
        return;  // Exit early if parsing fails
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
    const csrftoken = getCookie('csrftoken');

    $('.toggle-status').on('click', function() {
        var busId = $(this).data('bus-id');
        var $button = $(this);
        
        $.ajax({
            url: '/toggle-bus-status/' + busId + '/',
            type: 'POST',
            headers: {
                'X-CSRFToken': csrftoken
            },
            success: function(response) {
                if (response.status === 'success') {
                    $button.text(response.new_status === 'active' ? 'Set Under Maintenance' : 'Set Active');
                    var $statusBadge = $button.closest('.bus-card').find('.status-badge .badge');
                    $statusBadge
                        .removeClass('bg-success bg-warning')
                        .addClass(response.new_status === 'active' ? 'bg-success' : 'bg-warning')
                        .text(response.new_status === 'active' ? 'Active' : 'Under Maintenance');
                    
                    // Check if the current filter excludes this bus after status change
                    var currentStatus = new URLSearchParams(window.location.search).get('status');
                    if (currentStatus && currentStatus !== response.new_status) {
                        $button.closest('.bus-card').fadeOut();
                    }
                    updateRescheduleButtonState();
                } else {
                    alert('Failed to update status: ' + response.message);
                }
            },
            error: function(xhr, status, error) {
                console.error('Error:', error);
                alert('An error occurred while updating the status');
            }
        });
    });

    // Update this function to handle the reschedule button
    function updateRescheduleButtonState() {
        document.querySelectorAll('.reschedule-bus-btn').forEach(button => {
            const busStatus = button.getAttribute('data-bus-status');
            button.disabled = busStatus !== 'under_maintenance';
        });
    }

    // Call the function when the page loads
    updateRescheduleButtonState();

    // Function to handle bus rescheduling
    function rescheduleBus(busId) {
        const form = document.getElementById(`rescheduleBusForm${busId}`);
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(form);
            
            fetch('/reschedule_bus/', {  // Update this URL to match your Django URL configuration
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Bus rescheduled successfully!');
                    location.reload();  // Reload the page to show updated information
                } else {
                    alert('Error rescheduling bus: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while rescheduling the bus.');
            });
        });
    }

    // Call this function for each bus when the page loads
    document.addEventListener('DOMContentLoaded', function() {
        const buses = document.querySelectorAll('[id^="rescheduleBusForm"]');
        buses.forEach(bus => {
            const busId = bus.id.replace('rescheduleBusForm', '');
            rescheduleBus(busId);
        });
    });

    // Add this to initialize the modals
    var myModals = document.querySelectorAll('.modal')
    myModals.forEach(function (modal) {
        new bootstrap.Modal(modal);
    });

    // Add this function to handle form submission
    $('[id^=editBusForm]').on('submit', function(e) {
        e.preventDefault();
        var formData = $(this).serialize();
        var busId = $(this).find('input[name="bus_id"]').val();

        $.ajax({
            url: '/edit-bus-schedule/',
            type: 'POST',
            data: formData,
            success: function(response) {
                if (response.success) {
                    alert('Bus schedule updated successfully');
                    location.reload();
                } else {
                    alert('Error updating bus schedule: ' + response.error);
                }
            },
            error: function(xhr, status, error) {
                alert('An error occurred while updating the bus schedule');
            }
        });
    });

    // Function to populate departure locations
    function populateDepartureLocations(selectElement) {
        console.log('Populating departure locations');
        selectElement.empty().append('<option value="">Select Departure Location</option>');
        var uniqueSources = [...new Set(locationsData.map(loc => loc.source))];
        console.log('Unique sources:', uniqueSources);
        uniqueSources.forEach(source => {
            selectElement.append($('<option>', {
                value: source,
                text: source
            }));
        });
        console.log('Departure locations populated');
    }

    // Populate departure locations for all modals when the page loads
    $('[id^=new_departure_location]').each(function() {
        populateDepartureLocations($(this));
    });

    // Handle departure location change
    $('[id^=new_departure_location]').on('change', function() {
        var busId = this.id.replace('new_departure_location', '');
        var destinationSelect = $('#new_destination_location' + busId);
        var stopsSelect = $('#new_stops' + busId);
        var selectedDeparture = $(this).val();
        console.log('Selected departure:', selectedDeparture);

        destinationSelect.empty().append('<option value="">Select Destination Location</option>').prop('disabled', false);
        stopsSelect.empty().append('<option value="">Select Stops</option>').prop('disabled', true);

        if (selectedDeparture) {
            var availableDestinations = [...new Set(locationsData
                .filter(loc => loc.source === selectedDeparture)
                .map(loc => loc.destination))];
            console.log('Available destinations:', availableDestinations);

            availableDestinations.forEach(dest => {
                destinationSelect.append($('<option>', {
                    value: dest,
                    text: dest
                }));
            });
        }
    });

    // Handle destination location change
    $('[id^=new_destination_location]').on('change', function() {
        var busId = this.id.replace('new_destination_location', '');
        var departureSelect = $('#new_departure_location' + busId);
        var stopsSelect = $('#new_stops' + busId);
        var selectedDeparture = departureSelect.val();
        var selectedDestination = $(this).val();
        console.log('Selected destination:', selectedDestination);

        stopsSelect.empty().append('<option value="">Select Stops</option>').prop('disabled', false);

        if (selectedDeparture && selectedDestination) {
            var selectedLocations = locationsData.filter(loc => 
                loc.source === selectedDeparture && 
                loc.destination === selectedDestination
            );

            if (selectedLocations.length > 0) {
                selectedLocations.forEach((location) => {
                    if (location.stops) {
                        stopsSelect.append($('<option>', {
                            value: location.stops,
                            text: location.stops
                        }));
                    }
                });
            } else {
                stopsSelect.append($('<option>', {
                    value: "",
                    text: "No stops available for this route"
                }));
            }
        }
    });

    // Add this function to handle form submission for rescheduling
    function setupRescheduleForms() {
        $('[id^=rescheduleBusForm]').on('submit', function(e) {
            e.preventDefault();
            var formData = $(this).serialize();
            var busId = $(this).find('input[name="bus_id"]').val();

            $.ajax({
                url: '/reschedule_bus/',
                type: 'POST',
                data: formData,
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                },
                success: function(response) {
                    if (response.success) {
                        // Update the status badge to 'active'
                        $(`#bus-${busId} .status-badge`).removeClass('bg-warning').addClass('bg-success').text('Active');
                        // Close the reschedule modal
                        $(`#rescheduleModal${busId}`).modal('hide');
                        // Show the success modal
                        $('#rescheduleSuccessModal').modal('show');
                        $('.reschedule-message').text(response.message);
                        // Optionally, you can reload the page to refresh all data after a delay
                        setTimeout(function() {
                            window.location.href = '/mod_home/';  // Adjust this URL if necessary
                        }, 2000);
                    } else {
                        alert('Error rescheduling bus: ' + response.error);
                    }
                },
                error: function(xhr, status, error) {
                    console.error('Error:', error);
                    alert('An error occurred while rescheduling the bus');
                }
            });
        });
    }

    // Call this function when the document is ready
    setupRescheduleForms();

    // Add this at the end of the $(document).ready function
    $('#rescheduleSuccessModal').on('shown.bs.modal', function () {
        $('.success-animation').addClass('animate');
    });

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

    function updateBusStatus() {
        $('.status-badge .badge').each(function() {
            var arrivalDate = new Date($(this).data('arrival-date'));
            var today = new Date();
            
            if (arrivalDate < today) {
                $(this).removeClass('bg-success').addClass('bg-warning').text('Under Maintenance');
            }
        });
    }

    // Call the function when the page loads
    updateBusStatus();

    // Update the status every minute
    setInterval(updateBusStatus, 60000);

    // ... (keep existing code)
});

document.addEventListener('DOMContentLoaded', function() {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    document.querySelectorAll('.status-badge .badge').forEach(badge => {
        const arrivalDate = new Date(badge.dataset.arrivalDate);
        if (arrivalDate < today) {
            badge.textContent = 'Under Maintenance';
            badge.classList.remove('bg-success');
            badge.classList.add('bg-warning');
        }
    });

    document.querySelectorAll('.reschedule-btn').forEach(button => {
        const busCard = button.closest('.bus-card');
        const badge = busCard.querySelector('.status-badge .badge');
        const arrivalDate = new Date(badge.dataset.arrivalDate);

        if (arrivalDate < today) {
            button.disabled = false;
        }
    });

    // Add this function to handle the rescheduling process
    function handleReschedule(event) {
        event.preventDefault();
        const form = event.target;
        const formData = new FormData(form);

        fetch('/reschedule_bus/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const busId = formData.get('bus_id');
                const busCard = document.getElementById(`bus-${busId}`);
                const badge = busCard.querySelector('.status-badge .badge');
                
                badge.textContent = 'Active';
                badge.classList.remove('bg-warning');
                badge.classList.add('bg-success');

                const rescheduleBtn = busCard.querySelector('.reschedule-btn');
                rescheduleBtn.disabled = true;

                // Show success modal
                const successModal = new bootstrap.Modal(document.getElementById('rescheduleSuccessModal'));
                document.querySelector('.reschedule-message').textContent = data.message;
                successModal.show();

                // Close the reschedule modal
                const rescheduleModal = bootstrap.Modal.getInstance(document.getElementById(`rescheduleBusModal${busId}`));
                rescheduleModal.hide();
            } else {
                alert('Error rescheduling bus: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while rescheduling the bus.');
        });
    }

    // Add event listeners for rescheduling forms
    document.querySelectorAll('[id^="rescheduleBusForm"]').forEach(form => {
        form.addEventListener('submit', handleReschedule);
    });

    function updateRescheduleButton(busId, arrivalDate) {
        const rescheduleBtn = document.querySelector(`#bus-${busId} .reschedule-btn`);
        const arrivalDateObj = new Date(arrivalDate);
        rescheduleBtn.disabled = arrivalDateObj > today;
    }

    document.querySelectorAll('.bus-card').forEach(busCard => {
        const busId = busCard.id.replace('bus-', '');
        const arrivalDate = busCard.dataset.arrivalDate;
        updateRescheduleButton(busId, arrivalDate);
    });

    function handleReschedule(event) {
        event.preventDefault();
        const form = event.target;
        const formData = new FormData(form);

        fetch('/reschedule_bus/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const busId = formData.get('bus_id');
                const busCard = document.getElementById(`bus-${busId}`);
                const badge = busCard.querySelector('.status-badge .badge');
                
                badge.textContent = 'Active';
                badge.classList.remove('bg-warning');
                badge.classList.add('bg-success');

                busCard.dataset.arrivalDate = data.new_arrival_date;
                updateRescheduleButton(busId, data.new_arrival_date);

                // Show success modal
                const successModal = new bootstrap.Modal(document.getElementById('rescheduleSuccessModal'));
                document.querySelector('.reschedule-message').textContent = data.message;
                successModal.show();

                // Close the reschedule modal
                const rescheduleModal = bootstrap.Modal.getInstance(document.getElementById(`rescheduleBusModal${busId}`));
                rescheduleModal.hide();
            } else {
                alert('Error rescheduling bus: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while rescheduling the bus.');
        });
    }

    // Add event listeners for rescheduling forms
    document.querySelectorAll('[id^="rescheduleBusForm"]').forEach(form => {
        form.addEventListener('submit', handleReschedule);
    });
});