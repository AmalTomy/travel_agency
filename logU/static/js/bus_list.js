document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('filter-search');
    const busCards = document.querySelectorAll('.bus-card');
    const busCountElement = document.querySelector('#bus-count');
    const viewSeatButtons = document.querySelectorAll('.view_seat_btn');
    const seatModal = document.querySelector('.seat-modal');
    const overlay = document.querySelector('.overlay');
    const closeModalButton = document.querySelector('.seat-modal-close');
    let currentBusTicketPrice = 0;
    let currentBusId = null;
    let refreshInterval = null;

    // Bus search functionality
    searchInput.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        applyFilters(searchTerm);
    });

    function updateBusCount(count) {
        busCountElement.textContent = `${count} Bus${count !== 1 ? 'es' : ''} found`;
    }

    // View Seats modal functionality
    viewSeatButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            currentBusId = this.dataset.busId;
            currentBusTicketPrice = parseFloat(this.dataset.ticketPrice);
            console.log('Current Bus Ticket Price:', currentBusTicketPrice);
            seatModal.classList.add('show');
            overlay.classList.add('show');
            
            // Reset selected seats
            selectedSeats = [];
            updateSeatInfo();
            
            // Fetch booked seats for this bus
            refreshSeatAvailability(currentBusId);
    
            // Start the refresh interval
            startRefreshInterval();
        });
    });

    closeModalButton.addEventListener('click', function() {
        seatModal.classList.remove('show');
        overlay.classList.remove('show');
        stopRefreshInterval();
        currentBusId = null;
    });

    overlay.addEventListener('click', function() {
        seatModal.classList.remove('show');
        overlay.classList.remove('show');
        stopRefreshInterval();
        currentBusId = null;
    });

    function updateSeatAvailability(busId, availableSeats, bookedSeats) {
        const seatCountElement = document.querySelector(`#available-seats-${busId}`);
        if (seatCountElement) {
            seatCountElement.textContent = `${availableSeats} Seats Available`;
        }
    
        const seats = document.querySelectorAll('.seat');
        seats.forEach(seat => {
            const seatNumber = seat.dataset.seat;
            if (bookedSeats.includes(seatNumber)) {
                seat.classList.add('booked');
                seat.classList.remove('selected');
                seat.innerHTML = '<i class="fas fa-times"></i>';
                seat.style.pointerEvents = 'none';
            } else {
                seat.classList.remove('booked');
                seat.innerHTML = '<i class="fas fa-chair"></i><span class="seat-label">' + seatNumber + '</span>';
                seat.style.pointerEvents = 'auto';
            }
        });
        updateSeatInfo();
    }

    const seatMap = document.querySelector('.seat-map');
    const selectedSeatsElement = document.getElementById('selected-seats');
    const totalPriceElement = document.getElementById('total-price');
    const confirmButton = document.getElementById('confirm-seats');
    const maxSeats = 8;
    let selectedSeats = [];

    seatMap.addEventListener('click', function(e) {
        if (e.target.classList.contains('seat') || e.target.closest('.seat')) {
            const seatElement = e.target.classList.contains('seat') ? e.target : e.target.closest('.seat');
            
            if (seatElement.classList.contains('booked')) {
                alert('This seat is already booked.');
                return;
            }

            const seatNumber = seatElement.dataset.seat;

            if (seatElement.classList.contains('selected')) {
                seatElement.classList.remove('selected');
                selectedSeats = selectedSeats.filter(seat => seat !== seatNumber);
            } else {
                if (selectedSeats.length < maxSeats) {
                    seatElement.classList.add('selected');
                    selectedSeats.push(seatNumber);
                } else {
                    showMaxSeatsAlert();
                    return;
                }
            }

            updateSeatInfo();
        }
    });

    function updateSeatInfo() {
        selectedSeatsElement.textContent = selectedSeats.join(', ');
        const totalPrice = selectedSeats.length * currentBusTicketPrice;
        totalPriceElement.textContent = totalPrice.toFixed(2);
        confirmButton.disabled = selectedSeats.length === 0;
    }

    confirmButton.addEventListener('click', function() {
        console.log('Confirm button clicked');
    
        if (selectedSeats.length === 0) {
            console.log('No seats selected');
            return;
        }
    
        const busDetails = document.querySelector('.bus-card-content');
        const departureDateElement = document.querySelector('.date');
        
        console.log('Date element content:', departureDateElement ? departureDateElement.textContent : 'Date element not found');
    
        let formattedDate = formatDate(departureDateElement);
    
        console.log('Formatted date:', formattedDate);
    
        const bookingDetails = {
            bus_id: currentBusId,
            seats: selectedSeats.join(','),
            num_tickets: selectedSeats.length,
            total_amount: parseFloat(totalPriceElement.textContent),
            departure_location: busDetails.querySelector('.departure p:not(.bold)').textContent.trim(),
            destination: busDetails.querySelector('.arrival p:not(.bold)').textContent.trim(),
            departure_date: formattedDate,
        };
    
        console.log('Sending booking details:', bookingDetails);
    
        // Send the booking details to the server
        fetch('/create-booking/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(bookingDetails)
        })
        .then(response => response.json())
        .then(data => {
            console.log('Received response:', data);
            if (data.success) {
                window.location.href = data.redirect_url;
            } else {
                console.error('Error saving booking details:', data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    });
    
    function formatDate(dateElement) {
        if (dateElement) {
            const dateText = dateElement.textContent.trim();
            const dateParts = dateText.split(' ')[0].split('/');
            if (dateParts.length === 3) {
                const [day, month, year] = dateParts;
                return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
            } else if (dateParts.length === 2) {
                const [day, month] = dateParts;
                const year = new Date().getFullYear();
                return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
            }
        }
        console.error('Invalid date format:', dateElement ? dateElement.textContent : 'Date element not found');
        return new Date().toISOString().split('T')[0]; // Fallback to current date
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

    function refreshSeatAvailability(busId) {
        console.log(`Fetching seat availability for bus ${busId}`);
        fetch(`/api/bus-availability/${busId}/`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Received seat availability data:', data);
                if (data && data.available_seats !== undefined && data.booked_seats !== undefined) {
                    updateSeatAvailability(busId, data.available_seats, data.booked_seats);
                } else {
                    console.error('Invalid data received from server:', data);
                    throw new Error('Invalid data received from server');
                }
            })
            .catch(error => {
                console.error('Error fetching seat availability:', error);
                alert('Unable to fetch seat availability. Please try again.');
            });
    }
    // Add these new functions
    function startRefreshInterval() {
        // Clear any existing interval
        if (refreshInterval) {
            clearInterval(refreshInterval);
        }
        
        // Set a new interval
        refreshInterval = setInterval(() => {
            if (currentBusId) {
                refreshSeatAvailability(currentBusId);
            }
        }, 30000); // Refresh every 30 seconds
    }

    function stopRefreshInterval() {
        if (refreshInterval) {
            clearInterval(refreshInterval);
            refreshInterval = null;
        }
    }

    // Reset filters functionality
    const resetButton = document.getElementById('reset_filters');
    const filterCheckboxes = document.querySelectorAll('.filter_option input[type="checkbox"]');

    function resetFilters() {
        // Uncheck all checkboxes
        filterCheckboxes.forEach(checkbox => {
            checkbox.checked = false;
            checkbox.parentElement.classList.remove('selected');
        });

        // Clear the search input
        searchInput.value = '';

        // Show all buses
        busCards.forEach(card => {
            card.closest('tr').style.display = 'table-row';
        });

        // Update the bus count to show total number of buses
        updateBusCount(busCards.length);

        // Update filter counts
        updateFilterCounts();

        // Ensure all filter options are visible
        document.querySelectorAll('.filter_option').forEach(option => {
            option.style.display = 'flex';
        });

        // Ensure all filter section headers are visible
        document.querySelectorAll('.filter_div h6').forEach(header => {
            header.style.display = 'block';
        });
    }

    resetButton.addEventListener('click', resetFilters);

    // Add this to reset the bus search when clearing the search input
    searchInput.addEventListener('search', function() {
        if (this.value === '') {
            busCards.forEach(card => {
                card.closest('tr').style.display = 'table-row';
            });
            updateBusCount(busCards.length);
        }
    });

    // Add this function to handle departure time filters
    function applyDepartureTimeFilter() {
        const before6am = document.getElementById('before_6am').checked;
        const from6amTo12pm = document.getElementById('6am_to_12pm').checked;
        const from12pmTo6pm = document.getElementById('12pm_to_6pm').checked;
        const after6pm = document.getElementById('after_6pm').checked;

        let visibleBusCount = 0;

        busCards.forEach(card => {
            const departureTime = card.querySelector('.departure p.bold').textContent;
            const departureHour = parseInt(departureTime.split(':')[0]);

            let showBus = false;

            if (before6am && departureHour < 6) showBus = true;
            if (from6amTo12pm && departureHour >= 6 && departureHour < 12) showBus = true;
            if (from12pmTo6pm && departureHour >= 12 && departureHour < 18) showBus = true;
            if (after6pm && departureHour >= 18) showBus = true;

            // If no filters are selected, show all buses
            if (!before6am && !from6amTo12pm && !from12pmTo6pm && !after6pm) showBus = true;

            if (showBus) {
                card.closest('tr').style.display = 'table-row';
                visibleBusCount++;
            } else {
                card.closest('tr').style.display = 'none';
            }
        });

        updateBusCount(visibleBusCount);
    }

    // Add event listeners to the departure time checkboxes
    document.getElementById('before_6am').addEventListener('change', () => applyFilters(searchInput.value));
    document.getElementById('6am_to_12pm').addEventListener('change', () => applyFilters(searchInput.value));
    document.getElementById('12pm_to_6pm').addEventListener('change', () => applyFilters(searchInput.value));
    document.getElementById('after_6pm').addEventListener('change', () => applyFilters(searchInput.value));

    function updateDepartureTimeCounts() {
        let before6amCount = 0;
        let from6amTo12pmCount = 0;
        let from12pmTo6pmCount = 0;
        let after6pmCount = 0;

        busCards.forEach(card => {
            const departureTime = card.querySelector('.departure p.bold').textContent;
            const departureHour = parseInt(departureTime.split(':')[0]);

            if (departureHour < 6) before6amCount++;
            else if (departureHour >= 6 && departureHour < 12) from6amTo12pmCount++;
            else if (departureHour >= 12 && departureHour < 18) from12pmTo6pmCount++;
            else after6pmCount++;
        });

        document.getElementById('before_6am_count').textContent = before6amCount;
        document.getElementById('6am_to_12pm_count').textContent = from6amTo12pmCount;
        document.getElementById('12pm_to_6pm_count').textContent = from12pmTo6pmCount++;
        document.getElementById('after_6pm_count').textContent = after6pmCount;
    }

    // Call this function initially to set the counts
    updateDepartureTimeCounts();

    function updateFilterCounts() {
        let before6amCount = 0;
        let from6amTo12pmCount = 0;
        let from12pmTo6pmCount = 0;
        let after6pmCount = 0;
        let sleeperCount = 0;
        let semiSleeperCount = 0;
        let arrivalBefore6amCount = 0;
        let arrival6amTo12pmCount = 0;
        let arrival12pmTo6pmCount = 0;
        let arrivalAfter6pmCount = 0;

        busCards.forEach(card => {
            const departureTime = card.querySelector('.departure p.bold').textContent;
            const departureHour = parseInt(departureTime.split(':')[0]);
            const arrivalTime = card.querySelector('.arrival p.bold').textContent;
            const arrivalHour = parseInt(arrivalTime.split(':')[0]);
            const busType = card.querySelector('.bus_details p:not(.bold)').textContent.toLowerCase();

            // Departure Time
            if (departureHour < 6) before6amCount++;
            else if (departureHour >= 6 && departureHour < 12) from6amTo12pmCount++;
            else if (departureHour >= 12 && departureHour < 18) from12pmTo6pmCount++;
            else after6pmCount++;

            // Bus Types
            if (busType.includes('sleeper')) sleeperCount++;
            if (busType.includes('semi-sleeper')) semiSleeperCount++;

            // Arrival Time
            if (arrivalHour < 6) arrivalBefore6amCount++;
            else if (arrivalHour >= 6 && arrivalHour < 12) arrival6amTo12pmCount++;
            else if (arrivalHour >= 12 && arrivalHour < 18) arrival12pmTo6pmCount++;
            else arrivalAfter6pmCount++;
        });

        // Update Departure Time counts
        document.getElementById('before_6am_count').textContent = before6amCount;
        document.getElementById('6am_to_12pm_count').textContent = from6amTo12pmCount;
        document.getElementById('12pm_to_6pm_count').textContent = from12pmTo6pmCount;
        document.getElementById('after_6pm_count').textContent = after6pmCount;

        // Update Bus Types counts
        document.getElementById('sleeper_count').textContent = sleeperCount;
        document.getElementById('semi_sleeper_count').textContent = semiSleeperCount;

        // Update Arrival Time counts
        document.getElementById('arrival_before_6am_count').textContent = arrivalBefore6amCount;
        document.getElementById('arrival_6am_to_12pm_count').textContent = arrival6amTo12pmCount;
        document.getElementById('arrival_12pm_to_6pm_count').textContent = arrival12pmTo6pmCount;
        document.getElementById('arrival_after_6pm_count').textContent = arrivalAfter6pmCount;
    }

    // Call this function initially to set the counts
    updateFilterCounts();

    function applyFilters(searchTerm = '') {
        let visibleBusCount = 0;

        busCards.forEach(card => {
            const busName = card.querySelector('.bus_details p.bold').textContent.toLowerCase();
            const busType = card.querySelector('.bus_details p:not(.bold)').textContent.toLowerCase();
            const departureTime = card.querySelector('.departure p.bold').textContent;
            const departureHour = parseInt(departureTime.split(':')[0]);
            const arrivalTime = card.querySelector('.arrival p.bold').textContent;
            const arrivalHour = parseInt(arrivalTime.split(':')[0]);

            let showBus = (busName.includes(searchTerm) || busType.includes(searchTerm));

            // Apply departure time filters
            const before6am = document.getElementById('before_6am').checked;
            const from6amTo12pm = document.getElementById('6am_to_12pm').checked;
            const from12pmTo6pm = document.getElementById('12pm_to_6pm').checked;
            const after6pm = document.getElementById('after_6pm').checked;

            // Apply bus type filters
            const sleeper = document.getElementById('sleeper').checked;
            const semiSleeper = document.getElementById('ac').checked;

            // Apply arrival time filters
            const arrivalBefore6am = document.getElementById('arrival_before_6am').checked;
            const arrival6amTo12pm = document.getElementById('arrival_6am_to_12pm').checked;
            const arrival12pmTo6pm = document.getElementById('arrival_12pm_to_6pm').checked;
            const arrivalAfter6pm = document.getElementById('arrival_after_6pm').checked;

            // Check departure time
            if ((before6am && departureHour < 6) ||
                (from6amTo12pm && departureHour >= 6 && departureHour < 12) ||
                (from12pmTo6pm && departureHour >= 12 && departureHour < 18) ||
                (after6pm && departureHour >= 18) ||
                (!before6am && !from6amTo12pm && !from12pmTo6pm && !after6pm)) {
                showBus = showBus && true;
            } else {
                showBus = false;
            }

            // Check bus type
            if ((sleeper && busType.includes('sleeper')) ||
                (semiSleeper && busType.includes('semi-sleeper')) ||
                (!sleeper && !semiSleeper)) {
                showBus = showBus && true;
            } else {
                showBus = false;
            }

            // Check arrival time
            if ((arrivalBefore6am && arrivalHour < 6) ||
                (arrival6amTo12pm && arrivalHour >= 6 && arrivalHour < 12) ||
                (arrival12pmTo6pm && arrivalHour >= 12 && arrivalHour < 18) ||
                (arrivalAfter6pm && arrivalHour >= 18) ||
                (!arrivalBefore6am && !arrival6amTo12pm && !arrival12pmTo6pm && !arrivalAfter6pm)) {
                showBus = showBus && true;
            } else {
                showBus = false;
            }

            if (showBus) {
                card.closest('tr').style.display = 'table-row';
                visibleBusCount++;
            } else {
                card.closest('tr').style.display = 'none';
            }
        });

        updateBusCount(visibleBusCount);
        updateFilterCounts();
    }

    function resetFilters() {
        // Uncheck all checkboxes
        filterCheckboxes.forEach(checkbox => {
            checkbox.checked = false;
            checkbox.parentElement.classList.remove('selected');
        });

        // Clear the search input
        searchInput.value = '';

        // Show all buses
        busCards.forEach(card => {
            card.closest('tr').style.display = 'table-row';
        });

        // Update the bus count to show total number of buses
        updateBusCount(busCards.length);

        // Update filter counts
        updateFilterCounts();

        // Ensure all filter options are visible
        document.querySelectorAll('.filter_option').forEach(option => {
            option.style.display = 'flex';
        });

        // Ensure all filter section headers are visible
        document.querySelectorAll('.filter_div h6').forEach(header => {
            header.style.display = 'block';
        });
    }

    // Add event listeners for new filters
    document.getElementById('sleeper').addEventListener('change', () => applyFilters(searchInput.value));
    document.getElementById('ac').addEventListener('change', () => applyFilters(searchInput.value));
    document.getElementById('arrival_before_6am').addEventListener('change', () => applyFilters(searchInput.value));
    document.getElementById('arrival_6am_to_12pm').addEventListener('change', () => applyFilters(searchInput.value));
    document.getElementById('arrival_12pm_to_6pm').addEventListener('change', () => applyFilters(searchInput.value));
    document.getElementById('arrival_after_6pm').addEventListener('change', () => applyFilters(searchInput.value));

    const feedbackButtons = document.querySelectorAll('.feedback-btn');
    
    feedbackButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const busId = this.dataset.busId;
            const feedbackSection = document.getElementById(`feedback-section-${busId}`);
            
            if (feedbackSection.classList.contains('show')) {
                feedbackSection.classList.remove('show');
                setTimeout(() => {
                    feedbackSection.style.display = 'none';
                }, 500); // Match this delay with the CSS transition time
            } else {
                feedbackSection.style.display = 'block';
                // Force a reflow before adding the 'show' class
                feedbackSection.offsetHeight;
                feedbackSection.classList.add('show');
                fetchFeedback(busId);
            }
        });
    });

    function fetchFeedback(busId) {
        // Replace this with your actual API endpoint
        fetch(`/api/bus-feedback/${busId}/`)
            .then(response => response.json())
            .then(data => {
                updateFeedbackSection(busId, data);
            })
            .catch(error => console.error('Error fetching feedback:', error));
    }

    function updateFeedbackSection(busId, data) {
        const feedbackSection = document.getElementById(`feedback-section-${busId}`);
        const ratingSection = feedbackSection.querySelector('.rating-section');
        const feedbackListSection = feedbackSection.querySelector('.feedback-list-section');

        // Update rating section
        ratingSection.querySelector('.rating-value').textContent = data.overall_rating.toFixed(1);
        ratingSection.querySelector('.rating-count').textContent = `${data.total_ratings} Rating${data.total_ratings !== 1 ? 's' : ''}`;

        // Update rating bars
        const ratingBars = ratingSection.querySelectorAll('.rating-bar');
        data.rating_distribution.forEach((percentage, index) => {
            const bar = ratingBars[4 - index]; // 5 stars is at index 0, so we reverse
            bar.querySelector('.fill').style.width = `${percentage}%`;
            bar.querySelector('.percentage').textContent = `${percentage}%`;
        });

        // Update liked features
        const likedFeatures = ratingSection.querySelector('.liked-features');
        likedFeatures.innerHTML = data.liked_features.map(feature => `<li>${feature}</li>`).join('');

        // Update feedback list
        const feedbackList = feedbackListSection.querySelector('.feedback-list');
        feedbackList.innerHTML = data.recent_feedback.map(feedback => `
            <div class="feedback-item">
                <div class="feedback-header">
                    <span class="user-icon">👤</span>
                    <span class="user-name">${feedback.user_name}</span>
                    <span class="feedback-date">${feedback.date}</span>
                    <span class="feedback-rating">★ ${feedback.rating}</span>
                </div>
                <p class="feedback-comment">${feedback.comment}</p>
                ${feedback.could_be_better ? `<p class="feedback-improvements">Could Be Better: ${feedback.could_be_better}</p>` : ''}
            </div>
        `).join('');

        // Update view all reviews button
        const viewAllReviewsButton = feedbackListSection.querySelector('.view-all-reviews');
        viewAllReviewsButton.textContent = `View All Reviews (${data.total_ratings})`;
    }

    const viewAllReviewsButtons = document.querySelectorAll('.view-all-reviews');
    const reviewModal = document.getElementById('reviewModal');
    const closeReviewModal = document.querySelector('.close-review-modal');

    viewAllReviewsButtons.forEach(button => {
        button.addEventListener('click', function() {
            const busId = this.dataset.busId;
            fetchAllReviews(busId);
        });
    });

    closeReviewModal.addEventListener('click', function() {
        reviewModal.style.display = 'none';
    });

    window.addEventListener('click', function(event) {
        if (event.target == reviewModal) {
            reviewModal.style.display = 'none';
        }
    });

    function fetchAllReviews(busId) {
        console.log(`Fetching reviews for bus ID: ${busId}`);
        fetch(`/api/all-bus-reviews/${busId}/`)
            .then(response => {
                console.log('Response status:', response.status);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Received data:', data);
                updateReviewModal(data);
                reviewModal.style.display = 'block';
            })
            .catch(error => {
                console.error('Error fetching all reviews:', error);
                alert(`There was an error fetching the reviews: ${error.message}`);
            });
    }
    function updateReviewModal(data) {
        const overallRating = reviewModal.querySelector('.rating-value');
        const ratingBars = reviewModal.querySelector('.rating-bars');
        const reviewList = reviewModal.querySelector('.review-list');

        overallRating.textContent = data.overall_rating.toFixed(1);

        // Update rating bars
        ratingBars.innerHTML = data.rating_distribution.map((percentage, index) => `
            <div class="rating-bar">
                <span class="rating-label">${5 - index}</span>
                <div class="bar">
                    <div class="fill" style="width: ${percentage}%;"></div>
                </div>
                <span class="percentage">${percentage}%</span>
            </div>
        `).join('');

        // Update review list
        reviewList.innerHTML = data.reviews.map(review => `
            <div class="review-item">
                <div class="review-header">
                    <span class="user-icon">👤</span>
                    <span class="user-name">${review.user_name}</span>
                    <span class="review-date">${review.date}</span>
                    <span class="review-rating">★ ${review.rating}</span>
                </div>
                <p class="review-comment">${review.comment}</p>
                ${review.could_be_better ? `<p class="could-be-better">Could Be Better: ${review.could_be_better}</p>` : ''}
            </div>
        `).join('');
    }

    const imageButtons = document.querySelectorAll('.images-btn');

    imageButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const busId = this.dataset.busId;
            const imagesSection = document.getElementById(`images-section-${busId}`);
            
            if (imagesSection.classList.contains('show')) {
                imagesSection.classList.remove('show');
                setTimeout(() => {
                    imagesSection.style.display = 'none';
                }, 500); // Match this delay with the CSS transition time
            } else {
                imagesSection.style.display = 'block';
                // Force a reflow before adding the 'show' class
                imagesSection.offsetHeight;
                imagesSection.classList.add('show');
                fetchBusImages(busId);
            }
        });
    });

    function fetchBusImages(busId) {
        fetch(`/api/bus-images/${busId}/`)
            .then(response => response.json())
            .then(data => {
                updateImagesSection(busId, data);
            })
            .catch(error => console.error('Error fetching bus images:', error));
    }

    function updateImagesSection(busId, data) {
        const imagesSection = document.getElementById(`images-section-${busId}`);
        const imageGallery = imagesSection.querySelector('.image-gallery');

        if (data.images && data.images.length > 0) {
            imageGallery.innerHTML = data.images.map(image => `
                <div class="bus-image">
                    <img src="${image.url}" alt="${image.caption}">
                    <p>${image.caption}</p>
                </div>
            `).join('');
        } else {
            imageGallery.innerHTML = '<p>No images available for this bus.</p>';
        }
    }

    // Add this new function to show the max seats alert
    function showMaxSeatsAlert() {
        const alertElement = document.getElementById('max-seats-alert');
        alertElement.style.display = 'block';
        setTimeout(() => {
            alertElement.style.display = 'none';
        }, 3000);
    }
});