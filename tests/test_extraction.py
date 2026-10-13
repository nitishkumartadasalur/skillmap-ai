import unittest

from tests import conftest  # noqa: F401  (adds project root to sys.path)
from skillmap.extraction import extract_job_skills, extract_resume_skills


class ResumeSkillTests(unittest.TestCase):
    def test_java_is_not_javascript(self):
        self.assertEqual(set(extract_resume_skills("I write JavaScript daily")), {"JavaScript"})
        self.assertEqual(set(extract_resume_skills("Java and JavaScript")), {"Java", "JavaScript"})

    def test_sql_is_not_matched_inside_other_names(self):
        self.assertEqual(set(extract_resume_skills("MySQL")), {"MySQL"})
        self.assertEqual(set(extract_resume_skills("NoSQL")), {"NoSQL"})
        self.assertIn("SQL", extract_resume_skills("SQL/NoSQL"))

    def test_symbols_in_names(self):
        skills = extract_resume_skills("C++, C#, Node.js and CI/CD with scikit-learn on .NET")
        for expected in ("C++", "C#", "Node.js", "CI/CD", "scikit-learn", ".NET"):
            self.assertIn(expected, skills)

    def test_asp_net_is_not_also_dotnet(self):
        skills = extract_resume_skills("Built apps with ASP.NET")
        self.assertIn("ASP.NET", skills)
        self.assertNotIn(".NET", skills)

    def test_ambiguous_words_need_context(self):
        self.assertEqual(extract_resume_skills("We go to market. R&D team. Excel at teamwork."), {})
        skills = extract_resume_skills("Languages: Python, R, Go, C")
        for expected in ("Python", "R", "Go", "C"):
            self.assertIn(expected, skills)

    def test_excel_as_a_tool(self):
        self.assertIn("Excel", extract_resume_skills("Tools: Tableau, Excel, SQL"))

    def test_react_native_is_not_react(self):
        skills = extract_resume_skills("Shipped a React Native app")
        self.assertIn("React Native", skills)
        self.assertNotIn("React", skills)

    def test_case_and_spacing_variants(self):
        skills = extract_resume_skills("MACHINE-LEARNING, postgres, K8S")
        for expected in ("Machine Learning", "PostgreSQL", "Kubernetes"):
            self.assertIn(expected, skills)

    def test_ml_abbreviation_only_in_capitals(self):
        self.assertIn("Machine Learning", extract_resume_skills("ML models in production"))
        self.assertNotIn("Machine Learning", extract_resume_skills("Dose: 5 ml daily"))

    def test_mention_counts(self):
        self.assertEqual(extract_resume_skills("Python, python and PYTHON")["Python"], 3)

    def test_empty_text(self):
        self.assertEqual(extract_resume_skills(""), {})


class JobSkillTests(unittest.TestCase):
    JD = """Requirements
- Python and PostgreSQL
Nice to have
Kubernetes
- Terraform
Responsibilities
Build APIs with FastAPI. Experience with Kafka is a plus.
"""

    def test_required_vs_preferred(self):
        skills = {k: v.importance for k, v in extract_job_skills(self.JD).items()}
        self.assertEqual(skills["Python"], "required")
        self.assertEqual(skills["PostgreSQL"], "required")
        self.assertEqual(skills["FastAPI"], "required")  # after the "Responsibilities" header
        self.assertEqual(skills["Kubernetes"], "preferred")
        self.assertEqual(skills["Terraform"], "preferred")
        self.assertEqual(skills["Kafka"], "preferred")  # sentence-level "is a plus"

    def test_required_sorted_first(self):
        order = [v.importance for v in extract_job_skills(self.JD).values()]
        self.assertEqual(order, sorted(order, key=lambda i: i != "required"))

    def test_no_skills(self):
        self.assertEqual(extract_job_skills("We value kindness and curiosity."), {})


if __name__ == "__main__":
    unittest.main()
