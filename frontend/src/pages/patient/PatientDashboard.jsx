import { useState, useEffect } from 'react';
import { patientAPI, entryAPI, reportAPI } from '../../services/api';
import '../doctor/Dashboard.css';

const PatientDashboard = () => {
  const [profile, setProfile] = useState(null);
  const [entries, setEntries] = useState([]);
  const [selectedEntry, setSelectedEntry] = useState(null);
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [profileRes, entriesRes] = await Promise.all([
        patientAPI.getProfile(),
        entryAPI.getMyEntries()
      ]);
      setProfile(profileRes.data);
      setEntries(entriesRes.data);
    } catch {
      setError('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectEntry = async (entry) => {
    setSelectedEntry(entry);
    try {
      const response = await reportAPI.getForEntry(entry.id);
      setReports(response.data);
    } catch {
      setReports([]);
    }
  };

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleString();
  };

  if (loading) return <div className="dashboard-loading">Loading...</div>;
  if (error && !profile) return <div className="dashboard-error">{error}</div>;

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <h1>Patient Dashboard</h1>
        <p>Welcome back, {profile?.user?.username}</p>
      </div>

      {error && <div className="error-message">{error}</div>}

      <div className="dashboard-grid">
        {/* Profile Card */}
        <div className="dashboard-card profile-card">
          <div className="card-header">
            <h2>Profile Overview</h2>
          </div>
          <div className="card-content">
            <div className="profile-info">
              <div className="info-row">
                <span className="label">Email:</span>
                <span className="value">{profile?.user?.email}</span>
              </div>
              <div className="info-row">
                <span className="label">Age:</span>
                <span className="value">{profile?.age || 'N/A'}</span>
              </div>
              <div className="info-row">
                <span className="label">Gender:</span>
                <span className="value">{profile?.gender || 'N/A'}</span>
              </div>
              <div className="info-row">
                <span className="label">Phone:</span>
                <span className="value">{profile?.phone_number || 'N/A'}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Entries List */}
        <div className="dashboard-card entries-card">
          <div className="card-header">
            <h2>My Entries ({entries.length})</h2>
          </div>
          <div className="card-content">
            {entries.length === 0 ? (
              <p className="no-data">No entries yet. Create your first entry!</p>
            ) : (
              <div className="entries-list">
                {entries.map((entry) => (
                  <div
                    key={entry.id}
                    className={`entry-item ${selectedEntry?.id === entry.id ? 'selected' : ''}`}
                    onClick={() => handleSelectEntry(entry)}
                  >
                    <div className="entry-header">
                      <span className="entry-doctor">Dr. {entry.doctor_name || 'Unknown'}</span>
                      <span className="entry-time">{formatDate(entry.time)}</span>
                    </div>
                    <div className="entry-details">
                      {entry.notes && <p className="entry-notes">{entry.notes.substring(0, 50)}...</p>}
                      {entry.amount_voided && <span>Amount: {entry.amount_voided}ml</span>}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Entry Details & Reports */}
        {selectedEntry && (
          <div className="dashboard-card reports-card">
            <div className="card-header">
              <h2>Entry Details & Reports</h2>
            </div>
            <div className="card-content">
              <div className="entry-full-details">
                <p><strong>Time:</strong> {formatDate(selectedEntry.time)}</p>
                {selectedEntry.video_url && (
                  <p><strong>Video:</strong> <a href={selectedEntry.video_url} target="_blank" rel="noopener noreferrer">View Video</a></p>
                )}
                {selectedEntry.amount_voided && <p><strong>Amount Voided:</strong> {selectedEntry.amount_voided}ml</p>}
                {selectedEntry.diameter_of_commode && <p><strong>Diameter:</strong> {selectedEntry.diameter_of_commode}cm</p>}
                {selectedEntry.notes && <p><strong>Notes:</strong> {selectedEntry.notes}</p>}
              </div>

              <div className="reports-section">
                <div className="reports-header">
                  <h3>Doctor Reports ({reports.length})</h3>
                </div>
                
                {reports.length === 0 ? (
                  <p className="no-data">No reports from the doctor yet</p>
                ) : (
                  <div className="reports-list">
                    {reports.map((report) => (
                      <div key={report.id} className="report-item">
                        <div className="report-header">
                          <span className="report-type">{report.report_type}</span>
                        </div>
                        <h4>{report.title}</h4>
                        {report.description && <p>{report.description}</p>}
                        {report.report_url && (
                          <a href={report.report_url} target="_blank" rel="noopener noreferrer">View Document</a>
                        )}
                        <span className="report-date">{formatDate(report.created_at)}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PatientDashboard;
