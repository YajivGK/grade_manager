import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8050';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Students API
export const getStudents = (params) => {
  return api.get('/api/students', { params });
};

export const getClasses = () => {
  return api.get('/api/students/classes');
};

// Subjects API
export const getSubjects = () => {
  return api.get('/api/subjects');
};

// Criteria API
export const getCriteria = (subjectId) => {
  return api.get('/api/criteria', { params: { subject_id: subjectId } });
};

export const createCriterion = (data) => {
  return api.post('/api/criteria', data);
};

export const updateCriterion = (criterionId, data) => {
  return api.put(`/api/criteria/${criterionId}`, data);
};

export const deleteCriterion = (criterionId) => {
  return api.delete(`/api/criteria/${criterionId}`);
};

// Evaluations API
export const getEvaluations = (params) => {
  return api.get('/api/evaluations', { params });
};

export const evaluateStudents = (data) => {
  return api.post('/api/evaluations/evaluate', data);
};

// Reports API
export const generateReport = (data) => {
  return api.post('/api/reports/generate', data);
};

export const listReports = () => {
  return api.get('/api/reports');
};

export const getReportDownloadUrl = (s3Key) => {
  return api.get('/api/reports/download', { params: { s3_key: s3Key } });
};

export default api;

