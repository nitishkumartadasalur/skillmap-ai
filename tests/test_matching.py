import unittest

from tests import conftest  # noqa: F401
from skillmap.extraction import JobSkill
from skillmap.matching import blend, preprocess, skill_coverage, tfidf_similarity

RESUME = "Python developer with Django, PostgreSQL and Docker experience building REST APIs."


class TfidfTests(unittest.TestCase):
    def test_similar_job_scores_higher(self):
        close = "We need a Python developer to build REST APIs with Django and PostgreSQL."
        far = "Seeking a pastry chef to bake sourdough bread and croissants every morning."
        result = tfidf_similarity(RESUME, [close, far])
        self.assertGreater(result.similarities[0], result.similarities[1])
        self.assertAlmostEqual(result.similarities[1], 0.0, places=6)

    def test_scores_are_between_zero_and_one(self):
        for sim in tfidf_similarity(RESUME, [RESUME, "Python Django"]).similarities:
            self.assertGreaterEqual(sim, 0.0)
            self.assertLessEqual(sim, 1.0)

    def test_identical_text_is_near_one(self):
        self.assertGreater(tfidf_similarity(RESUME, [RESUME]).similarities[0], 0.99)

    def test_degenerate_inputs_do_not_crash(self):
        self.assertEqual(tfidf_similarity("", ["python"]).similarities, [0.0])
        self.assertEqual(tfidf_similarity("the and of", ["the and of"]).similarities, [0.0])
        self.assertEqual(tfidf_similarity("python", ["", "   "]).similarities, [0.0, 0.0])

    def test_symbol_skills_survive_preprocessing(self):
        text = preprocess("C++ and C# on .NET with CI/CD, Node.js and scikit-learn")
        for token in ("cpp", "csharp", "dotnet", "cicd", "nodejs", "scikitlearn"):
            self.assertIn(token, text.split())

    def test_one_similarity_per_job(self):
        self.assertEqual(len(tfidf_similarity(RESUME, ["a python job", "b java job", "c go job"]).similarities), 3)


class CoverageTests(unittest.TestCase):
    JOB = {
        "Python": JobSkill("required", 2),
        "Docker": JobSkill("required", 1),
        "Terraform": JobSkill("preferred", 1),
        "Kafka": JobSkill("preferred", 1),
    }

    def test_weighted_coverage(self):
        result = skill_coverage({"Python": 3, "Terraform": 1}, self.JOB)
        # got = 1.0 + 0.5, total = 1 + 1 + 0.5 + 0.5
        self.assertAlmostEqual(result.coverage, 1.5 / 3.0)
        self.assertEqual(result.matched, ["Python", "Terraform"])
        self.assertEqual(result.missing_required, ["Docker"])
        self.assertEqual(result.missing_preferred, ["Kafka"])

    def test_full_and_zero_coverage(self):
        self.assertEqual(skill_coverage({s: 1 for s in self.JOB}, self.JOB).coverage, 1.0)
        self.assertEqual(skill_coverage({}, self.JOB).coverage, 0.0)

    def test_no_job_skills_gives_none(self):
        self.assertIsNone(skill_coverage({"Python": 1}, {}).coverage)


class BlendTests(unittest.TestCase):
    def test_weights(self):
        self.assertAlmostEqual(blend(0.2, 0.8, 0.0), 0.2)
        self.assertAlmostEqual(blend(0.2, 0.8, 1.0), 0.8)
        self.assertAlmostEqual(blend(0.2, 0.8, 0.5), 0.5)

    def test_falls_back_to_text_similarity(self):
        self.assertEqual(blend(0.3, None, 0.9), 0.3)

    def test_weight_is_clamped(self):
        self.assertAlmostEqual(blend(0.2, 0.8, 5), 0.8)
        self.assertAlmostEqual(blend(0.2, 0.8, -1), 0.2)


if __name__ == "__main__":
    unittest.main()
