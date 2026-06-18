import logging
import re

import fitz

from application.interfaces import IPDFReader

logger = logging.getLogger(__name__)


class PyPDFReader(IPDFReader):
    """Concrete implementation for PDF processing."""

    def extract_optimized_text(self, file_path: str) -> str:
        """
        Extracts only Page 1, Last, and Penultimate pages.
        """
        doc = fitz.open(file_path)
        page_conunt = doc.page_count
        logger.info("Extracting the first page (Title, Authors, Keyword)")
        first_page = doc.load_page(0).get_text("text")
        second_page = doc.load_page(1).get_text("text")
        third_page = doc.load_page(2).get_text("text")
        conclusion_page = None
        for idx in range(page_conunt - 1, 0, -1):
            page_text = doc.load_page(idx).get_text("text")
            if re.search(
                r"(?m)^\s*(?:\d+\.?|[IVX]+\.?\s*)?Conclusions?\b", page_text, re.IGNORECASE
            ):
                logger.info(f"Extracting the conclusion page (Page {idx + 1})")
                conclusion_page = page_text
        raw_text = (
            first_page
            + "\n"
            + second_page
            + "\n"
            + third_page
            + "\n"
            + "\nCONCLUSIONS\n"
            + (conclusion_page if conclusion_page else "")
        )
        return raw_text
