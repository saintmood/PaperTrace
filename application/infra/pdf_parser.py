import logging
import re

import fitz

from application.interfaces import IPDFReader

logger = logging.getLogger(__name__)


class PyPDFReader(IPDFReader):
    """Implementation for PDF processing."""

    def extract_text(self, file_path: str) -> str:
        """
        Extracts up to the first 3 pages, and searches backwards for the Conclusion.
        Safely handles short documents (1 or 2 pages).
        """
        doc = fitz.open(file_path)
        page_count = doc.page_count
        logger.info(f"Starting extraction. Document has {page_count} page(s).")

        # 1. Safely extract up to the first 3 pages
        front_pages = []
        max_front_pages = min(3, page_count)

        for i in range(max_front_pages):
            logger.info(f"Extracting front page {i + 1}")
            front_pages.append(doc.load_page(i).get_text("text"))

        first_pages_combined = "\n".join(front_pages)

        # 2. Search for the conclusion starting from the last page, going backwards
        conclusion_page = None
        # Note: -1 as the stop argument ensures we check page 0 if it's a very short document
        for idx in range(page_count - 1, -1, -1):
            page_text = doc.load_page(idx).get_text("text")

            # Use regex to find the Conclusion section
            if re.search(
                r"(?m)^\s*(?:\d+\.?|[IVX]+\.?\s*)?Conclusions?\b", page_text, re.IGNORECASE
            ):
                logger.info(f"Conclusion found on page {idx + 1}")
                conclusion_page = page_text
                break  # CRITICAL: Stop searching once we find the last conclusion!

        # 3. Assemble the final raw text
        raw_text = first_pages_combined

        if conclusion_page:
            raw_text += "\n\nCONCLUSIONS\n" + conclusion_page

        return raw_text
