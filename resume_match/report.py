"""Render a Result for the terminal or as Markdown."""
import os
import sys


def _supports_color(stream):
    return hasattr(stream, "isatty") and stream.isatty() and os.environ.get("NO_COLOR") is None


class _Style:
    def __init__(self, enabled):
        self.enabled = enabled

    def _wrap(self, code, text):
        return f"\033[{code}m{text}\033[0m" if self.enabled else text

    def bold(self, t): return self._wrap("1", t)
    def dim(self, t): return self._wrap("2", t)
    def green(self, t): return self._wrap("32", t)
    def yellow(self, t): return self._wrap("33", t)
    def red(self, t): return self._wrap("31", t)
    def cyan(self, t): return self._wrap("36", t)


def _bar(pct, width=24):
    filled = round(width * pct / 100)
    return "█" * filled + "░" * (width - filled)


def _score_color(style, score):
    if score >= 70:
        return style.green
    if score >= 50:
        return style.yellow
    return style.red


def render_terminal(r, stream=None):
    stream = stream or sys.stdout
    s = _Style(_supports_color(stream))
    color = _score_color(s, r.score)
    out = []

    out.append("")
    out.append(s.bold("  RESUME MATCH REPORT"))
    out.append(f"  {color(s.bold(f'{r.score}/100'))}  {color(r.grade)}")
    out.append(f"  {color(_bar(r.score, 40))}")
    out.append("")

    names = {"skills": "Skills match", "keywords": "Job keywords", "format": "Format & contact", "impact": "Impact & wording"}
    for key, part in r.breakdown.items():
        if part["weight"] == 0:
            continue
        c = _score_color(s, part["score"])
        weight = s.dim(f"weight {part['weight']}")
        out.append(f"  {names[key]:<18} {c(_bar(part['score']))} {part['score']:>3}%  {weight}")
    out.append("")

    def skill_line(label, items, fmt):
        if items:
            out.append(f"  {s.bold(label)}")
            out.append("    " + ", ".join(fmt(i) for i in items))

    skill_line("✔ Required skills you have", r.matched_required, s.green)
    skill_line("✘ Required skills missing", r.missing_required, s.red)
    skill_line("✔ Nice-to-have skills you have", r.matched_preferred, s.green)
    skill_line("○ Nice-to-have skills missing", r.missing_preferred, s.yellow)
    skill_line("✔ Job keywords found", r.matched_keywords, s.green)
    skill_line("✘ Job keywords missing", r.missing_keywords, s.yellow)
    out.append("")

    contact = "  ".join((s.green("✔ ") if ok else s.red("✘ ")) + k for k, ok in r.contact.items())
    out.append(f"  {s.bold('Contact')}   {contact}")
    out.append(f"  {s.bold('Sections')}  {', '.join(r.sections) or s.red('none detected')}")
    imp = r.impact
    out.append(f"  {s.bold('Bullets')}   {imp['quantified']}/{imp['statements']} quantified, "
               f"{imp['action_led']}/{imp['statements']} start with an action verb, {r.word_count} words")
    out.append("")

    out.append(s.bold("  How to improve"))
    for i, tip in enumerate(r.suggestions, 1):
        out.append(f"  {s.cyan(str(i) + '.')} {tip}")
    out.append("")
    stream.write("\n".join(out) + "\n")


def render_markdown(r):
    lines = [
        "# Resume Match Report",
        "",
        f"**Score: {r.score}/100 — {r.grade}**",
        "",
        "| Area | Score | Weight |",
        "|---|---|---|",
    ]
    names = {"skills": "Skills match", "keywords": "Job keywords", "format": "Format & contact", "impact": "Impact & wording"}
    for key, part in r.breakdown.items():
        if part["weight"]:
            lines.append(f"| {names[key]} | {part['score']}% | {part['weight']} |")

    def section(title, items):
        lines.extend(["", f"### {title}", "", ", ".join(items) if items else "_None_"])

    section("Required skills you have", r.matched_required)
    section("Required skills missing", r.missing_required)
    section("Nice-to-have skills you have", r.matched_preferred)
    section("Nice-to-have skills missing", r.missing_preferred)
    section("Job keywords missing", r.missing_keywords)
    lines.extend(["", "### How to improve", ""])
    lines.extend(f"{i}. {t}" for i, t in enumerate(r.suggestions, 1))
    return "\n".join(lines) + "\n"
