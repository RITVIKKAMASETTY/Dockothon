import axios from 'axios';

const API_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth API
export const authAPI = {
  signupDoctor: (data) => api.post('/auth/signup/doctor', data),
  signupPatient: (data) => api.post('/auth/signup/patient', data),
  signin: (data) => api.post('/auth/signin', data),
};

// Doctor API
export const doctorAPI = {
  getProfile: () => api.get('/doctor/me'),
  updateProfile: (data) => api.put('/doctor/me', data),
  toggleAutoAccept: (autoAccept) => api.patch(`/doctor/me/auto-accept?auto_accept=${autoAccept}`),
  getDoctorById: (id) => api.get(`/doctor/${id}`),
  listDoctors: (params) => api.get('/doctor/', { params }),
};

// Patient API
export const patientAPI = {
  getProfile: () => api.get('/patient/me'),
  updateProfile: (data) => api.put('/patient/me', data),
  deleteAccount: () => api.delete('/patient/me'),
};

// Entry API
export const entryAPI = {
  create: (data) => {
    // If data is FormData, we need to remove the Content-Type header
    // so axios can set it automatically with the correct boundary
    if (data instanceof FormData) {
      return api.post('/entry/', data, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
    }
    return api.post('/entry/', data);
  },
  getMyEntries: () => api.get('/entry/my-entries'),
  getEntry: (id) => api.get(`/entry/${id}`),
};

// Report API
export const reportAPI = {
  create: (data) => api.post('/report/', data),
  getForEntry: (entryId) => api.get(`/report/entry/${entryId}`),
  delete: (id) => api.delete(`/report/${id}`),
  generate: (entryId) => api.post(`/report/generate/${entryId}`),
};

// Analysis API
export const analysisAPI = {
  createOrUpdate: (data) => api.post('/analysis/', data),
  getForEntry: (entryId) => api.get(`/analysis/entry/${entryId}`),
  delete: (entryId) => api.delete(`/analysis/entry/${entryId}`),
  runAnalysis: (entryId) => api.post(`/analysis/run/${entryId}`),
};

// Chat API
export const chatAPI = {
  sendMessage: (entryId, message, history = []) => 
    api.post('/chat/report', { entry_id: entryId, message, history }),
};

export default api;
