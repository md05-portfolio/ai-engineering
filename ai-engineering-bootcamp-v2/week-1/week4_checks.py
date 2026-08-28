"""
Week 4: Automated Checks
Code-based assertions to evaluate agent output quality.
"""

from dataclasses import dataclass
from typing import Optional, List
import re


@dataclass
class CheckResult:
    """Result of a single check."""

    check_name: str
    passed: bool
    error_message: Optional[str] = None
    details: dict = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}

    def to_dict(self) -> dict:
        return {
            "check_name": self.check_name,
            "passed": self.passed,
            "error_message": self.error_message,
            "details": self.details,
        }


class AnswerValidator:
    """Automated checks for agent answers."""

    @staticmethod
    def check_answer_not_empty(answer: Optional[str]) -> CheckResult:
        """CHECK 1: Answer must not be empty or None."""
        if not answer or not answer.strip():
            return CheckResult(
                check_name="answer_not_empty",
                passed=False,
                error_message="Answer is empty or None",
            )
        return CheckResult(check_name="answer_not_empty", passed=True)

    @staticmethod
    def check_answer_length(answer: str, min_length: int = 20) -> CheckResult:
        """CHECK 2: Answer must have minimum length (default 20 chars)."""
        if len(answer.strip()) < min_length:
            return CheckResult(
                check_name="answer_length",
                passed=False,
                error_message=f"Answer too short: {len(answer)} chars (min: {min_length})",
                details={"actual_length": len(answer), "min_length": min_length},
            )
        return CheckResult(check_name="answer_length", passed=True, details={"length": len(answer)})

    @staticmethod
    def check_no_error_strings(answer: str) -> CheckResult:
        """CHECK 3: Answer should not contain common error patterns."""
        error_patterns = [
            r"i don't have",
            r"i do not have",
            r"i cannot",
            r"cannot be answered",
            r"failed to",
            r"error:",
            r"exception:",
            r"traceback",
        ]

        found_errors = []
        for pattern in error_patterns:
            if re.search(pattern, answer, re.IGNORECASE):
                found_errors.append(pattern)

        if found_errors:
            return CheckResult(
                check_name="no_error_strings",
                passed=False,
                error_message=f"Found error patterns: {found_errors}",
                details={"patterns_found": found_errors},
            )
        return CheckResult(check_name="no_error_strings", passed=True)

    @staticmethod
    def check_no_hallucination_markers(answer: str) -> CheckResult:
        """CHECK 4: Answer should not contain obvious hallucination markers."""
        hallucination_patterns = [
            r"i'm (not sure|unsure)",
            r"i think|i guess|i assume",
            r"probably|maybe|possibly|allegedly",
            r"according to my training data",
            r"in general|typically|usually",
        ]

        # These are weaker signals - more lenient
        found_patterns = []
        for pattern in hallucination_patterns:
            if re.search(pattern, answer, re.IGNORECASE):
                found_patterns.append(pattern)

        # Only fail if multiple hallucination markers found
        if len(found_patterns) >= 3:
            return CheckResult(
                check_name="no_hallucination_markers",
                passed=False,
                error_message=f"Multiple hallucination markers: {found_patterns}",
                details={"markers_found": found_patterns, "count": len(found_patterns)},
            )
        return CheckResult(
            check_name="no_hallucination_markers",
            passed=True,
            details={"markers_found": found_patterns, "count": len(found_patterns)},
        )

    @staticmethod
    def check_answer_addresses_question(question: str, answer: str) -> CheckResult:
        """CHECK 5: Answer should contain some keywords from question."""
        # Extract keywords from question (words > 3 chars, excluding common words)
        common_words = {"what", "when", "where", "which", "about", "your", "this", "that"}
        q_words = set()
        for word in question.lower().split():
            clean_word = re.sub(r"[^\w]", "", word)
            if len(clean_word) > 3 and clean_word not in common_words:
                q_words.add(clean_word)

        answer_lower = answer.lower()
        matched_words = sum(1 for w in q_words if w in answer_lower)

        if len(q_words) > 0 and matched_words == 0:
            return CheckResult(
                check_name="answer_addresses_question",
                passed=False,
                error_message=f"No keywords from question found in answer",
                details={"question_keywords": list(q_words), "matched": matched_words},
            )

        return CheckResult(
            check_name="answer_addresses_question",
            passed=True,
            details={"question_keywords": list(q_words), "matched": matched_words},
        )


