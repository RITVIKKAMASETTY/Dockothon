import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { doctorAPI, entryAPI } from '../../services/api';
import '../doctor/Dashboard.css';
import './CreateEntry.css';

const CreateEntry = () => {
  const [doctors, setDoctors] = useState([]);
  const [filteredDoctors, setFilteredDoctors] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDoctor, setSelectedDoctor] = useState(null);
  const [showDropdown, setShowDropdown] = useState(false);
  const [formData, setFormData] = useState({
    top_view_url: '',
    bottom_view_url: '',
    amount_voided: '',
    diameter_of_commode: '',
    notes: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    fetchDoctors();
  }, []);

  useEffect(() => {
    if (searchTerm) {
      const filtered = doctors.filter(
        (doc) =>
          doc.user.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
          doc.specialization.toLowerCase().includes(searchTerm.toLowerCase()) ||
          doc.hospital.toLowerCase().includes(searchTerm.toLowerCase())
      );
      setFilteredDoctors(filtered);
    } else {
      setFilteredDoctors(doctors);
    }
  }, [searchTerm, doctors]);

  const fetchDoctors = async () => {
    try {
      const response = await doctorAPI.listDoctors({});
      setDoctors(response.data);
      setFilteredDoctors(response.data);
    } catch {
      setError('Failed to load doctors');
    }
  };

  const handleSelectDoctor = (doctor) => {
    setSelectedDoctor(doctor);
    setSearchTerm(`Dr. ${doctor.user.username} - ${doctor.specialization}`);
    setShowDropdown(false);
  };

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!selectedDoctor) {
      setError('Please select a doctor');
      return;
    }

    setLoading(true);

    try {
      const data = {
        doctor_id: selectedDoctor.id,
        top_view_url: formData.top_view_url || null,
        bottom_view_url: formData.bottom_view_url || null,
        amount_voided: formData.amount_voided ? parseFloat(formData.amount_voided) : null,
        diameter_of_commode: formData.diameter_of_commode ? parseFloat(formData.diameter_of_commode) : null,
        notes: formData.notes || null,
      };

      await entryAPI.create(data);
      setSuccess('Entry created successfully! The doctor has been notified.');
      setTimeout(() => navigate('/patient/dashboard'), 2000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create entry');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <h1>Create New Entry</h1>
        <button onClick={() => navigate('/patient/dashboard')} className="back-btn">
          ← Back to Dashboard
        </button>
      </div>

      <div className="profile-edit-card create-entry-card">
        {error && <div className="error-message">{error}</div>}
        {success && <div className="success-message">{success}</div>}

        <form onSubmit={handleSubmit} className="profile-form">
          {/* Doctor Selection with Search */}
          <div className="form-group doctor-search-container">
            <label>Select Doctor *</label>
            <div className="search-dropdown">
              <input
                type="text"
                placeholder="Search by name, specialization, or hospital..."
                value={searchTerm}
                onChange={(e) => {
                  setSearchTerm(e.target.value);
                  setShowDropdown(true);
                  if (!e.target.value) setSelectedDoctor(null);
                }}
                onFocus={() => setShowDropdown(true)}
                className="search-input"
              />
              {showDropdown && filteredDoctors.length > 0 && (
                <div className="dropdown-list">
                  {filteredDoctors.map((doctor) => (
                    <div
                      key={doctor.id}
                      className={`dropdown-item ${selectedDoctor?.id === doctor.id ? 'selected' : ''}`}
                      onClick={() => handleSelectDoctor(doctor)}
                    >
                      <div className="doctor-info">
                        <span className="doctor-name">Dr. {doctor.user.username}</span>
                        <span className="doctor-spec">{doctor.specialization}</span>
                      </div>
                      <div className="doctor-meta">
                        <span>{doctor.hospital}</span>
                        {doctor.auto_accept && (
                          <span className="auto-accept-badge">Auto Accept</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
              {showDropdown && filteredDoctors.length === 0 && searchTerm && (
                <div className="dropdown-list">
                  <div className="dropdown-item no-results">No doctors found</div>
                </div>
              )}
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Top View URL (optional)</label>
              <input
                type="url"
                name="top_view_url"
                value={formData.top_view_url}
                onChange={handleChange}
                placeholder="https://example.com/top-view"
              />
            </div>
            <div className="form-group">
              <label>Bottom View URL (optional)</label>
              <input
                type="url"
                name="bottom_view_url"
                value={formData.bottom_view_url}
                onChange={handleChange}
                placeholder="https://example.com/bottom-view"
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Amount Voided (ml)</label>
              <input
                type="number"
                name="amount_voided"
                value={formData.amount_voided}
                onChange={handleChange}
                placeholder="e.g., 250"
                step="0.1"
              />
            </div>
            <div className="form-group">
              <label>Diameter of Commode (cm)</label>
              <input
                type="number"
                name="diameter_of_commode"
                value={formData.diameter_of_commode}
                onChange={handleChange}
                placeholder="e.g., 30"
                step="0.1"
              />
            </div>
          </div>

          <div className="form-group">
            <label>Notes</label>
            <textarea
              name="notes"
              value={formData.notes}
              onChange={handleChange}
              placeholder="Any additional notes or observations..."
              rows="4"
            />
          </div>

          <button type="submit" className="save-btn" disabled={loading || !selectedDoctor}>
            {loading ? 'Creating Entry...' : 'Create Entry'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default CreateEntry;
