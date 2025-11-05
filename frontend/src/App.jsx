import React, { useState } from 'react';
import GradeEvaluationTable from './components/GradeEvaluationTable';
import ReportsList from './components/ReportsList';
import './styles/App.css';

function App() {
  const [activeTab, setActiveTab] = useState('evaluation');

  return (
    <div className="App">
      <nav className="navbar">
        <div className="nav-brand">Grade Manager</div>
        <div className="nav-tabs">
          <button
            className={`nav-tab ${activeTab === 'evaluation' ? 'active' : ''}`}
            onClick={() => setActiveTab('evaluation')}
          >
            Evaluation
          </button>
          <button
            className={`nav-tab ${activeTab === 'reports' ? 'active' : ''}`}
            onClick={() => setActiveTab('reports')}
          >
            Reports
          </button>
        </div>
      </nav>

      <main className="main-content">
        {activeTab === 'evaluation' && <GradeEvaluationTable />}
        {activeTab === 'reports' && <ReportsList />}
      </main>
    </div>
  );
}

export default App;