class ExecutionValidator:
    """Automated checks for agent execution quality."""

    @staticmethod
    def check_completion_status(status: str) -> CheckResult:
        """CHECK 6: Status should be 'complete' or 'success'."""
        if status not in ["complete", "success"]:
            return CheckResult(
                check_name="completion_status",
                passed=False,
                error_message=f"Status is '{status}', expected 'complete' or 'success'",
                details={"actual_status": status},
            )
        return CheckResult(check_name="completion_status", passed=True, details={"status": status})

    @staticmethod
    def check_reasonable_latency(latency_ms: int, max_latency_ms: int = 30000) -> CheckResult:
        """CHECK 7: Latency should be under max threshold (default 30 seconds)."""
        if latency_ms > max_latency_ms:
            return CheckResult(
                check_name="reasonable_latency",
                passed=False,
                error_message=f"Latency {latency_ms}ms exceeds {max_latency_ms}ms",
                details={"latency_ms": latency_ms, "max_latency_ms": max_latency_ms},
            )
        return CheckResult(
            check_name="reasonable_latency",
            passed=True,
            details={"latency_ms": latency_ms, "max_latency_ms": max_latency_ms},
        )

    @staticmethod
    def check_reasonable_iterations(iterations: int, max_iterations: int = 5) -> CheckResult:
        """CHECK 8: Should not max out iterations."""
        if iterations >= max_iterations:
            return CheckResult(
                check_name="reasonable_iterations",
                passed=False,
                error_message=f"Used {iterations} iterations (max: {max_iterations})",
                details={"iterations": iterations, "max_iterations": max_iterations},
            )
        return CheckResult(
            check_name="reasonable_iterations",
            passed=True,
            details={"iterations": iterations, "max_iterations": max_iterations},
        )

    @staticmethod
    def check_retrieved_documents(retrieved_count: int, min_relevant: int = 1) -> CheckResult:
        """CHECK 9: If search was performed, should retrieve relevant documents."""
        if retrieved_count == 0:
            return CheckResult(
                check_name="retrieved_documents",
                passed=False,
                error_message=f"No documents retrieved (minimum: {min_relevant})",
                details={"retrieved": retrieved_count, "minimum": min_relevant},
            )
        return CheckResult(
            check_name="retrieved_documents",
            passed=True,
            details={"retrieved": retrieved_count},
        )


class CheckSuite:
    """Run all checks against a trace."""

    def __init__(self, question_keywords_weight: float = 0.8):
        self.question_keywords_weight = question_keywords_weight
        self.checks_run = []

    def validate_trace(self, question: str, answer: Optional[str], status: str,
                      latency_ms: int, iterations: int, retrieved_count: int) -> dict:
        """Run all checks and return summary."""

        self.checks_run = []
        results = []

        # Content checks (if answer exists)
        if answer:
            results.append(AnswerValidator.check_answer_not_empty(answer))
            results.append(AnswerValidator.check_answer_length(answer))
            results.append(AnswerValidator.check_no_error_strings(answer))
            results.append(AnswerValidator.check_no_hallucination_markers(answer))
            results.append(AnswerValidator.check_answer_addresses_question(question, answer))

        # Execution checks
        results.append(ExecutionValidator.check_completion_status(status))
        results.append(ExecutionValidator.check_reasonable_latency(latency_ms))
        results.append(ExecutionValidator.check_reasonable_iterations(iterations))

        # Retrieval check (only if documents were supposedly searched)
        if retrieved_count > 0:
            results.append(ExecutionValidator.check_retrieved_documents(retrieved_count))

        self.checks_run = results

        # Summarize
        passed = sum(1 for r in results if r.passed)
        total = len(results)

        return {
            "total_checks": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": passed / total if total > 0 else 0.0,
            "results": [r.to_dict() for r in results],
        }
