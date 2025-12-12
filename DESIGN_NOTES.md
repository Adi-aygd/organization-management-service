# Design Notes - Organization Management Service

## Architecture Overview

This service implements a **multi-tenant organization management system** using a **collection-per-tenant** architecture pattern with MongoDB and FastAPI.

## Key Design Decisions

### 1. Multi-Tenancy Strategy: Collection-Per-Tenant

**Decision**: Each organization gets its own MongoDB collection within a single database.

**Rationale**:
- **Balance of Isolation**: Better data separation than shared collections, simpler than separate databases
- **Cost-Effective**: Single database connection pool, reduced infrastructure overhead
- **Operational Simplicity**: Easier backups, migrations, and maintenance compared to database-per-tenant
- **MongoDB Strength**: MongoDB handles multiple collections efficiently with minimal overhead

**Trade-offs**:
- ✅ **Pros**: Simple implementation, good for 100-1000 tenants, easy to reason about
- ⚠️ **Cons**: Tenants share database resources (CPU, memory, connections), one heavy user can impact others

**Alternatives Considered**:
1. **Shared Collection with Tenant ID**: Rejected due to weak data isolation and complex queries
2. **Database-Per-Tenant**: Rejected for MVP due to connection pool complexity and higher costs
3. **Separate Database Servers**: Rejected due to operational complexity and cost at current scale

---

### 2. Framework Choice: FastAPI

**Decision**: Use FastAPI over Django/Flask

**Rationale**:
- **Modern & Fast**: ASGI-based, async support, high performance
- **Auto-Documentation**: Built-in OpenAPI (Swagger) generation saves development time
- **Type Safety**: Pydantic integration catches errors at development time
- **Developer Experience**: Clear error messages, intuitive API design
- **Lightweight**: Less boilerplate than Django, more structured than Flask

**Trade-offs**:
- ✅ **Pros**: Fast development, excellent DX, production-ready
- ⚠️ **Cons**: Smaller ecosystem than Django, fewer built-in features for complex apps

---

### 3. Database Choice: MongoDB

**Decision**: Use MongoDB (NoSQL) over PostgreSQL/MySQL (SQL)

**Rationale**:
- **Dynamic Collection Creation**: MongoDB allows programmatic collection creation without schema migrations
- **Flexible Schema**: Easy to evolve organization-specific data models without ALTER TABLE statements
- **Document Model**: Natural fit for tenant metadata (nested objects, arrays)
- **Horizontal Scaling**: Built-in sharding support for future growth
- **Assignment Preference**: Explicitly preferred in requirements

**Trade-offs**:
- ✅ **Pros**: Schema flexibility, easy collection management, good for this use case
- ⚠️ **Cons**: Weaker ACID guarantees than PostgreSQL, less mature for complex transactions

**When to Reconsider**:
- If strong ACID compliance becomes critical
- If complex joins across tenant data are needed
- If regulatory compliance requires RDBMS

---

### 4. Architecture Pattern: Service Layer + Repository

**Decision**: Separate business logic (services) from data access (database) and API routes (routers)

**Structure**:
Routers (HTTP Layer) → Services (Business Logic) → Database (Data Access)

text

**Rationale**:
- **Separation of Concerns**: Each layer has a single responsibility
- **Testability**: Business logic can be tested independently of HTTP/database
- **Maintainability**: Changes to business rules don't affect API contracts
- **Reusability**: Services can be called from multiple routes or background tasks
- **Class-Based**: Follows assignment requirement for modular, class-based design

**Example Flow**:
POST /org/create → organization.py (router)
→ OrganizationService.create_organization() (business logic)
→ get_organizations_collection() (database access)

text

---

### 5. Authentication: JWT (JSON Web Tokens)

**Decision**: Use stateless JWT tokens for authentication

**Rationale**:
- **Stateless**: No server-side session storage needed, scales horizontally
- **Self-Contained**: Token contains user identity and organization ID
- **Standard**: Industry-standard approach (RFC 7519)
- **Simple**: No Redis/session store dependency for MVP

**Implementation Details**:
- **Payload**: `{email, org_id, organization_name, exp}`
- **Algorithm**: HS256 (HMAC with SHA-256)
- **Expiration**: 24 hours (configurable via environment)
- **Storage**: Client stores token, sends in Authorization header

**Trade-offs**:
- ✅ **Pros**: Scalable, no server-side state, works across services
- ⚠️ **Cons**: Can't invalidate tokens immediately (need token blacklist for that), tokens can grow large

**Future Improvements**:
- Add refresh tokens for better security
- Implement token blacklist for logout
- Use RS256 (asymmetric) for multi-service architectures

---

### 6. Password Security: Bcrypt

**Decision**: Use bcrypt for password hashing (via Passlib)

