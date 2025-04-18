# ai-powered-resume-optimizer
A web app to optimize resumes and recommend job matches.
# AI-Powered Resume Optimizer with Job Matching

### Team Members:
- Sebastian Placzek
- Raumaan Khan
- Jiajie Weng

### Project Overview:
The **AI-Powered Resume Optimizer with Job Matching** is a web application designed to help job seekers improve their resumes and find job roles that best fit their profile. Using **Natural Language Processing (NLP)**, the app analyzes resumes, calculates **ATS (Applicant Tracking System)** scores, suggests improvements, and recommends job listings based on the user’s qualifications.

### Tech Stack:
- **Frontend:** React JS
- **Backend:** Python with Flask
- **Database:** PostgreSQL
- **AI:** Hugging Face (for resume analysis and job matching)
- **Deployment:**
  - Frontend: Vercel
  - Backend: Render

---

### Functional Requirements:
- **Resume Parsing:** Parse resumes and extract relevant data.
- **ATS Score Calculation:** Calculate how well a resume matches Applicant Tracking Systems.
- **Resume Improvement Suggestions:** Provide AI-powered suggestions to improve the resume.
- **Job Matching:** Recommend job listings based on resume data.
- **Resume Export:** Allow users to download optimized resumes.

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
