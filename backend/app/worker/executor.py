
import time
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.job_execution import JobExecution
from app.worker.retry import handle_job_failure


def execute_job(
    db: Session,
    job: Job,
    worker_id: int,
):
    """
    Execute one claimed job and record execution history.
    """

    # ---------------------------------------------------------
    # MARK RUNNING
    # ---------------------------------------------------------

    job.status = "RUNNING"
    job.started_at = datetime.utcnow()

    execution = JobExecution(
        job_id=job.id,
        worker_id=worker_id,
        attempt_number=job.attempts + 1,
        status="RUNNING",
        started_at=datetime.utcnow(),
    )

    db.add(execution)
    db.commit()
    db.refresh(execution)

    start_time = time.time()

    try:
        print(
            f"[WORKER {worker_id}] "
            f"Executing job {job.id}"
        )

        print(
            f"[JOB {job.id}] "
            f"type={job.job_type} "
            f"payload={job.payload}"
        )

        # -----------------------------------------------------
        # DEMO JOB EXECUTION
        # -----------------------------------------------------

        if job.job_type == "sleep":
            seconds = int(
                job.payload.get("seconds", 1)
            )

            time.sleep(seconds)

        elif job.job_type == "print":
            print(
                f"[JOB {job.id}] "
                f"{job.payload.get('message', '')}"
            )

        elif job.job_type == "fail":
            raise Exception(
                job.payload.get(
                    "message",
                    "Intentional job failure",
                )
            )

        else:
            # Generic demo execution
            print(
                f"[JOB {job.id}] "
                f"Executing {job.job_type}"
            )

        # -----------------------------------------------------
        # SUCCESS
        # -----------------------------------------------------

        duration_ms = int(
            (time.time() - start_time) * 1000
        )

        job.status = "COMPLETED"
        job.completed_at = datetime.utcnow()
        job.worker_id = worker_id
        job.error_message = None

        execution.status = "COMPLETED"
        execution.finished_at = datetime.utcnow()
        execution.duration_ms = duration_ms

        db.commit()

        print(
            f"[WORKER {worker_id}] "
            f"Job {job.id} completed"
        )

        return True

    except Exception as exc:

        duration_ms = int(
            (time.time() - start_time) * 1000
        )

        error_message = str(exc)

        execution.status = "FAILED"
        execution.finished_at = datetime.utcnow()
        execution.duration_ms = duration_ms
        execution.error_message = error_message

        result = handle_job_failure(
            db=db,
            job=job,
            error_message=error_message,
            retry_strategy="exponential",
            base_delay=5,
        )

        print(
            f"[WORKER {worker_id}] "
            f"Job {job.id} failed: {error_message}"
        )

        print(
            f"[WORKER {worker_id}] "
            f"Failure action: {result['action']}"
        )

        return False