import logging

from application.interfaces import ILLMAgent, IPDFReader, IRepository
from application.models import ArticleState, ProcessingContext

logger = logging.getLogger(__name__)


class ProcessNewArticle:
    """
    Orchestrates the flat, linear pipeline for processing new articles.
    """

    def __init__(
        self,
        pdf_reader: IPDFReader,
        worker_agent: ILLMAgent,
        supervisor_agent: ILLMAgent,
        repo: IRepository,
    ):
        self.pdf_reader = pdf_reader
        self.worker_agent = worker_agent
        self.supervisor_agent = supervisor_agent
        self.article_repo = repo

    def execute(self, file_path: str):
        # 1. Initialize the State Object
        raw_text = self.pdf_reader.extract_optimized_text(file_path)
        context: ProcessingContext = ProcessingContext(file_path=file_path, raw_text=raw_text)

        # 2. Pipeline Execution (The State moves through the agents)
        context = self.worker_agent.process(context)
        context = self.supervisor_agent.process(context)
        # 3. Final Persistence (Extract only the clean Domain Model)
        if context.final_metadata:
            self.article_repo.save_article(
                metadata=context.final_metadata,
                proposed_filename=context.supervisor_review.proposed_filename,
                status=ArticleState.PENDING_REVIEW,
            )
        logger.info("✅ Pipeline successfully completed! Data saved to DB.")
