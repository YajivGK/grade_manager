import React, { useState, useEffect } from 'react';
import { listReports, generateReport, getSubjects } from '../services/api';
import '../styles/ReportsList.css';

const ReportsList = () => {
  const [reports, setReports] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [showGenerateForm, setShowGenerateForm] = useState(false);
  const [generateForm, setGenerateForm] = useState({
    subject_id: '',
    batch: '',
    evaluation_date: new Date().toISOString().split('T')[0],
  });

  useEffect(() => {
    loadReports();
    loadSubjects();
  }, []);

  const loadSubjects = async () => {
    try {
      const response = await getSubjects();
      setSubjects(response.data);
    } catch (error) {
      console.error('Error loading subjects:', error);
    }
  };

  const loadReports = async () => {
    setLoading(true);
    try {
      const response = await listReports();
      setReports(response.data);
    } catch (error) {
      console.error('Error loading reports:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = (downloadUrl) => {
    if (downloadUrl) {
      window.open(downloadUrl, '_blank');
    }
  };

  const handleGenerateReport = async () => {
    if (!generateForm.subject_id || !generateForm.batch || !generateForm.evaluation_date) {
      alert('Please fill in all fields');
      return;
    }

    setGenerating(true);
    try {
      await generateReport({
        subject_id: parseInt(generateForm.subject_id),
        batch: parseInt(generateForm.batch),
        evaluation_date: generateForm.evaluation_date,
      });
      alert('Report generated successfully!');
      setShowGenerateForm(false);
      loadReports();
    } catch (error) {
      console.error('Error generating report:', error);
      alert('Error generating report: ' + (error.response?.data?.detail || error.message));
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="reports-list-container">
      <div className="reports-header">
        <h2>Reports</h2>
        <button
          onClick={() => setShowGenerateForm(!showGenerateForm)}
          className="btn-generate-report"
        >
          {showGenerateForm ? 'Cancel' : '+ Generate Report'}
        </button>
      </div>

      {showGenerateForm && (
        <div className="generate-report-form">
          <h3>Generate New Report</h3>
          <div className="form-row">
            <div className="form-group">
              <label>Subject:</label>
              <select
                value={generateForm.subject_id}
                onChange={(e) => setGenerateForm({ ...generateForm, subject_id: e.target.value })}
                className="form-select"
              >
                <option value="">Select Subject</option>
                {subjects.map((subject) => (
                  <option key={subject.id} value={subject.id}>
                    {subject.code} - {subject.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Batch:</label>
              <select
                value={generateForm.batch}
                onChange={(e) => setGenerateForm({ ...generateForm, batch: e.target.value })}
                className="form-select"
              >
                <option value="">Select Batch</option>
                <option value="1">Odd</option>
                <option value="2">Even</option>
              </select>
            </div>
            <div className="form-group">
              <label>Evaluation Date:</label>
              <input
                type="date"
                value={generateForm.evaluation_date}
                onChange={(e) => setGenerateForm({ ...generateForm, evaluation_date: e.target.value })}
                className="form-input"
              />
            </div>
            <button
              onClick={handleGenerateReport}
              disabled={generating || !generateForm.subject_id || !generateForm.batch}
              className="btn-submit-generate"
            >
              {generating ? 'Generating...' : 'Generate'}
            </button>
          </div>
        </div>
      )}
      {loading ? (
        <div>Loading reports...</div>
      ) : reports.length === 0 ? (
        <div className="no-reports">No reports found.</div>
      ) : (
        <table className="reports-table">
          <thead>
            <tr>
              <th>Filename</th>
              <th>Size</th>
              <th>Last Modified</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {reports.map((report) => (
              <tr key={report.key}>
                <td>{report.filename}</td>
                <td>{report.size_mb} MB</td>
                <td>{new Date(report.last_modified).toLocaleString()}</td>
                <td>
                  <button
                    onClick={() => handleDownload(report.download_url)}
                    className="btn-download"
                    disabled={!report.download_url}
                  >
                    Download
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <button onClick={loadReports} className="btn-refresh">
        Refresh
      </button>
    </div>
  );
};

export default ReportsList;

