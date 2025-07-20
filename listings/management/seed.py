# alx_travel_app/listings/management/commands/seed.py

import uuid
from datetime import timedelta
import random
import decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker

# Import all models from your listings app
from listings.models import CustomUser, Property, Booking, Payment, Review, Message

fake = Faker()


class Command(BaseCommand):
    help = 'Seeds the database with sample data for users, properties, bookings, payments, reviews, and messages.'

    def add_arguments(self, parser):
        parser.add_argument('--num_users', type=int, default=10, help='Number of sample users.')
        parser.add_argument('--num_properties_per_host', type=int, default=3,
                            help='Number of properties per host user.')
        parser.add_argument('--num_bookings_per_guest', type=int, default=2,
                            help='Max number of bookings per guest user.')
        parser.add_argument('--num_reviews_per_booking', type=float, default=0.8,
                            help='Probability (0.0-1.0) of a review per booking.')
        parser.add_argument('--num_messages', type=int, default=20, help='Number of messages to create.')
        parser.add_argument('--clear', action='store_true', help='Clear existing data before seeding.')

    def handle(self, *args, **options):
        num_users = options['num_users']
        num_properties_per_host = options['num_properties_per_host']
        num_bookings_per_guest = options['num_bookings_per_guest']
        num_reviews_prob = options['num_reviews_per_booking']
        num_messages = options['num_messages']
        clear_data = options['clear']

        self.stdout.write(self.style.SUCCESS('Starting database seeding...'))

        if clear_data:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            Message.objects.all().delete()
            Review.objects.all().delete()
            Payment.objects.all().delete()
            Booking.objects.all().delete()
            Property.objects.all().delete()
            # Only delete users if they are not superusers
            CustomUser.objects.filter(is_superuser=False).delete()
            self.stdout.write(self.style.SUCCESS('Existing data cleared.'))

        # --- 1. Create Users ---
        self.stdout.write(f'Creating {num_users} sample users...')
        created_users = []
        for i in range(num_users):
            username = fake.unique.user_name()
            email = fake.unique.email()
            password = fake.password(length=12)
            # Randomly assign roles
            role = random.choice(
                [CustomUser.RoleChoices.GUEST, CustomUser.RoleChoices.HOST, CustomUser.RoleChoices.ADMIN])
            user, created = CustomUser.objects.get_or_create(
                email=email,  # Use email for get_or_create as it's the USERNAME_FIELD
                defaults={
                    'username': username,  # username is required by AbstractUser even if not USERNAME_FIELD
                    'first_name': fake.first_name(),
                    'last_name': fake.last_name(),
                    'phone_number': fake.phone_number(),
                    'role': role,
                    'created_at': timezone.now() - timedelta(days=random.randint(1, 365)),
                    'is_staff': (role == CustomUser.RoleChoices.ADMIN),
                    'is_superuser': (role == CustomUser.RoleChoices.ADMIN),
                    'is_active': True,
                    'date_joined': timezone.now() - timedelta(days=random.randint(1, 365))  # AbstractUser's field
                }
            )
            if created:
                user.set_password(password)
                user.save()
                created_users.append(user)
            else:  # If user already existed, add to list if not already there
                if user not in created_users:
                    created_users.append(user)

        users = list(CustomUser.objects.all())  # Get all users, including any existing ones
        if not users:  # Fallback if no users were created/found
            self.stdout.write(self.style.WARNING("No users found in the database. Creating one default user."))
            default_user = CustomUser.objects.create_user(
                email='default@example.com',
                username='default_user',  # Must provide username for AbstractUser
                password='password',
                first_name='Default',
                last_name='User',
                role=CustomUser.RoleChoices.GUEST,
                is_active=True
            )
            users.append(default_user)
            created_users.append(default_user)

        hosts = [u for u in users if u.role == CustomUser.RoleChoices.HOST or u.role == CustomUser.RoleChoices.ADMIN]
        if not hosts and users:  # Ensure at least one host if no explicit hosts created
            users[0].role = CustomUser.RoleChoices.HOST
            users[0].save()
            hosts = [users[0]]
            self.stdout.write(self.style.WARNING("No hosts found, assigned 'host' role to first user."))

        self.stdout.write(self.style.SUCCESS(f'Created/Ensured {len(users)} users.'))

        # --- 2. Create Properties ---
        self.stdout.write(f'Creating {num_properties_per_host} properties for each host...')
        properties = []
        for host in hosts:
            for _ in range(num_properties_per_host):
                property_obj = Property.objects.create(
                    host=host,
                    name=fake.catch_phrase(),
                    description=fake.paragraph(nb_sentences=5),
                    location=fake.address(),
                    pricepernight=decimal.Decimal(random.randrange(50, 1000)),  # e.g., 50.00 to 1000.00
                    created_at=timezone.now() - timedelta(days=random.randint(1, 365)),
                    updated_at=timezone.now()
                )
                properties.append(property_obj)
        self.stdout.write(self.style.SUCCESS(f'Created {len(properties)} properties.'))

        # --- 3. Create Bookings and Payments ---
        self.stdout.write(f'Creating bookings and payments...')
        bookings = []
        payments = []
        guests = [u for u in users if u.role == CustomUser.RoleChoices.GUEST or u.role == CustomUser.RoleChoices.ADMIN]
        if not guests:
            self.stdout.write(self.style.WARNING("No guests found. Skipping booking creation."))

        for guest in guests:
            num_bookings_for_guest = random.randint(0, num_bookings_per_guest)
            if not properties:
                self.stdout.write(self.style.WARNING("No properties available to book. Skipping bookings."))
                break
            for _ in range(num_bookings_for_guest):
                property_obj = random.choice(properties)
                start_date = fake.date_between(start_date='-90d', end_date='+90d')
                end_date = start_date + timedelta(days=random.randint(2, 14))
                num_nights = (end_date - start_date).days

                if num_nights <= 0:  # Ensure valid dates for calculation
                    continue

                total_price = property_obj.pricepernight * num_nights
                status = random.choice(Booking.BookingStatusChoices.choices)[0]

                try:
                    booking = Booking.objects.create(
                        property=property_obj,
                        user=guest,
                        start_date=start_date,
                        end_date=end_date,
                        total_price=total_price,
                        status=status,
                        created_at=timezone.now() - timedelta(days=random.randint(1, 90))
                    )
                    bookings.append(booking)

                    # Create a payment for confirmed or canceled bookings
                    if status in [Booking.BookingStatusChoices.CONFIRMED, Booking.BookingStatusChoices.CANCELED]:
                        payment = Payment.objects.create(
                            booking=booking,
                            amount=total_price if status == Booking.BookingStatusChoices.CONFIRMED else decimal.Decimal(
                                0.00),
                            # Payment date can be around booking creation or later
                            payment_date=booking.created_at + timedelta(hours=random.randint(1, 48)),
                            payment_method=random.choice(Payment.PaymentMethodChoices.choices)[0]
                        )
                        payments.append(payment)
                except Exception as e:
                    self.stdout.write(self.style.WARNING(
                        f"Could not create booking for {property_obj.name} by {guest.username}: {e}. Skipping."))

        self.stdout.write(self.style.SUCCESS(f'Created {len(bookings)} bookings and {len(payments)} payments.'))

        # --- 4. Create Reviews ---
        self.stdout.write(f'Creating reviews for some bookings...')
        reviews = []
        for booking in bookings:
            if random.random() < num_reviews_prob:  # Probability of creating a review
                # Reviewer must be the guest of the booking, and booking must be confirmed/completed implicitly
                if booking.status == Booking.BookingStatusChoices.CONFIRMED and booking.end_date < timezone.now().date():
                    try:
                        review = Review.objects.create(
                            property=booking.property,
                            user=booking.user,
                            rating=random.randint(1, 5),
                            comment=fake.paragraph(nb_sentences=2),  # Comment is NOT NULL as per spec
                            created_at=timezone.now() - timedelta(days=random.randint(1, 30))
                        )
                        reviews.append(review)
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(
                            f"Could not create review for {booking.property.name} by {booking.user.username}: {e}. Skipping. (e.g., unique_together)"))
        self.stdout.write(self.style.SUCCESS(f'Created {len(reviews)} reviews.'))

        # --- 5. Create Messages ---
        self.stdout.write(f'Creating {num_messages} messages...')
        messages = []
        if len(users) >= 2:
            for _ in range(num_messages):
                sender = random.choice(users)
                # Ensure recipient is different from sender
                possible_recipients = [u for u in users if u != sender]
                if not possible_recipients:
                    continue  # Skip if only one user exists
                recipient = random.choice(possible_recipients)

                message = Message.objects.create(
                    sender=sender,
                    recipient=recipient,
                    message_body=fake.sentence(nb_words=10, variable_nb_words=True),
                    sent_at=timezone.now() - timedelta(seconds=random.randint(1, 3600 * 24 * 7))  # Last 7 days
                )
                messages.append(message)
        else:
            self.stdout.write(self.style.WARNING("Not enough users to create messages (need at least 2)."))
        self.stdout.write(self.style.SUCCESS(f'Created {len(messages)} messages.'))

        self.stdout.write(self.style.SUCCESS('Database seeding completed successfully!'))