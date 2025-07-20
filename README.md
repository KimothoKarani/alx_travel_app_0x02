# ALX Travel App (0x00)

This project serves as a foundational backend for a travel application, inspired by platforms like Airbnb. It focuses on establishing the core database structure, data representation (serialization), and data population for properties, bookings, users, and related entities.

## Table of Contents

1.  [Project Overview](#project-overview)
2.  [Database Schema](#database-schema)
3.  [Features Implemented](#features-implemented)
4.  [Technologies Used](#technologies-used)
5.  [Getting Started](#getting-started)
    *   [Prerequisites](#prerequisites)
    *   [Cloning the Repository](#cloning-the-repository)
    *   [Virtual Environment](#virtual-environment)
    *   [Install Dependencies](#install-dependencies)
    *   [Configure Django Settings](#configure-django-settings)
    *   [Database Migrations](#database-migrations)
    *   [Database Seeding](#database-seeding)
6.  [Project Structure](#project-structure)
7.  [Further Development / Next Steps](#further-development--next-steps)
8.  [Author](#author)

## Project Overview

The `alx_travel_app_0x00` project establishes the backend infrastructure for a travel booking platform. It defines the core data models for managing user accounts, property listings, bookings, payments, and reviews. This initial phase focuses on robust database modeling, data integrity through constraints, data serialization for API readiness, and the ability to populate the database with sample data for development and testing.

## Database Schema

The application's data model is designed around the following entities and their attributes:

### User
*   `user_id`: Primary Key, UUID, Indexed
*   `first_name`: VARCHAR, NOT NULL
*   `last_name`: VARCHAR, NOT NULL
*   `email`: VARCHAR, UNIQUE, NOT NULL
*   `password_hash`: VARCHAR, NOT NULL (handled by Django's `password` field)
*   `phone_number`: VARCHAR, NULL
*   `role`: ENUM ('guest', 'host', 'admin'), NOT NULL
*   `created_at`: TIMESTAMP, DEFAULT CURRENT_TIMESTAMP
*   **Constraints**: Unique on email, Non-null on required fields.
*   **Indexes**: `email`.

### Property
*   `property_id`: Primary Key, UUID, Indexed
*   `host_id`: Foreign Key, references `User(user_id)`
*   `name`: VARCHAR, NOT NULL
*   `description`: TEXT, NOT NULL
*   `location`: VARCHAR, NOT NULL
*   `pricepernight`: DECIMAL, NOT NULL
*   `created_at`: TIMESTAMP, DEFAULT CURRENT_TIMESTAMP
*   `updated_at`: TIMESTAMP, ON UPDATE CURRENT_TIMESTAMP
*   **Constraints**: Foreign key on `host_id`, Non-null on essential attributes.
*   **Indexes**: `property_id`.

### Booking
*   `booking_id`: Primary Key, UUID, Indexed
*   `property_id`: Foreign Key, references `Property(property_id)`
*   `user_id`: Foreign Key, references `User(user_id)`
*   `start_date`: DATE, NOT NULL
*   `end_date`: DATE, NOT NULL
*   `total_price`: DECIMAL, NOT NULL
*   `status`: ENUM ('pending', 'confirmed', 'canceled'), NOT NULL
*   `created_at`: TIMESTAMP, DEFAULT CURRENT_TIMESTAMP
*   **Constraints**: Foreign keys on `property_id` and `user_id`, `status` must be one of the defined values.
*   **Indexes**: `property_id`, `booking_id`.

### Payment
*   `payment_id`: Primary Key, UUID, Indexed
*   `booking_id`: Foreign Key, references `Booking(booking_id)`
*   `amount`: DECIMAL, NOT NULL
*   `payment_date`: TIMESTAMP, DEFAULT CURRENT_TIMESTAMP
*   `payment_method`: ENUM ('credit_card', 'paypal', 'stripe'), NOT NULL
*   **Constraints**: Foreign key on `booking_id`.
*   **Indexes**: `booking_id`.

### Review
*   `review_id`: Primary Key, UUID, Indexed
*   `property_id`: Foreign Key, references `Property(property_id)`
*   `user_id`: Foreign Key, references `User(user_id)`
*   `rating`: INTEGER, CHECK: `rating >= 1 AND rating <= 5`, NOT NULL
*   `comment`: TEXT, NOT NULL
*   `created_at`: TIMESTAMP, DEFAULT CURRENT_TIMESTAMP
*   **Constraints**: Rating values (1-5), Foreign keys on `property_id` and `user_id`.
*   **Indexes**: `property_id`.

### Message
*   `message_id`: Primary Key, UUID, Indexed
*   `sender_id`: Foreign Key, references `User(user_id)`
*   `recipient_id`: Foreign Key, references `User(user_id)`
*   `message_body`: TEXT, NOT NULL
*   `sent_at`: TIMESTAMP, DEFAULT CURRENT_TIMESTAMP
*   **Constraints**: Foreign keys on `sender_id` and `recipient_id`.
*   **Indexes**: `sender_id`, `recipient_id`.

## Features Implemented

*   **Comprehensive Data Models:** Fully defined `User` (custom `AbstractUser`), `Property`, `Booking`, `Payment`, `Review`, and `Message` models in `listings/models.py`, adhering strictly to the provided database specification, including UUID primary keys, foreign key relationships, data types, and constraints.
*   **Data Serialization:** Implemented Django REST Framework serializers for `Property` and `Booking` models in `listings/serializers.py`, ensuring proper data representation, nested relationships (e.g., host/guest details within bookings), and correct handling of foreign key inputs.
*   **Database Seeding Management Command:** A custom Django management command (`seed.py`) in `listings/management/commands/` to effortlessly populate the database with realistic sample data for all defined models. This facilitates rapid development and testing.

## Technologies Used

*   **Python:** 3.x
*   **Django:** 5.x (or compatible version)
*   **Django REST Framework (DRF):** For building Web APIs.
*   **Faker:** For generating realistic dummy data for seeding the database.
*   **SQLite3:** Default database for development (can be configured for PostgreSQL, MySQL, etc.).

## Getting Started

Follow these steps to set up and run the project locally.

### Prerequisites

*   Python 3.x installed
*   `pip` (Python package installer)

### Cloning the Repository

```bash
git clone https://github.com/KimothoKarani/alx_travel_app_0x00.git
cd alx_travel_app_0x00
```
### Virtual Environment

It is highly recommended to use a virtual environment to manage project dependencies.
```
    python3 -m venv venv
    source venv/bin/activate  # On Linux/macOS
    # .\venv\Scripts\activate  # On Windows
```
### Install Dependencies

Navigate into the main Django project directory alx\_travel\_app (where manage.py resides) and install the required packages:

```
    cd alx_travel_app
    pip install djangorestframework Faker
    # You can also create a requirements.txt:
    # pip freeze > requirements.txt
    # pip install -r requirements.txt
```

### Configure Django Settings

Ensure your alx\_travel\_app/settings.py file is correctly configured:

*   **Add** :
    
       
        # alx_travel_app/settings.py
        
        INSTALLED_APPS = [
            # ... default Django apps
            'rest_framework',
            'listings', # Your application
            # ...
        ]
    
*   **Set** : This tells Django to use your custom User model defined in listings/models.py.
  
    
        # alx_travel_app/settings.py
        
        AUTH_USER_MODEL = 'listings.User'
    
 
### Database Migrations

Apply the database migrations to create the necessary tables in your database. Ensure you are in the alx\_travel\_app directory (where manage.py is).


    python manage.py makemigrations listings
    python manage.py migrate


### Database Seeding

Populate your database with sample data using the custom management command. This is very useful for testing and development.

For more details on the seeder, refer to: [listings/management/commands/README.md](https://www.google.com/url?sa=E&q=listings%2Fmanagement%2Fcommands%2FREADME.md)

*   **Basic Seeding (default quantities):**

    
        python manage.py seed
 
*   **Clear existing data and re-seed:**

    
        python manage.py seed --clear

*   **Custom seeding (e.g., 50 users, 5 properties per host):**

    
        python manage.py seed --num_users 50 --num_properties_per_host 5


## Project Structure


    alx_travel_app_0x00/
    ├── alx_travel_app/                 # Main Django project directory
    │   ├── listings/                   # Your Django app
    │   │   ├── migrations/
    │   │   ├── management/             # Directory for custom management commands
    │   │   │   └── commands/
    │   │   │       ├── __init__.py
    │   │   │       ├── seed.py         # Database seeder command
    │   │   │       └── README.md       # README for the seeder
    │   │   ├── __init__.py
    │   │   ├── admin.py
    │   │   ├── apps.py
    │   │   ├── models.py               # Database model definitions
    │   │   ├── serializers.py          # DRF Serializer definitions
    │   │   ├── tests.py
    │   │   └── views.py                # Placeholder for API views
    │   ├── alx_travel_app/             # Project configuration directory
    │   │   ├── __init__.py
    │   │   ├── asgi.py
    │   │   ├── settings.py             # Django settings
    │   │   ├── urls.py                 # Main URL configuration
    │   │   └── wsgi.py
    │   ├── manage.py                   # Django's command-line utility
    │   └── requirements.txt            # (Optional) Project dependencies
    ├── .gitignore
    └── README.md                       # This file


## Further Development / Next Steps

This project provides a solid foundation. Future development could include:

*   **API Endpoints:** Implementing ViewSets and Routers (using Django REST Framework) in listings/views.py and alx\_travel\_app/urls.py to expose the data models via a RESTful API.
    
*   **Authentication & Authorization:** Integrating token-based authentication (e.g., Djoser, Simple JWT) and robust permission handling to secure API endpoints.
    
*   **Advanced Validations:** Implementing more complex validation logic within serializers (e.g., checking property availability before booking).
    
*   **Testing:** Writing comprehensive unit and integration tests for models, serializers, and views.
    
*   **Frontend Integration:** Connecting a frontend application (e.g., React, Vue) to consume the API.
    
*   **Deployment:** Setting up the project for production deployment.
    

## Author

\[Simon Kimotho\]  
\[https://github.com/KimothoKarani\]