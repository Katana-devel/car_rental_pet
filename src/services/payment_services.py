"""
    1. User makes an unconfirmed booking → Payment is created (status=pending).
    2.    /pay endpoint → changes Payment.status to success. and calls create_booking (confirmed)
    3.    After success → confirmed Booking is created in Postgres.
	4.    If payment is still not success after 15 minutes → unconfirmed_booking in Redis is deleted.
"""