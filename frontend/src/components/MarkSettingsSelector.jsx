import React from 'react';
import '../styles/MarkSettingsSelector.css';

const MarkSettingsSelector = ({ value, onChange }) => {
  return (
    <div className="mark-settings-selector">
      <label htmlFor="internal-weight-select">Internal Weight:</label>
      <select
        id="internal-weight-select"
        value={value}
        onChange={(e) => onChange(parseInt(e.target.value))}
        className="mark-settings-select"
      >
        <option value="40">40%</option>
        <option value="60">60%</option>
      </select>
    </div>
  );
};

export default MarkSettingsSelector;

