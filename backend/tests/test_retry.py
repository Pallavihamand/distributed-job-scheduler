import unittest
from unittest.mock import MagicMock

from app.worker.retry import calculate_retry_delay, handle_job_failure


class TestRetryStrategies(unittest.TestCase):

    def test_fixed_retry_delay(self):
        delay = calculate_retry_delay(
            attempt=3,
            strategy="fixed",
            base_delay=5,
        )

        self.assertEqual(delay, 5)

    def test_linear_retry_delay(self):
        delay = calculate_retry_delay(
            attempt=3,
            strategy="linear",
            base_delay=5,
        )

        self.assertEqual(delay, 15)

    def test_exponential_retry_delay(self):
        delay = calculate_retry_delay(
            attempt=3,
            strategy="exponential",
            base_delay=5,
        )

        self.assertEqual(delay, 20)

    def test_failed_job_is_requeued(self):
        db = MagicMock()

        job = MagicMock()
        job.attempts = 0
        job.max_attempts = 3
        job.worker_id = 1

        result = handle_job_failure(
            db=db,
            job=job,
            error_message="Temporary failure",
            retry_strategy="fixed",
            base_delay=5,
        )

        self.assertEqual(result["action"], "RETRY")
        self.assertEqual(result["attempt"], 1)
        self.assertEqual(result["delay_seconds"], 5)

        self.assertEqual(job.status, "QUEUED")
        self.assertIsNone(job.worker_id)

        db.commit.assert_called()

    def test_failed_job_moves_to_dead_letter_queue(self):
        db = MagicMock()

        job = MagicMock()
        job.id = 100
        job.attempts = 2
        job.max_attempts = 3
        job.worker_id = 1

        result = handle_job_failure(
            db=db,
            job=job,
            error_message="Permanent failure",
        )

        self.assertEqual(result["action"], "DLQ")
        self.assertEqual(result["attempts"], 3)

        self.assertEqual(job.status, "DEAD_LETTER")
        self.assertIsNone(job.worker_id)

        db.add.assert_called_once()
        db.commit.assert_called_once()


if __name__ == "__main__":
    unittest.main()