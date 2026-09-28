import json
from pathlib import Path

import pytest

from resume_match.analyzer import (alternative_groups, analyze, detect_sections, extract_keywords,
                                   extract_skills, split_requirements)
from resume_match.cli import main
from resume_match.web import create_app

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"
RESUME = (EXAMPLES / "resume.txt").read_text()
JOB = (EXAMPLES / "job_description.txt").read_text()


# ------------------------------------------------------------ skill extraction

def test_aliases_map_to_canonical_names():
    skills = extract_skills("Built ML pipelines with sklearn and pyspark on AWS; used Postgres and k8s")
    assert {"scikit-learn", "Spark", "AWS", "PostgreSQL", "Kubernetes"} <= set(skills)


def test_symbols_in_skill_names():
    skills = extract_skills("Languages: C++, C#, Node.js, CI/CD")
    assert {"C++", "C#", "Node.js", "CI/CD"} <= set(skills)
    assert "C" not in skills  # "C++" must not count as C


def test_ambiguous_words_need_skills_context():
    prose = extract_skills("I will go to the office and rest before the sprint.")
    assert "Go" not in prose and "REST APIs" not in prose
    listed = extract_skills("Languages: Go, Python, R, SQL")
    assert {"Go", "R", "Python", "SQL"} <= set(listed)


def test_required_vs_preferred():
    jd = "Requirements:\n- Python and SQL\n\nNice to have:\n- Docker and AWS\n- Tableau is a plus"
    required, preferred = split_requirements(jd, extract_skills(jd))
    assert required == {"Python", "SQL"}
    assert preferred == {"Docker", "AWS", "Tableau"}


def test_either_or_skills_are_grouped():
    jd = "Requirements:\n- Experience with Flask or Django\n- Python"
    groups = alternative_groups(jd, extract_skills(jd))
    assert {"Flask", "Django"} in groups


def test_having_one_alternative_is_enough():
    result = analyze("Skills: Python, Flask\nBuilt 3 Flask apps", "Requirements:\n- Flask or Django\n- Python")
    assert "Django" not in result.missing_required
    assert result.breakdown["skills"]["score"] == 100


# ------------------------------------------------------------ keywords & sections

def test_keywords_skip_skills_and_filler():
    jd = ("We need someone to improve payment reliability. Payment reliability matters. "
          "Experience with Python. Payment systems at scale. Reliability reviews.")
    keywords = extract_keywords(jd)
    assert any("payment" in k for k in keywords)
    assert "python" not in keywords and "experience" not in keywords


def test_section_detection():
    text = "EDUCATION\nB.Tech\nTechnical Skills:\nPython\nProjects\nThing\nWork Experience\nIntern"
    assert set(detect_sections(text)) >= {"Education", "Skills", "Projects", "Experience"}


# ------------------------------------------------------------ full analysis

def test_example_analysis():
    r = analyze(RESUME, JOB)
    assert 0 <= r.score <= 100
    assert {"Python", "Flask", "PostgreSQL", "Docker"} <= set(r.matched_required)
    assert "Kubernetes" in r.missing_preferred
    assert all(r.contact.values())
    assert "responsible for" in r.impact["weak_phrases"]
    assert r.suggestions


def test_better_resume_scores_higher():
    weak = "Name\nI am a hardworking team player. Responsible for various tasks."
    assert analyze(RESUME, JOB).score > analyze(weak, JOB).score + 20


def test_result_is_json_serialisable():
    json.dumps(analyze(RESUME, JOB).to_dict())


# ------------------------------------------------------------ CLI

def test_cli_json(capsys):
    assert main([str(EXAMPLES / "resume.txt"), str(EXAMPLES / "job_description.txt"), "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert "score" in data and "suggestions" in data


def test_cli_min_score_exit_code():
    args = [str(EXAMPLES / "resume.txt"), str(EXAMPLES / "job_description.txt")]
    assert main(args + ["--min-score", "1"]) == 0
    assert main(args + ["--min-score", "100"]) == 1


def test_cli_missing_file(capsys):
    assert main(["nope.pdf", str(EXAMPLES / "job_description.txt")]) == 2
    assert "not found" in capsys.readouterr().err


def test_cli_markdown_file(tmp_path):
    out = tmp_path / "report.md"
    main([str(EXAMPLES / "resume.txt"), str(EXAMPLES / "job_description.txt"), "-o", str(out)])
    assert out.read_text().startswith("# Resume Match Report")


def test_docx_input(tmp_path):
    docx = pytest.importorskip("docx")
    doc = docx.Document()
    doc.add_paragraph("Skills: Python, Flask, PostgreSQL")
    path = tmp_path / "resume.docx"
    doc.save(path)
    from resume_match.text import read_text
    assert "Flask" in read_text(path)


# ------------------------------------------------------------ web

@pytest.fixture
def client():
    return create_app().test_client()


def test_web_form_with_pasted_text(client):
    resp = client.post("/", data={"resume_text": RESUME, "job_text": JOB})
    assert resp.status_code == 200
    assert b"How to improve" in resp.data


def test_web_requires_job(client):
    resp = client.post("/", data={"resume_text": RESUME, "job_text": ""})
    assert b"Paste the job description" in resp.data


def test_web_example_page(client):
    assert client.get("/example").status_code == 200


def test_api(client):
    resp = client.post("/api/analyze", json={"resume": RESUME, "job": JOB})
    assert resp.status_code == 200 and "score" in resp.get_json()
    assert client.post("/api/analyze", json={}).status_code == 400
