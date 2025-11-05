import React, { useState } from 'react';
import '../styles/EvaluateButton.css';

const EvaluateButton = ({ onEvaluate, disabled }) => {
  const [showConfirm, setShowConfirm] = useState(false);

  const handleClick = () => {
    setShowConfirm(true);
  };

  const handleConfirm = () => {
    setShowConfirm(false);
    if (onEvaluate) {
      onEvaluate();
    }
  };

  const handleCancel = () => {
    setShowConfirm(false);
  };

  return (
    <>
      <button
        onClick={handleClick}
        disabled={disabled}
        className="evaluate-button"
      >
        Evaluate
      </button>

      {showConfirm && (
        <div className="modal-overlay" onClick={handleCancel}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>Confirm Evaluation</h3>
            <p>Are you sure you want to evaluate and calculate grades for all students?</p>
            <div className="modal-buttons">
              <button onClick={handleConfirm} className="btn-confirm">
                Yes, Evaluate
              </button>
              <button onClick={handleCancel} className="btn-cancel">
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default EvaluateButton;

