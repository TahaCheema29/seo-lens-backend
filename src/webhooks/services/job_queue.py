import json
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID

from src.config.logger_config import setup_logger
from src.config.redis_client import redis_client
from src.config.database import get_db_session
from src.webhooks.repository.webhook_repository import DeploymentAnalysisRepository
from src.seo_tools.seo_tools_service import SeoToolsService
from src.seo_tools.schemas.analyze_site_seo import AnalyzeSiteSeoRequest
from src.models.cicd_integration import DeploymentAnalysis
from src.models.user import User
from src.notifications.email_service import email_service

logger = setup_logger(__name__)


class JobQueueError(Exception):
    """Base exception for job queue errors"""
    pass


class JobQueue:
    """
    Redis-based job queue for async SEO analysis

    This queue handles:
    1. Enqueuing analysis jobs
    2. Processing jobs asynchronously
    3. Updating job status in database
    4. Triggering notifications on completion
    """

    QUEUE_KEY = "seo_lens:job_queue"
    PROCESSING_KEY = "seo_lens:processing_jobs"
    JOB_PREFIX = "seo_lens:job:"

    def __init__(self):
        self.logger = logger
        self.seo_service = SeoToolsService()

    async def enqueue(
        self,
        job_id: str,
        analysis_id: UUID,
        user_id: UUID,
        target_url: str,
        crawl_mode: str,
        email: Optional[str] = None
    ) -> bool:
        """
        Add a job to the queue

        Args:
            job_id: Unique job identifier
            analysis_id: DeploymentAnalysis record ID
            user_id: User ID
            target_url: URL to analyze
            crawl_mode: Crawl mode (standard, deep, light)
            email: Email to send results to

        Returns:
            True if enqueued successfully
        """
        try:
            job_data = {
                "job_id": job_id,
                "analysis_id": str(analysis_id),
                "user_id": str(user_id),
                "target_url": target_url,
                "crawl_mode": crawl_mode,
                "email": email,
                "status": "queued",
                "created_at": datetime.utcnow().isoformat(),
                "attempts": 0,
            }

            # Store job data in Redis
            await redis_client.setex(
                f"{self.JOB_PREFIX}{job_id}",
                3600 * 24,  # 24 hour TTL
                json.dumps(job_data)
            )

            # Add to queue
            await redis_client.lpush(self.QUEUE_KEY, job_id)

            self.logger.info(f"Enqueued job {job_id} for URL: {target_url}")
            return True

        except Exception as e:
            self.logger.error(f"Error enqueuing job {job_id}: {e}", exc_info=True)
            return False

    async def dequeue(self) -> Optional[Dict[str, Any]]:
        """
        Get the next job from the queue

        Returns:
            Job data dict or None if queue is empty
        """
        try:
            # Use BRPOP for blocking pop (waits for jobs)
            # For non-blocking, use RPOP
            result = await redis_client.brpop(self.QUEUE_KEY, timeout=1)

            if not result:
                return None

            _, job_id = result
            job_id = job_id.decode() if isinstance(job_id, bytes) else job_id

            # Get job data
            job_data = await redis_client.get(f"{self.JOB_PREFIX}{job_id}")

            if not job_data:
                self.logger.warning(f"Job {job_id} data not found in Redis")
                return None

            return json.loads(job_data)

        except Exception as e:
            self.logger.error(f"Error dequeuing job: {e}", exc_info=True)
            return None

    async def update_job_status(
        self,
        job_id: str,
        status: str,
        progress: Optional[int] = None,
        error: Optional[str] = None,
        result: Optional[Dict] = None
    ) -> bool:
        """
        Update job status in Redis

        Args:
            job_id: Job identifier
            status: New status (processing, completed, failed)
            progress: Optional progress percentage
            error: Optional error message
            result: Optional result data

        Returns:
            True if updated successfully
        """
        try:
            key = f"{self.JOB_PREFIX}{job_id}"
            job_data = await redis_client.get(key)

            if not job_data:
                return False

            data = json.loads(job_data)
            data["status"] = status
            data["updated_at"] = datetime.utcnow().isoformat()

            if progress is not None:
                data["progress"] = progress
            if error:
                data["error"] = error
            if result:
                data["result"] = result

            # Reset TTL
            await redis_client.setex(key, 3600 * 24, json.dumps(data))
            return True

        except Exception as e:
            self.logger.error(f"Error updating job {job_id} status: {e}", exc_info=True)
            return False

    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job data by ID"""
        try:
            job_data = await redis_client.get(f"{self.JOB_PREFIX}{job_id}")
            if job_data:
                return json.loads(job_data)
            return None
        except Exception as e:
            self.logger.error(f"Error getting job {job_id}: {e}", exc_info=True)
            return None

    async def process_job(self, job_data: Dict[str, Any]) -> bool:
        """
        Process a single job

        This is the main worker function that:
        1. Runs SEO analysis
        2. Saves results to database
        3. Updates job status
        4. Triggers email notification

        Args:
            job_data: Job data dict

        Returns:
            True if processed successfully
        """
        job_id = job_data["job_id"]
        analysis_id = UUID(job_data["analysis_id"])
        user_id = UUID(job_data["user_id"])
        target_url = job_data["target_url"]
        crawl_mode = job_data["crawl_mode"]
        email = job_data.get("email")

        self.logger.info(f"Processing job {job_id} for URL: {target_url}")

        try:
            # Update status to processing
            await self.update_job_status(job_id, "processing", progress=10)

            async with get_db_session() as db:
                analysis_repo = DeploymentAnalysisRepository(db)

                # Update analysis status
                await analysis_repo.update_status(analysis_id, "processing")

                # Fetch deployment analysis record for details
                analysis_record = await analysis_repo.get_by_id(analysis_id)

                # Run SEO analysis
                await self.update_job_status(job_id, "processing", progress=30)

                # Map webhook crawl_mode to SEO service CrawlMode enum
                crawl_mode_mapping = {
                    "light": "SITEMAP_ONLY",
                    "standard": "FULL_CRAWL", 
                    "deep": "FULL_CRAWL"
                }
                seo_crawl_mode = crawl_mode_mapping.get(crawl_mode, "FULL_CRAWL")
                
                request = AnalyzeSiteSeoRequest(
                    url=target_url,
                    crawl_mode=seo_crawl_mode
                )

                # Run analysis (this takes ~2 minutes)
                results = await self.seo_service.analyze_site_seo(
                    user_input=request,
                    user_id=str(user_id)
                )

                await self.update_job_status(job_id, "processing", progress=80)

                # Get the saved SEO insight ID
                # The service saves it automatically, we need to fetch it
                # For now, we'll use the score from results
                score = self.seo_service._calculate_seo_score(
                    results.base_url_checks.model_dump() if results and results.base_url_checks else {},
                    [r.model_dump() for r in results.url_results] if results and results.url_results else []
                ) if results else None

                pages_analyzed = len(results.url_results) if results else 0

                # Update analysis record
                await analysis_repo.update_status(
                    analysis_id,
                    status="completed",
                    score=score
                )

                # Update job status
                await self.update_job_status(
                    job_id,
                    "completed",
                    progress=100,
                    result={
                        "score": score,
                        "pages_analyzed": pages_analyzed,
                    }
                )

                self.logger.info(f"Job {job_id} completed successfully with score {score}")

                # Send email notification
                await self._send_completion_email(
                    job_id=job_id,
                    user_id=user_id,
                    email=email,
                    target_url=target_url,
                    score=score,
                    pages_analyzed=pages_analyzed,
                    analysis_record=analysis_record
                )

                return True

        except Exception as e:
            self.logger.error(f"Error processing job {job_id}: {e}", exc_info=True)

            # Update job status to failed
            await self.update_job_status(job_id, "failed", error=str(e))

            # Update analysis record
            try:
                async with get_db_session() as db:
                    analysis_repo = DeploymentAnalysisRepository(db)
                    await analysis_repo.update_status(analysis_id, "failed")
            except Exception as db_error:
                self.logger.error(f"Error updating failed status: {db_error}")

            return False

    async def _send_completion_email(
        self,
        job_id: str,
        user_id: UUID,
        email: Optional[str],
        target_url: str,
        score: Optional[int],
        pages_analyzed: int,
        analysis_record: Optional[DeploymentAnalysis] = None
    ) -> bool:
        """
        Send completion email to user

        Args:
            job_id: Job identifier
            user_id: User ID
            email: Email address (optional, will fetch from user if not provided)
            target_url: URL that was analyzed
            score: SEO score
            pages_analyzed: Number of pages analyzed
            analysis_record: DeploymentAnalysis record for additional context

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            async with get_db_session() as db:
                # Fetch user details if email not provided
                if not email:
                    from sqlalchemy import select
                    result = await db.execute(select(User).where(User.id == user_id))
                    user = result.scalar_one_or_none()
                    if user:
                        email = user.email
                        user_name = user.full_name or user.email.split('@')[0]
                    else:
                        self.logger.warning(f"User {user_id} not found, cannot send email")
                        return False
                else:
                    user_name = email.split('@')[0]

                # Prepare report data
                report_data = {
                    "target_url": target_url,
                    "score": score or 0,
                    "pages_analyzed": pages_analyzed,
                    "job_id": job_id,
                }

                # Extract repository info from analysis record if available
                repository = None
                pr_number = None
                branch = None

                if analysis_record:
                    repository = analysis_record.repository_name
                    pr_number = analysis_record.pr_number
                    branch = analysis_record.branch_name

                # Send email
                email_sent = await email_service.send_seo_report_email(
                    to_email=email,
                    user_name=user_name,
                    report_data=report_data,
                    repository=repository,
                    pr_number=pr_number,
                    branch=branch
                )

                if email_sent:
                    self.logger.info(f"Email sent successfully to {email} for job {job_id}")
                else:
                    self.logger.error(f"Failed to send email to {email} for job {job_id}")

                return email_sent

        except Exception as e:
            self.logger.error(f"Error sending email for job {job_id}: {e}", exc_info=True)
            # Don't fail the job just because email failed
            return False

    async def start_worker(self, poll_interval: float = 1.0):
        """
        Start the job queue worker

        This runs indefinitely, processing jobs as they arrive.
        In production, this should be run as a separate process.

        Args:
            poll_interval: Seconds between queue polls when empty
        """
        self.logger.info("Starting job queue worker...")

        while True:
            try:
                job_data = await self.dequeue()

                if job_data:
                    await self.process_job(job_data)
                else:
                    # No jobs, wait before polling again
                    await asyncio.sleep(poll_interval)

            except Exception as e:
                self.logger.error(f"Worker error: {e}", exc_info=True)
                await asyncio.sleep(poll_interval)


# Global job queue instance
job_queue = JobQueue()
