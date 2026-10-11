"""Interview question bank with what a good answer covers.

Each entry:  skill -> [ {"question": ..., "points": [(what a good answer says, [keywords], need), ...]} ]

keywords are matched as lowercase pieces of the answer ("aggregat" matches aggregate, aggregation).
need = how many of the keywords must appear for the point to count as covered.
These are used (1) when no AI key is available and (2) to keep technical questions accurate.
Add questions by adding lines here. Keep points short and factually safe.
"""

BANK = {
    "sql": [
        {"question": "What is the difference between INNER JOIN and LEFT JOIN? Give a small example.",
         "points": [("INNER JOIN returns only the rows that match in both tables", ["inner", "match", "both"], 2),
                    ("LEFT JOIN returns every row of the left table, with NULL where the right table has no match", ["left", "null", "all rows", "every"], 2),
                    ("A concrete example, such as customers and orders", ["customer", "order", "example", "employee", "table"], 1)]},
        {"question": "What is the difference between WHERE and HAVING?",
         "points": [("WHERE filters individual rows before grouping", ["where", "before", "row"], 2),
                    ("HAVING filters groups after aggregation, together with GROUP BY", ["having", "after", "group", "aggregat"], 2),
                    ("An example such as HAVING COUNT(*) > 5", ["count", "sum", "example", "> "], 1)]},
    ],
    "window functions": [
        {"question": "What is a window function in SQL, and how is it different from GROUP BY?",
         "points": [("It calculates across related rows without collapsing them into one row", ["without", "collaps", "keep", "each row", "every row"], 1),
                    ("It uses OVER with PARTITION BY and ORDER BY", ["over", "partition", "order by"], 2),
                    ("Examples such as ROW_NUMBER, RANK, running total or LAG/LEAD", ["row_number", "rank", "running", "lag", "lead", "sum"], 1)]},
    ],
    "ctes": [
        {"question": "What is a CTE in SQL and when would you use it instead of a subquery?",
         "points": [("A named temporary result set defined with WITH, used by the query that follows", ["with", "named", "temporary", "result set"], 2),
                    ("It makes long queries easier to read and lets you reuse the same result more than once", ["read", "reuse", "clear", "multiple", "simpl"], 1),
                    ("It can be recursive, for example for hierarchies", ["recursive", "hierarch"], 1)]},
    ],
    "python": [
        {"question": "What is the difference between a list and a tuple in Python?",
         "points": [("Lists can be changed (mutable); tuples cannot (immutable)", ["mutable", "immutable", "change"], 2),
                    ("Tuples can be dictionary keys and suit fixed data", ["key", "fixed", "hash", "constant"], 1),
                    ("An example of when you would use each", ["example", "coordinates", "use"], 1)]},
        {"question": "What is a list comprehension and why would you use one?",
         "points": [("A short way to build a list from another iterable, optionally with a condition", ["list", "iterable", "condition", "loop", "short", "concise"], 2),
                    ("It is more readable and usually faster than an equivalent for loop", ["readable", "faster", "cleaner", "compact"], 1),
                    ("A small example such as [x * 2 for x in nums if x > 0]", ["for x", "example", "nums", " in "], 1)]},
    ],
    "pandas": [
        {"question": "How would you handle missing values in a pandas DataFrame?",
         "points": [("First find them, for example with isna() or info()", ["isna", "isnull", "info", "detect", "find", "check"], 1),
                    ("Drop rows or columns with dropna when only a few are missing", ["dropna", "drop", "remove"], 1),
                    ("Fill them with fillna using the mean, median, mode or a forward fill", ["fillna", "mean", "median", "mode", "fill"], 1),
                    ("Choose the method based on what the column means and how much is missing", ["depends", "column", "meaning", "percentage", "context"], 1)]},
    ],
    "excel": [
        {"question": "What is the difference between VLOOKUP and XLOOKUP (or INDEX-MATCH)?",
         "points": [("VLOOKUP only looks to the right of the lookup column and uses a column number", ["right", "column number", "index"], 1),
                    ("XLOOKUP or INDEX-MATCH can look in any direction and do not break when columns are inserted", ["left", "any direction", "flexible", "insert", "break"], 1),
                    ("Mention exact match (FALSE or 0) versus approximate match", ["exact", "false", "approximate"], 1)]},
        {"question": "What is a pivot table and when would you use one?",
         "points": [("It summarises a large table by dragging fields into rows, columns, values and filters", ["summar", "rows", "columns", "values", "filter"], 2),
                    ("It aggregates quickly (sum, count, average) without writing formulas", ["sum", "count", "average", "aggregat", "formula"], 1),
                    ("It must be refreshed when the source data changes", ["refresh", "update", "source"], 1)]},
    ],
    "tableau": [
        {"question": "What is the difference between a dimension and a measure in Tableau?",
         "points": [("Dimensions are categories or descriptive fields used to slice the data, such as region or date", ["categor", "descriptive", "slice", "region", "qualitative", "text"], 1),
                    ("Measures are numeric values that get aggregated, such as sales or profit", ["numeric", "number", "aggregat", "sales", "profit", "quantitative"], 1),
                    ("An example that uses both in one chart", ["example", "chart", "by region", "per"], 1)]},
        {"question": "What is the difference between a live connection and an extract in Tableau?",
         "points": [("A live connection queries the data source in real time", ["live", "real time", "real-time", "directly"], 1),
                    ("An extract is a saved snapshot of the data inside Tableau, often faster and usable offline", ["snapshot", "extract", "faster", "offline", "hyper"], 1),
                    ("An extract must be refreshed to show new data", ["refresh", "schedule", "update"], 1)]},
    ],
    "power bi": [
        {"question": "What is DAX in Power BI, and how is a measure different from a calculated column?",
         "points": [("DAX is the formula language used in Power BI", ["dax", "formula", "language"], 1),
                    ("A calculated column is computed row by row and stored in the model", ["row", "stored", "column"], 2),
                    ("A measure is calculated when the report is viewed and responds to filters", ["measure", "filter", "aggregat", "context", "dynamic"], 2)]},
    ],
    "statistics": [
        {"question": "Explain mean, median and mode. When is the median a better choice than the mean?",
         "points": [("Mean is the average, median is the middle value, mode is the most frequent value", ["average", "middle", "frequent", "most common"], 2),
                    ("The median is better when there are outliers or skewed data", ["outlier", "skew", "extreme"], 1),
                    ("An example such as salaries or house prices", ["salar", "price", "income", "example"], 1)]},
        {"question": "What is a p-value, in simple words?",
         "points": [("The probability of seeing a result at least this extreme if the null hypothesis were true", ["null", "probab", "extreme", "chance"], 2),
                    ("A small p-value (commonly below 0.05) is evidence against the null hypothesis", ["0.05", "small", "reject", "significan", "against"], 1),
                    ("It does not prove the hypothesis and is not the probability that the null is true", ["not prove", "does not prove", "doesn't prove", "not the probability"], 1)]},
    ],
    "machine learning": [
        {"question": "What is overfitting and how do you reduce it?",
         "points": [("The model learns noise in the training data, so it scores well on training data but badly on new data", ["noise", "training", "new data", "unseen", "test", "memoriz"], 2),
                    ("Ways to reduce it: more data, a simpler model, regularisation, dropout or early stopping", ["more data", "simpler", "regulari", "dropout", "early stopping"], 1),
                    ("Use cross-validation or a separate test set to detect it", ["cross", "validation", "test set", "split"], 1)]},
        {"question": "What is the difference between supervised and unsupervised learning?",
         "points": [("Supervised learning uses labelled data; unsupervised learning has no labels", ["label", "unlabel", "no label"], 1),
                    ("Supervised examples: classification and regression", ["classification", "regression", "predict"], 1),
                    ("Unsupervised examples: clustering and dimensionality reduction", ["cluster", "dimension", "pattern", "group"], 1)]},
    ],
    "deep learning": [
        {"question": "What is a CNN and why is it used for images?",
         "points": [("Convolution layers use small filters to detect local features such as edges and textures", ["filter", "kernel", "edge", "feature", "convolution"], 2),
                    ("Pooling reduces the size and keeps the important information", ["pool", "reduce", "downsampl"], 1),
                    ("It needs far fewer parameters than a fully connected network on images", ["fewer", "parameter", "weight sharing", "efficient"], 1)]},
    ],
    "data cleaning": [
        {"question": "What steps do you take to clean a messy dataset?",
         "points": [("Check and handle missing values", ["missing", "null", "nan"], 1),
                    ("Remove duplicates and fix wrong data types or formats", ["duplicate", "type", "format"], 1),
                    ("Handle outliers and standardise inconsistent categories or spellings", ["outlier", "standard", "inconsistent", "spelling", "categor"], 1),
                    ("Validate the result afterwards", ["validat", "verify", "check again", "re-check"], 1)]},
    ],
    "etl": [
        {"question": "What is ETL, and how would you explain each step?",
         "points": [("Extract: pull data from sources such as files, databases or APIs", ["extract", "source", "pull", "api"], 1),
                    ("Transform: clean, join and aggregate the data into the shape you need", ["transform", "clean", "join", "aggregat"], 1),
                    ("Load: write the result into a target such as a data warehouse", ["load", "warehouse", "target", "database"], 1)]},
    ],
    "data warehousing": [
        {"question": "What is a data warehouse, and how is it different from an operational database?",
         "points": [("A warehouse stores integrated, historical data for analysis and reporting", ["historical", "analysis", "reporting", "integrat", "olap"], 1),
                    ("An operational database handles day-to-day transactions", ["transaction", "day-to-day", "daily", "oltp", "operational"], 1),
                    ("Mention fact and dimension tables or a star schema", ["fact", "dimension", "star", "schema"], 1)]},
    ],
    "git": [
        {"question": "What is the difference between git fetch and git pull?",
         "points": [("git fetch downloads new changes but does not change your working files", ["fetch", "download", "does not merge", "without merg"], 1),
                    ("git pull is a fetch followed by a merge into your current branch", ["pull", "merge"], 2)]},
    ],
    "aws": [
        {"question": "What are Amazon S3 and EC2 used for?",
         "points": [("S3 stores files (objects) in buckets", ["s3", "bucket", "object", "storage", "files"], 2),
                    ("EC2 provides virtual servers to run applications", ["ec2", "virtual", "server", "instance"], 2),
                    ("An example, such as storing a dataset in S3 and running an app on EC2", ["example", "dataset", "host", "deploy"], 1)]},
    ],
    "django": [
        {"question": "Explain Django's MVT architecture.",
         "points": [("Model: defines the data and talks to the database (ORM)", ["model", "database", "orm"], 2),
                    ("View: the logic that receives a request and returns a response", ["view", "request", "response", "logic"], 2),
                    ("Template: the HTML that is shown to the user; URLs route requests to views", ["template", "html", "url", "rout"], 2)]},
    ],
    "flask": [
        {"question": "How would a Flask API receive an uploaded image and return a prediction?",
         "points": [("A route that accepts POST requests", ["route", "post", "endpoint"], 1),
                    ("Read the file from the request, preprocess it and run the model", ["request.files", "file", "preprocess", "predict", "model"], 2),
                    ("Return the result as JSON, for example with jsonify", ["json", "jsonify", "response"], 1)]},
    ],
    "rest api": [
        {"question": "What is a REST API, and which HTTP methods do you know?",
         "points": [("A way for programs to talk over HTTP using URLs that represent resources", ["http", "url", "resource", "client", "server"], 2),
                    ("Methods: GET to read, POST to create, PUT or PATCH to update, DELETE to remove", ["get", "post", "put", "delete", "patch"], 3),
                    ("Responses usually come as JSON with status codes", ["json", "status code", "200", "404"], 1)]},
    ],
    "java": [
        {"question": "What is the difference between an abstract class and an interface in Java?",
         "points": [("An abstract class can hold state (fields), constructors and ready-made methods", ["field", "state", "constructor", "implementation", "concrete"], 1),
                    ("A class can extend only one abstract class but implement many interfaces", ["one", "single", "multiple", "many"], 2),
                    ("An interface describes a contract that classes agree to follow", ["contract", "behaviour", "behavior", "implements"], 1)]},
    ],
    "oop": [
        {"question": "Explain the four pillars of object-oriented programming with a simple example.",
         "points": [("Encapsulation: keep data and the methods that use it together, hiding the details", ["encapsulat", "hiding", "private"], 1),
                    ("Inheritance: a class reuses and extends another class", ["inherit", "extend", "parent", "child"], 1),
                    ("Polymorphism: the same method name behaves differently for different classes", ["polymorph", "overrid", "overload"], 1),
                    ("Abstraction: show only what is needed and hide complexity", ["abstract"], 1)]},
    ],
    "opencv": [
        {"question": "What preprocessing steps do you apply to images before giving them to a model?",
         "points": [("Resize every image to the size the model expects", ["resize", "size", "shape"], 1),
                    ("Normalise the pixel values, for example to the range 0 to 1", ["normali", "scale", "0 to 1", "0-1", "255"], 1),
                    ("Convert colour format or grayscale, remove noise, or augment the data", ["grayscale", "gray", "noise", "augment", "colour", "color", "rgb"], 1)]},
    ],
    "nlp": [
        {"question": "What is tokenization, and why do we use embeddings in NLP?",
         "points": [("Tokenization splits text into smaller pieces such as words or sub-words", ["token", "split", "words", "sub-word", "subword"], 1),
                    ("Embeddings turn tokens into vectors (numbers) that capture meaning", ["vector", "number", "meaning", "embedding", "semantic"], 2),
                    ("Similar meanings end up close together, so we can compare texts", ["similar", "close", "compar", "cosine", "distance"], 1)]},
    ],
    "generative ai": [
        {"question": "At a high level, how does a diffusion model such as Stable Diffusion generate an image from a text prompt?",
         "points": [("It starts from random noise", ["noise", "random"], 1),
                    ("It removes the noise step by step (denoising)", ["step", "denois", "iterative", "gradual", "remove"], 1),
                    ("The text prompt is turned into an embedding that guides each step", ["prompt", "text", "embedding", "guide", "condition", "clip"], 2),
                    ("It works in a compressed latent space and a decoder produces the final image", ["latent", "decoder", "vae", "compress"], 1)]},
    ],
}

