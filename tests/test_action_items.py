"""
Test Suite for Action Item Extraction Engine (Milestone 2 Task 3)
Tests extraction pipeline, attribute validation (assignee, deadline, priority, status),
filtering, sorting, metrics, and export formats.
"""

import sys
import json
from pathlib import Path
from unittest.mock import Mock

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.action_item_extractor import ActionItemExtractor, ExtractedActionItem
from src.llm.exceptions import InputValidationError


class TestExtractedActionItem:
    """Test ExtractedActionItem dataclass."""

    def test_default_values(self):
        """Test default priority and status."""
        item = ExtractedActionItem(action="Refactor auth module")
        assert item.priority == "Medium"
        assert item.status == "Pending"
        assert item.assignee_display == "Unassigned"
        assert item.deadline_display == "No deadline"
        print("✅ TEST 1 - Action item default values: PASSED")

    def test_custom_values(self):
        """Test custom attribute assignment."""
        item = ExtractedActionItem(
            action="Deploy release v2",
            owner="Ravi",
            deadline="Friday",
            priority="High",
            status="In Progress"
        )
        assert item.owner == "Ravi"
        assert item.deadline == "Friday"
        assert item.priority == "High"
        assert item.status == "In Progress"
        assert item.assignee_display == "Ravi"
        assert item.deadline_display == "Friday"
        print("✅ TEST 2 - Action item custom attributes: PASSED")


class TestActionItemExtractionPipeline:
    """Test extraction pipeline with mock LLM."""

    def setup_method(self):
        self.mock_llm = Mock()
        self.extractor = ActionItemExtractor(llm_service=self.mock_llm)

    def test_extract_action_items_success(self):
        """Test extraction of tasks with all required attributes."""
        mock_response = json.dumps({
            "action_items": [
                {
                    "action": "Complete API integration",
                    "owner": "Ravi",
                    "deadline": "Friday",
                    "priority": "High",
                    "status": "Pending"
                },
                {
                    "action": "Prepare UI testing report",
                    "owner": "Priya",
                    "deadline": "Next Monday",
                    "priority": "Medium",
                    "status": "In Progress"
                },
                {
                    "action": "Update documentation",
                    "owner": None,
                    "deadline": None,
                    "priority": "Low",
                    "status": "Pending"
                }
            ]
        })
        self.mock_llm._call_llm_with_retry.return_value = mock_response

        transcript = "Meeting transcript: Ravi will complete API integration by Friday. Priya is working on UI testing report due next Monday. Documentation needs updating."
        items = self.extractor.extract_action_items(transcript)

        assert len(items) == 3
        
        # Verify Item 1 (Assigned participant, deadline, priority, status)
        assert items[0].action == "Complete API integration"
        assert items[0].owner == "Ravi"
        assert items[0].deadline == "Friday"
        assert items[0].priority == "High"
        assert items[0].status == "Pending"

        # Verify Item 2
        assert items[1].action == "Prepare UI testing report"
        assert items[1].owner == "Priya"
        assert items[1].deadline == "Next Monday"
        assert items[1].priority == "Medium"
        assert items[1].status == "In Progress"

        # Verify Item 3 (unassigned)
        assert items[2].action == "Update documentation"
        assert items[2].owner is None
        assert items[2].priority == "Low"
        print("✅ TEST 3 - Pipeline extraction & attributes verification: PASSED")

    def test_extract_empty_transcript_validation(self):
        """Test input validation for empty transcript."""
        try:
            self.extractor.extract_action_items("")
            assert False, "Should have raised InputValidationError"
        except InputValidationError:
            print("✅ TEST 4 - Empty transcript rejection: PASSED")


