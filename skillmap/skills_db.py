"""Skill taxonomy: category -> canonical skill -> aliases.

Each entry is written as ``"Canonical|alias one|alias two"``. The canonical
name is added as an alias automatically, except for the names listed in
``CONTEXT_SKILLS`` (``Go``, ``R``, ``C``...), which are too ambiguous as plain
words and are matched with context-aware, case-sensitive rules instead
(see ``extraction.py``).
"""

from __future__ import annotations

_RAW: dict[str, list[str]] = {
    "Programming Languages": [
        "Python|python3|python 3",
        "Java",
        "JavaScript|ecmascript|es6",
        "TypeScript",
        "C++|cpp",
        "C#|csharp|c sharp",
        "Go|golang",
        "R|r programming|r language|rstudio",
        "C|c programming|c language",
        "Rust",
        "Kotlin",
        "Swift|swiftui",
        "PHP",
        "Ruby",
        "Scala",
        "Dart",
        "MATLAB",
        "Perl",
        "Bash|shell scripting|bash scripting",
    ],
    "Frontend & Mobile": [
        "React|react.js|reactjs|react js",
        "React Native",
        "Angular|angularjs",
        "Vue.js|vue|vuejs|vue js",
        "Next.js|nextjs|next js",
        "Svelte",
        "Redux",
        "HTML|html5",
        "CSS|css3",
        "Sass|scss",
        "Tailwind CSS|tailwind",
        "Webpack|vite",
        "Responsive Design|responsive web design",
        "Accessibility|wcag|a11y|web accessibility",
        "Flutter",
        "Android",
        "iOS",
    ],
    "Backend & APIs": [
        "Node.js|nodejs|node js",
        "Express.js|expressjs",
        "NestJS|nest.js",
        "FastAPI|fast api",
        "Django|django rest framework|drf",
        "Flask",
        "Spring Boot|springboot|spring framework|spring mvc",
        "ASP.NET|asp.net core|asp.net mvc",
        ".NET|dotnet|.net core|.net framework",
        "Ruby on Rails",
        "Laravel",
        "REST APIs|rest api|rest apis|restful|restful api|restful apis",
        "GraphQL",
        "gRPC",
        "API Design",
        "Microservices|microservice",
        "Kafka|apache kafka",
        "RabbitMQ",
        "Celery",
        "Message Queues|message queue",
        "WebSockets|websocket",
        "OAuth|oauth2|oauth 2.0",
    ],
    "Databases": [
        "SQL|t-sql|pl/sql|plsql",
        "PostgreSQL|postgres|psql",
        "MySQL|mariadb",
        "SQLite",
        "SQL Server|mssql|microsoft sql server|ms sql",
        "Oracle|oracle db|oracle database",
        "MongoDB|mongo",
        "Redis",
        "Elasticsearch|elastic search|opensearch",
        "DynamoDB",
        "Cassandra",
        "NoSQL",
        "Database Design|schema design",
        "Query Optimization|query tuning",
    ],
    "Data Engineering": [
        "Spark|apache spark|pyspark|spark sql",
        "Hadoop",
        "Airflow|apache airflow",
        "dbt",
        "ETL|etl pipelines|elt",
        "Data Pipelines|data pipeline",
        "Data Warehousing|data warehouse",
        "Data Modeling|data modelling",
        "Snowflake",
        "BigQuery",
        "Redshift",
        "Databricks",
    ],
    "Data & Analytics": [
        "Pandas",
        "NumPy",
        "SciPy",
        "Matplotlib",
        "Seaborn",
        "Plotly",
        "Jupyter|jupyter notebook|jupyter notebooks|jupyterlab",
        "Tableau",
        "Power BI|powerbi",
        "Looker",
        "Excel|microsoft excel|ms excel|advanced excel|excel formulas|pivot tables|vlookup",
        "Google Analytics",
        "Dashboards|dashboarding",
        "Data Visualization|data visualisation|data viz",
        "Data Cleaning|data cleansing|data wrangling|data preparation",
        "Statistics|statistical analysis|statistical modeling|statistical modelling",
        "Hypothesis Testing",
        "A/B Testing|a/b tests|a/b test|ab testing|split testing",
    ],
    "Machine Learning & AI": [
        "Machine Learning",
        "Deep Learning",
        "Neural Networks|neural network",
        "NLP|natural language processing",
        "Computer Vision",
        "scikit-learn|sklearn|scikit learn",
        "TensorFlow",
        "PyTorch",
        "Keras",
        "XGBoost",
        "LightGBM",
        "Hugging Face|huggingface",
        "LLMs|llm|large language models|large language model",
        "RAG|retrieval-augmented generation|retrieval augmented generation",
        "LangChain",
        "Generative AI|genai|gen ai|generative artificial intelligence",
        "Prompt Engineering",
        "OpenCV",
        "spaCy|spacy",
        "NLTK",
        "MLOps",
        "MLflow",
        "Model Deployment|model serving",
        "Feature Engineering",
        "Hyperparameter Tuning|hyperparameter",
        "Time Series|forecasting",
        "Recommendation Systems|recommender systems|recommender system|recommendation system|recommendation engines",
        "Reinforcement Learning",
    ],
    "Cloud & DevOps": [
        "AWS|amazon web services|ec2|s3|aws lambda|cloudwatch|sagemaker",
        "Azure|microsoft azure",
        "GCP|google cloud|google cloud platform",
        "Docker|docker compose|dockerfile",
        "Kubernetes|k8s|eks|gke",
        "Helm",
        "Terraform",
        "Ansible",
        "CloudFormation",
        "Infrastructure as Code|iac",
        "CI/CD|cicd|continuous integration|continuous delivery|continuous deployment",
        "Jenkins",
        "GitHub Actions",
        "GitLab CI|gitlab ci/cd",
        "ArgoCD|argo cd",
        "Linux|unix",
        "Nginx",
        "Prometheus",
        "Grafana",
        "Datadog",
        "Observability|opentelemetry",
        "Serverless",
    ],
    "Testing & Quality": [
        "Pytest",
        "Unit Testing|unit tests|unit test|unittest",
        "Integration Testing|integration tests|integration test",
        "Test Automation|automated testing|qa automation",
        "TDD|test-driven development|test driven development",
        "Jest",
        "JUnit",
        "Selenium",
        "Cypress",
        "Playwright",
        "Postman",
        "Code Review|code reviews",
        "SonarQube",
    ],
    "Tools & Practices": [
        "Git",
        "GitHub",
        "GitLab",
        "Bitbucket",
        "Jira",
        "Confluence",
        "Agile|agile methodologies",
        "Scrum",
        "Kanban",
        "OOP|object-oriented programming|object oriented programming|object-oriented design",
        "Design Patterns|design pattern",
        "Data Structures",
        "System Design",
        "Distributed Systems",
        "Figma",
    ],
}

