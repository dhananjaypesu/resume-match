"""resume-match: score a resume against a job description like an ATS."""
from .analyzer import Result, analyze

__version__ = "0.1.0"
__all__ = ["analyze", "Result", "__version__"]
