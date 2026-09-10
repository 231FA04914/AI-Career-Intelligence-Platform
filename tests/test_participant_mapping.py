"""
Test Suite for Task 4: Participant & Responsibility Mapping
Verifies:
- Participant names are correctly identified
- Names are mapped consistently
- Multiple participants are handled
- Unknown participants are handled safely
- Duplicate participant records are avoided
- Responsibilities are linked to the correct meeting
"""

import sys
from pathlib import Path
from unittest.mock import Mock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.participant_mapper import ParticipantMapper, Participant


class TestParticipantMappingTask4:
    """Test suite verifying all Task 4 requirements."""

    def setup_method(self):
        self.mock_llm = Mock()
        self.mapper = ParticipantMapper(llm_service=self.mock_llm)

    def test_participant_names_identified_and_multiple_participants(self):
        """Verify: Participant names are correctly identified and multiple participants are handled."""
        self.mock_llm.process_transcript.return_value = {
            "participants": ["Ravi", "Priya", "Amit"],
            "action_items": [
                {"action": "Complete API integration", "owner": "Ravi", "deadline": "Friday", "priority": "High"},
                {"action": "Prepare UI testing report", "owner": "Priya", "deadline": "Monday", "priority": "Medium"},
                {"action": "Review system architecture", "owner": "Amit", "deadline": None, "priority": "Low"}
            ]
        }

        transcript = "Team meeting with Ravi, Priya, and Amit. Tasks were assigned to each."
        participants = self.mapper.map_responsibilities(transcript, meeting_id="meeting_2026_09")

        assert len(participants) == 3
        names = [p.canonical_name for p in participants]
        assert "Ravi" in names
        assert "Priya" in names
        assert "Amit" in names
        print("✅ VERIFICATION 1 - Participant names correctly identified & multiple participants handled: PASSED")

    def test_names_mapped_consistently(self):
        """Verify: Names are mapped consistently (title stripping, casing, trim)."""
        assert self.mapper.normalize_name("mr. ravi kumar") == "Ravi Kumar"
        assert self.mapper.normalize_name("Dr. Priya") == "Priya"
        assert self.mapper.normalize_name("   amit   ") == "Amit"
        assert self.mapper.normalize_name("MS. ANITA") == "Anita"
        print("✅ VERIFICATION 2 - Names mapped consistently: PASSED")

    def test_unknown_participants_handled_safely(self):
        """Verify: Unknown participants are handled safely without errors."""
        assert self.mapper.normalize_name(None) == "Unassigned"
        assert self.mapper.normalize_name("") == "Unassigned"
        assert self.mapper.normalize_name("null") == "Unassigned"
        assert self.mapper.normalize_name("unknown") == "Unassigned"
        assert self.mapper.normalize_name("N/A") == "Unassigned"

        # Test in pipeline
        self.mock_llm.process_transcript.return_value = {
            "participants": ["Ravi"],
            "action_items": [
                {"action": "Generic cleanup task", "owner": None, "deadline": None, "priority": "Low"}
            ]
        }

        participants = self.mapper.map_responsibilities("Some meeting transcript", meeting_id="meeting_safe")
        unassigned = [p for p in participants if not p.is_known]
        assert len(unassigned) == 1
        assert unassigned[0].canonical_name == "Unassigned"
        assert len(unassigned[0].responsibilities) == 1
        print("✅ VERIFICATION 3 - Unknown participants handled safely: PASSED")

    def test_duplicate_participant_records_avoided(self):
        """Verify: Duplicate participant records are avoided and responsibilities merged."""
        raw_list = [
            Participant(name="Ravi", canonical_name="Ravi", responsibilities=[{"action": "Task 1"}]),
            Participant(name="mr. ravi", canonical_name="Ravi", responsibilities=[{"action": "Task 2"}]),
            Participant(name="Priya", canonical_name="Priya", responsibilities=[{"action": "Task 3"}]),
            Participant(name="Ravi", canonical_name="Ravi", responsibilities=[{"action": "Task 1"}])  # duplicate task
        ]

        deduped = self.mapper.deduplicate_participants(raw_list)
        assert len(deduped) == 2  # Only Ravi and Priya

        ravi = next(p for p in deduped if p.canonical_name == "Ravi")
        assert len(ravi.responsibilities) == 2  # Task 1 and Task 2 merged without duplicates
        print("✅ VERIFICATION 4 - Duplicate participant records avoided & merged: PASSED")

    def test_responsibilities_linked_to_correct_meeting(self):
        """Verify: Responsibilities are linked to the correct meeting."""
        self.mock_llm.process_transcript.return_value = {
            "participants": ["Ravi", "Priya"],
            "action_items": [
                {"action": "API Integration", "owner": "Ravi", "deadline": "Friday", "priority": "High"},
                {"action": "UI Testing", "owner": "Priya", "deadline": "Friday", "priority": "High"}
            ]
        }

        meeting_id = "sprint_planning_2026_q3"
        participants = self.mapper.map_responsibilities("Meeting transcript...", meeting_id=meeting_id)

        for p in participants:
            assert p.meeting_id == meeting_id
            for r in p.responsibilities:
                assert r["meeting_id"] == meeting_id

        # Verify Markdown Matrix formatting
        md_matrix = self.mapper.to_matrix_markdown(participants)
        assert meeting_id in md_matrix
        assert "API Integration" in md_matrix
        assert "UI Testing" in md_matrix
        print("✅ VERIFICATION 5 - Responsibilities linked to correct meeting: PASSED")


def run_all_tests():
    """Run Task 4 verification tests."""
    print("=" * 65)
    print("Running Task 4: Participant & Responsibility Mapping Verification")
    print("=" * 65)
    print()

    tester = TestParticipantMappingTask4()
    tester.setup_method()
    tester.test_participant_names_identified_and_multiple_participants()
    tester.test_names_mapped_consistently()
    tester.test_unknown_participants_handled_safely()
    tester.test_duplicate_participant_records_avoided()
    tester.test_responsibilities_linked_to_correct_meeting()

    print()
    print("=" * 65)
    print("✅ All Task 4 Requirements Verified & PASSED!")
    print("=" * 65)


if __name__ == "__main__":
    run_all_tests()
