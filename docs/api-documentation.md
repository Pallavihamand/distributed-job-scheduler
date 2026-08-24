\# API Documentation



\## Distributed Job Scheduler



\*\*Version:\*\* 1.0.0

\*\*API Specification:\*\* OpenAPI 3.1

\*\*Base URL:\*\* `http://127.0.0.1:8000`



The Distributed Job Scheduler is a production-inspired platform for scheduling and executing asynchronous background jobs across distributed workers.



Interactive Swagger documentation is available at:



`http://127.0.0.1:8000/docs`



OpenAPI specification:



`http://127.0.0.1:8000/openapi.json`



\---



\## 1. Users



\### Create User



\*\*POST\*\* `/users`



Creates a new user account.



Request body: `UserCreate`



Response: `UserResponse`



\---



\## 2. Authentication



\### Login



\*\*POST\*\* `/auth/login`



Authenticates a user and returns an access token.



Request body: `LoginRequest`



Response: `TokenResponse`



The returned token can be used to authorize protected API requests.



\---



\## 3. Organizations



\### Get Organizations



\*\*GET\*\* `/organizations`



Returns the organizations accessible to the authenticated user.



\### Create Organization



\*\*POST\*\* `/organizations`



Creates a new organization.



Request body: `OrganizationCreate`



Response: `OrganizationResponse`



\### Get Organization



\*\*GET\*\* `/organizations/{organization\_id}`



Returns an organization by its ID.



Path parameter:



\* `organization\_id` — integer



\---



\## 4. Projects



Projects belong to organizations and can contain multiple job queues.



\### Get Projects



\*\*GET\*\* `/projects`



Returns available projects.



\### Create Project



\*\*POST\*\* `/projects`



Creates a new project.



Request body: `ProjectCreate`



Response: `ProjectResponse`



\### Get Project



\*\*GET\*\* `/projects/{project\_id}`



Returns a project by its ID.



Path parameter:



\* `project\_id` — integer



\---



\## 5. Queues



Queues are used to organize and control background jobs.



\### Get Queues



\*\*GET\*\* `/queues`



Returns available job queues.



\### Create Queue



\*\*POST\*\* `/queues`



Creates a new queue.



Request body: `QueueCreate`



Response: `QueueResponse`



Queue configuration can include scheduling and execution settings such as priority, concurrency, and retry behavior.



\### Pause Queue



\*\*POST\*\* `/queues/{queue\_id}/pause`



Pauses processing for a queue.



Path parameter:



\* `queue\_id` — integer



\### Resume Queue



\*\*POST\*\* `/queues/{queue\_id}/resume`



Resumes processing for a paused queue.



Path parameter:



\* `queue\_id` — integer



\### Queue Statistics



\*\*GET\*\* `/queues/{queue\_id}/stats`



Returns statistics for a queue.



Path parameter:



\* `queue\_id` — integer



\---



\## 6. Jobs



Jobs represent asynchronous background tasks submitted to queues.



\### Create Job



\*\*POST\*\* `/jobs`



Creates a new background job.



Request body: `JobCreate`



Response: `JobResponse`



\### Get Jobs



\*\*GET\*\* `/jobs`



Returns jobs available to the authenticated user.



\### Create Batch Jobs



\*\*POST\*\* `/jobs/batch`



Creates multiple jobs as a batch.



\### Get Job



\*\*GET\*\* `/jobs/{job\_id}`



Returns a job by its ID.



Path parameter:



\* `job\_id` — integer



\### Delete Job



\*\*DELETE\*\* `/jobs/{job\_id}`



Deletes a job by its ID.



Path parameter:



\* `job\_id` — integer



\### Retry Job



\*\*POST\*\* `/jobs/{job\_id}/retry`



Retries a failed job.



Path parameter:



\* `job\_id` — integer



\---



\## 7. Workers



Workers execute jobs from the configured queues.



\### Register Worker



\*\*POST\*\* `/workers/register`



Registers a worker with the scheduler.



\### Worker Heartbeat



\*\*POST\*\* `/workers/{worker\_id}/heartbeat`



Updates the worker heartbeat and indicates that the worker is still active.



Path parameter:



\* `worker\_id` — integer



\### Get Worker Status



\*\*GET\*\* `/workers/{worker\_id}/status`



Returns the current status of a worker.



Path parameter:



\* `worker\_id` — integer



\### Worker Health Check



\*\*POST\*\* `/workers/health-check`



