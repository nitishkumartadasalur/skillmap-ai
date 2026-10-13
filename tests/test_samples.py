import unittest

from tests import conftest  # noqa: F401
from skillmap.extraction import extract_job_skills, extract_resume_skills
from skillmap.samples import read_sample_resume, sample_job_list, sample_resume_labels


class SampleDataTests(unittest.TestCase):
    def test_sample_resumes(self):
        labels = sample_resume_labels()
        self.assertGreaterEqual(len(labels), 3)
        for label in labels:
            text = read_sample_resume(label)
            self.assertGreater(len(text.split()), 150)
            self.assertGreaterEqual(len(extract_resume_skills(text)), 10)

    def test_sample_jobs(self):
        jobs = sample_job_list()
        self.assertGreaterEqual(len(jobs), 5)
        self.assertEqual(len({title for title, _ in jobs}), len(jobs))
        for title, text in jobs:
            self.assertFalse(title.lower().startswith("title:"))
            skills = extract_job_skills(text)
            self.assertGreaterEqual(len(skills), 8, title)
            self.assertIn("preferred", {s.importance for s in skills.values()}, title)
            self.assertIn("required", {s.importance for s in skills.values()}, title)


if __name__ == "__main__":
    unittest.main()
