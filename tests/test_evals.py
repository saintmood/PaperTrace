import json
from typing import Annotated

from deepeval import assert_test
from deepeval.metrics import GEval
from deepeval.models.base_model import DeepEvalBaseLLM
from deepeval.test_case import LLMTestCase, LLMTestCaseParams

from application.infra.agents import WorkerAgent
from application.infra.pdf_parser import PyPDFReader
from application.models import ProcessingContext


def test_worker_agent_extraction(
    test_study_path, deepeval_judge: Annotated[DeepEvalBaseLLM, "pytest.fixture"]
):
    pdf_reader = PyPDFReader()
    worker_agent = WorkerAgent()
    raw_text = pdf_reader.extract_text(test_study_path)
    context: ProcessingContext = ProcessingContext(
        file_path=str(test_study_path), raw_text=raw_text
    )
    context = worker_agent.process(context)
    actual_json_output = context.draft_metadata.model_dump_json()
    expected_data = {
        "title": "The Psychology of a Goat While Chewing Grass",
        "authors": ["Dr. C. Yellow", "Prof. B. Green"],
        "abstract": "This whitepaper investigates the cognitive states and psychological frameworks of Capra hircus (the domestic goat) during the active phase of masticating forage. While previous studies have extensively documented the physiological mechanics of the four-chambered stomach, the neurological and emotional experiences of the goat during the prolonged chewing process remain underexplored. Through observational analytics and neuro-telemetry, we propose that the act of chewing grass induces a complex, trance-like state.",
        "keywords": [
            "Rumination",
            "Cognitive Ecology",
            "Ungulate Mindfulness",
            "Dietary Focus",
            "Herbivore Psychology",
        ],
    }
    test_case = LLMTestCase(
        input=raw_text,
        actual_output=actual_json_output,
        expected_output=json.dumps(expected_data),
    )

    extraction_metric = GEval(
        name="Metadata Accuracy Metric",
        criteria="Verify if the actual_output correctly extracted the expected data.",
        evaluation_params=[
            LLMTestCaseParams.INPUT,
            LLMTestCaseParams.ACTUAL_OUTPUT,
            LLMTestCaseParams.EXPECTED_OUTPUT,
        ],
        model=deepeval_judge,
        threshold=0.9,
    )

    assert_test(test_case, [extraction_metric])
