from application.interfaces import ILLMAgent, IPDFReader
from application.models import ArticleState, DocumentRecord, ProcessingContext


class ProcessNewArticle:
    """
    Orchestrates the flat, linear pipeline.
    """

    def __init__(
        self,
        pdf_reader: IPDFReader,
        worker_agent: ILLMAgent,
        supervisor_agent: ILLMAgent,
    ):
        self.pdf_reader = pdf_reader
        self.worker_agent = worker_agent
        self.supervisor_agent = supervisor_agent

    def execute(self, file_path: str):
        # 1. Initialize the State Object
        raw_text = self.pdf_reader.extract_optimized_text(file_path)
        context = ProcessingContext(file_path=file_path, raw_text=raw_text)

        # 2. Pipeline Execution (The State moves through the agents)
        context = self.worker_agent.process(context)
        context = self.supervisor_agent.process(context)
        # 3. Final Persistence (Extract only the clean Domain Model)
        record = DocumentRecord(
            file_path=context.file_path,
            metadata=context.final_metadata,  # The pure Pydantic model
            state=ArticleState.PENDING_REVIEW,
        )
        return record
