// app.js

// Wait for the HTML document to be fully loaded
document.addEventListener('DOMContentLoaded', () => {

    // --- Global Variables ---
    const API_URL = 'http://127.0.0.1:5000';
    let userToken = localStorage.getItem('token'); // Store the token

    // --- Element Selectors ---
    // Auth Section
    const authSection = document.getElementById('auth-section');
    const registerForm = document.getElementById('register-form');
    const registerMessage = document.getElementById('register-message');
    const loginForm = document.getElementById('login-form');
    const loginMessage = document.getElementById('login-message');

    // Main App Section
    const mainSection = document.getElementById('main-section');
    const welcomeMessage = document.getElementById('welcome-username');
    const logoutButton = document.getElementById('logout-button');
    
    // Doctors
    const doctorList = document.getElementById('doctor-list');
    const doctorSelect = document.getElementById('doctor-select');

    // Booking
    const bookingForm = document.getElementById('booking-form');
    const bookingTime = document.getElementById('booking-time');
    const bookingMessage = document.getElementById('booking-message');

    // My Appointments
    const appointmentList = document.getElementById('appointment-list');


    // --- Core Functions ---

    /**
     * 1. Registration
     */
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault(); // Stop form from reloading page
        
        const username = document.getElementById('register-username').value;
        const email = document.getElementById('register-email').value;
        const password = document.getElementById('register-password').value;

        try {
            const response = await fetch(`${API_URL}/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, email, password })
            });

            const data = await response.json();

            if (response.ok) {
                registerMessage.textContent = data.message;
                registerMessage.style.color = 'green';
                registerForm.reset();
            } else {
                throw new Error(data.error);
            }
        } catch (error) {
            registerMessage.textContent = `Error: ${error.message}`;
            registerMessage.style.color = 'red';
        }
    });

    /**
     * 2. Login
     */
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;

        try {
            const response = await fetch(`${API_URL}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });

            const data = await response.json();

            if (response.ok) {
                // IMPORTANT: Store the token
                userToken = data.access_token;
                localStorage.setItem('token', userToken);
                
                loginMessage.textContent = "Login successful!";
                loginMessage.style.color = 'green';
                
                // Show the main app
                showMainApp();
            } else {
                throw new Error(data.error);
            }
        } catch (error) {
            loginMessage.textContent = `Error: ${error.message}`;
            loginMessage.style.color = 'red';
        }
    });

    /**
     * 3. Logout
     */
    logoutButton.addEventListener('click', () => {
        userToken = null;
        localStorage.removeItem('token');
        showAuthSection();
    });

    /**
     * 4. Fetch Doctors
     * (Called when app loads)
     */
    async function fetchDoctors() {
        try {
            const response = await fetch(`${API_URL}/api/doctors`);
            if (!response.ok) throw new Error('Could not fetch doctors.');
            
            const data = await response.json();

            // Clear old data
            doctorList.innerHTML = '';
            doctorSelect.innerHTML = '';

            // Create a default "please select" option
            const defaultOption = document.createElement('option');
            defaultOption.value = "";
            defaultOption.textContent = "-- Select a Doctor --";
            doctorSelect.appendChild(defaultOption);

            // Populate list and dropdown
            data.doctors.forEach(doc => {
                // Add to list
                const docDiv = document.createElement('div');
                docDiv.innerHTML = `<strong>${doc.full_name}</strong> (${doc.specialty})`;
                doctorList.appendChild(docDiv);

                // Add to dropdown
                const docOption = document.createElement('option');
                docOption.value = doc.id;
                docOption.textContent = `${doc.full_name} - ${doc.specialty}`;
                doctorSelect.appendChild(docOption);
            });

        } catch (error) {
            doctorList.textContent = error.message;
        }
    }

    /**
     * 5. Fetch User's Appointments
     * (Called when app loads)
     */
    async function fetchAppointments() {
        if (!userToken) return; // Don't run if logged out

        try {
            const response = await fetch(`${API_URL}/api/appointments`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${userToken}`
                }
            });

            if (!response.ok) throw new Error('Could not fetch appointments.');
            
            const data = await response.json();
            appointmentList.innerHTML = ''; // Clear old list

            if (data.appointments.length === 0) {
                appointmentList.textContent = 'You have no appointments.';
                return;
            }

            // Populate appointment list
            const ul = document.createElement('ul');
            data.appointments.forEach(appt => {
                const li = document.createElement('li');
                // Format the time to be more readable
                const time = new Date(appt.appointment_time).toLocaleString();
                
                // ADD THE CANCEL BUTTON HERE
                li.innerHTML = `
                    <span>
                        <strong>${time}</strong> 
                        with ${appt.doctor_name} (${appt.specialty})
                        - <i>Status: ${appt.status}</i>
                    </span>
                    <button class="cancel-btn" data-id="${appt.id}">Cancel</button>
                `;
                ul.appendChild(li);
            });
            appointmentList.appendChild(ul);

        } catch (error) {
            appointmentList.textContent = error.message;
        }
    }

    /**
     * 6. Book Appointment
     */
    bookingForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const doctorId = doctorSelect.value;
        const time = bookingTime.value; // This is already in "YYYY-MM-DDTHH:MM" format

        if (!doctorId) {
            bookingMessage.textContent = 'Please select a doctor.';
            bookingMessage.style.color = 'red';
            return;
        }

        try {
            const response = await fetch(`${API_URL}/api/appointments`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${userToken}`
                },
                body: JSON.stringify({
                    doctor_id: doctorId,
                    appointment_time: `${time}:00` // Add seconds for ISO format
                })
            });

            const data = await response.json();

            if (response.ok) {
                bookingMessage.textContent = data.message;
                bookingMessage.style.color = 'green';
                bookingForm.reset();
                // Refresh the appointment list
                fetchAppointments(); 
            } else {
                throw new Error(data.error);
            }

        } catch (error) {
            bookingMessage.textContent = `Error: ${error.message}`;
            bookingMessage.style.color = 'red';
        }
    });

    // app.js (add this new block)

    /**
     * 7. Cancel Appointment
     * We use event delegation on the list itself.
     */
    appointmentList.addEventListener('click', async (e) => {
        // Only run if the clicked element has the 'cancel-btn' class
        if (e.target.classList.contains('cancel-btn')) {
            
            // Get the appointment ID from the button's data-id attribute
            const appointmentId = e.target.dataset.id;
            
            // Confirm with the user
            if (!confirm('Are you sure you want to cancel this appointment?')) {
                return; // Stop if they click 'Cancel'
            }

            try {
                const response = await fetch(`${API_URL}/api/appointments/${appointmentId}`, {
                    method: 'DELETE',
                    headers: {
                        'Authorization': `Bearer ${userToken}`
                    }
                });

                const data = await response.json();

                if (response.ok) {
                    alert(data.message); // Show success message
                    fetchAppointments(); // Refresh the appointment list
                } else {
                    throw new Error(data.error);
                }

            } catch (error) {
                alert(`Error: ${error.message}`);
            }
        }
    });


    // --- UI Control Functions ---

    function showMainApp() {
        authSection.style.display = 'none';
        mainSection.style.display = 'block';
        // When we show the main app, load the data
        fetchDoctors();
        fetchAppointments();
    }

    function showAuthSection() {
        mainSection.style.display = 'none';
        authSection.style.display = 'block';
    }

    // --- Initial Page Load Logic ---
    if (userToken) {
        // If the user already has a token, show the main app
        showMainApp();
    } else {
        // Otherwise, show the login/register forms
        showAuthSection();
    }

});