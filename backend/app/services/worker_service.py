import time
import socket
import traceback
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

from app.database import SessionLocal
from app.services.job_service import claim_next_job

from app.models.job import Job
from app.models.job_execution import JobExecution
from app.models.worker import Worker
from app.models.worker_heartbeat import WorkerHeartbeat
from app.models.job_log import JobLog
from app.models.dead_letter import DeadLetterJob
from app.models.queue import Queue
from app.models.retry_policy import RetryPolicy


# ============================================================
# HEARTBEAT
# ============================================================

def send_heartbeat(worker_id: int):
    db = SessionLocal()

    try:
        worker = (
            db.query(Worker)
            .filter(Worker.id == worker_id)
            .first()
        )

        if not worker:
            return

        worker.status = "ONLINE"
        worker.last_heartbeat = datetime.utcnow()

        heartbeat = WorkerHeartbeat(
            worker_id=worker_id,
            active_jobs=worker.active_jobs
        )

        db.add(heartbeat)
        db.commit()

    except Exception as e:
        db.rollback()
        print(f"Heartbeat error: {e}")

    finally:
        db.close()


# ============================================================
# LOG JOB MESSAGE
# ============================================================

def add_job_log(
    job_id: int,
    message: str,
    level: str = "INFO",
    execution_id: int | None = None
):
    db = SessionLocal()

    try:
        log = JobLog(
            job_id=job_id,
            execution_id=execution_id,
            level=level,
            message=message
        )

        db.add(log)
        db.commit()

    except Exception as e:
        db.rollback()
        print(f"Log error: {e}")

    finally:
        db.close()


# ============================================================
# RETRY DELAY
# ============================================================

def calculate_retry_delay(
    strategy: str,
    base_delay: int,
    attempt: int
):
    """
    fixed:
        5, 5, 5

    linear:
        5, 10, 15

    exponential:
        5, 10, 20, 40
    """

    if strategy == "linear":
        return base_delay * attempt

    if strategy == "exponential":
        return base_delay * (2 ** (attempt - 1))

    return base_delay


# ============================================================
# EXECUTE ONE JOB
# ============================================================

def execute_job(job_id: int, worker_id: int):

    db = SessionLocal()

    execution = None
    start_time = datetime.utcnow()

    try:

        # ----------------------------------------------------
        # Get job
        # ----------------------------------------------------

        job = (
            db.query(Job)
            .filter(Job.id == job_id)
            .first()
        )

        if not job:
            return

        # ----------------------------------------------------
        # Increment attempt
        # ----------------------------------------------------

        job.attempts += 1

        attempt_number = job.attempts

        # ----------------------------------------------------
        # Create execution record
        # ----------------------------------------------------

        execution = JobExecution(
            job_id=job.id,
            worker_id=worker_id,
            attempt_number=attempt_number,
            status="RUNNING",
            started_at=start_time
        )

        db.add(execution)

        # ----------------------------------------------------
        # Job becomes RUNNING
        # ----------------------------------------------------

        job.status = "RUNNING"
        job.started_at = start_time

        db.commit()
        db.refresh(execution)

        print(
            f"Worker {worker_id} executing "
            f"Job {job.id}, attempt {attempt_number}"
        )

        add_job_log(
            job.id,
            f"Job started by worker {worker_id}, attempt {attempt_number}",
            "INFO",
            execution.id
        )

        # ====================================================
        # ACTUAL JOB EXECUTION
        # ====================================================

        job_type = job.job_type

        # Simple demo job
        if job_type == "print":

            message = job.payload.get(
                "message",
                "Hello from worker"
            )

            print(
                f"JOB {job.id}: {message}"
            )

            # Simulate work
            time.sleep(2)

        # Simulated failure job
        elif job_type == "fail":

            raise Exception(
                job.payload.get(
                    "message",
                    "Simulated job failure"
                )
            )

        # Generic job
        else:

            print(
                f"Executing job type: {job_type}"
            )

            time.sleep(2)

        # ====================================================
        # JOB SUCCESS
        # ====================================================

        finished_time = datetime.utcnow()

        duration = int(
            (finished_time - start_time).total_seconds() * 1000
        )

        execution.status = "COMPLETED"
        execution.finished_at = finished_time
        execution.duration_ms = duration

        job.status = "COMPLETED"
        job.completed_at = finished_time
        job.worker_id = worker_id

        db.commit()

        add_job_log(
            job.id,
            f"Job completed successfully in {duration} ms",
            "INFO",
            execution.id
        )

        print(
            f"Worker {worker_id} completed "
            f"Job {job.id}"
        )

    except Exception as e:

        db.rollback()

        error_message = str(e)

        print(
            f"Job {job_id} failed: {error_message}"
        )

        # ----------------------------------------------------
        # Reload job after rollback
        # ----------------------------------------------------

        job = (
            db.query(Job)
            .filter(Job.id == job_id)
            .first()
        )

        if not job:
            return

        # ----------------------------------------------------
        # Find execution
        # ----------------------------------------------------

        execution = (
            db.query(JobExecution)
            .filter(
                JobExecution.job_id == job.id,
                JobExecution.attempt_number == job.attempts
            )
            .order_by(JobExecution.id.desc())
            .first()
        )

        now = datetime.utcnow()

        if execution:

            execution.status = "FAILED"
            execution.finished_at = now
            execution.duration_ms = int(
                (now - start_time).total_seconds() * 1000
            )
            execution.error_message = error_message

        job.error_message = error_message
        job.failed_at = now

        # ====================================================
        # RETRY
        # ====================================================

        if job.attempts < job.max_attempts:

            queue = (
                db.query(Queue)
                .filter(Queue.id == job.queue_id)
                .first()
            )

            retry_policy = None

            if queue and queue.retry_policy_id:

                retry_policy = (
                    db.query(RetryPolicy)
                    .filter(
                        RetryPolicy.id ==
                        queue.retry_policy_id
                    )
                    .first()
                )

            strategy = "fixed"
            base_delay = 5

            if retry_policy:

                strategy = retry_policy.strategy
                base_delay = retry_policy.base_delay_seconds

            delay = calculate_retry_delay(
                strategy,
                base_delay,
                job.attempts
            )

            job.status = "QUEUED"
            job.worker_id = None
            job.claimed_at = None
            job.started_at = None
            job.next_retry_at = now + timedelta(
                seconds=delay
            )

            db.commit()

            add_job_log(
                job.id,
                f"Job failed. Retry {job.attempts + 1} "
                f"scheduled after {delay} seconds.",
                "WARNING",
                execution.id if execution else None
            )

            print(
                f"Job {job.id} will retry in "
                f"{delay} seconds"
            )

        # ====================================================
        # DEAD LETTER QUEUE
        # ====================================================

        else:

            job.status = "DEAD"

            job.worker_id = None

            dlq = DeadLetterJob(
                job_id=job.id,
                reason="Maximum retry attempts exceeded",
                last_error=error_message,
                attempts=job.attempts
            )

            db.add(dlq)

            db.commit()

            add_job_log(
                job.id,
                "Job moved to Dead Letter Queue",
                "ERROR",
                execution.id if execution else None
            )

            print(
                f"Job {job.id} moved to DLQ"
            )

    finally:

        db.close()


