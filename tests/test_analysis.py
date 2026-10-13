import io
import unittest

import pandas as pd

from tests import conftest  # noqa: F401
from skillmap.analysis import analyze
from skillmap.samples import read_sample_resume, sample_job_list, sample_resume_labels


class AnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.jobs = sample_job_list()

    def test_each_sample_resume_ranks_its_own_role_first(self):
        expected = {
            "Backend Engineer": "Backend",
            "Data Analyst": "Data Analyst",
            "ML Engineer": "Machine Learning",
        }
        self.assertEqual(set(sample_resume_labels()), set(expected))
        for label, needle in expected.items():
            result = analyze(read_sample_resume(label), self.jobs)
            self.assertIn(needle, result.matches[0].title, label)

    def test_ranking_is_sorted_and_ranks_are_sequential(self):
        result = analyze(read_sample_resume("Backend Engineer"), self.jobs)
        scores = [m.overall for m in result.matches]
        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertEqual([m.rank for m in result.matches], list(range(1, len(self.jobs) + 1)))

    def test_skill_weight_extremes(self):
        resume = read_sample_resume("Data Analyst")
        text_only = analyze(resume, self.jobs, skill_weight=0.0)
        skills_only = analyze(resume, self.jobs, skill_weight=1.0)
        for m in text_only.matches:
            self.assertAlmostEqual(m.overall, m.text_similarity)
        for m in skills_only.matches:
            self.assertAlmostEqual(m.overall, m.skill_coverage)

    def test_matched_and_missing_are_consistent(self):
        result = analyze(read_sample_resume("Backend Engineer"), self.jobs)
        for m in result.matches:
            self.assertEqual(set(m.matched) | set(m.missing), set(m.job_skills))
            self.assertFalse(set(m.matched) & set(m.missing))
            for skill in m.matched:
                self.assertIn(skill, result.resume_skills)
            for skill in m.missing:
                self.assertNotIn(skill, result.resume_skills)

    def test_known_gaps_for_backend_resume(self):
        result = analyze(read_sample_resume("Backend Engineer"), self.jobs)
        top = result.matches[0]
        self.assertIn("Kafka", top.missing_required)
        self.assertIn("FastAPI", top.missing_required)
        self.assertIn("Kubernetes", top.missing_preferred)
        self.assertIn("Python", top.matched)

    def test_dataframes_and_csv_round_trip(self):
        result = analyze(read_sample_resume("ML Engineer"), self.jobs)
        for df in (result.summary_df(), result.gap_df(), result.resume_skills_df()):
            self.assertFalse(df.empty)
            restored = pd.read_csv(io.StringIO(df.to_csv(index=False)))
            self.assertEqual(list(restored.columns), list(df.columns))
            self.assertEqual(len(restored), len(df))
        summary = result.summary_df()
        self.assertTrue(summary["Overall match (%)"].between(0, 100).all())
        self.assertEqual(summary["Rank"].tolist(), sorted(summary["Rank"]))

    def test_skill_matrix_codes(self):
        result = analyze(read_sample_resume("Backend Engineer"), self.jobs)
        matrix = result.skill_matrix(max_rows=200)
        self.assertEqual(list(matrix.columns), [m.title for m in result.matches])
        self.assertTrue(set(matrix.to_numpy().ravel()) <= {0, 1, 2, 3})
        self.assertEqual(matrix.loc["Python", result.matches[0].title], 3)  # matched
        self.assertEqual(matrix.loc["Kafka", result.matches[0].title], 2)  # missing, required

    def test_truncated_matrix_keeps_gaps_before_matches(self):
        result = analyze(read_sample_resume("Backend Engineer"), self.jobs)
        small = result.skill_matrix(max_rows=10)
        self.assertEqual(len(small), 10)
        full = result.skill_matrix(max_rows=200)
        demand = (full != 0).sum(axis=1)
        cutoff = demand[small.index].min()
        dropped = [s for s in full.index if s not in small.index and demand[s] == cutoff]
        for skill in dropped:  # anything dropped at the cutoff demand is a match, never a gap
            self.assertIn(skill, result.resume_skills)

    def test_category_and_top_missing_tables(self):
        result = analyze(read_sample_resume("Backend Engineer"), self.jobs)
        cats = result.category_df(result.matches[0])
        self.assertTrue(cats["Coverage (%)"].between(0, 100).all())
        top = result.top_missing_df()
        self.assertEqual(top["Jobs missing in"].tolist(), sorted(top["Jobs missing in"], reverse=True))

    def test_duplicate_titles_are_made_unique(self):
        jd = "Python developer building REST APIs with Django and Docker."
        result = analyze("Python Django developer", [("Dev", jd), ("Dev", jd)])
        self.assertEqual(len({m.title for m in result.matches}), 2)

    def test_job_without_known_skills_uses_text_similarity(self):
        result = analyze("Python developer", [("Poet", "We seek a poet who writes sonnets about the sea at dawn.")])
        match = result.matches[0]
        self.assertIsNone(match.skill_coverage)
        self.assertAlmostEqual(match.overall, match.text_similarity)
        self.assertIn(None, [None if pd.isna(v) else v for v in result.summary_df()["Skill coverage (%)"]])

    def test_invalid_input(self):
        with self.assertRaises(ValueError):
            analyze("", self.jobs)
        with self.assertRaises(ValueError):
            analyze("Python developer", [])
        with self.assertRaises(ValueError):
            analyze("Python developer", [("Blank", "   ")])


if __name__ == "__main__":
    unittest.main()
