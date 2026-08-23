# Design Decisions — Distributed Job Scheduler

## 1. Overview

The Distributed Job Scheduler is designed as a production-inspired platform for creating, scheduling, executing, monitoring, and retrying asynchronous background jobs.

The system separates the frontend, REST API backend, database, and worker execution layer to provide a modular architecture that can be extended to multiple workers and larger workloads.

---

## 2. Technology Choices

### Backend — FastAPI

FastAPI was selected for the backend because it provides:

* High-performance asynchronous API support
* Automatic OpenAPI/Swagger documentation
* Request and response validation using Pydantic
* Clean dependency injection
* Easy integration with SQLAlchemy
* Clear REST API structure

### Database — Relational Database

A relational database is used because the system contains strongly related entities such as:

* Users
* Organizations
* Projects
* Queues
* Jobs
* Workers
* Job executions
* Scheduled jobs
* Retry information

Foreign keys and relational constraints help maintain data integrity.

### ORM — SQLAlchemy

SQLAlchemy is used to separate database operations from application logic.

Benefits include:

* Reusable models
* Relationship management
* Transaction support
* Database abstraction
* Easier maintenance

### Frontend — React

React was selected to build a responsive dashboard for managing:

* Organizations
* Projects
* Queues
* Jobs
* Workers
* Scheduled jobs
* System statistics

The frontend communicates with the backend through REST APIs.

---

## 3. Authentication Decision

JWT-based authentication is used for API authentication.

The login process is:

1. User submits email and password.
2. Backend validates the credentials.
3. Backend generates a JWT access token.
4. Frontend stores the access token.
5. The token is sent with authenticated API requests.
6. Backend validates the token before accessing protected resources.

Passwords are not stored directly. Password hashes are stored in the database.

This approach keeps authentication stateless and allows the backend to support multiple frontend clients or services.

---

## 4. Project and Queue Hierarchy

The system follows this hierarchy:

```text
User
  ↓
Organization
  ↓
Project
  ↓
Queue
  ↓
Job
```

A project can contain multiple queues, while each queue can contain multiple jobs.

This structure provides logical isolation and allows different projects to configure their own job processing behavior.

---

## 5. Queue Design

Queues are used to organize jobs before execution.

Each queue can contain configuration such as:

* Priority
* Concurrency limit
* Pause/resume state
* Job statistics
* Retry configuration

Queues allow the worker service to process jobs independently and provide a foundation for distributed execution.

---

## 6. Job Lifecycle

Jobs follow a controlled lifecycle:

```text
QUEUED
   ↓
SCHEDULED
   ↓
CLAIMED
   ↓
RUNNING
   ↓
COMPLETED
```

When a job fails, it can enter the retry process:

```text
RUNNING
   ↓
FAILED
   ↓
RETRY
   ↓
QUEUED
```

If the maximum retry count is reached:

```text
FAILED
   ↓
DEAD
```

This lifecycle makes job state observable and simplifies monitoring and troubleshooting.

---

## 7. Retry Strategy

Retry handling is required because background jobs can fail due to temporary problems.

The system supports configurable retry behavior such as:

* Fixed delay
* Linear backoff
* Exponential backoff

Exponential backoff is particularly useful for temporary failures because it avoids repeatedly retrying a failing operation immediately.

Example:

```text
Attempt 1 → 1 second
Attempt 2 → 2 seconds
Attempt 3 → 4 seconds
Attempt 4 → 8 seconds
```

Jobs that permanently fail after the configured retry limit are moved to the Dead Letter Queue.

---

## 8. Dead Letter Queue

The Dead Letter Queue provides a separate location for jobs that cannot be successfully executed after the configured retry attempts.

This prevents permanently failing jobs from continuously consuming worker capacity.

It also allows administrators to inspect failed jobs and manually retry them when appropriate.

---

## 9. Worker Architecture

Workers are independent execution processes responsible for processing jobs from queues.

A worker performs the following operations:

1. Poll available queues.
2. Find executable jobs.
3. Claim a job.
4. Execute the job.
5. Update job status.
6. Record execution information.
7. Send heartbeats.
8. Continue processing additional jobs.

Multiple workers can operate simultaneously, allowing the platform to scale horizontally.

---

## 10. Worker Heartbeats

Workers periodically send heartbeat information to the backend.

The heartbeat mechanism allows the system to determine whether a worker is:

* ONLINE
* OFFLINE
* Available
* Deactivated

Heartbeat timestamps also provide a mechanism for detecting workers that have stopped responding.

---

## 11. Concurrency and Duplicate Execution

One of the important reliability requirements is preventing multiple workers from executing the same job simultaneously.

Job claiming is designed around database transactions and state transitions.

The intended process is:

```text
Find available job
      ↓
Atomically claim job
      ↓
Mark as CLAIMED
      ↓
Execute
```

The database transaction ensures that the job state is changed consistently.

This provides a foundation for safe distributed execution when multiple workers are polling the same queues.

---

## 12. Idempotency

Job execution should be designed to be idempotent wherever possible.

For example, if a job performs an external operation, repeating the same operation should not unintentionally create duplicate side effects.

Job IDs and execution records provide identifiers that can be used to track individual executions.

---

## 13. Database Normalization

The database is divided into separate entities rather than storing all information in a single table.

For example:

```text
Users
Organizations
Projects
Queues
Jobs
Workers
Scheduled Jobs
Job Executions
Retry Policies
```

This reduces data duplication and improves consistency.

Relationships are maintained using primary keys and foreign keys.

---

## 14. Foreign Keys

Foreign keys maintain relationships between entities.

Examples:

