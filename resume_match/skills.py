"""Skill taxonomy: canonical skill name -> (category, aliases).

Aliases are matched as whole words/phrases, case-insensitively, so "JS" in a
resume counts as JavaScript and "scikit learn" counts as scikit-learn.
Add to this list freely — it is the main thing that makes matching smart.
"""

SKILLS = {
    # Languages
    "Python": ("Languages", ["python", "python3"]),
    "Java": ("Languages", ["java"]),
    "JavaScript": ("Languages", ["javascript", "js", "ecmascript"]),
    "TypeScript": ("Languages", ["typescript", "ts"]),
    "C": ("Languages", ["c", "c language", "c programming"]),
    "C++": ("Languages", ["c++", "cpp"]),
    "C#": ("Languages", ["c#", "csharp"]),
    "Go": ("Languages", ["go", "golang", "go lang"]),
    "Rust": ("Languages", ["rust"]),
    "Kotlin": ("Languages", ["kotlin"]),
    "Swift": ("Languages", ["swift"]),
    "R": ("Languages", ["r", "r programming", "r language", "rstudio"]),
    "SQL": ("Languages", ["sql", "t-sql", "pl/sql"]),
    "Bash": ("Languages", ["bash", "shell scripting", "shell script"]),
    "HTML": ("Languages", ["html", "html5"]),
    "CSS": ("Languages", ["css", "css3", "scss", "sass"]),

    # Backend & web
    "Flask": ("Web & Backend", ["flask"]),
    "Django": ("Web & Backend", ["django"]),
    "FastAPI": ("Web & Backend", ["fastapi"]),
    "Node.js": ("Web & Backend", ["node.js", "nodejs", "node"]),
    "Express": ("Web & Backend", ["express", "express.js", "expressjs"]),
    "Spring Boot": ("Web & Backend", ["spring boot", "springboot", "spring"]),
    "React": ("Web & Backend", ["react", "react.js", "reactjs"]),
    "Next.js": ("Web & Backend", ["next.js", "nextjs"]),
    "Angular": ("Web & Backend", ["angular"]),
    "Vue": ("Web & Backend", ["vue", "vue.js", "vuejs"]),
    "REST APIs": ("Web & Backend", ["rest", "restful", "rest api", "rest apis", "restful api", "restful apis"]),
    "GraphQL": ("Web & Backend", ["graphql"]),
    "Microservices": ("Web & Backend", ["microservices", "microservice"]),

    # Data & databases
    "PostgreSQL": ("Databases", ["postgresql", "postgres"]),
    "MySQL": ("Databases", ["mysql"]),
    "SQLite": ("Databases", ["sqlite"]),
    "MongoDB": ("Databases", ["mongodb", "mongo"]),
    "Redis": ("Databases", ["redis"]),
    "Elasticsearch": ("Databases", ["elasticsearch"]),
    "Snowflake": ("Databases", ["snowflake"]),
    "BigQuery": ("Databases", ["bigquery"]),

    # Data science & ML
    "pandas": ("Data & ML", ["pandas"]),
    "NumPy": ("Data & ML", ["numpy"]),
    "scikit-learn": ("Data & ML", ["scikit-learn", "scikit learn", "sklearn"]),
    "TensorFlow": ("Data & ML", ["tensorflow"]),
    "PyTorch": ("Data & ML", ["pytorch", "torch"]),
    "Keras": ("Data & ML", ["keras"]),
    "Machine Learning": ("Data & ML", ["machine learning", "ml"]),
    "Deep Learning": ("Data & ML", ["deep learning", "neural networks", "neural network"]),
    "NLP": ("Data & ML", ["nlp", "natural language processing"]),
    "Computer Vision": ("Data & ML", ["computer vision", "opencv", "image processing"]),
    "LLMs": ("Data & ML", ["llm", "llms", "large language models", "generative ai", "genai"]),
    "Statistics": ("Data & ML", ["statistics", "statistical analysis", "hypothesis testing", "a/b testing"]),
    "Data Analysis": ("Data & ML", ["data analysis", "data analytics", "exploratory data analysis", "eda"]),
    "Data Visualization": ("Data & ML", ["data visualization", "data visualisation", "matplotlib", "seaborn", "plotly"]),
    "Tableau": ("Data & ML", ["tableau"]),
    "Power BI": ("Data & ML", ["power bi", "powerbi"]),
    "Excel": ("Data & ML", ["excel", "ms excel", "microsoft excel", "advanced excel", "vlookup", "pivot tables"]),
    "Spark": ("Data & ML", ["spark", "pyspark", "apache spark"]),
    "ETL": ("Data & ML", ["etl", "data pipelines", "data pipeline"]),
    "Jupyter": ("Data & ML", ["jupyter", "jupyter notebook"]),

    # Cloud & DevOps
    "AWS": ("Cloud & DevOps", ["aws", "amazon web services", "ec2", "s3", "lambda"]),
    "Azure": ("Cloud & DevOps", ["azure", "microsoft azure"]),
    "GCP": ("Cloud & DevOps", ["gcp", "google cloud", "google cloud platform"]),
    "Docker": ("Cloud & DevOps", ["docker", "containerization", "containers"]),
    "Kubernetes": ("Cloud & DevOps", ["kubernetes", "k8s"]),
    "CI/CD": ("Cloud & DevOps", ["ci/cd", "ci cd", "continuous integration", "github actions", "jenkins"]),
    "Terraform": ("Cloud & DevOps", ["terraform"]),
    "Linux": ("Cloud & DevOps", ["linux", "unix", "ubuntu"]),

    # Tools & practices
    "Git": ("Tools & Practices", ["git", "github", "gitlab", "version control"]),
    "Agile": ("Tools & Practices", ["agile", "scrum", "kanban", "sprint planning"]),
    "Jira": ("Tools & Practices", ["jira"]),
    "Unit Testing": ("Tools & Practices", ["unit testing", "pytest", "junit", "test-driven development", "tdd"]),
    "Data Structures": ("Tools & Practices", ["data structures", "algorithms", "dsa"]),
    "OOP": ("Tools & Practices", ["oop", "object oriented programming", "object-oriented programming", "object oriented"]),
    "System Design": ("Tools & Practices", ["system design", "distributed systems"]),

    # Business
    "Communication": ("Business & Soft Skills", ["communication", "communication skills", "presentation skills"]),
    "Leadership": ("Business & Soft Skills", ["leadership", "team lead", "led a team", "managed a team"]),
    "Stakeholder Management": ("Business & Soft Skills", ["stakeholder management", "stakeholders", "client management"]),
    "Problem Solving": ("Business & Soft Skills", ["problem solving", "problem-solving", "analytical skills", "analytical thinking"]),
    "Business Development": ("Business & Soft Skills", ["business development", "lead generation", "partnerships"]),
    "Sales": ("Business & Soft Skills", ["sales", "b2b sales", "cold calling", "pipeline management", "negotiation"]),
    "CRM": ("Business & Soft Skills", ["crm", "salesforce", "hubspot", "zoho crm"]),
    "Market Research": ("Business & Soft Skills", ["market research", "competitive analysis", "competitor analysis"]),
    "Project Management": ("Business & Soft Skills", ["project management", "program management"]),
    "Product Management": ("Business & Soft Skills", ["product management", "product roadmap", "roadmapping"]),
}

# Aliases that are too ambiguous to trust on their own in free text.
# "go", "r", "c", "node", "spring", "rest", "ts", "ml" etc. only count
# when they appear in a skills-like context (comma lists, "Skills:" lines).
AMBIGUOUS = {"go", "r", "c", "node", "spring", "rest", "ts", "ml", "swift",
             "rust", "express", "angular", "torch", "containers", "lambda",
             "s3", "stakeholders", "partnerships", "negotiation", "sprint planning"}
