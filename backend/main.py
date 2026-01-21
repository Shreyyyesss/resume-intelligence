# =========================
# IMPORTS
# =========================
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import pdfplumber
import docx
import re
from collections import Counter

# =========================
# APP SETUP
# =========================
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# CONSTANTS
# =========================
BASELINE_ATS_SCORE = 25

ROLES = {
    "backend": "Backend Developer",
    "frontend": "Frontend Developer",
    "fullstack": "Full Stack Developer",
    "data": "Data Analyst",
    "ml": "Machine Learning Engineer",
    "devops": "DevOps Engineer",
}

CORE_SKILLS = {
    "backend": {"python", "sql"},
    "frontend": {"javascript", "react"},
    "fullstack": {"javascript", "python"},
    "data": {"python", "sql"},
    "ml": {"python"},
    "devops": {"aws", "docker"},
}

DOMAIN_SIGNALS = {
    "backend": {"python", "java", "project", "database", "api"},
    "frontend": {"javascript", "react", "html", "css", "ui"},
    "fullstack": {"python", "javascript", "project", "api"},
    "data": {"python", "data", "analysis", "sql"},
    "ml": {"python", "model", "training"},
    "devops": {"aws", "docker", "ci", "cd"},
}

SKILL_WEIGHTS = {
    "python": 5,
    "sql": 5,
    "javascript": 5,
    "react": 4,
    "aws": 4,
    "docker": 3,
    "fastapi": 3,
    "flask": 2,
    "node": 3,
    "git": 2,
    "kubernetes": 3,
    "pandas": 3,
    "numpy": 2,
}

SKILL_SYNONYMS = {
    "python": ["python"],
    "sql": ["sql", "mysql", "postgres", "postgresql"],
    "javascript": ["javascript", "js"],
    "react": ["react", "reactjs"],
    "aws": ["aws", "amazon web services"],
    "docker": ["docker"],
    "fastapi": ["fastapi"],
    "flask": ["flask"],
    "node": ["node", "nodejs"],
    "git": ["git"],
    "kubernetes": ["kubernetes", "k8s"],
    "pandas": ["pandas"],
    "numpy": ["numpy"],
}

# =========================
# RESUME TEXT EXTRACTION
# =========================
def extract_resume_text(file: UploadFile):
    text = ""
    if file.filename.endswith(".pdf"):
        with pdfplumber.open(file.file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
    elif file.filename.endswith(".docx"):
        document = docx.Document(file.file)
        for para in document.paragraphs:
            text += para.text + " "
    return text.lower()

# =========================
# SKILL FREQUENCY EXTRACTION
# =========================
def extract_skill_frequencies(text: str):
    freq = Counter()
    text = text.lower()

    for skill, variants in SKILL_SYNONYMS.items():
        for v in variants:
            matches = re.findall(rf"\b{re.escape(v)}\b", text)
            freq[skill] += len(matches)

    return freq

# =========================
# DOMAIN SIGNAL DETECTION
# =========================
def detect_domain_signal(text: str, role: str):
    signals = DOMAIN_SIGNALS.get(role, set())
    count = 0
    for s in signals:
        if re.search(rf"\b{s}\b", text):
            count += 1
    return count

# =========================
# ATS SCORE CALCULATION (TUNED)
# =========================
def calculate_ats_score(resume_text: str, jd_text: str, role: str):
    resume_freq = extract_skill_frequencies(resume_text)
    jd_freq = extract_skill_frequencies(jd_text)

    jd_skills = {k for k, v in jd_freq.items() if v > 0}
    resume_skills = {k for k, v in resume_freq.items() if v > 0}

    reasons = []

    # ---- Generic / weak JD fallback ----
    if len(jd_skills) < 2:
        domain_boost = detect_domain_signal(resume_text, role)
        score = BASELINE_ATS_SCORE + (domain_boost * 5)
        score = min(score, 50)

        reasons.append("Job description too generic for precise ATS matching")
        reasons.append("Score based on general role relevance")

        return score, list(resume_skills), [], reasons

    # ---- Weighted matching ----
    total_weight = 0
    matched_weight = 0

    for skill in jd_skills:
        weight = SKILL_WEIGHTS.get(skill, 1)
        total_weight += weight

        if resume_freq[skill] > 0:
            # tuned confidence saturation (student-friendly)
            confidence = min(resume_freq[skill] / 2, 1.0)
            matched_weight += weight * confidence

    score = int((matched_weight / total_weight) * 100)

    # ---- Core skill penalty (softened) ----
    missing_core = CORE_SKILLS.get(role, set()) - resume_skills
    score -= len(missing_core) * 8

    # ---- Domain signal boost ----
    score += detect_domain_signal(resume_text, role) * 4

    # ---- Baseline protection ----
    score = max(score, BASELINE_ATS_SCORE)
    score = min(score, 100)

    if missing_core:
        reasons.append(f"Missing core skills: {', '.join(missing_core)}")

    if score >= 70:
        reasons.append("Strong alignment with job description")
    elif score >= 40:
        reasons.append("Partial alignment with job description")
    else:
        reasons.append("Weak alignment with job description")

    return (
        score,
        list(resume_skills & jd_skills),
        list(jd_skills - resume_skills),
        reasons
    )

# =========================
# RESUME STRENGTH (0–10)
# =========================
def resume_strength_score(text: str):
    score = 0
    reasons = []

    projects = len(re.findall(r"\bproject\b", text))
    if projects >= 3:
        score += 3
        reasons.append("Strong project portfolio")
    elif projects >= 1:
        score += 1
        reasons.append("Some project experience")

    if re.search(r"\d+%|\d+\+|\d+k|\d+\s+users", text):
        score += 3
        reasons.append("Quantified impact present")

    if "intern" in text or "experience" in text:
        score += 2
        reasons.append("Real-world experience mentioned")

    if len(extract_skill_frequencies(text)) >= 6:
        score += 2
        reasons.append("Good skill breadth")

    return min(score, 10), reasons

# =========================
# CTC ESTIMATION
# =========================
def estimate_ctc(strength: int):
    if strength <= 3:
        return "₹3–5 LPA", "₹5–8 LPA"
    elif strength <= 6:
        return "₹5–8 LPA", "₹8–12 LPA"
    else:
        return "₹8–12 LPA", "₹12+ LPA"

# =========================
# FINAL API
# =========================
@app.post("/analyze")
async def analyze_resume(
    resume: UploadFile = File(...),
    job_description: str = Form(...),
    role: str = Form("backend"),
):
    resume_text = extract_resume_text(resume)

    ats_score, matched, missing, ats_expl = calculate_ats_score(
        resume_text, job_description, role
    )

    strength, strength_reasons = resume_strength_score(resume_text)
    ctc, next_ctc = estimate_ctc(strength)

    return {
        "role": ROLES.get(role, role),
        "ats_score": ats_score,
        "ats_explanation": ats_expl,
        "jd_gap": {
            "matched_keywords": matched,
            "missing_keywords": missing,
        },
        "resume_strength": {
            "score": strength,
            "explanation": strength_reasons,
        },
        "estimated_ctc": ctc,
        "next_target_ctc": next_ctc,
    }
