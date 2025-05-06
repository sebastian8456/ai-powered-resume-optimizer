import axios from 'axios';

// Update this to match your FastAPI server URL
const API_BASE_URL = 'http://localhost:8000'; 

const api = axios.create({
  baseURL: API_BASE_URL,
});

// Resume endpoints
export const getResumes = () => api.get('/resumes');
export const addResume = (resume) => api.post('/resume', resume);
export const deleteResume = (id) => api.delete(`/resume?resume_id=${id}`);
export const generateResume = () => api.get('/create-resume');

// Suggestion endpoints
export const getSuggestions = () => api.get('/suggestions');
export const addSuggestion = (suggestion) => api.post('/suggestion', suggestion);
export const deleteSuggestion = (id) => api.delete(`/suggestion?suggestion_id=${id}`);

// Job Posting endpoints
export const getJobPostings = () => api.get('/job-postings');
export const addJobPosting = (jobPosting) => api.post('/job-posting', jobPosting);
export const deleteJobPosting = (id) => api.delete(`/job-posting?job_posting_id=${id}`);

export default api;