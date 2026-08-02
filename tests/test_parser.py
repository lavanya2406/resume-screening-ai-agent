import sys
from pathlib import Path
# Add parent directory to path to allow direct imports
sys.path.append(str(Path(__file__).parent.parent))

import unittest
from tempfile import TemporaryDirectory
from parser import clean_whitespace, load_resume

class TestParser(unittest.TestCase):
    def test_clean_whitespace(self) -> None:
        raw_text = "  Hello   \xa0  World! \n\n\n\nTest.  "
        cleaned = clean_whitespace(raw_text)
        self.assertEqual(cleaned, "Hello World!\n\nTest.")

    def test_load_resume_txt(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "resume.txt"
            content = "John Doe\nEmail: john@example.com"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            loaded = load_resume(file_path)
            self.assertEqual(loaded, content)
            
    def test_load_resume_nonexistent(self) -> None:
        loaded = load_resume("nonexistent_file.pdf")
        self.assertEqual(loaded, "")

if __name__ == "__main__":
    unittest.main()
