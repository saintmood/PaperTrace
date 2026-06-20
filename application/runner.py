import asyncio
import logging
from pathlib import Path

from config import settings
from application.interfaces import IRunner

logger = logging.getLogger(__name__)


class PipelineRunner(IRunner):
    def __init__(self, use_case, concurrency: int = 1):
        self.use_case = use_case
        self.queue = asyncio.Queue()
        # 'concurrency' determines how many files we process in parallel.
        # For local LLMs, it's best to keep it at 1 to prevent out-of-memory (OOM) errors.
        self.concurrency = concurrency

    async def _load_files_to_queue(self) -> int:
        """Producer: Scans the folder once and populates the queue."""
        raw_dir = Path(settings.raw_whitepapers_path)
        files = list(raw_dir.glob("*.pdf"))

        if not files:
            logger.info("🤷‍♂️ The folder is empty. No new files to process.")
            return 0

        for pdf_path in files:
            await self.queue.put(pdf_path)

        logger.info(f"📥 Found {len(files)} files. Starting batch processing.")
        return len(files)

    async def _worker(self, worker_id: int):
        """Consumer: Performs the heavy processing until the queue is empty."""
        while True:
            pdf_path = await self.queue.get()
            try:
                logger.info(f"🚀 [Worker-{worker_id}] picking up: {pdf_path.name}")
                # Offload the synchronous workload (LLM, SQLite, File IO) to a separate thread
                await asyncio.to_thread(self.use_case.execute, str(pdf_path))
            except Exception as e:
                logger.error(f"⚠️ [Worker-{worker_id}] Critical error with {pdf_path.name}: {e}")
                self._mark_as_failed(pdf_path)
            finally:
                # Always notify the queue that the task is complete, even if it failed
                self.queue.task_done()

    def _mark_as_failed(self, pdf_path: Path):
        """Renames a broken file to prevent it from blocking future runs."""
        try:
            failed_path = pdf_path.with_suffix(".pdf.failed")
            pdf_path.rename(failed_path)
        except Exception as e:
            logger.error(f"Failed to rename the broken file: {e}")

    async def run(self):
        """Entry point: loads files, starts workers, and waits for completion."""
        total_files = await self._load_files_to_queue()

        if total_files == 0:
            return

        # Start N consumers (in our case, 1)
        workers = [asyncio.create_task(self._worker(i)) for i in range(self.concurrency)]

        # Block script execution until all items in the queue have received task_done()
        await self.queue.join()

        # Once the queue is fully processed and empty, cancel the infinite worker loops
        for w in workers:
            w.cancel()

        logger.info("🎉 Batch processing successfully completed! All files moved to the archive.")
