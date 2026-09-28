"""Core analysis: match a resume against a job description and score it."""
import re
from collections import Counter
from dataclasses import asdict, dataclass, field

from .skills import AMBIGUOUS, SKILLS
from .text import normalize, phrase_pattern, tokenize

# ---------------------------------------------------------------- patterns

_ALIAS_PATTERNS = [
    (canonical, alias, phrase_pattern(alias))
    for canonical, (_cat, aliases) in SKILLS.items()
    for alias in aliases
]
ALL_ALIASES = {a for _c, (_cat, aliases) in SKILLS.items() for a in aliases}

LIST_HEADING = re.compile(
    r"^\s*(technical\s+)?(skills|technologies|tech\s*stack|languages|tools|frameworks|"
    r"libraries|platforms|databases|stack|core competencies)\b", re.I)

PREFERRED_HEADING = re.compile(
    r"(preferred|nice[\s-]to[\s-]have|good[\s-]to[\s-]have|bonus|desirable|"
    r"a plus|is a plus|added advantage|optional)", re.I)
REQUIRED_HEADING = re.compile(
    r"^\s*(required|requirements|must[\s-]have|minimum|basic qualifications|qualifications|"
    r"what you('|’)ll (need|bring)|who you are|responsibilities|what you('|’)ll do|about the role)", re.I)

SECTION_PATTERNS = {
    "Summary": r"(summary|objective|profile|about me)",
    "Experience": r"(experience|work history|employment|internships?)",
    "Education": r"(education|academics?|academic background)",
    "Skills": r"(skills|technical skills|technologies|tech stack|core competencies)",
    "Projects": r"(projects|personal projects|academic projects)",
    "Certifications": r"(certifications?|certificates?|courses)",
    "Achievements": r"(achievements|awards|honou?rs|accomplishments)",
    "Leadership": r"(leadership|positions? of responsibility|extra[\s-]?curricular|activities|volunteering)",
}

HEADING_PREFIX = r"(work|professional|relevant|technical|academic|personal|key|internship|industry|other)\s+"

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"(\+?\d[\d\s().-]{8,}\d)")
LINKEDIN_RE = re.compile(r"linkedin\.com/in/[\w-]+|linkedin", re.I)
GITHUB_RE = re.compile(r"github\.com/[\w-]+|github", re.I)
NUMBER_RE = re.compile(r"(\d+(\.\d+)?\s*(%|x|\+|k|lakh|cr|crore|million|users|ms|hrs?|hours|days)?|[₹$€£]\s?\d)", re.I)

ACTION_VERBS = set("""
achieved analyzed analysed architected automated boosted built collaborated conducted created cut
decreased delivered deployed designed developed drove engineered enhanced established executed
expanded generated grew implemented improved increased initiated integrated launched led managed
mentored migrated negotiated optimized optimised orchestrated organized organised owned pioneered
produced reduced redesigned refactored resolved scaled secured shipped simplified spearheaded
streamlined trained transformed won wrote coordinated presented researched modeled modelled
evaluated trained tested maintained configured prototyped closed acquired onboarded
""".split())

WEAK_PHRASES = [
    "responsible for", "worked on", "helped with", "helped in", "duties included",
    "tasked with", "involved in", "participated in", "assisted with", "assisted in",
    "hardworking", "team player", "go-getter", "detail-oriented", "etc",
]

FIRST_PERSON = re.compile(r"\b(i|me|my|myself)\b", re.I)


# ---------------------------------------------------------------- helpers

def _is_list_context(line):
    if LIST_HEADING.search(line):
        return True
    return len(re.findall(r"[,|/•·;]", line)) >= 2


