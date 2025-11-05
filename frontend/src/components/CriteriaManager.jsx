import React, { useState, useEffect, useCallback } from 'react';
import { getCriteria, createCriterion, deleteCriterion } from '../services/api';
import '../styles/CriteriaManager.css';

const CriteriaManager = ({ subjectId, onCriteriaChange }) => {
  const [criteria, setCriteria] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newCriterionName, setNewCriterionName] = useState('');
  const [newCriterionMaxScore, setNewCriterionMaxScore] = useState(100);

  const loadCriteria = useCallback(async () => {
    if (!subjectId) return;
    
    setLoading(true);
    try {
      const response = await getCriteria(subjectId);
      setCriteria(response.data);
    } catch (error) {
      console.error('Error loading criteria:', error);
    } finally {
      setLoading(false);
    }
  }, [subjectId]);

  useEffect(() => {
    if (subjectId) {
      loadCriteria();
    }
  }, [subjectId, loadCriteria]);

  useEffect(() => {
    if (onCriteriaChange && subjectId) {
      onCriteriaChange(criteria);
    }
  }, [criteria, onCriteriaChange, subjectId]);

  const handleAddCriterion = async (e) => {
    e.preventDefault();
    if (!newCriterionName.trim()) return;

    try {
      const orderIndex = criteria.length;
      await createCriterion({
        subject_id: subjectId,
        name: newCriterionName,
        max_score: parseFloat(newCriterionMaxScore),
        order_index: orderIndex,
      });
      setNewCriterionName('');
      setNewCriterionMaxScore(100);
      setShowAddForm(false);
      loadCriteria();
    } catch (error) {
      console.error('Error adding criterion:', error);
      alert('Error adding criterion: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleDeleteCriterion = async (criterionId) => {
    if (!window.confirm('Are you sure you want to delete this criterion?')) {
      return;
    }

    try {
      await deleteCriterion(criterionId);
      loadCriteria();
    } catch (error) {
      console.error('Error deleting criterion:', error);
      alert('Error deleting criterion: ' + (error.response?.data?.detail || error.message));
    }
  };

  if (!subjectId) {
    return <div className="criteria-manager">Please select a subject first</div>;
  }

  return (
    <div className="criteria-manager">
      <div className="criteria-header">
        <h3>Criteria Management</h3>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="btn-add-criterion"
        >
          {showAddForm ? 'Cancel' : '+ Add Criterion'}
        </button>
      </div>

      {showAddForm && (
        <form onSubmit={handleAddCriterion} className="add-criterion-form">
          <input
            type="text"
            value={newCriterionName}
            onChange={(e) => setNewCriterionName(e.target.value)}
            placeholder="Criterion name"
            className="criterion-name-input"
            required
          />
          <input
            type="number"
            value={newCriterionMaxScore}
            onChange={(e) => setNewCriterionMaxScore(e.target.value)}
            placeholder="Max Score"
            min="0"
            step="0.01"
            className="criterion-max-score-input"
          />
          <button type="submit" className="btn-submit-criterion">Add</button>
        </form>
      )}

      {loading ? (
        <div>Loading criteria...</div>
      ) : (
        <div className="criteria-list">
          {criteria.length === 0 ? (
            <div className="no-criteria">No criteria defined. Add one to get started.</div>
          ) : (
            criteria.map((criterion) => (
              <div key={criterion.id} className="criterion-item">
                <span className="criterion-name">{criterion.name}</span>
                <span className="criterion-max-score">Max: {criterion.max_score}</span>
                <button
                  onClick={() => handleDeleteCriterion(criterion.id)}
                  className="btn-delete-criterion"
                >
                  Delete
                </button>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};

export default CriteriaManager;

