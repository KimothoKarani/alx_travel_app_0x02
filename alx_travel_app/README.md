# ALX Travel App (0x02): Secure Travel Booking with Chapa Payment Integration

## Overview

This project is a Django-based travel booking application, an evolution of alx\_travel\_app\_0x01. The primary focus of this iteration (0x02) is the robust integration of the **Chapa Payment Gateway** to enable secure and efficient online payment processing for bookings. The application supports user authentication, property listings, booking management, reviews, messaging, and now, a complete payment lifecycle including initiation, verification, and automated email confirmations.

## Features

*   **User Management:** Secure user registration, authentication (JWT), and profile management with distinct roles (Guest, Host, Admin).
    
*   **Property Listings:** Create, view, update, and delete property listings with detailed information (name, description, location, price per night).
    
*   **Booking System:** Users can book properties, and hosts can manage bookings for their properties.
    
*   **Reviews & Ratings:** Users can leave reviews and ratings for properties they have booked.
    
*   **Messaging System:** Threaded messaging for communication between users (e.g., guest-to-host).
    
*   **Comprehensive Chapa Payment Integration:**
    
    *   **Secure Credential Management:** API keys stored safely using environment variables (dotenv).
        
    *   **Payment Model:** Dedicated Django model (Payment) for tracking transaction details, status, and Chapa's unique identifiers.
        
    *   **Payment Initiation API:** Endpoint to initiate payments with Chapa, generating a secure checkout URL.
        
    *   **Payment Verification API:** Callback endpoint to verify payment status with Chapa after user redirection.
        
    *   **Payment Status Handling:** Updates internal payment and booking records based on Chapa's response (Pending, Completed, Failed).
        
    *   **Asynchronous Email Notifications:** Uses Celery to send automated payment confirmation emails in the background, ensuring a responsive user experience.
        
    
*   **API Documentation:** Self-generating OpenAPI (Swagger UI/Redoc) documentation using drf-spectacular.
    

## Project Structure (Key Files)



    alx_travel_app_0x02/
    ├── alx_travel_app/
    │   ├── __init__.py           # Includes Celery app setup
    │   ├── settings.py           # Django settings, Chapa credentials, Celery config
    │   ├── urls.py               # Main project URL configurations (admin, API, JWT, docs)
    │   └── celery.py             # Celery application instance definition
    ├── listings/
    │   ├── models.py             # Defines Django models (User, Property, Booking, Payment, Review, Message) - Payment model updated
    │   ├── serializers.py        # DRF serializers for API data validation and serialization - PaymentSerializer updated
    │   ├── views.py              # DRF ViewSets for CRUD operations + Chapa payment initiation/verification views
    │   ├── urls.py               # App-specific URL patterns (DRF router, Chapa endpoints)
    │   └── tasks.py              # (Optional, but good practice if more Celery tasks are added)
    ├── .env.example              # Example .env file (DO NOT COMMIT YOUR ACTUAL .env)
    ├── .gitignore                # Ensures sensitive files (.env) are not committed
    └── manage.py                 # Django's command-line utility

## Setup and Installation

Follow these steps to get the project running on your local machine.

### Prerequisites

*   Python 3.8+
    
*   PostgreSQL
    
*   Redis (for Celery message broker)
    

### 1\. Clone the Repository



    git clone https://github.com/yourusername/alx_travel_app_0x02.git
    cd alx_travel_app_0x02

### 2\. Set Up a Virtual Environment

It's highly recommended to use a virtual environment to manage dependencies.



    python3 -m venv venv
    source venv/bin/activate # On Windows: .\venv\Scripts\activate

### 3\. Install Dependencies

Install all required Python packages:



    pip install -r requirements.txt
    # If requirements.txt is not provided, manually install:
    pip install Django djangorestframework djangorestframework-simplejwt drf-spectacular psycopg2-binary python-dotenv requests celery redis

### 4\. Database Setup (PostgreSQL)

*   Create a PostgreSQL database for your project.
    
    codeSQL
    
        CREATE DATABASE alx_travel_app;
        CREATE USER alx_user WITH PASSWORD 'your_password';
        GRANT ALL PRIVILEGES ON DATABASE alx_travel_app TO alx_user;
    
