import unittest

from tests import conftest  # noqa: F401
from skillmap.analysis import analyze
from skillmap.samples import read_sample_resume, sample_job_list
from skillmap.suggestions import all_suggestions_df, build_job_suggestions, general_suggestions

JOBS = sample_job_list()


class HonestySuggestionTests(unittest.TestCase):
    def test_skill_gap_suggestions_are_conditional(self):
        result = analyze(read_sample_resume("Backend Engineer"), JOBS)
        top = result.matches[0]
        gap_tips = [s for s in build_job_suggestions(top, result.resume_skills) if s.area == "Skill gap"]
        self.assertTrue(gap_tips)
        for tip in gap_tips:
            text = tip.detail.lower()
            self.assertTrue(
                "only if" in text or "only where" in text or "if you have real" in text,
                f"Unconditional skill-gap advice: {tip.detail}",
            )

    def test_no_suggestion_tells_the_user_to_claim_experience(self):
        banned = ("add experience", "claim experience", "lie", "fabricate", "pretend", "list it anyway")
        for label in ("Backend Engineer", "Data Analyst", "ML Engineer"):
            resume = read_sample_resume(label)
            result = analyze(resume, JOBS)
            tips = general_suggestions(resume)
            for match in result.matches:
                tips += build_job_suggestions(match, result.resume_skills)
            for tip in tips:
                blob = f"{tip.title} {tip.detail}".lower()
                for phrase in banned:
                    self.assertNotIn(phrase, blob)

    def test_suggestions_only_mention_skills_from_the_job(self):
        result = analyze(read_sample_resume("Data Analyst"), JOBS)
        match = result.matches[0]
        for tip in build_job_suggestions(match, result.resume_skills):
            if tip.title.startswith("Required skill not found: "):
                self.assertIn(tip.title.split(": ", 1)[1], match.missing_required)

    def test_transferable_skills_are_framed_as_overlap(self):
        resume = "Python developer. Skills: Python, MySQL, Docker."
        job = "Requirements\n- Python\n- PostgreSQL\n- Kubernetes"
        result = analyze(resume, [("Backend", job)])
        details = {s.title: s.detail for s in build_job_suggestions(result.matches[0], result.resume_skills)}
        pg = details["Required skill not found: PostgreSQL"]
        self.assertIn("MySQL", pg)
        self.assertIn("rather than claiming PostgreSQL itself", pg)

    def test_priorities_are_sorted(self):
        result = analyze(read_sample_resume("Backend Engineer"), JOBS)
        order = {"High": 0, "Medium": 1, "Low": 2}
        ranks = [order[s.priority] for s in build_job_suggestions(result.matches[-1], result.resume_skills)]
        self.assertEqual(ranks, sorted(ranks))


class GeneralCheckTests(unittest.TestCase):
    def test_short_resume_without_sections(self):
        titles = {s.title for s in general_suggestions("Python developer.")}
        self.assertTrue(any(t.startswith("The resume is short") for t in titles))
        self.assertIn("No skills section found", titles)
        self.assertIn("No summary found", titles)

    def test_passive_phrasing_detected(self):
        text = "EXPERIENCE\n" + "- Responsible for reports\n- Worked on dashboards\n" * 3
        self.assertTrue(any(s.area == "Wording" for s in general_suggestions(text)))

    def test_unquantified_bullets_detected(self):
        text = "EXPERIENCE\n- Built reports\n- Wrote queries\n- Fixed bugs\n- Updated pages\n- Helped users\n"
        self.assertTrue(any(s.area == "Impact" for s in general_suggestions(text)))

    def test_quantified_bullets_not_flagged(self):
        text = "- Cut latency by 40%\n- Served 2000 users\n- Wrote 30 tests\n- Saved 5 hours weekly\n"
        self.assertFalse(any(s.area == "Impact" for s in general_suggestions(text)))


class ExportTests(unittest.TestCase):
    def test_all_suggestions_df(self):
        resume = read_sample_resume("ML Engineer")
        result = analyze(resume, JOBS)
        df = all_suggestions_df(result, resume)
        self.assertEqual(list(df.columns), ["Job", "Priority", "Area", "Suggestion", "Details"])
        self.assertTrue(set(df["Job"]) <= {"All jobs", *[m.title for m in result.matches]})
        self.assertFalse(df.empty)


if __name__ == "__main__":
    unittest.main()
