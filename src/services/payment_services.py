"""
    1. Юзер делает unconfirmed бронирование → создаётся Payment (status=pending).
	2.	/pay эндпоинт → меняет Payment.status на success. и вызывает create_booking (confirmed)
	3.	После success → создаётся confirmed Booking в Postgresя.
	4.	Если payment через 15 минут так и не стал success → unconfirmed_booking в Redis удаляется
"""