class TestFilteringAndSorting:
    """Test filtering and sorting engine."""

    def setup_method(self):
        self.extractor = ActionItemExtractor(llm_service=Mock())
        self.items = [
            ExtractedActionItem(action="Task A", owner="Ravi", deadline="Friday", priority="High", status="Pending"),
            ExtractedActionItem(action="Task B", owner="Priya", deadline="Monday", priority="Medium", status="In Progress"),
            ExtractedActionItem(action="Task C", owner="Ravi", deadline="Wednesday", priority="Low", status="Completed"),
            ExtractedActionItem(action="Task D", owner=None, deadline=None, priority="High", status="Pending"),
        ]

    def test_filter_by_assignee(self):
        """Test filtering by participant."""
        ravi_tasks = self.extractor.filter_items(self.items, assignee="Ravi")
        assert len(ravi_tasks) == 2
        assert all(i.owner == "Ravi" for i in ravi_tasks)

        unassigned = self.extractor.filter_items(self.items, assignee="Unassigned")
        assert len(unassigned) == 1
        assert unassigned[0].action == "Task D"
        print("✅ TEST 5 - Filter by assignee: PASSED")

    def test_filter_by_priority_and_status(self):
        """Test filtering by priority and status."""
        high_tasks = self.extractor.filter_items(self.items, priority="High")
        assert len(high_tasks) == 2

        completed_tasks = self.extractor.filter_items(self.items, status="Completed")
        assert len(completed_tasks) == 1
        assert completed_tasks[0].action == "Task C"
        print("✅ TEST 6 - Filter by priority and status: PASSED")

    def test_filter_by_search_query(self):
        """Test text search filtering."""
        result = self.extractor.filter_items(self.items, search_query="Task B")
        assert len(result) == 1
        assert result[0].owner == "Priya"
        print("✅ TEST 7 - Filter by search query: PASSED")

    def test_sort_by_priority(self):
        """Test sorting by priority (High -> Medium -> Low)."""
        sorted_items = self.extractor.sort_items(self.items, sort_by="priority")
        assert sorted_items[0].priority == "High"
        assert sorted_items[-1].priority == "Low"
        print("✅ TEST 8 - Sort by priority: PASSED")

    def test_sort_by_assignee(self):
        """Test sorting alphabetically by assignee."""
        sorted_items = self.extractor.sort_items(self.items, sort_by="assignee")
        assert sorted_items[0].assignee_display == "Priya"
        print("✅ TEST 9 - Sort by assignee: PASSED")


class TestMetricsAndExports:
    """Test metrics calculations and export functions."""

    def setup_method(self):
        self.extractor = ActionItemExtractor(llm_service=Mock())
        self.items = [
            ExtractedActionItem(action="Task 1", owner="Ravi", deadline="Friday", priority="High", status="Pending"),
            ExtractedActionItem(action="Task 2", owner="Priya", deadline="Monday", priority="Medium", status="In Progress"),
            ExtractedActionItem(action="Task 3", owner=None, deadline=None, priority="Low", status="Completed"),
        ]

    def test_metrics(self):
        """Test summary metrics calculation."""
        metrics = self.extractor.get_metrics(self.items)
        assert metrics["total"] == 3
        assert metrics["high_priority"] == 1
        assert metrics["pending"] == 1
        assert metrics["in_progress"] == 1
        assert metrics["completed"] == 1
        assert metrics["assigned"] == 2
        assert metrics["unassigned"] == 1
        print("✅ TEST 10 - Metrics calculation: PASSED")

    def test_markdown_table_export(self):
        """Test markdown table generation."""
        md = self.extractor.to_markdown_table(self.items)
        assert "| # | Task / Action | Assigned Participant | Deadline | Priority | Status |" in md
        assert "Task 1" in md
        assert "Ravi" in md
        assert "High" in md
        print("✅ TEST 11 - Markdown table export: PASSED")

    def test_csv_export(self):
        """Test CSV export."""
        csv_out = self.extractor.to_csv(self.items)
        assert "ID,Task,Assigned Participant,Deadline,Priority,Status,Created At" in csv_out
        assert "Task 1,Ravi,Friday,High,Pending" in csv_out
        print("✅ TEST 12 - CSV export: PASSED")

    def test_json_export(self):
        """Test JSON export."""
        json_out = self.extractor.to_json(self.items)
        parsed = json.loads(json_out)
        assert len(parsed) == 3
        assert parsed[0]["action"] == "Task 1"
        assert parsed[0]["priority"] == "High"
        print("✅ TEST 13 - JSON export: PASSED")


def run_all_tests():
    """Run all action item extraction tests."""
    print("=" * 60)
    print("Running Action Item Extraction Tests (Milestone 2 Task 3)")
    print("=" * 60)
    print()

    t1 = TestExtractedActionItem()
    t1.test_default_values()
    t1.test_custom_values()
    print()

    t2 = TestActionItemExtractionPipeline()
    t2.setup_method()
    t2.test_extract_action_items_success()
    t2.test_extract_empty_transcript_validation()
    print()

    t3 = TestFilteringAndSorting()
    t3.setup_method()
    t3.test_filter_by_assignee()
    t3.test_filter_by_priority_and_status()
    t3.test_filter_by_search_query()
    t3.test_sort_by_priority()
    t3.test_sort_by_assignee()
    print()

    t4 = TestMetricsAndExports()
    t4.setup_method()
    t4.test_metrics()
    t4.test_markdown_table_export()
    t4.test_csv_export()
    t4.test_json_export()
    print()

    print("=" * 60)
    print("✅ All Milestone 2 Task 3 Tests PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