def extract_skills(text):
    """Return {canonical_skill: [lines it appeared on]}."""
    found = {}
    lines = [l for l in normalize(text).splitlines() if l.strip()]
    for line in lines:
        lower = line.lower()
        list_ctx = None
        for canonical, alias, pattern in _ALIAS_PATTERNS:
            for m in pattern.finditer(lower):
                if alias in AMBIGUOUS:
                    if list_ctx is None:
                        list_ctx = _is_list_context(line)
                    if not list_ctx:
                        continue
                    original = line[m.start():m.end()]
                    if alias.isalpha() and len(alias) <= 7 and not original[:1].isupper():
                        continue
                found.setdefault(canonical, []).append(line.strip())
                break
    return found


def split_requirements(job_text, jd_skills):
    """Split job-description skills into required and preferred."""
    mode = "required"
    required, preferred = set(), set()
    line_mode = {}
    for line in normalize(job_text).splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        is_heading = len(stripped) < 60 and (stripped.endswith(":") or stripped.isupper() or len(stripped.split()) <= 5)
        if is_heading and PREFERRED_HEADING.search(stripped):
            mode = "preferred"
        elif is_heading and REQUIRED_HEADING.search(stripped):
            mode = "required"
        inline_pref = bool(PREFERRED_HEADING.search(stripped)) and not is_heading
        line_mode[stripped] = "preferred" if (mode == "preferred" or inline_pref) else "required"

    for skill, lines in jd_skills.items():
        if any(line_mode.get(l, "required") == "required" for l in lines):
            required.add(skill)
        else:
            preferred.add(skill)
    return required, preferred


def alternative_groups(job_text, jd_skills):
    """Skills offered as alternatives on one line ("Flask or Django") form a group."""
    groups = []
    for line in normalize(job_text).splitlines():
        if not re.search(r"\bor\b", line, re.I):
            continue
        on_line = {s for s, lines in jd_skills.items() if line.strip() in lines}
        if len(on_line) >= 2:
            groups.append(on_line)
    return groups


