
import signal
import socket
import time
from datetime import datetime
from threading import Event, Thread
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.job import Job
from app.models.worker import Worker
from app.models.job_execution import JobExecution
from app.models.dead_letter import DeadLetterJob


# ============================================================
# CONFIGURATION
# ============================================================

WORKER_NAME = f"worker-{socket.gethostname()}"

POLL_INTERVAL_SECONDS = 2

HEARTBEAT_INTERVAL_SECONDS = 5

DEFAULT_CONCURRENCY = 5


# ============================================================
# WORKER SERVICE
# ============================================================

class WorkerService:

    def __init__(self):

        self.shutdown_event = Event()

        self.worker_id = None

        self.worker_name = WORKER_NAME

        self.executor = ThreadPoolExecutor(
            max_workers=DEFAULT_CONCURRENCY
        )

        self.last_heartbeat = 0


    # ========================================================
    # REGISTER WORKER
    # ========================================================

    def register_worker(self):

        db: Session = SessionLocal()

        try:

            worker = (
                db.query(Worker)
                .filter(
                    Worker.name == self.worker_name
                )
                .first()
            )

            hostname = socket.gethostname()

            if worker:

                worker.status = "ONLINE"

                worker.hostname = hostname

                worker.is_active = True

                worker.last_heartbeat = datetime.utcnow()

                worker.concurrency_limit = (
                    worker.concurrency_limit
                    or DEFAULT_CONCURRENCY
                )

            else:

                worker = Worker(
                    name=self.worker_name,
                    status="ONLINE",
                    hostname=hostname,
                    active_jobs=0,
                    concurrency_limit=DEFAULT_CONCURRENCY,
                    is_active=True,
                    started_at=datetime.utcnow(),
                    last_heartbeat=datetime.utcnow(),
                )

                db.add(worker)

            db.commit()

            db.refresh(worker)

            self.worker_id = worker.id

            print(
                f"[WORKER] Registered worker "
                f"{worker.name} "
                f"(ID={worker.id})"
            )

        finally:

            db.close()


    # ========================================================
    # HEARTBEAT
    # ========================================================

    def heartbeat(self):

        db: Session = SessionLocal()

        try:

            worker = (
                db.query(Worker)
                .filter(
                    Worker.id == self.worker_id
                )
                .first()
            )

            if not worker:
                return

            worker.status = "ONLINE"

            worker.last_heartbeat = datetime.utcnow()

            db.commit()

        finally:

            db.close()


    # ========================================================
    # CHECK CONCURRENCY
    # ========================================================

    def can_execute(self):

        db: Session = SessionLocal()

        try:

            worker = (
                db.query(Worker)
                .filter(
                    Worker.id == self.worker_id
                )
                .first()
            )

            if not worker:
                return False

            return (
                worker.active_jobs
                < worker.concurrency_limit
            )

        finally:

            db.close()


    # ========================================================
    # ATOMIC JOB CLAIM
    # ========================================================

    def claim_job(self):

        db: Session = SessionLocal()

        try:

            now = datetime.utcnow()

            # ------------------------------------------------
            # Find an eligible job
            # ------------------------------------------------

            job = (
                db.query(Job)
                .filter(
                    and_(
                        Job.status == "QUEUED",

                        (
                            (Job.scheduled_at.is_(None))
                            |
                            (Job.scheduled_at <= now)
                        ),

                        (
                            (Job.next_retry_at.is_(None))
                            |
                            (Job.next_retry_at <= now)
                        ),
                    )
                )
                .order_by(
                    Job.priority.desc(),
                    Job.created_at.asc(),
                )
                .with_for_update(
                    skip_locked=True
                )
                .first()
            )

            if not job:
                db.rollback()
                return None

            # ------------------------------------------------
            # Claim job
            # ------------------------------------------------

            job.status = "CLAIMED"

            job.worker_id = self.worker_id

            job.claimed_at = now

            job.attempts += 1

            # ------------------------------------------------
            # Increase active jobs
            # ------------------------------------------------

            worker = (
                db.query(Worker)
                .filter(
                    Worker.id == self.worker_id
                )
                .with_for_update()
                .first()
            )

            if worker:

                worker.active_jobs += 1

            db.commit()

            print(
                f"[WORKER {self.worker_id}] "
                f"Claimed job {job.id}"
            )

            return job.id

        except Exception:

            db.rollback()

            raise

        finally:

            db.close()


    # ========================================================
    # EXECUTE JOB
    # ========================================================

    def execute_job(self, job_id: int):

        db: Session = SessionLocal()

        execution = None

        start_time = datetime.utcnow()

        try:

            job = (
                db.query(Job)
                .filter(Job.id == job_id)
                .first()
            )

            if not job:

                return

            # ------------------------------------------------
            # RUNNING
            # ------------------------------------------------

            job.status = "RUNNING"

            job.started_at = start_time

            execution = JobExecution(
                job_id=job.id,
                worker_id=self.worker_id,
                attempt_number=job.attempts,
                status="RUNNING",
                started_at=start_time,
            )

            db.add(execution)

            db.commit()

            print(
                f"[WORKER {self.worker_id}] "
                f"Executing job {job.id}"
            )

            # ------------------------------------------------
            # ACTUAL JOB EXECUTION
            # ------------------------------------------------

            self.run_job(job)

            # ------------------------------------------------
            # SUCCESS
            # ------------------------------------------------

            finish_time = datetime.utcnow()

            job.status = "COMPLETED"

            job.completed_at = finish_time

            job.error_message = None

            if execution:

                execution.status = "COMPLETED"

                execution.finished_at = finish_time

                execution.duration_ms = int(
                    (
                        finish_time - start_time
                    ).total_seconds()
                    * 1000
                )

            db.commit()

            print(
                f"[WORKER {self.worker_id}] "
                f"Job {job.id} completed"
            )

        except Exception as exc:

            db.rollback()

            self.handle_failure(
                job_id=job_id,
                error=str(exc),
            )

        finally:

            self.decrease_active_jobs()


    # ========================================================
    # JOB EXECUTION LOGIC
    # ========================================================

    def run_job(self, job):

        """
        Execute the actual background task.

        For the assignment demo, different job_type
        values can simulate different operations.
        """

        job_type = job.job_type

        payload = job.payload or {}

        print(
            f"[JOB {job.id}] "
            f"type={job_type} "
            f"payload={payload}"
        )

        # ----------------------------------------------------
        # Demo task
        # ----------------------------------------------------

        if job_type == "sleep":

            seconds = payload.get(
                "seconds",
                2
            )

            time.sleep(seconds)

        elif job_type == "print":

            message = payload.get(
                "message",
                "Hello from worker"
            )

            print(
                f"[JOB {job.id}] {message}"
            )

        elif job_type == "fail":

            raise RuntimeError(
                "Intentional job failure"
            )

        else:

            # Generic demo execution
            time.sleep(1)


    # ========================================================
    # HANDLE FAILURE
    # ========================================================

    def handle_failure(
        self,
        job_id: int,
        error: str,
    ):

        db: Session = SessionLocal()

        try:

            job = (
                db.query(Job)
                .filter(Job.id == job_id)
                .first()
            )

            if not job:
                return

            now = datetime.utcnow()

            job.failed_at = now

            job.error_message = error

            # ------------------------------------------------
            # Retry
            # ------------------------------------------------

            if job.attempts < job.max_attempts:

                job.status = "QUEUED"

                # Simple exponential backoff
                delay_seconds = (
                    2 ** (job.attempts - 1)
                )

                from datetime import timedelta

                job.next_retry_at = (
                    now
                    + timedelta(
                        seconds=delay_seconds
                    )
                )

                print(
                    f"[WORKER {self.worker_id}] "
                    f"Job {job.id} failed. "
                    f"Retry {job.attempts}/"
                    f"{job.max_attempts} "
                    f"in {delay_seconds}s"
                )

            else:

                # ------------------------------------------------
                # MOVE TO DEAD LETTER QUEUE
                # ------------------------------------------------

                job.status = "DEAD_LETTER"

                dlq = DeadLetterJob(
                    job_id=job.id,
                    reason="Maximum retry attempts exceeded",
                    last_error=error,
                    attempts=job.attempts,
                )

                db.add(dlq)

                print(
                    f"[WORKER {self.worker_id}] "
                    f"Job {job.id} moved to DLQ"
                )

            db.commit()

        except Exception:

            db.rollback()

            print(
                f"[WORKER] Failed handling "
                f"job {job_id} failure"
            )

        finally:

            db.close()


    # ========================================================
    # DECREASE ACTIVE JOB COUNT
    # ========================================================

    def decrease_active_jobs(self):

        db: Session = SessionLocal()

        try:

            worker = (
                db.query(Worker)
                .filter(
                    Worker.id == self.worker_id
                )
                .first()
            )

            if worker:

                worker.active_jobs = max(
                    0,
                    worker.active_jobs - 1
                )

                db.commit()

        finally:

            db.close()


    # ========================================================
    # WORKER LOOP
    # ========================================================

    def run(self):

        self.register_worker()

        print(
            f"[WORKER] Starting worker loop..."
        )

        while not self.shutdown_event.is_set():

            try:

                # ------------------------------------------------
                # Heartbeat
                # ------------------------------------------------

                current_time = time.time()

                if (
                    current_time
                    - self.last_heartbeat
                    >= HEARTBEAT_INTERVAL_SECONDS
                ):

                    self.heartbeat()

                    self.last_heartbeat = (
                        current_time
                    )

                # ------------------------------------------------
                # Check concurrency
                # ------------------------------------------------

                if not self.can_execute():

                    time.sleep(
                        POLL_INTERVAL_SECONDS
                    )

                    continue

                # ------------------------------------------------
                # Claim job
                # ------------------------------------------------

                job_id = self.claim_job()

                if job_id is None:

                    time.sleep(
                        POLL_INTERVAL_SECONDS
                    )

                    continue

                # ------------------------------------------------
                # Execute concurrently
                # ------------------------------------------------

                self.executor.submit(
                    self.execute_job,
                    job_id,
                )

            except Exception as exc:

                print(
                    f"[WORKER ERROR] {exc}"
                )

                time.sleep(2)

        self.shutdown()


    # ========================================================
    # GRACEFUL SHUTDOWN
    # ========================================================

    def shutdown(self):

        print(
            "[WORKER] Shutting down..."
        )

        self.shutdown_event.set()

        self.executor.shutdown(
            wait=True
        )

        db: Session = SessionLocal()

        try:

            worker = (
                db.query(Worker)
                .filter(
                    Worker.id == self.worker_id
                )
                .first()
            )

            if worker:

                worker.status = "OFFLINE"

                worker.is_active = False

                worker.last_heartbeat = datetime.utcnow()

                db.commit()

        finally:

            db.close()

        print(
            "[WORKER] Shutdown complete"
        )


# ============================================================
# SIGNAL HANDLING
# ============================================================

worker_service = WorkerService()


def handle_shutdown_signal(
    signum,
    frame,
):

    print(
        f"[WORKER] Shutdown signal received: {signum}"
    )

    worker_service.shutdown_event.set()


signal.signal(
    signal.SIGINT,
    handle_shutdown_signal,
)

signal.signal(
    signal.SIGTERM,
    handle_shutdown_signal,
)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    worker_service.run()

