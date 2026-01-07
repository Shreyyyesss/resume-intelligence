"use client";

import { useState } from "react";

export default function Home() {
  const [resume, setResume] = useState<File | null>(null);
  const [jobDescription, setJobDescription] = useState("");
  const [role, setRole] = useState("backend");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const analyzeResume = async () => {
    if (!resume) {
      alert("Upload a resume first");
      return;
    }

    const formData = new FormData();
    formData.append("resume", resume);
    formData.append("job_description", jobDescription);
    formData.append("role", role);

    setLoading(true);
    const res = await fetch("http://localhost:8000/analyze", {
      method: "POST",
      body: formData,
    });
    const data = await res.json();
    setResult(data);
    setLoading(false);
  };

  const atsColor =
    result?.ats_score >= 70
      ? "text-emerald-400"
      : result?.ats_score >= 40
      ? "text-amber-400"
      : "text-rose-400";

  return (
    <main className="min-h-screen bg-slate-900 text-white p-8">
      <div className="max-w-7xl mx-auto space-y-6">

        {/* Header */}
        <div className="bg-slate-800 p-6 rounded-2xl">
          <h1 className="text-3xl font-bold text-indigo-400">
            Resume Intelligence
          </h1>
          <p className="text-slate-400">
            ATS • Salary • Skill Gaps • Career Roadmap
          </p>
        </div>

        {/* INPUT CARD */}
        <div className="bg-slate-800 p-6 rounded-2xl space-y-4">
          <input
            type="file"
            accept=".pdf,.docx"
            onChange={(e) => setResume(e.target.files?.[0] || null)}
            className="file:bg-indigo-500 file:px-4 file:py-2 file:rounded-lg"
          />

          <textarea
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            placeholder="Paste job description..."
            className="w-full h-28 p-3 rounded-lg bg-slate-900 border border-slate-700"
          />

          <select
            value={role}
            onChange={(e) => setRole(e.target.value)}
            className="w-full p-3 rounded-lg bg-slate-900 border border-slate-700"
          >
            <option value="backend">Backend Developer</option>
            <option value="frontend">Frontend Developer</option>
            <option value="fullstack">Full Stack Developer</option>
            <option value="data">Data Analyst</option>
            <option value="ml">ML Engineer</option>
          </select>

          <button
            onClick={analyzeResume}
            className="w-full bg-indigo-500 hover:bg-indigo-600 py-3 rounded-xl font-semibold"
          >
            {loading ? "Analyzing..." : "Analyze Resume"}
          </button>
        </div>

        {/* BENTO GRID */}
        {result && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">

            {/* ATS HERO */}
            <div className="md:col-span-2 bg-slate-800 p-8 rounded-2xl flex flex-col justify-center items-center">
              <p className="text-slate-400 mb-2">ATS Score</p>
              <div className={`text-7xl font-bold ${atsColor}`}>
                {result.ats_score}%
              </div>
              <p className={`mt-2 font-semibold ${atsColor}`}>
                {result.ats_explanation[0]}
              </p>
            </div>

            {/* SALARY */}
            <div className="md:col-span-2 bg-linear-to-br from-emerald-500 to-emerald-700 p-6 rounded-2xl">
              <p className="opacity-90">Estimated CTC</p>
              <p className="text-4xl font-bold">{result.estimated_ctc}</p>
              <p className="opacity-90">
                Next Target: {result.next_target_ctc}
              </p>
            </div>

            {/* MATCHED SKILLS */}
            <div className="md:col-span-2 bg-slate-800 p-6 rounded-2xl">
              <h3 className="text-emerald-400 font-semibold mb-3">
                Matched Skills ({result.jd_gap.matched_keywords.length})
              </h3>
              <div className="flex flex-wrap gap-2">
                {result.jd_gap.matched_keywords.map(
                  (skill: string, i: number) => (
                    <span
                      key={i}
                      className="px-3 py-1 rounded-full bg-emerald-900 text-emerald-300 text-sm"
                    >
                      {skill}
                    </span>
                  )
                )}
              </div>
            </div>

            {/* MISSING SKILLS */}
            <div className="md:col-span-2 bg-slate-800 p-6 rounded-2xl">
              <h3 className="text-rose-400 font-semibold mb-3">
                Missing Skills ({result.jd_gap.missing_keywords.length})
              </h3>
              <div className="flex flex-wrap gap-2">
                {result.jd_gap.missing_keywords.map(
                  (skill: string, i: number) => (
                    <span
                      key={i}
                      className="px-3 py-1 rounded-full bg-rose-900 text-rose-300 text-sm"
                    >
                      {skill}
                    </span>
                  )
                )}
              </div>
            </div>

            {/* ROADMAP */}
            <div className="md:col-span-4 bg-slate-800 p-6 rounded-2xl">
              <h3 className="font-semibold mb-3">
                How to reach {result.next_target_ctc}
              </h3>
              <ul className="grid md:grid-cols-2 gap-2 text-slate-300">
                {result.resume_strength.explanation.map(
                  (item: string, i: number) => (
                    <li key={i}>✔ {item}</li>
                  )
              )}
            </ul>

            </div>

          </div>
        )}
      </div>
    </main>
  );
}
