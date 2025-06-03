import React, { useState, useEffect } from 'react';
import { getResumes, addResume, deleteResume, generateResume } from '../services/api';

const ResumePage = () => {
  const [resumes, setResumes] = useState([]);
  const [newResume, setNewResume] = useState({ text: '' });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchResumes();
  }, []);

  const fetchResumes = async () => {
    try {
      setLoading(true);
      const response = await getResumes();
      setResumes(response.data);
    } catch (error) {
      console.error('Error fetching resumes:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddResume = async (e) => {
    e.preventDefault();
    try {
      await addResume(newResume);
      setNewResume({ text: '' });
      fetchResumes();
    } catch (error) {
      console.error('Error adding resume:', error);
    }
  };

  const handleDeleteResume = async (id) => {
    try {
      await deleteResume(id);
      fetchResumes();
    } catch (error) {
      console.error('Error deleting resume:', error);
    }
  };

  const handleGenerateResume = async () => {
    try {
      const response = await generateResume();
      alert(`Generated resume: ${JSON.stringify(response.data)}`);
    } catch (error) {
      console.error('Error generating resume:', error);
    }
  };

  return (
    <div>
      <h1>Resumes</h1>
      
      <form onSubmit={handleAddResume}>
        <h2>Add New Resume</h2>
        <textarea
          value={newResume.text}
          onChange={(e) => setNewResume({ text: e.target.value })}
          placeholder="Enter resume text"
          required
        />
        <button type="submit">Add Resume</button>
      </form>

      <button onClick={handleGenerateResume}>Generate Resume with AI</button>

      <h2>Existing Resumes</h2>
      {loading ? (
        <p>Loading...</p>
      ) : (
        <div>
          {resumes.map((resume) => (
            <div key={resume.id} className="item">
              <p>{resume.text}</p>
              <button onClick={() => handleDeleteResume(resume.id)}>Delete</button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ResumePage;