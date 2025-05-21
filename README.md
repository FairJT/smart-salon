# Smart Beauty Salon Platform

A Python-based MVP for a Smart Beauty Salon platform using FastAPI and PostgreSQL, featuring AI-powered recommendations.

## Features

- 🔒 JWT-based authentication with role-based access (client, salon, stylist, admin)
- 💅 Salon and service management
- 👩‍💼 Stylist profiles and scheduling
- 📅 Booking system with time slots
- ⭐ Rating system for services and stylists
- 🤖 AI-powered chatbot for service recommendations
- 🔍 Vector search using FAISS + OpenAI embeddings
- 📊 Simple dashboard using Streamlit

## Architecture

The application follows a microservices structure with the following components:

- **API Layer**: FastAPI-based RESTful API
- **Data Layer**: PostgreSQL database with SQLAlchemy ORM
- **Business Logic Layer**: Services for business operations
- **AI Layer**: OpenAI integration for recommendations + FAISS for vector search
- **UI Layer**: Simple Streamlit dashboard

## Prerequisites

- Python 3.9+
- PostgreSQL 12+
- Docker and Docker Compose (optional, for containerized setup)
- OpenAI API key (for AI features)

## Installation

### Local Development

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/smart-salon.git
   cd smart-salon
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your configuration:
   ```
   DATABASE_URL=postgresql://postgres:password@localhost/smart_salon
   SECRET_KEY=your-secret-key-change-in-production
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   OPENAI_API_KEY=your-openai-api-key
   ENVIRONMENT=development
   ```

5. Initialize the database:
   ```
   alembic upgrade head
   ```

6. Run the application:
   ```
   uvicorn app.main:app --reload
   ```

7. Run the Streamlit dashboard (in a separate terminal):
   ```
   streamlit run app/ui/streamlit_app.py
   ```

### Using Docker

1. Clone the repository

2. Create a `.env` file with your OpenAI API key:
   ```
   OPENAI_API_KEY=your-openai-api-key
   ```

3. Start the application using Docker Compose:
   ```
   docker-compose up -d
   ```

4. Run database migrations:
   ```
   docker-compose exec api alembic upgrade head
   ```

## API Documentation

Once the application is running, you can access the API documentation at:

- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## Streamlit Dashboard

Access the Streamlit dashboard at:
- http://localhost:8501

## Default Users

In development mode, the following test users are created:

- Admin: admin@example.com / adminpassword
- Salon Owner: salon@example.com / password
- Client: client@example.com / password
- Stylist: stylist@example.com / password

## Project Structure

```
smart_salon/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── config.py            # Application configuration
│   ├── database.py          # Database connection
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── routers/             # API routes
│   ├── services/            # Business logic
│   ├── auth/                # Authentication and authorization
│   ├── chatbot/             # AI assistant functionality
│   └── ui/                  # Streamlit dashboard
├── alembic/                 # Database migrations
├── tests/                   # Unit and integration tests
├── requirements.txt         # Python dependencies
├── Dockerfile               # Docker image definition
├── docker-compose.yml       # Docker Compose configuration
└── README.md                # Project documentation
```

## License

MIT