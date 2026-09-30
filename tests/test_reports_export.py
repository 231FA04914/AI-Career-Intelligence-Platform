"""
Reports & Export Unit & Integration Tests (Milestone 4 - Task 6)
Validates PDF and CSV report generation, content correctness, and structure.
"""

import csv
import io
import pytest
from src.reports.exporter import generate_meeting_pdf, generate_meeting_csv, MeetingReportExporter


@pytest.fixture
def sample_meeting_data():
    return {
        "id": "meet_test_99",
        "title": "Quarterly Product & Engineering Review",
        "created_at": "2026-09-21T14:30:00",
        "duration": 2700.0,
        "original_filename": "q3_review.mp4",
        "summary": "The executive committee reviewed Q3 deliverables and approved the mobile architecture roadmap.",
        "decisions": [
            "Adopt FastAPI backend architecture across all microservices.",
            "Deploy dense vector embeddings for meeting search."
        ],
        "action_items": [
            {
                "action": "Complete REST API endpoints",
                "owner": "Ravi",
                "deadline": "2026-09-28",
                "priority": "High",
                "status": "In Progress"
            },
            {
                "action": "Run end-to-end regression tests",
                "owner": "Elena",
                "deadline": "2026-09-30",
                "priority": "Medium",
                "status": "Pending"
            }
        ],
        "participants": [
            {"name": "Ravi Kumar", "canonical_name": "Ravi Kumar", "role": "Backend Lead"},
            {"name": "Elena Rostova", "canonical_name": "Elena Rostova", "role": "QA Architect"}
        ]
    }


def test_generate_meeting_csv(sample_meeting_data):
    """Verify CSV export contains all metadata, decisions, actions, and participants."""
    csv_text = generate_meeting_csv(sample_meeting_data)
    assert csv_text is not None
    assert len(csv_text) > 100

    # Validate CSV parseability
    reader = list(csv.reader(io.StringIO(csv_text)))
    flat_cells = [cell for row in reader for cell in row]

    assert "meet_test_99" in flat_cells
    assert "Quarterly Product & Engineering Review" in flat_cells
    assert "Adopt FastAPI backend architecture across all microservices." in flat_cells
    assert "Complete REST API endpoints" in flat_cells
    assert "Ravi" in flat_cells
    assert "Elena Rostova" in flat_cells


def test_generate_meeting_pdf(sample_meeting_data):
    """Verify PDF export produces valid, non-empty binary PDF stream."""
    pdf_bytes = generate_meeting_pdf(sample_meeting_data)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 500
    assert pdf_bytes.startswith(b"%PDF")


def test_report_exporter_wrapper(sample_meeting_data):
    """Verify MeetingReportExporter class interface."""
    pdf = MeetingReportExporter.export_pdf(sample_meeting_data)
    assert isinstance(pdf, bytes) and len(pdf) > 500

    csv_data = MeetingReportExporter.export_csv(sample_meeting_data)
    assert isinstance(csv_data, str) and "meet_test_99" in csv_data
