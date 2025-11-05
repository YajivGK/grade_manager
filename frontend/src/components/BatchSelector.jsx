import React from 'react';
import '../styles/BatchSelector.css';

const BatchSelector = ({ value, onChange }) => {
  return (
    <div className="batch-selector">
      <label htmlFor="batch-select">Batch:</label>
      <select
        id="batch-select"
        value={value || ''}
        onChange={(e) => onChange(e.target.value ? parseInt(e.target.value) : null)}
        className="batch-select"
      >
        <option value="">All</option>
        <option value="1">Odd</option>
        <option value="2">Even</option>
      </select>
    </div>
  );
};

export default BatchSelector;

