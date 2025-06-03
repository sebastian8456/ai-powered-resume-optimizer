import React, { useState, useEffect } from 'react';
import { getJobPostings, addJobPosting, deleteJobPosting } from '../services/api';

const JobPostingPage = () => {
  const [jobPostings, setJobPostings] = useState([]);
  const [newJobPosting, setNewJobPosting] = useState({ title: '', company: '' });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchJobPostings();
  }, []);

  const fetchJobPostings = async () => {
    try {
      setLoading(true);
      const response = await getJobPostings();
      setJobPostings(response.data);
    } catch (error) {
      console.error('Error fetching job postings:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddJobPosting = async (e) => {
    e.preventDefault();
    try {
      await addJobPosting(newJobPosting);
      setNewJobPosting({ title: '', company: '' });
      fetchJobPostings();
    } catch (error) {
      console.error('Error adding job posting:', error);
    }
  };

  const handleDeleteJobPosting = async (id) => {
    try {
      await deleteJobPosting(id);
      fetchJobPostings();
    } catch (error) {
      console.error('Error deleting job posting:', error);
    }
  };

  return (
    <div>
      <h1>Job Postings</h1>
      
      <form onSubmit={handleAddJobPosting}>
        <h2>Add New Job Posting</h2>
        <input
          type="text"
          value={newJobPosting.title}
          onChange={(e) => setNewJobPosting({ ...newJobPosting, title: e.target.value })}
          placeholder="Job title"
          required
        />
        <input
          type="text"
          value={newJobPosting.company}
          onChange={(e) => setNewJobPosting({ ...newJobPosting, company: e.target.value })}
          placeholder="Company name"
          required
        />
        <button type="submit">Add Job Posting</button>
      </form>

      <h2>Existing Job Postings</h2>
      {loading ? (
        <p>Loading...</p>
      ) : (
        <div>
          {jobPostings.map((job) => (
            <div key={job.id} className="item">
              <h3>{job.title}</h3>
              <p>Company: {job.company}</p>
              <button onClick={() => handleDeleteJobPosting(job.id)}>Delete</button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default JobPostingPage;