# Questions asked in every interview. The "{role}" placeholder is filled from the job description.
INTRO = {"question": "Tell me about yourself.",
         "points": [("Your education and background in one or two lines", ["b.tech", "btech", "degree", "graduat", "student", "engineering", "studied"], 1),
                    ("The skills and projects that matter for this role", ["project", "skill", "python", "sql", "tableau", "excel", "internship", "built"], 2),
                    ("Why you want this kind of role", ["want", "interest", "passion", "goal", "looking", "excited", "role"], 1),
                    ("Short and clear (about one to two minutes)", [], 0)]}

BEHAVIORAL = [
    {"question": "Tell me about a time you worked in a team or organised something with other people. What was your part and what was the result?",
     "points": [("A specific situation, not a general statement", ["when", "during", "once", "event", "project", "college", "team"], 1),
                ("What YOU did personally", ["i ", "my role", "i was", "i organi", "i led", "i coordinat", "responsible"], 1),
                ("The result, ideally with a number or a clear outcome", ["result", "outcome", "successful", "completed", "improved", "achieved", "%"], 1)]},
    {"question": "Describe a problem you faced in a project and how you solved it.",
     "points": [("A real, specific problem", ["error", "problem", "issue", "challenge", "bug", "stuck", "difficult"], 1),
                ("The steps you took to find the cause or a solution", ["tried", "searched", "debug", "checked", "tested", "asked", "fixed", "solved"], 1),
                ("What you learned or what changed afterwards", ["learn", "result", "improved", "now", "next time", "worked"], 1)]},
]

