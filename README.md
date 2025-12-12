# Organization Management Service

A multi-tenant backend service built with FastAPI and MongoDB that supports creating and managing organizations with JWT-based authentication.

## Features

- ✅ Create organizations with admin users
- ✅ Dynamic collection creation per organization
- ✅ JWT-based authentication
- ✅ Secure password hashing with bcrypt
- ✅ RESTful API design
- ✅ Class-based service architecture
- ✅ Comprehensive error handling
- ✅ API documentation with Swagger UI

## Tech Stack

- **Framework**: FastAPI 0.115.0
- **Database**: MongoDB (Local or Atlas)
- **Authentication**: JWT (python-jose)
- **Password Hashing**: Passlib with bcrypt
- **Python Version**: 3.13

## Project Structure

org-management-service/
├── app/
│ ├── init.py
│ ├── main.py # FastAPI application entry point
│ ├── config.py # Configuration settings
│ ├── database.py # MongoDB connection handling
│ ├── routers/
│ │ ├── init.py
│ │ ├── auth.py # Authentication routes
│ │ └── organization.py # Organization CRUD routes
│ ├── services/
│ │ ├── init.py
│ │ ├── auth_service.py # Authentication business logic
│ │ └── org_service.py # Organization business logic
│ ├── models/
│ │ ├── init.py
│ │ └── schemas.py # Pydantic models
│ └── utils/
│ ├── init.py
│ ├── security.py # Password hashing utilities
│ └── jwt_handler.py # JWT token handling
├── .env # Environment variables
├── requirements.txt # Python dependencies
└── README.md # This file

text

## Installation

### Prerequisites

- Python 3.13+
- MongoDB (Local installation or Atlas account)

### Setup Steps

1. **Clone the repository**
git clone <your-repo-url>
cd org-management-service

text

2. **Create virtual environment**
python3 -m venv venv
source venv/bin/activate # On Mac/Linux

venv\Scripts\activate # On Windows
text

3. **Install dependencies**
pip install -r requirements.txt

text

4. **Install and start MongoDB (Local)**
Mac
brew tap mongodb/brew
brew install mongodb-community@8.0
brew services start mongodb-community@8.0

Or run directly
mkdir -p ~/data/db
mongod --dbpath ~/data/db

text

5. **Configure environment variables**

Create `.env` file in the root directory:
MONGODB_URL=mongodb://localhost:27017/
DATABASE_NAME=master_database
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_HOURS=24
APP_NAME=Organization Management Service
DEBUG=True

text

For MongoDB Atlas, use:
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority

text

6. **Run the application**
uvicorn app.main:app --reload

text

The API will be available at: `http://127.0.0.1:8000`

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

## API Endpoints

### Organization Management

#### 1. Create Organization
POST /org/create
Content-Type: application/json

{
"organization_name": "TechCorp",
"email": "admin@techcorp.com",
"password": "SecurePass123"
}

text

**Response (201 Created)**:
{
"organization_name": "TechCorp",
"collection_name": "org_techcorp",
"admin_email": "admin@techcorp.com",
"created_at": "2025-12-13T01:30:00.000Z"
}

text

#### 2. Get Organization
GET /org/get?organization_name=TechCorp

text

**Response (200 OK)**:
{
"organization_name": "TechCorp",
"collection_name": "org_techcorp",
"admin_email": "admin@techcorp.com",
"created_at": "2025-12-13T01:30:00.000Z"
}

text

#### 3. Update Organization (Requires Authentication)
PUT /org/update
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
"organization_name": "TechCorp Industries",
"email": "admin@techcorp.com",
"password": "NewPassword456"
}

text

#### 4. Delete Organization (Requires Authentication)
DELETE /org/delete?organization_name=TechCorp
Authorization: Bearer <jwt_token>

text

### Authentication

#### Admin Login
POST /admin/login
Content-Type: application/json

{
"email": "admin@techcorp.com",
"password": "SecurePass123"
}

text

**Response (200 OK)**:
{
"access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
"token_type": "bearer",
"organization_name": "TechCorp",
"admin_email": "admin@techcorp.com"
}

text

## Architecture & Design

### Multi-Tenant Strategy

This application implements a **collection-per-tenant** approach:

- **Master Database**: Stores organization metadata and admin credentials
- **Dynamic Collections**: Each organization gets its own collection (`org_<name>`)
- **Single Database**: All collections reside in one database for simplified management

### Design Choices

**✅ Advantages:**
- Simple to implement and maintain
- Cost-effective for small-to-medium scale
- Easy backup and restore
- Shared infrastructure reduces overhead
- Good isolation between tenants

**⚠️ Trade-offs:**
- Tenants share database resources (CPU, memory)
- One noisy neighbor can impact others
- Scaling requires vertical scaling of the database
- Less isolation than database-per-tenant

### Alternative Approaches

1. **Database-per-Tenant**: Better isolation but more complex connection management
2. **Shared Collection with Tenant ID**: Simpler but weaker data isolation
3. **Separate Database Servers**: Maximum isolation but highest cost

### Scalability Improvements

For production at scale, consider:

1. **Connection Pooling**: Implement robust connection pooling with limits
2. **Caching Layer**: Add Redis for organization metadata caching
3. **Rate Limiting**: Per-tenant rate limiting to prevent resource abuse
4. **Async Operations**: Use background tasks for collection creation/migration
5. **Database-per-Tenant**: Migrate to database-per-tenant with dynamic routing
6. **Monitoring**: Add tenant-level metrics and alerting
7. **Sharding**: Implement MongoDB sharding for horizontal scaling

## Testing

Use Swagger UI at `http://127.0.0.1:8000/docs` to test all endpoints interactively.

### Test Flow:
1. Create an organization
2. Login with admin credentials
3. Copy the JWT token
4. Click "Authorize" and paste the token
5. Test update and delete endpoints

## Security Features

- ✅ Password hashing with bcrypt
- ✅ JWT token-based authentication
- ✅ Protected endpoints with dependency injection
- ✅ Input validation with Pydantic
- ✅ SQL injection prevention (NoSQL context)
- ✅ CORS middleware configured

## Development

### Code Style
- Class-based service layer for business logic
- Pydantic models for request/response validation
- Comprehensive logging
- Error handling with appropriate HTTP status codes

### Future Enhancements
- [ ] Add user roles and permissions
- [ ] Implement refresh tokens
- [ ] Add email verification
- [ ] Tenant-specific rate limiting
- [ ] Audit logging
- [ ] Data export/import features


