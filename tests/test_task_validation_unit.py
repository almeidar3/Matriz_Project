import unittest

from tasks import validate_task_payload


class TaskPayloadValidationTests(unittest.TestCase):
    def test_accepts_minimum_and_maximum_title_lengths(self):
        for title in ("a" * 3, "a" * 150):
            with self.subTest(length=len(title)):
                payload, error = validate_task_payload({"title": title})
                self.assertIsNone(error)
                self.assertEqual(payload["title"], title)

    def test_rejects_empty_short_long_and_non_string_titles(self):
        invalid_titles = ("", "   ", "ab", "a" * 151, None)
        for title in invalid_titles:
            with self.subTest(title=repr(title)):
                payload, error = validate_task_payload({"title": title})
                self.assertIsNone(payload)
                self.assertEqual(error[0], "validation_error")
                self.assertEqual(error[2], 422)

    def test_accepts_description_at_maximum_length(self):
        description = "d" * 2000
        payload, error = validate_task_payload({"title": "Tarefa", "description": description})
        self.assertIsNone(error)
        self.assertEqual(len(payload["description"]), 2000)

    def test_rejects_description_over_maximum_length(self):
        payload, error = validate_task_payload({"title": "Tarefa", "description": "d" * 2001})
        self.assertIsNone(payload)
        self.assertEqual(error[0], "validation_error")
        self.assertEqual(error[2], 422)

    def test_accepts_supported_statuses_priorities_and_iso_date(self):
        for status in ("TODO", "IN_PROGRESS", "DONE"):
            for priority in ("LOW", "MEDIUM", "HIGH"):
                with self.subTest(status=status, priority=priority):
                    payload, error = validate_task_payload({
                        "title": "Tarefa",
                        "status": status,
                        "priority": priority,
                        "dueDate": "2026-11-11",
                    })
                    self.assertIsNone(error)
                    self.assertEqual(payload["status"], status)
                    self.assertEqual(payload["priority"], priority)
                    self.assertEqual(payload["due_date"], "2026-11-11")

    def test_rejects_invalid_status_priority_and_date(self):
        invalid_payloads = (
            {"title": "Tarefa", "status": "BLOCKED"},
            {"title": "Tarefa", "priority": "URGENT"},
            {"title": "Tarefa", "dueDate": "2026-02-30"},
        )
        for values in invalid_payloads:
            with self.subTest(values=values):
                payload, error = validate_task_payload(values)
                self.assertIsNone(payload)
                self.assertEqual(error[0], "validation_error")
                self.assertEqual(error[2], 422)

    def test_rejects_missing_title_unknown_fields_and_non_object_body(self):
        invalid_payloads = (None, [], {}, {"title": "Tarefa", "ownerId": 1})
        for values in invalid_payloads:
            with self.subTest(values=values):
                payload, error = validate_task_payload(values)
                self.assertIsNone(payload)
                self.assertIsNotNone(error)


if __name__ == "__main__":
    unittest.main()