**Rationale**:
- **Industry Standard**: Battle-tested, recommended by OWASP
- **Adaptive**: Configurable work factor (rounds) to stay ahead of hardware improvements
- **Salt Built-in**: Automatically generates and stores salt with hash
- **Slow by Design**: Intentionally slow to prevent brute-force attacks

**Configuration**:
- **Rounds**: 12 (default) - balances security and performance
- **Max Length**: 72 bytes (bcrypt limitation) - passwords truncated if longer

**Alternative Considered**:
- **Argon2**: More modern, but bcrypt is more widely supported and sufficient for this use case

---

### 7. Data Validation: Pydantic

**Decision**: Use Pydantic models for all request/response validation

**Rationale**:
- **Type Safety**: Catches type errors before they reach business logic
- **Auto-Documentation**: Schemas appear in Swagger UI automatically
- **Clear Errors**: User-friendly validation error messages
- **Performance**: Fast validation using Python type hints
- **Composability**: Models can be nested and reused

**Example**:
class OrganizationCreate(BaseModel):
organization_name: str = Field(..., min_length=3, max_length=50)
email: EmailStr # Built-in email validation
password: str = Field(..., min_length=8)

text
@field_validator('organization_name')
def validate_org_name(cls, v):
    # Custom business rules
    return v.strip()
text

---

### 8. Error Handling Strategy

**Decision**: Use HTTP status codes with detailed error messages

**Approach**:
- **201 Created**: Successful resource creation
- **200 OK**: Successful retrieval/update/delete
- **400 Bad Request**: Invalid input (duplicate org, validation failure)
- **401 Unauthorized**: Invalid credentials
- **403 Forbidden**: Authenticated but not authorized (wrong tenant)
- **404 Not Found**: Resource doesn't exist
- **500 Internal Server Error**: Unexpected server errors (caught by middleware)

**Rationale**:
- **RESTful**: Follows HTTP standards
- **Client-Friendly**: Clients can handle errors programmatically
- **Debuggable**: Detailed messages help identify issues quickly

---

### 9. Configuration Management

**Decision**: Use environment variables with Pydantic Settings

**Rationale**:
- **12-Factor App**: Environment-based config is deployment best practice
- **Security**: Secrets (JWT key, DB password) never committed to code
- **Flexibility**: Easy to change config per environment (dev/staging/prod)
- **Type-Safe**: Pydantic validates config on startup

**Variables**:
MONGODB_URL=mongodb://localhost:27017/
DATABASE_NAME=master_database
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_HOURS=24

text

---

### 10. Database Connection Management

**Decision**: Singleton MongoDB client with lazy initialization

**Rationale**:
- **Connection Pooling**: MongoDB driver handles pool internally
- **Efficiency**: Single connection pool shared across requests
- **Startup Check**: Verify database connectivity at application startup
- **Graceful Shutdown**: Close connections cleanly on app shutdown

**Implementation**:
class MongoDB:
client = None # Singleton

text
@classmethod
def connect(cls):
    cls.client = MongoClient(settings.MONGODB_URL)
    cls.client.admin.command('ping')  # Verify connection
text

---

## Scalability Analysis

### Current Architecture Limits

**Estimated Capacity** (with single MongoDB instance):
- **Tenants**: 500-1000 organizations
- **Collections**: MongoDB handles 10,000+ collections per database easily
- **Concurrent Users**: 1000-5000 (depends on query complexity)
- **Data**: Limited by single server storage (hundreds of GB feasible)

### Bottlenecks:

1. **Database Resources**: All tenants share CPU, RAM, IOPS
2. **Connection Pool**: Limited by MongoDB connection limits (~65K theoretical, ~1000 practical)
3. **Write Performance**: Single MongoDB primary handles all writes
4. **Network**: Single server network bandwidth

---

## Scalability Improvements for Production

### Phase 1: Optimize Current Architecture (100-1K tenants)

1. **Add Redis Caching**
Cache organization metadata (rarely changes)
@cache(ttl=3600)
def get_organization(org_name):
return orgs_collection.find_one(...)

text
**Impact**: Reduces database reads by 60-80%

2. **Connection Pool Tuning**
client = MongoClient(
MONGODB_URL,
maxPoolSize=100, # Tune based on load
minPoolSize=10
)

text

3. **Database Indexing**
Index on organization_name for fast lookups
orgs_collection.create_index("organization_name", unique=True)
orgs_collection.create_index("admin_email", unique=True)

text

4. **Rate Limiting**
Per-tenant rate limits
@limiter.limit("100/minute", key_func=lambda: token_data['org_id'])
def create_resource():
pass

text

### Phase 2: Horizontal Scaling (1K-10K tenants)

1. **MongoDB Replica Set**
- Add read replicas for horizontal read scaling
- Read organization data from secondaries
- Writes still go to primary