GAP = {"question": "This role uses {skill}, which is not on your resume. How would you get up to speed on it in your first month?",
       "points": [("Honesty about your current level, and any related skill you already have", ["haven't", "have not", "not used", "not yet", "similar", "related", "basic", "familiar"], 1),
                  ("A concrete learning plan, such as courses, documentation or a practice project", ["course", "tutorial", "documentation", "practice", "project", "plan", "learn"], 1),
                  ("Asking teammates or a mentor for help and applying it on real work", ["ask", "mentor", "team", "senior", "colleague", "real work", "feedback"], 1)]}

PROJECT = {"question": "Walk me through your project \"{title}\". What problem did it solve, which tools did you use and why, what was your own part, and what was the result?",
           "points": [("The problem or goal in one or two lines", ["problem", "goal", "aim", "objective", "purpose", "to analy", "to build", "to predict"], 1),
                      ("The tools used and why you chose them", ["used", "using", "python", "sql", "tableau", "excel", "django", "flask", "because"], 1),
                      ("What YOU personally did", ["i ", "my part", "i built", "i created", "i cleaned", "i analy", "i designed", "i implemented"], 1),
                      ("The result, a number, or what you learned", ["result", "accuracy", "insight", "found", "learned", "%", "improved", "trend"], 1)]}

TECHNICAL_FALLBACK = {"question": "Explain how you have used {skill} in your work or projects. What is one mistake beginners make with it?",
                      "points": [("A real example of using it", ["project", "used", "built", "analy", "created", "worked on"], 1),
                                 ("What it is used for and why", ["because", "used for", "helps", "allows", "purpose"], 1),
                                 ("A common mistake and how to avoid it", ["mistake", "avoid", "careful", "issue", "common", "error"], 1)]}