#: Too ambiguous as ordinary words; matched with context-aware rules instead.
CONTEXT_SKILLS = {"Go", "R", "C", "Swift", "Excel"}

#: Skills whose plain-word match must not be followed by a given pattern.
NOT_FOLLOWED_BY = {"React": r"[\s\-]*native"}

#: Category display order (used for charts).
CATEGORIES: list[str] = list(_RAW)

SKILL_ALIASES: dict[str, list[str]] = {}
CATEGORY_OF: dict[str, str] = {}

for _category, _entries in _RAW.items():
    for _entry in _entries:
        _canonical, *_aliases = _entry.split("|")
        _all = list(_aliases)
        if _canonical not in CONTEXT_SKILLS:
            _all.append(_canonical.lower())
        SKILL_ALIASES[_canonical] = _all
        CATEGORY_OF[_canonical] = _category

#: Groups of skills that do similar jobs. Used only to point out *transferable*
#: experience a candidate may already have, never to claim a skill.
SKILL_GROUPS: list[set[str]] = [
    {"React", "Angular", "Vue.js", "Svelte", "Next.js"},
    {"PyTorch", "TensorFlow", "Keras"},
    {"PostgreSQL", "MySQL", "SQL Server", "Oracle", "SQLite", "SQL"},
    {"MongoDB", "DynamoDB", "Cassandra", "Redis", "NoSQL"},
    {"AWS", "Azure", "GCP"},
    {"Django", "Flask", "FastAPI"},
    {"Node.js", "Express.js", "NestJS"},
    {"Java", "Spring Boot", "Kotlin", "C#", ".NET", "ASP.NET"},
    {"Tableau", "Power BI", "Looker"},
    {"Terraform", "CloudFormation", "Ansible", "Infrastructure as Code"},
    {"Jenkins", "GitHub Actions", "GitLab CI", "CI/CD"},
    {"Docker", "Kubernetes", "Helm"},
    {"Kafka", "RabbitMQ", "Message Queues", "Celery"},
    {"Snowflake", "BigQuery", "Redshift", "Databricks", "Data Warehousing"},
    {"Spark", "Hadoop", "Airflow", "ETL", "Data Pipelines"},
    {"Pytest", "Unit Testing", "Jest", "JUnit", "Test Automation"},
    {"Selenium", "Cypress", "Playwright"},
    {"Prometheus", "Grafana", "Datadog", "Observability"},
    {"Machine Learning", "Deep Learning", "scikit-learn", "NLP"},
    {"MLflow", "MLOps", "Model Deployment"},
    {"Pandas", "NumPy", "SciPy", "Matplotlib", "Seaborn"},
]


def related_skills(skill: str, have) -> list[str]:
    """Skills from the same group as ``skill`` that the candidate already has."""
    out: list[str] = []
    for group in SKILL_GROUPS:
        if skill in group:
            out.extend(sorted(s for s in group if s != skill and s in have))
    seen: set[str] = set()
    return [s for s in out if not (s in seen or seen.add(s))]
