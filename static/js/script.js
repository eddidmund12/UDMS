let lastOtpSent = 0;

document.addEventListener('DOMContentLoaded', function () {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('keyup', function () {
            const filter = searchInput.value.toLowerCase();
            const table = document.getElementById('logsTable');
            if (!table) return;
            const trs = table.getElementsByTagName('tr');

            for (let i = 1; i < trs.length; i++) { // start from 1 to skip header row
                const tds = trs[i].getElementsByTagName('td');
                let textContent = '';
                for (let j = 0; j < tds.length; j++) {
                    textContent += tds[j].textContent.toLowerCase() + ' ';
                }
                if (textContent.indexOf(filter) > -1) {
                    trs[i].style.display = '';
                } else {
                    trs[i].style.display = 'none';
                }
            }
        });
    }

    // Age validator
    const dobInput = document.getElementById('dob');
    if (dobInput) {
        dobInput.addEventListener('input', validateAge);
    }

    // Signup form validators
    document.getElementById('firstname').addEventListener('input', validateFirstname);
    document.getElementById('lastname').addEventListener('input', validateLastname);
    document.getElementById('sex').addEventListener('change', validateSex);
    document.getElementById('email').addEventListener('input', validateEmail);

    // Form submit validation
    const form = document.querySelector('.signup-container');
    if (form) {
        form.addEventListener('submit', function(e) {
            validateFirstname();
            validateLastname();
            validateSex();
            validateEmail();
            validatePassword(document.getElementById('password'));
            validateConfirmPassword();
            validateAge();
            const errors = document.querySelectorAll('.error[style*="display: block"]');
            if (errors.length > 0) {
                e.preventDefault();
            }
        });
    }

    // Show OTP modal if it exists (after signup OTP sent)
    const otpModal = document.getElementById('otpModal');
    if (otpModal) {
        otpModal.classList.add('show');
        // Countdown for resend
        const now = Date.now() / 1000;
        const lastSent = lastOtpSent;
        if (lastSent) {
            const remaining = 60 - (now - lastSent);
            if (remaining > 0) {
                const resendLink = document.getElementById('resendOtp');
                resendLink.style.pointerEvents = 'none';
                resendLink.style.color = 'gray';
                const countdownEl = document.getElementById('countdown');
                countdownEl.textContent = `in ${Math.ceil(remaining)}s`;
                const interval = setInterval(() => {
                    const rem = 60 - (Date.now()/1000 - lastSent);
                    if (rem <= 0) {
                        clearInterval(interval);
                        resendLink.style.pointerEvents = 'auto';
                        resendLink.style.color = '';
                        countdownEl.textContent = '';
                    } else {
                        countdownEl.textContent = `in ${Math.ceil(rem)}s`;
                    }
                }, 1000);
            }
        }
    }

    // Password toggle functions (assuming they exist or add if needed)
    // If togglePassword is called but not defined, add it
});

function validatePassword(input) {
    const feedback = document.getElementById('password-feedback');
    const pattern = /^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{6,}$/;
    if (!input.value.trim()) {
        feedback.innerHTML = 'Password is required';
        feedback.style.display = 'block';
    } else if (!pattern.test(input.value)) {
        feedback.innerHTML = 'Password cannot be less than six characters.<br />Must contain letters and numbers.';
        feedback.style.display = 'block';
    } else {
        feedback.style.display = 'none';
    }
}

function validateConfirmPassword() {
    const password = document.getElementById('password');
    const confirmPassword = document.getElementById('c-password');
    const feedback = document.getElementById('confirm-feedback');
    if (!confirmPassword.value.trim()) {
        feedback.textContent = 'This field is required';
        feedback.style.display = 'block';
    } else if (password.value !== confirmPassword.value) {
        feedback.textContent = 'Passwords do not match.';
        feedback.style.display = 'block';
    } else {
        feedback.style.display = 'none';
    }
}