# ============================================================
# POLL FOR JOB
# ============================================================

def poll_for_job(worker_id: int):

    db = SessionLocal()

    try:

        return claim_next_job(
            db=db,
            worker_id=worker_id
        )

    except Exception as e:

        db.rollback()

        print(
            f"Worker {worker_id} polling error: {e}"
        )

        return None

    finally:

        db.close()


# ============================================================
# UPDATE WORKER ACTIVE JOB COUNT
# ============================================================

def update_worker_count(
    worker_id: int,
    delta: int
):

    db = SessionLocal()

    try:

        worker = (
            db.query(Worker)
            .filter(Worker.id == worker_id)
            .first()
        )

        if worker:

            worker.active_jobs = max(
                0,
                worker.active_jobs + delta
            )

            db.commit()

    finally:

        db.close()


# ============================================================
# WORKER LOOP
# ============================================================

def worker_loop(worker_id: int):

    db = SessionLocal()

    worker = (
        db.query(Worker)
        .filter(Worker.id == worker_id)
        .first()
    )

    if not worker:

        print(
            f"Worker {worker_id} does not exist"
        )

        db.close()

        return

    concurrency = worker.concurrency_limit

    db.close()

    print(
        f"Worker {worker_id} started "
        f"with concurrency={concurrency}"
    )

    # --------------------------------------------------------
    # Thread pool allows concurrent jobs
    # --------------------------------------------------------

    executor = ThreadPoolExecutor(
        max_workers=concurrency
    )

    futures = []

    try:

        while True:

            # ----------------------------------------------
            # Heartbeat
            # ----------------------------------------------

            send_heartbeat(worker_id)

            # ----------------------------------------------
            # Remove completed futures
            # ----------------------------------------------

            active_futures = []

            for future in futures:

                if future.done():

                    try:
                        future.result()
                    except Exception as e:
                        print(
                            f"Worker execution error: {e}"
                        )

                    update_worker_count(
                        worker_id,
                        -1
                    )

                else:

                    active_futures.append(
                        future
                    )

            futures = active_futures

            # ----------------------------------------------
            # Respect concurrency limit
            # ----------------------------------------------

            if len(futures) >= concurrency:

                time.sleep(1)

                continue

            # ----------------------------------------------
            # Claim next job
            # ----------------------------------------------

            job = poll_for_job(worker_id)

            if job is None:

                time.sleep(2)

                continue

            # ----------------------------------------------
            # Update worker count
            # ----------------------------------------------

            update_worker_count(
                worker_id,
                1
            )

            print(
                f"Worker {worker_id} claimed "
                f"Job {job.id}"
            )

            # ----------------------------------------------
            # Execute asynchronously
            # ----------------------------------------------

            future = executor.submit(
                execute_job,
                job.id,
                worker_id
            )

            futures.append(future)

    except KeyboardInterrupt:

        print(
            f"Worker {worker_id} shutting down..."
        )

        executor.shutdown(
            wait=True
        )

        db = SessionLocal()

        try:

            worker = (
                db.query(Worker)
                .filter(Worker.id == worker_id)
                .first()
            )

            if worker:

                worker.status = "OFFLINE"
                worker.active_jobs = 0

                db.commit()

        finally:

            db.close()

        print(
            f"Worker {worker_id} stopped"
        )