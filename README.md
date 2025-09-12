# Car Rental Pet (In Progress)

Pet project for demonstrating my knowledge and backend development skills.  
Repository: [car_rental_pet](https://github.com/Katana-devel/car_rental_pet)

---

## 🚀 Tech Stack

- **Language & Framework:** Python, FastAPI  
- **Database:** PostgreSQL, SQLAlchemy (Async)  
- **Caching & Storage:** Redis  
- **Message Broker:** RabbitMQ  
- **Containerization:** Docker  
- **Version Control:** Git  
- **Dependency Management:** Poetry  

---

## ⚙️ Features

### Implemented
- **Car Rental Backend**
  - Shopping cart with Redis as in-memory storage  
  - Dynamic price calculator  
  - Booking system: car availability tracking, collision protection, order statuses  
  - Change history processing via RabbitMQ (in progress)  
  - Customer profiles  

- **Authentication & Authorization**
  - JWT tokens (access, refresh, email)  
  - Redis-based token storage  
  - Role separation: Admin / User  

- **Architecture**
  - Modular structure with models, CRUD layer, services  
  - Async SQLAlchemy integration  
  - Configurable via `.env`  
  - Containerized with Docker  

---

## 📌 Roadmap

Planned functionality:  

-  OCR document check (e.g. Smart Engines)  
-  Payment system integration  
-  Booking history via RabbitMQ  
-  Notifications & email sending  
-  Multi-language support (JSON translations or [Babel](http://babel.pocoo.org/))  
-  Multi-currency support (e.g. [ExchangeRatesAPI.io](https://exchangeratesapi.io))  
-  Promo codes and discounts  
-  Google OpenID Connect authorization
-  Deploy 

---

## 🔧 Installation & Run

1. **Clone the repository**
   ```bash
   git clone https://github.com/Katana-devel/car_rental_pet.git
   cd car_rental_pet

2. 	**Install dependencies**
poetry install

3. **Apply migrations**
alembic upgrade head

4.	Configure environment
	•	Copy .env.example → .env
	•	Set up DB, Redis, RabbitMQ credentials
5.	Run server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

API Documentation

Swagger UI:
http://localhost:8000/docs

All development done by me, from scratch.
GitHub: [Katana-devel](https://github.com/Katana-devel)
