import reflex as rx

import unittest

from app.states.notes_state import (
    decode_notes,
    filter_notes,
    remove_note,
    serialize_notes,
    upsert_note,
)


class NotesOperationsTests(unittest.TestCase):
    def test_create_and_round_trip(self):
        notes, note = upsert_note(
            [], "", " A thought ", "Hello नमस्ते", "Ideas", False
        )
        self.assertEqual(note["title"], "A thought")
        self.assertTrue(note["id"])
        self.assertEqual(decode_notes(serialize_notes(notes)), notes)

    def test_edit_retains_identity_and_creation(self):
        notes, first = upsert_note([], "", "First", "Text", "Personal", False)
        updated, second = upsert_note(
            notes, first["id"], "Second", "New text", "Work", True
        )
        self.assertEqual(len(updated), 1)
        self.assertEqual(first["created_at"], second["created_at"])
        self.assertEqual(first["id"], second["id"])
        self.assertTrue(second["favorite"])

    def test_empty_validation_and_untitled(self):
        with self.assertRaises(ValueError):
            upsert_note([], "", " ", " ", "Personal", False)
        _, note = upsert_note([], "", "", "Something", "Personal", False)
        self.assertEqual(note["title"], "Untitled note")
        with self.assertRaises(ValueError):
            upsert_note([], "missing", "Title", "Text", "Personal", False)

    def test_filter_and_sort(self):
        notes, a = upsert_note([], "", "Zebra", "Meeting notes", "Work", True)
        notes, b = upsert_note(notes, "", "Apple", "An idea", "Ideas", False)
        self.assertEqual(
            filter_notes(notes, "MEETING", "Work", True, "Recently updated"),
            [a],
        )
        self.assertEqual(
            filter_notes(notes, "", "All notes", False, "Title A–Z"), [b, a]
        )
        self.assertEqual(
            filter_notes(
                notes, "no match", "All notes", False, "Recently updated"
            ),
            [],
        )

    def test_delete_and_invalid_storage(self):
        notes, note = upsert_note([], "", "Title", "Text", "Personal", False)
        self.assertEqual(remove_note(notes, note["id"]), [])
        for raw in ("{}", "[{}]", "not json", serialize_notes([note, note])):
            with self.assertRaises(ValueError):
                decode_notes(raw)

    def test_size_limit(self):
        _, note = upsert_note([], "", "Title", "x" * 100000, "Work", False)
        with self.assertRaises(ValueError):
            serialize_notes([note] * 40)

    def test_reflex_storage_type(self):
        self.assertIsInstance(rx.LocalStorage("[]"), str)


if __name__ == "__main__":
    unittest.main()
