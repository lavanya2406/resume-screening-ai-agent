import sys
from pathlib import Path
# Add parent directory to path to allow direct imports
sys.path.append(str(Path(__file__).parent.parent))

import unittest
from similarity import calculate_jaccard_similarity, calculate_skill_overlap

class TestSimilarity(unittest.TestCase):
    def test_calculate_jaccard_similarity(self) -> None:
        set_a = {"python", "ml"}
        set_b = {"python", "ml", "sql"}
        score = calculate_jaccard_similarity(set_a, set_b)
        self.assertAlmostEqual(score, 2/3)

    def test_calculate_skill_overlap(self) -> None:
        cand = ["Python", "Machine Learning", "FastAPI"]
        req = ["Python", "Machine Learning", "SQL"]
        score = calculate_skill_overlap(cand, req)
        self.assertAlmostEqual(score, 2/3)

if __name__ == "__main__":
    unittest.main()
