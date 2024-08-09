$(document).ready(function() {
    var debounceTimer;
    var emailAvailable = false;

    function debounce(func, delay) {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(func, delay);
    }

    function showError(field, message) {
        const errorDiv = field.next('.error-message');
        if (errorDiv.length === 0) {
            field.after('<div class="error-message text-danger">' + message + '</div>');
        } else {
            errorDiv.text(message);
        }
        field.addClass('is-invalid');
    }

    function clearError(field) {
        field.next('.error-message').remove();
        field.removeClass('is-invalid');
    }

    function validateName(field) {
        const value = field.val().trim();
        if (value === '') {
            showError(field, 'This field is required.');
            return false;
        } else if (/\d/.test(value)) {
            showError(field, 'Name should not contain numbers.');
            return false;
        }
        clearError(field);
        return true;
    }

    function validateEmail(field) {
        const value = field.val().trim();
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (value === '') {
            showError(field, 'Email is required.');
            return false;
        } else if (!emailRegex.test(value)) {
            showError(field, 'Please enter a valid email address.');
            return false;
        }
        
        // Check email availability
        $.ajax({
            url: '/check-email/',  // Make sure this matches your URL configuration
            method: 'POST',
            data: { 
                email: value,
                csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val()
            },
            success: function(response) {
                if (response.available) {
                    clearError(field);
                    emailAvailable = true;
                } else {
                    showError(field, 'This email is already taken.');
                    emailAvailable = false;
                }
            },
            error: function(xhr, status, error) {
                console.error("Error checking email:", error);
                showError(field, 'An error occurred while checking email availability.');
            }
        });

        return true; // We return true here because the actual availability is checked asynchronously
    }

    function validatePassword(field) {
        const value = field.val();
        const passwordRegex = /^(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*])[A-Za-z\d!@#$%^&*]{8,}$/;
        if (value === '') {
            showError(field, 'Password is required.');
            return false;
        } else if (!passwordRegex.test(value)) {
            showError(field, 'Password must be at least 8 characters long, contain one uppercase letter, one number, and one special character.');
            return false;
        }
        clearError(field);
        return true;
    }

    function validatePasswordConfirm(field) {
        const password = $('#password').val();
        const confirmPassword = field.val();
        if (confirmPassword === '') {
            showError(field, 'Please confirm your password.');
            return false;
        } else if (password !== confirmPassword) {
            showError(field, 'Passwords do not match.');
            return false;
        }
        clearError(field);
        return true;
    }

    function validatePhone(field) {
        const value = field.val().trim();
        const phoneRegex = /^\+?[\d\s-]{10,15}$/;
        if (value === '') {
            showError(field, 'Phone number is required.');
            return false;
        } else if (!phoneRegex.test(value)) {
            showError(field, 'Please enter a valid phone number.');
            return false;
        }
        clearError(field);
        return true;
    }

    // Real-time validation
    $('#fname, #lname').on('input', function() {
        debounce(() => validateName($(this)), 300);
    });

    $('#email').on('input', function() {
        debounce(() => validateEmail($(this)), 300);
    });

    $('#password').on('input', function() {
        debounce(() => validatePassword($(this)), 300);
    });

    $('#re-password').on('input', function() {
        debounce(() => validatePasswordConfirm($(this)), 300);
    });

    $('#phone').on('input', function() {
        debounce(() => validatePhone($(this)), 300);
    });

    // Form submission
    $('#signup-form').on('submit', function(e) {
        e.preventDefault();

        const isFirstNameValid = validateName($('#fname'));
        const isLastNameValid = validateName($('#lname'));
        const isEmailValid = validateEmail($('#email'));
        const isPasswordValid = validatePassword($('#password'));
        const isPasswordConfirmValid = validatePasswordConfirm($('#re-password'));
        const isPhoneValid = validatePhone($('#phone'));

        if (isFirstNameValid && isLastNameValid && isEmailValid && isPasswordValid && isPasswordConfirmValid && isPhoneValid && emailAvailable) {
            // If all validations pass, submit the form
            this.submit();
        }
    });
});