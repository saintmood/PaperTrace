import logging
import sys

import click

from application.infra.agents import SupervisorAgent, WorkerAgent
from application.infra.pdf_parser import PyPDFReader
from application.infra.sqlite_repo import SQLiteRepository
from application.pipeline import ProcessNewArticle

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def build_process_use_case() -> ProcessNewArticle:
    return ProcessNewArticle(
        pdf_reader=PyPDFReader(),
        worker_agent=WorkerAgent(),
        supervisor_agent=SupervisorAgent(),
        repo=SQLiteRepository(db_name="papertrace.db"),
    )


@click.group()
def cli():
    """📑 PaperTrace: Smart Scientific Article Archiver (Sarcophagus Edition)"""
    pass


@cli.command()
@click.argument("file_path", type=click.Path(exists=True, dir_okay=False))
def process(file_path: str):
    """Parse, extract, and critique a new PDF whitepaper."""
    click.secho(f"🚀 Initializing PaperTrace Pipeline for: {file_path}", fg="blue")

    use_case = build_process_use_case()

    try:
        record = use_case.execute(file_path)
        click.secho("\n✨ Pipeline Completed Successfully!", fg="green", bold=True)
        click.echo(f"ID: {record.id}")
        click.echo(f"Title: {record.metadata.title}")
        click.secho(f"State: {record.state.value} (Waiting for human review)", fg="yellow")

    except Exception as e:
        click.secho(f"\n❌ Pipeline failed: {e}", fg="red", bold=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
