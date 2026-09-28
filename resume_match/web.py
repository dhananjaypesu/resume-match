"""Flask web UI: upload a resume, paste a job description, get the report."""
import os
import tempfile
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from .analyzer import analyze
from .text import UnsupportedFileError, read_text

ALLOWED = {".pdf", ".docx", ".txt"}
EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def create_app():
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB

    def _resume_text_from_request():
        pasted = request.form.get("resume_text", "").strip()
        upload = request.files.get("resume_file")
        if upload and upload.filename:
            suffix = Path(upload.filename).suffix.lower()
            if suffix not in ALLOWED:
                raise UnsupportedFileError("Please upload a PDF, DOCX or TXT resume.")
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                upload.save(tmp.name)
                path = tmp.name
            try:
                return read_text(path)
            finally:
                os.unlink(path)
        return pasted

    @app.route("/", methods=["GET", "POST"])
    def index():
        result = error = None
        job_text = request.form.get("job_text", "")
        if request.method == "POST":
            try:
                resume_text = _resume_text_from_request()
                if not resume_text.strip():
                    error = "Upload a resume or paste its text. (Scanned PDFs have no readable text.)"
                elif not job_text.strip():
                    error = "Paste the job description."
                else:
                    result = analyze(resume_text, job_text)
            except UnsupportedFileError as exc:
                error = str(exc)
            except Exception:  # corrupt PDFs etc.
                error = "Couldn't read that file. Try exporting your resume again as PDF or DOCX."
        return render_template("index.html", result=result, error=error, job_text=job_text)

    @app.get("/example")
    def example():
        if not (EXAMPLES / "resume.txt").exists():
            return render_template("index.html", result=None, error="Example files aren't bundled with this install.",
                                   job_text="")
        result = analyze((EXAMPLES / "resume.txt").read_text(), (EXAMPLES / "job_description.txt").read_text())
        return render_template("index.html", result=result, error=None,
                               job_text=(EXAMPLES / "job_description.txt").read_text(), example=True)

    @app.post("/api/analyze")
    def api_analyze():
        data = request.get_json(silent=True) or {}
        resume_text, job_text = data.get("resume", ""), data.get("job", "")
        if not resume_text.strip() or not job_text.strip():
            return jsonify(error="Send JSON with non-empty 'resume' and 'job' text fields."), 400
        return jsonify(analyze(resume_text, job_text).to_dict())

    @app.errorhandler(413)
    def too_large(_e):
        return render_template("index.html", result=None, error="File is too large (max 5 MB).", job_text=""), 413

    return app


def main():
    port = int(os.environ.get("PORT", 5000))
    create_app().run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG") == "1")


if __name__ == "__main__":
    main()
