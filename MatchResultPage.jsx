import { useLocation, useNavigate } from "react-router-dom";

export default function MatchResultPage() {
  const { state } = useLocation();
  const navigate = useNavigate();
  const job = state?.jobPosting;

  if (!job) {
    return (
      <div style={{ padding: 20 }}>
        <p>No job data found.</p>
        <button onClick={() => navigate("/")}>Go Back</button>
      </div>
    );
  }

  const renderBulletList = (text) =>
    text?.split("\n").filter(Boolean).map((item, idx) => (
      <li key={idx}>{item.replace(/^-+\s*/, "")}</li>
    ));

  return (
    <div style={{ maxWidth: 800, margin: "auto", padding: 20 }}>
      <h2>{job.job_title}</h2>
      <p><strong>Position Summary:</strong> {job.position_summary}</p>
      <p><strong>Overview:</strong> {job.overview}</p>

      <h4>Responsibilities</h4>
      <ul>{renderBulletList(job.responsibilities)}</ul>

      <h4>Qualifications</h4>
      <ul>{renderBulletList(job.qualifications)}</ul>

      <h4>Education</h4>
      <p>{job.education}</p>

      <h4>Salary Range</h4>
      <p>{job.salary_range}</p>

      <h4>Benefits</h4>
      <ul>{renderBulletList(job.benefits)}</ul>

      <button onClick={() => navigate("/")}>Back to Resume Form</button>
    </div>
  );
}