2. **Application Load Balancing**
[FastAPI Instance 1]
[FastAPI Instance 2] <-- Load Balancer <-- Users
[FastAPI Instance 3]

text

3. **Async Background Tasks**
Offload heavy operations to workers
from celery import Celery

@celery.task
def migrate_organization_collection(old_name, new_name):
# Heavy data migration in background
pass

text

### Phase 3: Database-Per-Tenant (10K+ tenants)

**Migration Strategy**:

1. **Dynamic Connection Routing**
class TenantDatabase:
_connections = {} # Connection pool per tenant

text
   def get_connection(org_id):
       if org_id not in _connections:
           conn_string = master_db.get_tenant_connection(org_id)
           _connections[org_id] = MongoClient(conn_string)
       return _connections[org_id]
text

2. **Tenant Sharding**
- Group tenants by size/activity
- Small tenants: shared databases (1000 per DB)
- Large tenants: dedicated databases

3. **Master Database Design**
{
"org_id": "uuid",
"organization_name": "TechCorp",
"database_type": "shared" | "dedicated",
"shard_id": "shard_001",
"connection_string": "mongodb://shard001:27017/db_techcorp"
}

text

### Phase 4: Microservices (100K+ tenants)

1. **Service Decomposition**
[Auth Service] [Organization Service] [Tenant Data Service]
| | |
+------------------+----------------------+
|
[Message Queue]

text

2. **Event-Driven Architecture**
Publish events when org created
event_bus.publish('org.created', {
'org_id': org.id,
'org_name': org.name
})

text

---

## Security Considerations

### Current Implementation

✅ **Password Hashing**: Bcrypt with 12 rounds
✅ **JWT Tokens**: HS256 with 24hr expiration
✅ **Input Validation**: Pydantic models prevent injection
✅ **CORS**: Configured (currently allows all origins)
✅ **HTTPS**: Should be handled by reverse proxy (nginx)

### Production Enhancements

1. **Rate Limiting**: Prevent brute-force attacks on login
2. **Token Blacklist**: Allow immediate token revocation on logout
3. **Password Policy**: Enforce complexity rules (uppercase, numbers, special chars)
4. **Audit Logging**: Log all sensitive operations (create, update, delete)
5. **CORS Restrictions**: Whitelist only known frontend origins
6. **Database Encryption**: Enable MongoDB encryption at rest
7. **Secrets Management**: Use AWS Secrets Manager / HashiCorp Vault

---

## Monitoring & Observability

### Recommended Additions

1. **Application Metrics**
from prometheus_client import Counter, Histogram

org_created = Counter('organizations_created_total')
login_duration = Histogram('login_duration_seconds')

text

2. **Logging Strategy**
Structured logging with context
logger.info("Organization created", extra={
'org_name': org_name,
'admin_email': email,
'collection_name': collection_name,
'request_id': request.headers.get('x-request-id')
})

text

3. **Health Checks**
- Database connectivity
- Disk space usage
- Memory usage
- Response times

4. **Alerting**
- Failed login attempts > threshold
- Database connection failures
- API response time > 1s
- Error rate > 1%

---

## Testing Strategy (Future Work)

### Unit Tests
def test_create_organization():
service = OrganizationService()
result = service.create_organization(mock_data)
assert result.organization_name == "TechCorp"

text

### Integration Tests
def test_create_and_login_flow():
# Test full user journey
org_response = client.post('/org/create', json=org_data)
token_response = client.post('/admin/login', json=credentials)
assert token_response.status_code == 200

text

### Load Tests
Using locust or k6
locust -f loadtest.py --users 1000 --spawn-rate 10

text

---

## Cost Considerations

### Current Setup (MVP)

**Monthly Costs** (estimated):
- MongoDB Atlas M0 (Free): $0
- Heroku/Railway (Hobby): $5-7/month
- Total: **~$5-7/month**

### Production Costs (1000 tenants)

- MongoDB Atlas M10 (Shared): $57/month
- AWS EC2 t3.medium (2 instances): $60/month
- Load Balancer: $20/month
- Redis (ElastiCache): $15/month
- Total: **~$150-200/month**

---

## Conclusion

This architecture represents a **pragmatic balance** between:
- ✅ **Simplicity**: Easy to understand and maintain
- ✅ **Scalability**: Clear path to scale to thousands of tenants
- ✅ **Cost**: Minimal infrastructure for MVP
- ✅ **Security**: Industry-standard practices

The **collection-per-tenant** approach is ideal for this use case because:
1. It provides good isolation without complexity
2. MongoDB handles it efficiently
3. It's simple to implement and debug
4. Clear migration path to database-per-tenant when needed

For an **early-stage product** or **proof-of-concept**, this design delivers maximum value with minimum complexity.

---
