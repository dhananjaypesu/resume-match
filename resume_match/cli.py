"""Command-line interface: resume-match RESUME JOB [options]."""
import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .analyzer import analyze
from .report import render_markdown, render_terminal
from .text import UnsupportedFileError, read_text


def build_parser():
    p = argparse.ArgumentParser(
        prog="resume-match",
        description="Score a resume against a job description like an ATS, and get concrete fixes.",
    )
    p.add_argument("resume", type=Path, help="resume file (.pdf, .docx or .txt)")
    p.add_argument("job", help="job description file (.txt/.pdf/.docx), or '-' to read it from stdin")
    fmt = p.add_mutually_exclusive_group()
    fmt.add_argument("--json", action="store_true", help="print the full result as JSON")
    fmt.add_argument("--markdown", action="store_true", help="print a Markdown report")
    p.add_argument("-o", "--output", type=Path, help="write the report to a file instead of the terminal")
    p.add_argument("--min-score", type=int, metavar="N",
                   help="exit with code 1 if the score is below N (handy in scripts)")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        resume_text = read_text(args.resume)
        job_text = sys.stdin.read() if args.job == "-" else read_text(Path(args.job))
    except FileNotFoundError as exc:
        print(f"error: file not found: {exc.filename}", file=sys.stderr)
        return 2
    except UnsupportedFileError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if not resume_text.strip():
        print("error: no text could be read from the resume. If it's a scanned PDF, export it as text-based PDF or DOCX.",
              file=sys.stderr)
        return 2
    if not job_text.strip():
        print("error: the job description is empty.", file=sys.stderr)
        return 2

    result = analyze(resume_text, job_text)

    if args.json:
        text = json.dumps(result.to_dict(), indent=2, ensure_ascii=False) + "\n"
    elif args.markdown or (args.output and args.output.suffix.lower() == ".md"):
        text = render_markdown(result)
    else:
        text = None

    if args.output:
        if text is None:
            import io
            buf = io.StringIO()
            render_terminal(result, buf)
            text = buf.getvalue()
        args.output.write_text(text, encoding="utf-8")
        print(f"Report written to {args.output}  (score {result.score}/100)")
    elif text is not None:
        sys.stdout.write(text)
    else:
        render_terminal(result)

    if args.min_score is not None and result.score < args.min_score:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
