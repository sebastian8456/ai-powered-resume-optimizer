# ai-powered-resume-optimizer
A web app to optimize resumes and recommend job matches.
# AI-Powered Resume Optimizer with Job Matching

### Team Members:
- Sebastian Placzek
- Raumaan Khan
- Jiajie Weng
- Pahul Mal

### Project Overview:
The **AI-Powered Resume Optimizer with Job Matching** is a web application designed to help job seekers improve their resumes and find job roles that best fit their profile. Using **Natural Language Processing (NLP)**, the app analyzes resumes, calculates **ATS (Applicant Tracking System)** scores, suggests improvements, and recommends job listings based on the user’s qualifications.

### Tech Stack:
- **Frontend:** React JS
- **Backend:** Python with FastAPI
- **Database:** PostgreSQL
- **AI:** OpenAI (for resume analysis and job matching)
- **Deployment:**
  - Frontend: Vercel
  - Backend: Render

---

### Functional Requirements:
- **Resume Uploading:** Users should be able to upload their resume.
- **ATS Score Calculation:** Users should get an ATS score associated with their resume.
- **Resume Improvement Suggestions:** Users should get AI-powered suggestions to improve their resume.
- **Job Matching:** Users should be recommended job listings based on resume data.
- **Resume Export:** Users should be able to download and save optimized resumes.

### Non-Functional Requirements:
- **Performance:** The app should return resume analysis and job recommendations in under 3 seconds.
- **Security:** Use AES-256 encryption to securely store and transmit sensitive data.
- **Scalability:** Handle up to 100 concurrent users without performance issues.
- **Availability:** Maintain high uptime with minimal downtime.
- **Usability:** Provide an intuitive and accessible user interface.

---

#### Prerequisites:
Make sure you have the following installed:
- **React.js** (for frontend)
- **Python 3.x** (for backend)
- **PostgreSQL** (for the database)