def _stem(word):
    for suffix in ("ations", "ation", "ments", "ment", "ings", "ing", "ies", "ers", "er", "ed", "es", "s"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 4:
            return word[: -len(suffix)]
    return word


def _alias_tokens():
    tokens = set()
    for alias in ALL_ALIASES:
        tokens.update(alias.split())
    return tokens


_SKILL_TOKENS = _alias_tokens()


def extract_keywords(job_text, limit=15):
    """Important non-skill terms in a job description (single words and two-word phrases)."""
    tokens = [t for t in tokenize(job_text) if t not in _SKILL_TOKENS and not t.isdigit()]
    unigrams = Counter(tokens)
    bigrams = Counter(f"{a} {b}" for a, b in zip(tokens, tokens[1:]))

    scored = {}
    for phrase, count in bigrams.items():
        if count >= 2:
            scored[phrase] = count * 2.5
    for word, count in unigrams.items():
        if len(word) >= 4 and count >= 2:
            scored[word] = count
    if len(scored) < limit:  # short JDs: fall back to single mentions of longer words
        for word, count in unigrams.items():
            if len(word) >= 6 and word not in scored:
                scored[word] = count * 0.5

    ranked = sorted(scored.items(), key=lambda kv: (-kv[1], kv[0]))
    chosen = []
    for phrase, _score in ranked:
        # skip single words already covered by a chosen phrase
        stems = " ".join(_stem(p) for p in phrase.split())
        if any(phrase in c.split() or stems == " ".join(_stem(p) for p in c.split()) for c in chosen):
            continue
        chosen.append(phrase)
        if len(chosen) == limit:
            break
    return chosen


def keyword_present(keyword, resume_stems):
    return all(_stem(part) in resume_stems for part in keyword.split())


def detect_sections(text):
    found = []
    for line in normalize(text).splitlines():
        s = line.strip().strip(":").strip()
        if not s or len(s) > 40 or len(s.split()) > 5:
            continue
        for name, pat in SECTION_PATTERNS.items():
            if name not in found and re.fullmatch(rf"[\W\d]*({HEADING_PREFIX})?{pat}[\W\d]*(&.*|and .*)?", s, re.I):
                found.append(name)
    return found


def _is_quantified(line):
    """True if a line contains a measurable number (not just a year or a date)."""
    cleaned = re.sub(r"\b(19|20)\d{2}\b", "", line)          # years
    cleaned = re.sub(r"\b\d{1,2}/\d{1,4}\b", "", cleaned)    # dates like 06/2025
    cleaned = re.sub(r"\b(cgpa|gpa|sgpa)\b.*", "", cleaned, flags=re.I)
    return bool(NUMBER_RE.search(cleaned)) and bool(re.search(r"\d", cleaned))


def analyze_impact(text):
    lines = [l.strip(" -*•\t") for l in normalize(text).splitlines()]
    statements = [l for l in lines if len(l.split()) >= 6]
    quantified = [l for l in statements if _is_quantified(l)]
    action = [l for l in statements if l.split()[0].lower().strip(",.") in ACTION_VERBS]
    lower = text.lower()
    weak = sorted({p for p in WEAK_PHRASES if re.search(rf"\b{re.escape(p)}\b", lower)})
    first_person = len(FIRST_PERSON.findall(text))
    return {
        "statements": len(statements),
        "quantified": len(quantified),
        "action_led": len(action),
        "weak_phrases": weak,
        "first_person": first_person,
        "unquantified_examples": [l for l in statements if l not in quantified and l in action][:3],
    }


# ---------------------------------------------------------------- result

@dataclass
class Result:
    score: int
    grade: str
    breakdown: dict
    matched_required: list
    missing_required: list
    matched_preferred: list
    missing_preferred: list
    extra_skills: list
    matched_keywords: list
    missing_keywords: list
    sections: list
    contact: dict
    word_count: int
    impact: dict
    suggestions: list = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


def grade_for(score):
    if score >= 85:
        return "Excellent match"
    if score >= 70:
        return "Strong match"
    if score >= 55:
        return "Fair match"
    if score >= 40:
        return "Weak match"
    return "Poor match"


def _ratio(n, d):
    return n / d if d else 1.0


def analyze(resume_text, job_text):
    resume_skills = extract_skills(resume_text)
    jd_skills = extract_skills(job_text)
    required, preferred = split_requirements(job_text, jd_skills)

    have = set(resume_skills)
    # If the resume has one skill from an "X or Y" group, the others aren't gaps.
    covered = set()
    for group in alternative_groups(job_text, jd_skills):
        if group & have:
            covered |= group - have
    required -= covered
    preferred -= covered

    matched_req = sorted(required & have)
    missing_req = sorted(required - have)
    matched_pref = sorted(preferred & have)
    missing_pref = sorted(preferred - have)
    extra = sorted(have - required - preferred)

    keywords = extract_keywords(job_text)
    resume_stems = {_stem(t) for t in tokenize(resume_text)}
    matched_kw = [k for k in keywords if keyword_present(k, resume_stems)]
    missing_kw = [k for k in keywords if k not in matched_kw]

    sections = detect_sections(resume_text)
    contact = {
        "email": bool(EMAIL_RE.search(resume_text)),
        "phone": bool(PHONE_RE.search(resume_text)),
        "linkedin": bool(LINKEDIN_RE.search(resume_text)),
        "github": bool(GITHUB_RE.search(resume_text)),
    }
    word_count = len(resume_text.split())
    impact = analyze_impact(resume_text)

    # ---- scoring (0-100)
    def weight(skill, is_required):
        soft = SKILLS[skill][0] == "Business & Soft Skills"
        return (2 if is_required else 1) * (0.5 if soft else 1)

    skill_weight_total = (sum(weight(s, True) for s in required)
                          + sum(weight(s, False) for s in preferred))
    skill_score = _ratio(sum(weight(s, True) for s in matched_req)
                         + sum(weight(s, False) for s in matched_pref), skill_weight_total)
    keyword_score = _ratio(len(matched_kw), len(keywords))

    core_sections = {"Education", "Skills"} | ({"Experience"} if "Experience" in sections else {"Projects"})
    section_score = len(core_sections & set(sections)) / len(core_sections)
    contact_score = (contact["email"] + contact["phone"] + (contact["linkedin"] or contact["github"])) / 3
    length_score = 1.0 if 300 <= word_count <= 900 else 0.6 if 200 <= word_count <= 1200 else 0.3
    format_score = 0.4 * section_score + 0.4 * contact_score + 0.2 * length_score

    st = impact["statements"] or 1
    impact_score = (0.6 * min(1.0, impact["quantified"] / st / 0.4)
                    + 0.4 * min(1.0, impact["action_led"] / st / 0.5))
    impact_score = max(0.0, impact_score - 0.05 * len(impact["weak_phrases"]))

    if skill_weight_total == 0 and keywords:
        weights = {"skills": 0, "keywords": 55, "format": 20, "impact": 25}
    else:
        weights = {"skills": 50, "keywords": 20, "format": 15, "impact": 15}
    parts = {"skills": skill_score, "keywords": keyword_score, "format": format_score, "impact": impact_score}
    breakdown = {k: {"score": round(parts[k] * 100), "weight": w} for k, w in weights.items()}
    score = round(sum(parts[k] * w for k, w in weights.items()))

    result = Result(
        score=score, grade=grade_for(score), breakdown=breakdown,
        matched_required=matched_req, missing_required=missing_req,
        matched_preferred=matched_pref, missing_preferred=missing_pref,
        extra_skills=extra, matched_keywords=matched_kw, missing_keywords=missing_kw,
        sections=sections, contact=contact, word_count=word_count, impact=impact,
    )
    result.suggestions = suggest(result, core_sections)
    return result


def suggest(r, core_sections):
    tips = []
    if r.missing_required:
        tips.append("Add required skills you genuinely have: " + ", ".join(r.missing_required[:8])
                    + ". Mention each in your Skills section and in a project or experience bullet that shows it.")
    if r.missing_keywords:
        tips.append("Mirror the job's language where it's true for you: " + ", ".join(r.missing_keywords[:6]) + ".")
    if r.missing_preferred:
        tips.append("Nice-to-have skills you could highlight or pick up: " + ", ".join(r.missing_preferred[:6]) + ".")
    missing_sections = sorted(core_sections - set(r.sections))
    if missing_sections:
        tips.append("Add clearly labelled section headings for: " + ", ".join(missing_sections)
                    + ". ATS parsers look for standard headings.")
    if not r.contact["email"] or not r.contact["phone"]:
        tips.append("Put your email and phone number at the top of the resume.")
    if not (r.contact["linkedin"] or r.contact["github"]):
        tips.append("Add your LinkedIn and GitHub profile links in the header.")
    st = r.impact["statements"] or 1
    if r.impact["quantified"] / st < 0.3:
        example = r.impact["unquantified_examples"][:1]
        tip = ("Quantify more bullets with numbers — users, %, time saved, ₹ value, dataset size.")
        if example:
            tip += f' For example, add a result to: "{example[0][:90]}"'
        tips.append(tip)
    if r.impact["action_led"] / st < 0.4:
        tips.append("Start bullets with strong action verbs (Built, Designed, Reduced, Led) instead of descriptions.")
    if r.impact["weak_phrases"]:
        tips.append("Replace weak phrases: " + ", ".join(f'"{p}"' for p in r.impact["weak_phrases"][:5]) + ".")
    if r.impact["first_person"] > 2:
        tips.append("Drop first-person words (I, my, me) — resume bullets read better without them.")
    if r.word_count < 300:
        tips.append(f"Your resume is short ({r.word_count} words). Add detail to projects and experience.")
    elif r.word_count > 900:
        tips.append(f"Your resume is long ({r.word_count} words). Trim to the most relevant 1–2 pages.")
    if not tips:
        tips.append("Looks great. Tailor the top summary line to this specific role before applying.")
    return tips