```text
Organization → User
Project → Organization
Queue → Project
Job → Queue
Job Execution → Job
Scheduled Job → Job/Queue
Worker Heartbeat → Worker
```

This prevents orphaned records and maintains referential integrity.

---

## 15. Indexing Strategy

Indexes should be applied to frequently queried columns.

Important candidates include:

* User email
* Organization ID
* Project ID
* Queue ID
* Job status
* Job queue ID
* Worker status
* Scheduled execution time

For jobs, indexing queue and status fields is particularly important because workers frequently search for executable jobs.

---

## 16. Transaction Management

Database transactions are used for operations that modify multiple related records.

Examples include:

* Creating jobs
* Updating job state
* Claiming jobs
* Recording execution results
* Updating worker information
* Retrying failed jobs

Transactions help prevent partially completed database operations.

---

## 17. REST API Design

The backend exposes REST APIs organized by resource.

Examples:

```text
/auth/login

/users

/organizations

/projects

/queues

/jobs

/workers

/scheduled-jobs

/dashboard
```

The API uses appropriate HTTP methods:

```text
GET     → Retrieve resources
POST    → Create or trigger operations
DELETE  → Remove resources
```

FastAPI automatically generates OpenAPI documentation for API inspection and testing.

---

## 18. Validation and Error Handling

Pydantic schemas validate incoming API data before it reaches the database layer.

The API returns structured HTTP errors for cases such as:

* Invalid credentials
* Missing resources
* Invalid project IDs
* Invalid queue IDs
* Inactive users
* Invalid request parameters

This prevents invalid data from propagating through the application.

---

## 19. Frontend Architecture

The React frontend is organized around page-level modules.

Current pages include:

```text
Login
Dashboard
Organizations
Projects
Queues
Jobs
Workers
Scheduled Jobs
```

API communication is separated into service modules.

Examples:

```text
services/
├── api.js
├── auth.js
├── jobs.js
├── organizations.js
├── projects.js
├── queues.js
└── workers.js
```

This separation keeps API communication independent from UI pages.

---

## 20. Dashboard Design

The dashboard provides an overview of the scheduler.

It displays live information such as:

* Organizations
* Projects
* Queues
* Jobs
* Workers

Additional pages allow administrators/users to inspect and manage individual resources.

The frontend obtains these values from backend APIs rather than using hardcoded dashboard statistics.

---

## 21. Scheduling Design

Scheduled jobs are separated from normal immediate jobs so that recurring scheduling information can be maintained independently.

The backend supports operations for:

* Creating recurring jobs
* Listing scheduled jobs
* Processing scheduled jobs
* Pausing schedules
* Resuming schedules
* Deleting schedules

This allows scheduling logic to be extended independently of normal job execution.

---

## 22. Why REST Polling Was Preferred

For the current assignment implementation, REST APIs and periodic refresh/polling were preferred over introducing WebSockets.

The reason is simplicity and reliability within the project scope.

The architecture can later be extended with WebSockets for real-time:

* Worker status
* Job status
* Queue statistics
* Dashboard metrics

WebSockets are therefore considered an extension rather than a core dependency.

---

## 23. Security Considerations

Security considerations include:

* Password hashing
* JWT authentication
* Protected API access
* Input validation
* Environment-based configuration
* Avoiding credentials in source control

Sensitive configuration such as database credentials and secret keys should be stored in environment variables rather than committed to GitHub.

---

## 24. Scalability Considerations

The architecture supports horizontal scaling by allowing multiple worker processes to operate against the same backend and database.

Conceptually:

```text
                 ┌─────────────┐
                 │   Frontend  │
                 └──────┬──────┘
                        │
                        ▼
                 ┌─────────────┐
                 │  FastAPI    │
                 │   Backend   │
                 └──────┬──────┘
                        │
             ┌──────────┴──────────┐
             ▼                     ▼
       ┌───────────┐         ┌───────────┐
       │ Database  │         │   Queues  │
       └───────────┘         └─────┬─────┘
                                   │
                    ┌──────────────┼──────────────┐
                    ▼              ▼              ▼
                 Worker 1       Worker 2       Worker N
```

Additional workers can be added without changing the frontend.

---

## 25. Maintainability

The project separates responsibilities into:

```text
Frontend
   ↓
REST API
   ↓
Services / Business Logic
   ↓
Database
```

This modular structure makes it easier to:

* Add new APIs
* Add new job types
* Modify retry strategies
* Add worker capabilities
* Extend dashboard functionality
* Replace infrastructure components

---

## 26. Trade-offs

### Simplicity vs. Advanced Distributed Infrastructure

A production system could use Kafka, Redis, distributed locks, or a dedicated message broker.

For this assignment, the implementation focuses on a relational database and worker architecture to demonstrate the fundamental scheduling, reliability, and concurrency concepts without unnecessary infrastructure complexity.

### Polling vs. WebSockets

Polling is simpler to implement and debug.

WebSockets would provide better real-time behavior but introduce additional connection-management complexity.

### Relational Database vs. NoSQL

A relational database was selected because the assignment contains many strongly related entities and requires transactional consistency.

---

## 27. Future Improvements

Possible future enhancements include:

* WebSocket live updates
* Redis-based distributed locking
* Queue sharding
* Rate limiting
* Workflow dependencies
* Advanced role-based access control
* AI-generated failure summaries
* Prometheus/Grafana monitoring
* Kubernetes-based worker scaling
* More advanced job idempotency mechanisms

These features can be added without fundamentally changing the core project architecture.

---

## 28. Conclusion

The architecture prioritizes reliability, modularity, database consistency, distributed worker execution, and maintainability.

The implementation focuses on the core requirements of the Distributed Job Scheduler assignment while keeping the design extensible for future production-scale improvements.
