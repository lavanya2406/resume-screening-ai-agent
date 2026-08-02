import sys
from pathlib import Path
# Add parent directory to path to allow direct imports
sys.path.append(str(Path(__file__).parent.parent))

import unittest
from extractor import extract_name, extract_email, extract_phone, extract_skills, extract_experience_years

class TestExtractor(unittest.TestCase):
    def test_extract_name(self) -> None:
        self.assertEqual(extract_name("Name: Alice Johnson\nDeveloper"), "Alice Johnson")
        self.assertEqual(extract_name("Alice Johnson\nDeveloper"), "Alice Johnson")

    def test_extract_email(self) -> None:
        self.assertEqual(extract_email("Contact at alice@example.com now"), "alice@example.com")
        self.assertEqual(extract_email("No email here"), "")

    def test_extract_phone(self) -> None:
        self.assertEqual(extract_phone("Call 555-123-4567"), "555-123-4567")

    def test_extract_experience_years(self) -> None:
        self.assertEqual(extract_experience_years("Wrote Python for 3.5 years of experience"), 3.5)
        self.assertEqual(extract_experience_years("No years here"), 0.0)

    def test_extract_skills(self) -> None:
        text = "Experienced in Python programming and TensorFlow frameworks."
        skills = extract_skills(text)
        self.assertIn("Python", skills["programming"])
        self.assertIn("TensorFlow", skills["ai"])

if __name__ == "__main__":
    unittest.main()
