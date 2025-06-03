import React, { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useResume } from './ResumeContext';

export default function MatchResultPage() {
  const { resumeText, setResumeText } = useResume();
  const [jobs, setJobs] = useState([]);
  const [keywords, setKeywords] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showResults, setShowResults] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();


  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setShowResults(false);
    try {
      const response = await fetch("http://127.0.0.1:8000/match-jobs/?save_results=true", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ text: resumeText }),
      });


      if (!response.ok) {
        throw new Error("Network response was not ok");
      }

      const data = await response.json();
      setJobs(Array.isArray(data.jobs) ? data.jobs : [data.jobs]);
      setKeywords(data.keywords);
      setShowResults(true);
    } catch (err) {
      setError("Failed to fetch jobs.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (location.state && location.state.jobPosting) {
      const data = location.state.jobPosting;
      setJobs(Array.isArray(data.jobs) ? data.jobs : [data.jobs]);
      setKeywords(data.keywords || []);
      setShowResults(true);
    } else {

      navigate("/");
    }
  }, [location, navigate]);

  const resetForm = () => {
    navigate("/");
  };


  return (
    <div style={{ maxWidth: "900px", margin: "2rem auto", padding: "1rem", fontFamily: "Segoe UI, sans-serif" }}>
      {!showResults ? (
        <div
          style={{
            maxWidth: "700px",
            margin: "3rem auto",
            padding: "2rem",
            backgroundColor: "#fdfdfd",
            borderRadius: "12px",
            boxShadow: "0 2px 10px rgba(0,0,0,0.1)",
          }}
        >
          <h2 style={{ marginBottom: "1.5rem", fontSize: "1.8rem", fontWeight: 600 }}>
            Match Me Job Postings
          </h2>
          <form onSubmit={handleSubmit}>
            <textarea
              value={resumeText}
              onChange={(e) => setResumeText(e.target.value)}
              placeholder="Paste your resume here..."
              rows={12}
              style={{
                width: "100%",
                fontSize: "15px",
                padding: "12px",
                border: "1px solid #ccc",
                borderRadius: "8px",
                marginBottom: "1rem",
                resize: "vertical",
                fontFamily: "inherit",
              }}
            />
            <button
              type="submit"
              disabled={loading || !resumeText.trim()}
              style={{
                padding: "12px 24px",
                fontSize: "16px",
                backgroundColor: loading ? "#aaa" : "#007bff",
                color: "#fff",
                border: "none",
                borderRadius: "6px",
                cursor: loading ? "not-allowed" : "pointer",
                transition: "background-color 0.2s ease-in-out",
              }}
            >
              {loading ? "Matching..." : "Find Matching Jobs"}
            </button>
          </form>
          {error && (
            <div
              style={{
                marginTop: "1rem",
                padding: "0.75rem 1rem",
                backgroundColor: "#ffe6e6",
                border: "1px solid #cc0000",
                color: "#cc0000",
                borderRadius: "6px",
              }}
            >
              Error: {error}
            </div>
          )}
        </div>
      ) : (
        <>
          <h2 style={{ fontSize: "1.8rem", marginBottom: "1.5rem" }}>Matched Job Postings</h2>
          {jobs.length === 0 ? (
            <p>No job matches found.</p>
          ) : (
            jobs.map((job, idx) => (
              <div
                key={idx}
                style={{
                  backgroundColor: "#fff",
                  borderRadius: "10px",
                  padding: "1.5rem",
                  boxShadow: "0 2px 10px rgba(0,0,0,0.08)",
                  marginBottom: "1.5rem",
                }}
              >
                <h3 style={{ marginBottom: "0.5rem", fontSize: "1.4rem", fontWeight: "bold" }}>
                  {job?.title || "Untitled Job"}
                </h3>
                <p><strong>🏢 Organization:</strong> {job?.organization || "Information not available"}</p>
                <p><strong>📍 Location:</strong> {job?.location || "Information not available"}</p>
                {job?.url ? (
                  <a
                    href={job.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{
                      display: "inline-block",
                      marginTop: "0.5rem",
                      padding: "0.5rem 1rem",
                      backgroundColor: "#007bff",
                      color: "#fff",
                      borderRadius: "6px",
                      textDecoration: "none",
                      fontWeight: "bold",
                    }}
                  >
                    View Job Posting →
                  </a>
                ) : (
                  <p>No link available</p>
                )}
              </div>
            ))
          )}
          <div style={{ textAlign: "center", marginTop: "2rem" }}>
            <button
              onClick={resetForm}
              style={{
                padding: "12px 24px",
                backgroundColor: "#6c63ff",
                color: "#fff",
                border: "none",
                borderRadius: "8px",
                fontSize: "16px",
                cursor: "pointer",
              }}
            >
              ← Back to Resume Form
            </button>
          </div>
        </>
      )}
    </div>
  );
}

