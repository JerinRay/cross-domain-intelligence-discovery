import json
import logging
from datetime import datetime, timezone
from pathlib import Path


class IntelligenceOrchestrator:
    """
    Coordinates the project's existing intelligence modules.

    Individual stages are isolated so that one stage failure
    does not automatically stop the remaining workflow.
    """

    def __init__(
        self,
        raw_directory="datasets/raw",
        processed_directory="datasets/processed",
        output_directory="logs/pipeline"
    ):
        self.raw_directory = Path(raw_directory)
        self.processed_directory = Path(processed_directory)
        self.output_directory = Path(output_directory)

        self.output_directory.mkdir(
            parents=True,
            exist_ok=True
        )

        self.logger = logging.getLogger(
            "intelligence_pipeline"
        )

        self.logger.setLevel(logging.INFO)

        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s | %(levelname)s | %(message)s"
                )
            )
            self.logger.addHandler(handler)

        self.results = {
            "pipeline": "Cross-Domain Intelligence Discovery",
            "started_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "stages": {}
        }

    def execute_stage(self, stage_name, operation):
        """Execute one stage and record its result."""

        self.logger.info("Starting stage: %s", stage_name)

        try:
            result = operation()

            self.results["stages"][stage_name] = {
                "status": "SUCCESS",
                "result": result
            }

            self.logger.info(
                "Completed stage: %s",
                stage_name
            )

            return result

        except Exception as error:
            self.results["stages"][stage_name] = {
                "status": "FAILED",
                "error": str(error)
            }

            self.logger.exception(
                "Stage failed: %s",
                stage_name
            )

            return None

    def save_pipeline_report(self):
        """Save a JSON summary of all pipeline stages."""

        self.results["completed_at"] = datetime.now(
            timezone.utc
        ).isoformat()

        successful = sum(
            stage["status"] == "SUCCESS"
            for stage in self.results["stages"].values()
        )

        failed = sum(
            stage["status"] == "FAILED"
            for stage in self.results["stages"].values()
        )

        self.results["summary"] = {
            "total_stages": len(self.results["stages"]),
            "successful_stages": successful,
            "failed_stages": failed,
            "overall_status": (
                "SUCCESS" if failed == 0
                else "PARTIAL_SUCCESS" if successful > 0
                else "FAILED"
            )
        }

        report_path = (
            self.output_directory /
            "pipeline_execution_report.json"
        )

        with open(
            report_path,
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                self.results,
                file,
                indent=4,
                ensure_ascii=False,
                default=str
            )

        self.logger.info(
            "Pipeline report saved: %s",
            report_path
        )

        return str(report_path)
