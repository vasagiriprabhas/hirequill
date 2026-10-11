"""Free learning resources for common skills. Used for the learning plan.

Only well-known free platforms, kept at the top-level so links do not break.
Add more lines as you find good ones. Format: skill -> (hours to get job-ready basics, [resources]).
Hours are rough estimates for a beginner to reach "can use it in a small project".
"""

KAGGLE = "Kaggle Learn (kaggle.com/learn), free short courses"
MS_LEARN = "Microsoft Learn (learn.microsoft.com), free learning paths"
FCC = "freeCodeCamp (freecodecamp.org), free courses"
W3 = "W3Schools (w3schools.com), free tutorials and practice"
AWS_TRAIN = "AWS Skill Builder (skillbuilder.aws), free digital courses"
TABLEAU = "Tableau free training videos (tableau.com/learn/training)"
GOOGLE_CLOUD = "Google Cloud Skills Boost (cloudskillsboost.google), free intro labs"
NPTEL = "NPTEL (nptel.ac.in), free courses (certificate exam is paid, learning is free)"
YT = "YouTube: search the skill name + 'for beginners project'"

RESOURCES = {
    "sql": (15, [KAGGLE + ": Intro to SQL, Advanced SQL", W3 + ": SQL"]),
    "window functions": (4, [KAGGLE + ": Advanced SQL (analytic functions)"]),
    "ctes": (2, [KAGGLE + ": Advanced SQL (JOINs and UNIONs, then WITH)"]),
    "joins": (3, [KAGGLE + ": Intro to SQL"]),
    "python": (20, [KAGGLE + ": Python", FCC + ": Python"]),
    "pandas": (10, [KAGGLE + ": Pandas"]),
    "numpy": (4, [FCC + ": Data Analysis with Python"]),
    "excel": (10, [MS_LEARN + ": Excel", YT]),
    "pivot tables": (3, [MS_LEARN + ": Excel", YT]),
    "lookups": (2, [MS_LEARN + ": Excel", YT]),
    "power query": (4, [MS_LEARN + ": Power Query", YT]),
    "tableau": (12, [TABLEAU]),
    "power bi": (15, [MS_LEARN + ": Power BI (PL-300 learning path)"]),
    "qlik": (10, ["Qlik free learning (learning.qlik.com)"]),
    "data visualization": (6, [KAGGLE + ": Data Visualization"]),
    "dashboards": (6, [TABLEAU, MS_LEARN + ": Power BI"]),
    "statistics": (15, [NPTEL + ": Statistics for data science", "Khan Academy (khanacademy.org): Statistics and probability"]),
    "machine learning": (25, [KAGGLE + ": Intro to ML, Intermediate ML", NPTEL]),
    "deep learning": (20, [KAGGLE + ": Intro to Deep Learning", FCC + ": Deep learning"]),
    "scikit-learn": (8, [KAGGLE + ": Intro to ML"]),
    "tensorflow": (12, [FCC + ": TensorFlow course"]),
    "pytorch": (12, [FCC + ": PyTorch course"]),
    "nlp": (12, [KAGGLE + ": Natural Language Processing"]),
    "data warehousing": (8, [MS_LEARN + ": Data warehousing concepts", YT]),
    "etl": (8, [FCC + ": Data engineering / ETL basics", YT]),
    "data pipelines": (8, [FCC + ": Data engineering basics"]),
    "data cleaning": (5, [KAGGLE + ": Data Cleaning"]),
    "exploratory data analysis": (6, [KAGGLE + ": Data Cleaning, Pandas"]),
    "aws": (12, [AWS_TRAIN + ": Cloud Practitioner Essentials"]),
    "azure": (12, [MS_LEARN + ": Azure Fundamentals (AZ-900)"]),
    "gcp": (10, [GOOGLE_CLOUD]),
    "git": (4, [FCC + ": Git and GitHub for beginners"]),
    "github": (2, [FCC + ": Git and GitHub for beginners"]),
    "docker": (6, [FCC + ": Docker for beginners"]),
    "linux": (6, [FCC + ": Linux for beginners"]),
    "spark": (10, [FCC + ": Apache Spark / PySpark", YT]),
    "pyspark": (10, [FCC + ": PySpark", YT]),
    "databricks": (8, ["Databricks free training (databricks.com/learn)"]),
    "snowflake": (8, ["Snowflake free quickstarts (quickstarts.snowflake.com)"]),
    "mongodb": (6, ["MongoDB University (learn.mongodb.com), free courses"]),
    "rest api": (5, [FCC + ": APIs for beginners"]),
    "flask": (6, [FCC + ": Flask course"]),
    "django": (10, [FCC + ": Django course"]),
    "html": (4, [FCC + ": Responsive Web Design"]),
    "css": (4, [FCC + ": Responsive Web Design"]),
    "javascript": (15, [FCC + ": JavaScript"]),
    "java": (25, [NPTEL + ": Programming in Java", FCC + ": Java"]),
    "selenium": (8, [YT]),
    "manual testing": (8, [YT]),
    "agile": (3, [YT + " (Agile and Scrum basics)"]),
    "business analysis": (10, [YT + " (business analysis basics)"]),
    "financial analysis": (12, ["Khan Academy (khanacademy.org): Finance and capital markets", YT]),
    "reconciliation": (3, [YT + " (bank reconciliation in Excel)"]),
    "audit": (8, [YT + " (audit basics for beginners)"]),
    "accounting": (12, ["Khan Academy (khanacademy.org): Accounting basics"]),
    "tally": (8, [YT]),
    "generative ai": (8, ["Hugging Face courses (huggingface.co/learn)", KAGGLE]),
    "llm": (8, ["Hugging Face courses (huggingface.co/learn)"]),
    "prompt engineering": (4, ["DeepLearning.AI short courses (deeplearning.ai), free to audit"]),
    "rag": (8, ["DeepLearning.AI short courses (deeplearning.ai), free to audit"]),
    "powerpoint": (4, ["Microsoft Support PowerPoint training (support.microsoft.com), free video lessons"]),
    "vba": (10, [MS_LEARN + ": Excel VBA reference", YT + " (Excel VBA macros for beginners)"]),
    "salesforce": (15, ["Trailhead by Salesforce (trailhead.salesforce.com), free hands-on modules"]),
    "compliance": (4, [YT.replace("the skill name + 'for beginners project'", "'compliance basics for freshers'") + " (pick one for the job's industry)"]),
    "stakeholder management": (3, [YT.replace("the skill name + 'for beginners project'", "'stakeholder management basics'") + " (1-2 short videos)"]),
    "documentation": (2, [YT.replace("the skill name + 'for beginners project'", "'how to write project documentation'")]),
    "requirement gathering": (4, [YT.replace("the skill name + 'for beginners project'", "'requirement gathering for business analysts'")]),
    "process improvement": (3, [YT.replace("the skill name + 'for beginners project'", "'process improvement basics'")]),
    "risk management": (4, [YT.replace("the skill name + 'for beginners project'", "'risk management basics'")]),
    "project management": (5, [YT.replace("the skill name + 'for beginners project'", "'project management basics'")]),
}

# Ideas, not tools: you show these with a real example, not by "using a tool in a project".
CONCEPT_SKILLS = {"compliance", "stakeholder management", "documentation", "requirement gathering",
                  "process improvement", "risk management", "project management", "process mapping",
                  "user stories", "business analysis"}

DEFAULT = (8, ["Search the official documentation + one beginner project tutorial on YouTube"])


def lookup(skill: str):
    """(hours, resources) for a skill. The generic YouTube line gets the real skill name."""
    hours, resources = RESOURCES.get(skill, DEFAULT)
    generic = "search the skill name + 'for beginners project'"
    return hours, [r.replace(generic, f"search '{skill} for beginners project'") for r in resources]