function validateAge() {
    const dobInput = document.getElementById('dob');
    const ageError = document.getElementById('ageError');
    if (!dobInput.value) {
        ageError.textContent = 'Date of birth is required';
        ageError.style.display = 'block';
        return;
    }
    const dob = new Date(dobInput.value);
    const today = new Date();
    let age = today.getFullYear() - dob.getFullYear();
    const monthDiff = today.getMonth() - dob.getMonth();
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < dob.getDate())) {
        age--;
    }
    if (age < 18) {
        ageError.textContent = 'You must be at least 18 years old.';
        ageError.style.display = 'block';
    } else {
        ageError.textContent = '';
        ageError.style.display = 'none';
    }
}

function validateFirstname() {
    const input = document.getElementById('firstname');
    const error = document.getElementById('firstname-error');
    if (!input.value.trim()) {
        error.style.display = 'block';
    } else {
        error.style.display = 'none';
    }
}

function validateLastname() {
    const input = document.getElementById('lastname');
    const error = document.getElementById('lastname-error');
    if (!input.value.trim()) {
        error.style.display = 'block';
    } else {
        error.style.display = 'none';
    }
}

function validateSex() {
    const input = document.getElementById('sex');
    const error = document.getElementById('sex-error');
    if (!input.value) {
        error.style.display = 'block';
    } else {
        error.style.display = 'none';
    }
}

function validateImage() {
    const input = document.getElementById('image');
    const error = document.getElementById('image-error');
    if (!input.value){
        error.textContent = 'This field is required';
        error.style.display = 'block';
    } else {
        error.style.display = 'block';
    }
}
function validateEmail() {
    const input = document.getElementById('email');
    const error = document.getElementById('email-error');
    const emailPattern = /^[a-zA-Z0-9._%+-]+@(gmail\.com|yahoo\.com|outlook\.com|icloud\.com)$/;
    if (!input.value.trim()) {
        error.textContent = 'Email is required';
        error.style.display = 'block';
    } else if (!emailPattern.test(input.value)) {
        error.textContent = '';
        error.style.display = 'block';
    } else {
        error.style.display = 'none';
    }
}

function togglePassword(inputId, element) {
    const input = document.getElementById(inputId);
    const eyeIcon = element.querySelector('svg');
    if (input.type === 'password') {
        input.type = 'text';
        eyeIcon.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21"/>';
    } else {
        input.type = 'password';
        eyeIcon.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>';
    }
}

function resendOtp() {
    fetch('/resend_otp', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        if (data.success) {
            // Reset countdown
            lastOtpSent = Date.now() / 1000;
            const resendLink = document.getElementById('resendOtp');
            resendLink.style.pointerEvents = 'none';
            resendLink.style.color = 'gray';
            const countdownEl = document.getElementById('countdown');
            countdownEl.textContent = 'in 60s';
            const interval = setInterval(() => {
                const rem = 60 - (Date.now()/1000 - lastOtpSent);
                if (rem <= 0) {
                    clearInterval(interval);
                    resendLink.style.pointerEvents = 'auto';
                    resendLink.style.color = '';
                    countdownEl.textContent = '';
                } else {
                    countdownEl.textContent = `in ${Math.ceil(rem)}s`;
                }
            }, 1000);
        }
    })
    .catch(error => {
        alert('Error resending OTP');
    });
}

// Close modal when clicking outside of it
window.onclick = function(event) {
    var modal = document.getElementById('otpModal');
    if (modal && event.target == modal) {
        modal.style.display = "none";
    }
}

    let deleteUrl = null;
    document.querySelectorAll('.delete-link').forEach(function(link) {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            deleteUrl = this.getAttribute('data-href');
            document.getElementById('deleteModal').style.display = 'flex';
        });
    });
    document.getElementById('cancelDeleteBtn').onclick = function() {
        document.getElementById('deleteModal').style.display = 'none';
        deleteUrl = null;
    };
    document.getElementById('confirmDeleteBtn').onclick = function() {
        if(deleteUrl) {
            window.location.href = deleteUrl;
        }
    };
    // Close modal on outside click
    document.getElementById('deleteModal').onclick = function(e) {
        if(e.target === this) {
            this.style.display = 'none';
            deleteUrl = null;
        }
    };