*   Configure your database settings in alx\_travel\_app/alx\_travel\_app/settings.py:
    
    codePython
    
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': 'alx_travel_app',
                'USER': 'alx_user',
                'PASSWORD': 'your_password',
                'HOST': 'localhost', # Or your database host
                'PORT': '5432',
            }
        }
    

### 5\. Chapa API Credentials

*   **Create a Chapa Account:**  
    Go to [https://developer.chapa.co/](https://www.google.com/url?sa=E&q=https%3A%2F%2Fdeveloper.chapa.co%2F) and sign up. You will get access to your **Test Secret Key** from your dashboard (usually under settings or API keys). It typically starts with sk\_test\_.
    
*   **Create**   
    In the root of your alx\_travel\_app\_0x02/alx\_travel\_app/ directory (where manage.py is), create a file named .env.
    
*   **Add your Secret Key:**
    
    codeCode
    
        CHAPA_SECRET_KEY="sk_test_YOUR_CHAPA_TEST_SECRET_KEY"
    
    **Important:** Ensure .env is listed in your .gitignore file to prevent committing sensitive information to your repository.
    

### 6\. Run Database Migrations

Apply the database schema changes, including the updated Payment model:



    python manage.py makemigrations
    python manage.py migrate

### 7\. Create a Superuser (Optional, for Admin Access)



    python manage.py createsuperuser

Follow the prompts to create an admin user for accessing the Django admin panel.

### 8\. Start Redis Server

Ensure your Redis server is running.

*   **On Linux (Ubuntu/Debian):** sudo systemctl start redis-server or redis-server
    
*   **On macOS (Homebrew):** brew services start redis or redis-server
    
*   **On Windows:** Follow Redis installation guides for Windows.
    

### 9\. Start Celery Worker

In a **separate terminal window** from your Django server, navigate to the project root (alx\_travel\_app\_0x02/) and start the Celery worker:



    celery -A alx_travel_app worker -l info

This worker will process background tasks like sending payment confirmation emails. Keep this terminal open while testing.

### 10\. Start Django Development Server

In your main terminal window, start the Django server:



    python manage.py runserver

The API will now be accessible at http://127.0.0.1:8000/.

## API Endpoints

The API is self-documented using drf-spectacular. You can explore all endpoints and their schemas via:

*   **Swagger UI:** http://127.0.0.1:8000/api/docs/
    
*   **Redoc:** http://127.0.0.1:8000/api/redoc/
    
*   **OpenAPI Schema:** http://127.0.0.1:8000/api/schema/
    

### Key Endpoints for Chapa Integration

*   **POST /api/payments/chapa/initiate/**
    
    *   **Description:** Initiates a payment process with the Chapa gateway for a specific booking.
        
    *   **Authentication:** Required (User must be authenticated).
        
    *   **Request Body (JSON):**
        
        
        
            {
                "booking_id": "string (UUID of the booking)",
                "amount": "decimal (total price of the booking)"
            }
        
    *   **Response (JSON):**

            {
                "status": "success",
                "checkout_url": "https://api.chapa.co/v1/hosted/checkout/...",
                "tx_ref": "your-internal-transaction-reference"
            }
        
        The checkout\_url should be used to redirect the user's browser.
        
    
*   **GET /api/payments/chapa/verify/{tx\_ref}/**
    
    *   **Description:** This is the callback URL provided to Chapa during initiation. Chapa redirects the user's browser to this endpoint after payment completion (success or failure). This endpoint verifies the payment status directly with Chapa's API and updates the internal payment and booking records.
        
    *   **Authentication:** Not strictly required by Chapa for the redirect, but the view performs internal authentication checks for safety if the user is logged in.
        
    *   **Parameters:** tx\_ref (path parameter, your unique transaction reference).
        
    *   **Response:** Redirects to /payment-success/ or /payment-fail/ after processing.
        
    

## Payment Workflow

*   **Create Booking:** A user creates a booking via POST /api/bookings/. The booking status is initially pending.
    
*   **Initiate Payment:** The frontend (after booking creation) makes a POST request to http://127.0.0.1:8000/api/payments/chapa/initiate/ with the booking\_id and amount.
    
*   **Redirect to Chapa:** The backend returns Chapa's checkout\_url. The frontend redirects the user's browser to this URL.
    
*   **User Pays on Chapa's Site:** The user enters their payment details on Chapa's secure hosted page.
    
*   **Chapa Callback & Verification:** Chapa redirects the user's browser back to http://127.0.0.1:8000/api/payments/chapa/verify/{tx\_ref}/.
    
    *   Your backend verifies the transaction's definitive status with Chapa's API.
        
    *   The Payment record's status is updated (e.g., COMPLETED, FAILED).
        
    *   If successful, the associated Booking status is updated to CONFIRMED.
        
    *   A Celery task is dispatched to send a confirmation email.
        
    
*   **User Lands on Status Page:** The user is redirected to a success or failure page on your application (e.g., /payment-success/ or /payment-fail/).
    

## Testing Chapa Payment Integration (Sandbox)

To fully test the payment flow, you'll use Chapa's sandbox environment.

*   **Ensure all servers are running:** Django server, Redis server, and Celery worker.
    
*   **Obtain Test API Key:** Make sure your CHAPA\_SECRET\_KEY in .env is your **test** secret key from Chapa's developer dashboard.
    
*   **Create Test Data:**
    
    *   Create a User (e.g., via createsuperuser or your registration API).
        
    *   Create a Property (via admin or API).
        
    *   Create a Booking for the User and Property (e.g., POST to /api/bookings/). Note the booking\_id and total\_price.
        
    
*   **Initiate Payment:**
    
    *   Using a tool like Postman, Insomnia, or a simple curl command, make a POST request to http://127.0.0.1:8000/api/payments/chapa/initiate/.
        
    *   **Headers:** Include Authorization: Bearer YOUR\_JWT\_TOKEN (get a token from /api/token/).
        
    *   **Body (JSON):**
        
    
        
            {
                "booking_id": "THE_UUID_OF_YOUR_TEST_BOOKING",
                "amount": 123.45 # Make sure this matches your booking's total_price
            }
        
    
*   **Redirect to Chapa:**
    
    *   From the response of the initiate call, copy the checkout\_url.
        
    *   Paste this URL into your web browser. You will be redirected to Chapa's sandbox payment page.
        
    
*   **Complete Payment on Chapa:**
    
    *   Follow the instructions on Chapa's sandbox page. Use the provided test card numbers (often generic like "4444...4444" or specific ones detailed in Chapa's docs) and any dummy details.
        
    
*   **Observe Results:**
    
    *   **Browser:** After payment, your browser should redirect back to your Django app (e.g., http://127.0.0.1:8000/payment-success/).
        
    *   **Django Server Console:** You should see DEBUG logs from initiate\_chapa\_payment and verify\_chapa\_payment indicating the API calls and status updates.
        
    *   **Celery Worker Console:** If the payment was successful, you should see the DEBUG message from the send\_payment\_confirmation\_email task.
        
    *   **Django Admin:** Log in to http://127.0.0.1:8000/admin/.
        
        *   Navigate to Listings -> Payments. Find your payment record; its status should be COMPLETED and chapa\_transaction\_id populated.
            
        *   Navigate to Listings -> Bookings. The associated booking's status should be confirmed.
            
        
    


## Future Improvements / Considerations

*   **Webhooks:** For truly robust payment processing, consider implementing Chapa webhooks in addition to the redirect-based verification. Webhooks allow Chapa to notify your server directly and asynchronously about payment status changes, making your system more resilient to user browser issues.
    
*   **Frontend Integration:** Develop a user-friendly frontend (e.g., with React, Vue, or simple Django templates) that smoothly handles the payment redirection and displays appropriate success/failure messages.
    
*   **Detailed Error Messages:** Enhance error handling to provide more specific and actionable messages to users and for debugging.
    
*   **Refunds/Cancellations:** Implement API endpoints and logic for handling refunds or cancellations of payments.
    
*   **Payment History:** Develop richer views/reporting for users and administrators to track payment history.
    
*   **Concurrency & Locking:** For high-volume applications, consider database transaction locking to prevent race conditions during payment status updates.