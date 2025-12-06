import { useState, useEffect } from 'react';
import { entryAPI, reportAPI, doctorAPI, analysisAPI } from '../../services/api';
import './Dashboard.css';

const DoctorDashboard = () => {
  const [profile, setProfile] = useState(null);
  const [entries, setEntries] = useState([]);
  const [selectedEntry, setSelectedEntry] = useState(null);
  const [reports, setReports] = useState([]);
  const [analysis, setAnalysis] = useState(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [showReportModal, setShowReportModal] = useState(false);
  const [reportForm, setReportForm] = useState({
    report_type: 'diagnosis',
    title: '',
    description: '',
    report_url: '',
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [profileRes, entriesRes] = await Promise.all([
        doctorAPI.getProfile(),
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
    setAnalysis(null);
    try {
      const [reportsRes] = await Promise.all([
        reportAPI.getForEntry(entry.id)
      ]);
      setReports(reportsRes.data);
      
      // Try to get analysis (may not exist)
      try {
        const analysisRes = await analysisAPI.getForEntry(entry.id);
        setAnalysis(analysisRes.data);
      } catch {
        setAnalysis(null);
      }
    } catch {
      setReports([]);
    }
  };

  const toggleAutoAccept = async () => {
    try {
      const response = await doctorAPI.toggleAutoAccept(!profile.auto_accept);
      setProfile(response.data);
    } catch {
      setError('Failed to update auto-accept setting');
    }
  };

  const handleRunAnalysis = async () => {
    if (!selectedEntry) return;
    
    setAnalysisLoading(true);
    setError('');
    
    try {
      const response = await analysisAPI.runAnalysis(selectedEntry.id);
      setAnalysis(response.data);
      setSuccess('Analysis completed successfully!');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to run analysis');
    } finally {
      setAnalysisLoading(false);
    }
  };

  const handleReportSubmit = async (e) => {
    e.preventDefault();
    if (!selectedEntry) return;

    try {
      await reportAPI.create({
        entry_id: selectedEntry.id,
        ...reportForm
      });
      setSuccess('Report added successfully!');
      setShowReportModal(false);
      setReportForm({ report_type: 'diagnosis', title: '', description: '', report_url: '' });
      const response = await reportAPI.getForEntry(selectedEntry.id);
      setReports(response.data);
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to add report');
    }
  };

  const handleDeleteReport = async (reportId) => {
    if (!confirm('Are you sure you want to delete this report?')) return;
    
    try {
      await reportAPI.delete(reportId);
      setReports(reports.filter(r => r.id !== reportId));
      setSuccess('Report deleted');
      setTimeout(() => setSuccess(''), 3000);
    } catch {
      setError('Failed to delete report');
    }
  };

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleString();
  };

  const parseQmaxReport = (jsonStr) => {
    try {
      return JSON.parse(jsonStr);
    } catch {
      return null;
    }
  };

  if (loading) return <div className="dashboard-loading">Loading...</div>;
  if (error && !profile) return <div className="dashboard-error">{error}</div>;

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <h1>Doctor Dashboard</h1>
        <p>Welcome back, Dr. {profile?.user?.username}</p>
      </div>

      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">{success}</div>}

      <div className="dashboard-grid">
        {/* Profile Card */}
        <div className="dashboard-card profile-card">
          <div className="card-header">
            <h2>Profile Overview</h2>
          </div>
          <div className="card-content">
            <div className="profile-info">
              <div className="info-row">
                <span className="label">Hospital:</span>
                <span className="value">{profile?.hospital}</span>
              </div>
              <div className="info-row">
                <span className="label">Specialization:</span>
                <span className="value">{profile?.specialization}</span>
              </div>
            </div>
            <div className="setting-item" style={{ marginTop: '1rem' }}>
              <div className="setting-info">
                <h3>Auto Accept & Auto Analysis</h3>
                <p style={{ fontSize: '0.8rem', color: '#666' }}>When enabled, analysis runs automatically on new entries</p>
              </div>
              <label className="toggle-switch">
                <input
                  type="checkbox"
                  checked={profile?.auto_accept || false}
                  onChange={toggleAutoAccept}
                />
                <span className="toggle-slider"></span>
              </label>
            </div>
          </div>
        </div>

        {/* Entries List */}
        <div className="dashboard-card entries-card">
          <div className="card-header">
            <h2>Patient Entries ({entries.length})</h2>
          </div>
          <div className="card-content">
            {entries.length === 0 ? (
              <p className="no-data">No entries yet</p>
            ) : (
              <div className="entries-list">
                {entries.map((entry) => (
                  <div
                    key={entry.id}
                    className={`entry-item ${selectedEntry?.id === entry.id ? 'selected' : ''}`}
                    onClick={() => handleSelectEntry(entry)}
                  >
                    <div className="entry-header">
                      <span className="entry-patient">Patient: {entry.patient_name || 'Unknown'}</span>
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

        {/* Entry Details & Analysis */}
        {selectedEntry && (
          <div className="dashboard-card reports-card">
            <div className="card-header">
              <h2>Entry Details & Analysis</h2>
            </div>
            <div className="card-content">
              <div className="entry-full-details">
                <p><strong>Time:</strong> {formatDate(selectedEntry.time)}</p>
                {selectedEntry.top_view_url && (
                  <p><strong>Top View:</strong> <a href={selectedEntry.top_view_url} target="_blank" rel="noopener noreferrer">View Video</a></p>
                )}
                {selectedEntry.bottom_view_url && (
                  <p><strong>Bottom View:</strong> <a href={selectedEntry.bottom_view_url} target="_blank" rel="noopener noreferrer">View Video</a></p>
                )}
                {selectedEntry.amount_voided && <p><strong>Amount Voided:</strong> {selectedEntry.amount_voided}ml</p>}
                {selectedEntry.diameter_of_commode && <p><strong>Diameter:</strong> {selectedEntry.diameter_of_commode}cm</p>}
                {selectedEntry.notes && <p><strong>Notes:</strong> {selectedEntry.notes}</p>}
              </div>

              {/* Analysis Section - Only visible to doctors */}
              <div className="analysis-section">
                <div className="reports-header">
                  <h3>📊 AI Analysis</h3>
                  {(selectedEntry.top_view_url || selectedEntry.bottom_view_url) && (
                    <button 
                      className="add-report-btn" 
                      onClick={handleRunAnalysis}
                      disabled={analysisLoading}
                    >
                      {analysisLoading ? 'Running...' : (analysis ? '🔄 Re-run Analysis' : '🔬 Run Analysis')}
                    </button>
                  )}
                </div>
                
                {analysisLoading && (
                  <div className="analysis-loading">
                    <p>🔄 Running CNN analysis on video... This may take a few minutes.</p>
                  </div>
                )}
                
                {analysis ? (
                  <div className="analysis-results">
                    {analysis.qmax_report_json && (() => {
                      const qmax = parseQmaxReport(analysis.qmax_report_json);
                      return qmax ? (
                        <div className="qmax-summary">
                          <div className="qmax-item highlight">
                            <span className="qmax-label">Qmax</span>
                            <span className="qmax-value">{qmax.Qmax?.toFixed(2) || 'N/A'} ml/s</span>
                          </div>
                          <div className="qmax-item highlight">
                            <span className="qmax-label">Voided Volume</span>
                            <span className="qmax-value">{qmax.Voided_Volume?.toFixed(2) || 'N/A'} ml</span>
                          </div>
                          <div className="qmax-item">
                            <span className="qmax-label">Time to Qmax</span>
                            <span className="qmax-value">{qmax.Time_to_Qmax?.toFixed(2) || 'N/A'} s</span>
                          </div>
                          <div className="qmax-item">
                            <span className="qmax-label">Hesitancy</span>
                            <span className="qmax-value">{qmax.Hesitancy?.toFixed(2) || 'N/A'} s</span>
                          </div>
                          <div className="qmax-item">
                            <span className="qmax-label">Voiding Time</span>
                            <span className="qmax-value">{qmax.Voiding_Time?.toFixed(2) || 'N/A'} s</span>
                          </div>
                          <div className="qmax-item">
                            <span className="qmax-label">Flow Time</span>
                            <span className="qmax-value">{qmax.Flow_Time?.toFixed(2) || 'N/A'} s</span>
                          </div>
                          <div className="qmax-item">
                            <span className="qmax-label">Average Flow Rate</span>
                            <span className="qmax-value">{qmax.Average_Flow_Rate?.toFixed(2) || 'N/A'} ml/s</span>
                          </div>
                        </div>
                      ) : null;
                    })()}
                    
                    <div className="analysis-links">
                      {analysis.annotated_video_url && (
                        <a href={analysis.annotated_video_url} target="_blank" rel="noopener noreferrer" className="analysis-link">
                          🎬 Annotated Video
                        </a>
                      )}
                      {analysis.clinical_report_url && (
                        <a href={analysis.clinical_report_url} target="_blank" rel="noopener noreferrer" className="analysis-link">
                          📈 Clinical Report
                        </a>
                      )}
                      {analysis.flow_timeseries_url && (
                        <a href={analysis.flow_timeseries_url} target="_blank" rel="noopener noreferrer" className="analysis-link">
                          📊 Flow Data (CSV)
                        </a>
                      )}
                    </div>
                  </div>
                ) : (
                  !analysisLoading && <p className="no-data">No analysis yet. Click "Run Analysis" to start.</p>
                )}
              </div>

              {/* Reports Section */}
              <div className="reports-section">
                <div className="reports-header">
                  <h3>Reports ({reports.length})</h3>
                  <button className="add-report-btn" onClick={() => setShowReportModal(true)}>
                    + Add Report
                  </button>
                </div>
                
                {reports.length === 0 ? (
                  <p className="no-data">No reports yet</p>
                ) : (
                  <div className="reports-list">
                    {reports.map((report) => (
                      <div key={report.id} className="report-item">
                        <div className="report-header">
                          <span className="report-type">{report.report_type}</span>
                          <button className="delete-btn-small" onClick={() => handleDeleteReport(report.id)}>×</button>
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

      {/* Add Report Modal */}
      {showReportModal && (
        <div className="modal-overlay" onClick={() => setShowReportModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Add Report</h2>
              <button className="close-btn" onClick={() => setShowReportModal(false)}>×</button>
            </div>
            <form onSubmit={handleReportSubmit} className="report-form">
              <div className="form-group">
                <label>Report Type</label>
                <select
                  value={reportForm.report_type}
                  onChange={(e) => setReportForm({ ...reportForm, report_type: e.target.value })}
                >
                  <option value="diagnosis">Diagnosis</option>
                  <option value="prescription">Prescription</option>
                  <option value="lab_results">Lab Results</option>
                  <option value="notes">Clinical Notes</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div className="form-group">
                <label>Title *</label>
                <input
                  type="text"
                  value={reportForm.title}
                  onChange={(e) => setReportForm({ ...reportForm, title: e.target.value })}
                  required
                  placeholder="Report title"
                />
              </div>
              <div className="form-group">
                <label>Description</label>
                <textarea
                  value={reportForm.description}
                  onChange={(e) => setReportForm({ ...reportForm, description: e.target.value })}
                  rows="3"
                  placeholder="Report description"
                />
              </div>
              <div className="form-group">
                <label>Document URL (optional)</label>
                <input
                  type="url"
                  value={reportForm.report_url}
                  onChange={(e) => setReportForm({ ...reportForm, report_url: e.target.value })}
                  placeholder="https://..."
                />
              </div>
              <button type="submit" className="save-btn">Add Report</button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default DoctorDashboard;
