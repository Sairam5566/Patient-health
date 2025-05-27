// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Add fade-in animation to elements
    const fadeElements = document.querySelectorAll('.fade-in');
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    });

    fadeElements.forEach(element => {
        observer.observe(element);
    });

    // Auto-hide alerts after 5 seconds
    var alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            alert.classList.add('fade');
            setTimeout(function() {
                alert.remove();
            }, 150);
        }, 5000);
    });

    // Form validation
    var forms = document.querySelectorAll('.needs-validation');
    Array.prototype.slice.call(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // Add loading state to buttons
    const buttons = document.querySelectorAll('button[type="submit"]');
    buttons.forEach(button => {
        button.addEventListener('click', function() {
            if (this.form && this.form.checkValidity()) {
                this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Loading...';
                this.disabled = true;
            }
        });
    });

    // Handle file input changes
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            const fileName = this.files[0]?.name;
            const label = this.nextElementSibling;
            if (label && fileName) {
                label.textContent = fileName;
            }
        });
    });

    // Add smooth scrolling to all links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Initialize Feather icons
    if (typeof feather !== 'undefined') {
        feather.replace();
    }

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Dynamic appointment status updates
    var appointmentStatusSelects = document.querySelectorAll('.appointment-status-select');
    appointmentStatusSelects.forEach(function(select) {
        select.addEventListener('change', function() {
            var appointmentId = this.dataset.appointmentId;
            var status = this.value;
            
            fetch('/api/appointments/' + appointmentId + '/status', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ status: status })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showAlert('Status updated successfully', 'success');
                } else {
                    showAlert('Failed to update status', 'danger');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showAlert('An error occurred', 'danger');
            });
        });
    });

    // Set maximum date for date of birth to today
    var dateOfBirthInputs = document.querySelectorAll('input[name*="date_of_birth"]');
    dateOfBirthInputs.forEach(function(input) {
        input.max = formatDate(new Date());
    });
});

// Show alert function
function showAlert(message, type) {
    var alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-' + type + ' alert-dismissible fade show';
    alertDiv.role = 'alert';
    alertDiv.innerHTML = message +
        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>';
    
    var alertContainer = document.querySelector('.alert-container');
    if (!alertContainer) {
        alertContainer = document.createElement('div');
        alertContainer.className = 'alert-container';
        document.querySelector('main').prepend(alertContainer);
    }
    
    alertContainer.appendChild(alertDiv);
    
    setTimeout(function() {
        alertDiv.classList.add('fade');
        setTimeout(function() {
            alertDiv.remove();
        }, 150);
    }, 5000);
}

// Handle file uploads with preview
function handleFileUpload(input) {
    if (input.files && input.files[0]) {
        var reader = new FileReader();
        
        reader.onload = function(e) {
            var preview = document.querySelector('#file-preview');
            if (preview) {
                if (input.files[0].type.startsWith('image/')) {
                    preview.innerHTML = '<img src="' + e.target.result + '" class="img-fluid">';
                } else {
                    preview.innerHTML = '<div class="alert alert-info">File selected: ' + input.files[0].name + '</div>';
                }
            }
        }
        
        reader.readAsDataURL(input.files[0]);
    }
}

// Format date inputs
function formatDate(date) {
    var d = new Date(date),
        month = '' + (d.getMonth() + 1),
        day = '' + d.getDate(),
        year = d.getFullYear();

    if (month.length < 2) month = '0' + month;
    if (day.length < 2) day = '0' + day;

    return [year, month, day].join('-');
}

// Set minimum date for appointment booking
var appointmentDateInputs = document.querySelectorAll('input[name*="appointment_date"]');
appointmentDateInputs.forEach(function(input) {
    input.min = formatDate(new Date());
});

// Initialize Bootstrap tooltips and popovers
document.addEventListener('DOMContentLoaded', function() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
});

// Flash message auto-dismiss
document.addEventListener('DOMContentLoaded', function() {
    var alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        if (!alert.classList.contains('alert-danger')) {
            setTimeout(function() {
                var bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }, 5000);
        }
    });
});

// Form validation
document.addEventListener('DOMContentLoaded', function() {
    var forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
});

// Confirm delete actions
document.addEventListener('DOMContentLoaded', function() {
    var deleteButtons = document.querySelectorAll('[data-confirm]');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(event) {
            if (!confirm(this.dataset.confirm || 'Are you sure you want to delete this item?')) {
                event.preventDefault();
            }
        });
    });
});

// File input preview
document.addEventListener('DOMContentLoaded', function() {
    var fileInputs = document.querySelectorAll('input[type="file"][data-preview]');
    fileInputs.forEach(function(input) {
        input.addEventListener('change', function() {
            var preview = document.querySelector(this.dataset.preview);
            if (preview && this.files && this.files[0]) {
                var reader = new FileReader();
                reader.onload = function(e) {
                    preview.src = e.target.result;
                };
                reader.readAsDataURL(this.files[0]);
            }
        });
    });
});

// Dynamic form fields
function addFormField(containerId, template) {
    var container = document.getElementById(containerId);
    var index = container.children.length;
    var newField = template.replace(/__index__/g, index);
    container.insertAdjacentHTML('beforeend', newField);
}

function removeFormField(element) {
    element.closest('.form-group').remove();
}

// AJAX form submission
function submitFormAjax(form, successCallback, errorCallback) {
    var formData = new FormData(form);
    fetch(form.action, {
        method: form.method,
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            if (successCallback) successCallback(data);
        } else {
            if (errorCallback) errorCallback(data);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        if (errorCallback) errorCallback({ message: 'An error occurred. Please try again.' });
    });
}

// Date formatting
function formatDate(date) {
    return new Date(date).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

// Time formatting
function formatTime(time) {
    return new Date('1970-01-01T' + time).toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
    });
}

// Format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

// Format phone number
function formatPhoneNumber(phoneNumber) {
    var cleaned = ('' + phoneNumber).replace(/\D/g, '');
    var match = cleaned.match(/^(\d{3})(\d{3})(\d{4})$/);
    if (match) {
        return '(' + match[1] + ') ' + match[2] + '-' + match[3];
    }
    return phoneNumber;
}

// Debounce function for search inputs
function debounce(func, wait) {
    var timeout;
    return function() {
        var context = this;
        var args = arguments;
        clearTimeout(timeout);
        timeout = setTimeout(function() {
            func.apply(context, args);
        }, wait);
    };
} 