import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function JobMatcher() {
  const [resumeText, setResumeText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleSubmit = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch("http://127.0.0.1:8000/match-me-job-posting", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: resumeText }),
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || "Failed to fetch job posting");
      }

      const data = await response.json();
      navigate("/match-result", { state: { jobPosting: data } });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        maxWidth: 800,
        margin: "auto",
        padding: 20,
        fontFamily: "Arial, sans-serif",
      }}
    >
      <h2>Match Me Job Postings</h2>

      <textarea
        placeholder="Paste your resume text here..."
        rows={10}
        value={resumeText}
        onChange={(e) => setResumeText(e.target.value)}
        style={{ width: "100%", fontSize: 16, padding: 10, marginBottom: 10 }}
      />

      <button
        onClick={handleSubmit}
        disabled={loading || !resumeText.trim()}
        style={{ padding: "10px 20px", fontSize: 16, cursor: "pointer" }}
      >
        {loading ? "Matching..." : "Match Me Job Postings"}
      </button>

      {error && <p style={{ color: "red", marginTop: 10 }}>Error: {error}</p>}
    </div>
  );
}