Performs a worker health check.



\### Deactivate Worker



\*\*POST\*\* `/workers/{worker\_id}/deactivate`



Deactivates a worker.



Path parameter:



\* `worker\_id` — integer



\### Get Workers



\*\*GET\*\* `/workers`



Returns the registered workers.



\### Get Worker



\*\*GET\*\* `/workers/{worker\_id}`



Returns a worker by ID.



Path parameter:



\* `worker\_id` — integer



\---



\## 8. Scheduled and Recurring Jobs



Scheduled jobs allow jobs to be executed according to a recurring schedule.



\### Create Recurring Job



\*\*POST\*\* `/scheduled-jobs`



Creates a recurring job.



\### Get Recurring Jobs



\*\*GET\*\* `/scheduled-jobs`



Returns configured recurring jobs.



\### Process Recurring Jobs



\*\*POST\*\* `/scheduled-jobs/process`



Processes recurring jobs that are due for execution.



\### Pause Recurring Job



\*\*POST\*\* `/scheduled-jobs/{scheduled\_job\_id}/pause`



Pauses a recurring job.



Path parameter:



\* `scheduled\_job\_id` — integer



\### Resume Recurring Job



\*\*POST\*\* `/scheduled-jobs/{scheduled\_job\_id}/resume`



Resumes a paused recurring job.



Path parameter:



\* `scheduled\_job\_id` — integer



\### Delete Recurring Job



\*\*DELETE\*\* `/scheduled-jobs/{scheduled\_job\_id}`



Deletes a recurring job.



Path parameter:



\* `scheduled\_job\_id` — integer



\---



\## 9. Dashboard



\### Get Dashboard



\*\*GET\*\* `/dashboard`



Returns dashboard information and scheduler statistics.



\---



\## 10. System Endpoints



\### Root



\*\*GET\*\* `/`



Returns the root response of the API.



\### Health



\*\*GET\*\* `/health`



Checks whether the backend service is healthy.



\---



\## 11. Authentication



Protected endpoints require an access token obtained from:



`POST /auth/login`



The token should be supplied using the HTTP authorization header:



```text

Authorization: Bearer <access\_token>

```



\---



\## 12. HTTP Status Codes



The API may return the following HTTP status codes:



| Status Code | Meaning                                        |

| ----------- | ---------------------------------------------- |

| `200`       | Request successful                             |

| `201`       | Resource created                               |

| `400`       | Bad request                                    |

| `401`       | Authentication required or invalid credentials |

| `403`       | Access forbidden                               |

| `404`       | Resource not found                             |

| `409`       | Resource conflict                              |

| `422`       | Request validation error                       |

| `500`       | Internal server error                          |



\---



\## 13. Validation Errors



Invalid request data may return a `422 Unprocessable Entity` response.



Example:



```json

{

&#x20; "detail": \[

&#x20;   {

&#x20;     "loc": \[

&#x20;       "body",

&#x20;       "field"

&#x20;     ],

&#x20;     "msg": "Field required",

&#x20;     "type": "missing"

&#x20;   }

&#x20; ]

}

```



\---



\## 14. API Schemas



The API exposes the following OpenAPI schemas:



\* `UserCreate`

\* `UserResponse`

\* `LoginRequest`

\* `TokenResponse`

\* `OrganizationCreate`

\* `OrganizationResponse`

\* `ProjectCreate`

\* `ProjectResponse`

\* `QueueCreate`

\* `QueueResponse`

\* `JobCreate`

\* `JobResponse`

\* `HTTPValidationError`

\* `ValidationError`



The exact request and response fields for each schema can be viewed in the Swagger UI.



\---



\## 15. Testing



Automated backend tests are located in:



```text

backend/tests/

```



Run the tests from the backend directory using:



```powershell

python -m unittest discover -s tests -v

```



Current test suite:



\* `test\_fixed\_retry\_delay`

\* `test\_linear\_retry\_delay`

\* `test\_exponential\_retry\_delay`

\* `test\_failed\_job\_is\_requeued`

\* `test\_failed\_job\_moves\_to\_dead\_letter\_queue`



All 5 tests currently pass successfully.



\---



\## 16. Interactive API Documentation



For complete request/response schemas and endpoint testing, run the backend and open:



`http://127.0.0.1:8000/docs`



The generated OpenAPI specification is available at:



`http://127.0.0.1:8000/openapi.json`



The running OpenAPI specification should be treated as the source of truth for the exact API contract.



