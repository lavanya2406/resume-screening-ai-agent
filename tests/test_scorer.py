import sys
from pathlib import Path
# Add parent directory to path to allow direct imports
sys.path.append(str(Path(__file__).parent.parent))

import unittest
from scorer import score_experience, score_education

class TestScorer(unittest.TestCase):
    def test_score_experience(self) -> None:
        # Candidate 5 years, required 3 years -> capped at 1.2 ratio, score is 1.0
        self.assertEqual(score_experience(5.0, 3.0), 1.0)
        # Candidate 1.8 years, required 3.0 years -> 1.8/3.0 = 0.6 -> 0.6 / 1.2 = 0.5
        self.assertAlmostEqual(score_experience(1.8, 3.0), 0.5)

    def test_score_education(self) -> None:
        candidate_edu = [{"details": "Master of Science in Computer Science"}]
        self.assertEqual(score_education(candidate_edu, "Master's Degree"), 1.0)
        self.assertEqual(score_education(candidate_edu, "Bachelor's Degree"), 1.0)

if __name__ == "__main__":
    unittest.main()
