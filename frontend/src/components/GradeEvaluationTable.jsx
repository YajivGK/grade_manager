import React, { useState, useEffect, useCallback } from 'react';
import { getStudents, getSubjects, getCriteria, evaluateStudents, getEvaluations } from '../services/api';
import SearchBar from './SearchBar';
import BatchSelector from './BatchSelector';
import MarkSettingsSelector from './MarkSettingsSelector';
import CriteriaManager from './CriteriaManager';
import EvaluateButton from './EvaluateButton';
import '../styles/GradeEvaluationTable.css';

const GradeEvaluationTable = () => {
  const [students, setStudents] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [criteria, setCriteria] = useState([]);
  const [selectedSubject, setSelectedSubject] = useState(null);
  const [selectedBatch, setSelectedBatch] = useState(null);
  const [internalWeight, setInternalWeight] = useState(40);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(false);
  const [evaluationData, setEvaluationData] = useState({});
  const [evaluationDate, setEvaluationDate] = useState(new Date().toISOString().split('T')[0]);
  const [existingEvaluations, setExistingEvaluations] = useState({});

  

  const loadSubjects = useCallback(async () => {
    try {
      const response = await getSubjects();
      setSubjects(response.data);
    } catch (error) {
      console.error('Error loading subjects:', error);
    }
  }, []);

  const loadCriteria = useCallback(async () => {
    if (!selectedSubject) return;
    
    try {
      const response = await getCriteria(selectedSubject);
      setCriteria(response.data);
    } catch (error) {
      console.error('Error loading criteria:', error);
    }
  }, [selectedSubject]);

  const loadExistingEvaluations = useCallback(async () => {
    if (!selectedSubject || !selectedBatch || !evaluationDate) return;
    
    try {
      const response = await getEvaluations({
        subject_id: selectedSubject,
        batch: selectedBatch,
        evaluation_date: evaluationDate,
      });
      
      // Map evaluations by student_id
      const evaluationsMap = {};
      response.data.forEach((evaluation) => {
        evaluationsMap[evaluation.student_id] = evaluation;
      });
      setExistingEvaluations(evaluationsMap);
      
      // Restore marks from existing evaluations so they don't disappear
      setEvaluationData((prev) => {
        const updated = { ...prev };
        response.data.forEach((evaluation) => {
          // Normalize internal_marks to an object keyed by criterion_id
          const internalObj = Array.isArray(evaluation.internal_marks)
            ? evaluation.internal_marks.reduce((acc, item) => {
                if (item && item.criterion_id != null) {
                  acc[item.criterion_id] = item.marks_obtained || 0;
                }
                return acc;
              }, {})
            : (evaluation.internal_marks || {});
          if (updated[evaluation.student_id]) {
            // Preserve existing input values but restore from evaluation if needed
            updated[evaluation.student_id] = {
              ...updated[evaluation.student_id],
              internal_marks: updated[evaluation.student_id].internal_marks && Object.keys(updated[evaluation.student_id].internal_marks).length > 0
                ? updated[evaluation.student_id].internal_marks
                : internalObj,
              external_total: updated[evaluation.student_id].external_total || evaluation.external_total || 0,
              attendance_percent: evaluation.attendance_percent,
            };
          } else {
            // Initialize with evaluation data
            updated[evaluation.student_id] = {
              internal_marks: internalObj,
              external_total: evaluation.external_total || 0,
              attendance_percent: evaluation.attendance_percent,
            };
          }
        });
        return updated;
      });
    } catch (error) {
      console.error('Error loading evaluations:', error);
    }
  }, [selectedSubject, selectedBatch, evaluationDate]);

  const loadStudents = useCallback(async () => {
    if (!selectedSubject) return;
    
    setLoading(true);
    try {
      const params = {
        batch: selectedBatch,
        search: searchTerm || undefined,
      };
      const response = await getStudents(params);
      setStudents(response.data);
      
      // Initialize evaluation data for each student, preserving existing data if available
      setEvaluationData((prev) => {
        const newData = {};
        response.data.forEach((student) => {
          // Preserve existing data if student already has data
          if (prev[student.id]) {
            newData[student.id] = prev[student.id];
          } else {
            newData[student.id] = {
              internal_marks: {},
              external_total: 0,
              attendance_percent: null,
            };
          }
        });
        return newData;
      });
    } catch (error) {
      console.error('Error loading students:', error);
    } finally {
      setLoading(false);
    }
  }, [selectedSubject, selectedBatch, searchTerm]);

  useEffect(() => {
    loadSubjects();
  }, [loadSubjects]);

  useEffect(() => {
    if (selectedSubject) {
      loadStudents();
      if (selectedBatch && evaluationDate) {
        loadExistingEvaluations();
      }
    }
  }, [selectedSubject, selectedBatch, searchTerm, evaluationDate, loadStudents, loadExistingEvaluations]);

  const handleCriteriaChange = useCallback((newCriteria) => {
    const same = JSON.stringify(criteria) === JSON.stringify(newCriteria);
    if (same) return;
    setCriteria(newCriteria);
    // Preserve existing internal marks for matching criteria (from current inputs or existing evaluations)
    setEvaluationData((prev) => {
      const next = {};
      const newIds = new Set((newCriteria || []).map((c) => c.id));
      students.forEach((student) => {
        const prevData = prev[student.id] || {};
        const fromExisting = existingEvaluations[student.id] || {};
        // Normalize any array form to object (defensive)
        const existingInternal = Array.isArray(fromExisting.internal_marks)
          ? fromExisting.internal_marks.reduce((acc, item) => {
              if (item && item.criterion_id != null) {
                acc[item.criterion_id] = item.marks_obtained || 0;
              }
              return acc;
            }, {})
          : (fromExisting.internal_marks || {});
        const prevInternal = prevData.internal_marks || {};
        const mergedInternal = {};
        newIds.forEach((cid) => {
          if (prevInternal[cid] != null) {
            mergedInternal[cid] = prevInternal[cid];
          } else if (existingInternal[cid] != null) {
            mergedInternal[cid] = existingInternal[cid];
          } else {
            // leave empty to avoid forcing 0 into inputs
          }
        });
        next[student.id] = {
          internal_marks: mergedInternal,
          external_total: prevData.external_total ?? fromExisting.external_total ?? 0,
          attendance_percent: prevData.attendance_percent ?? fromExisting.attendance_percent ?? null,
        };
      });
      return next;
    });
  }, [students, criteria, existingEvaluations]);

  const handleInternalMarkChange = (studentId, criterionId, value) => {
    setEvaluationData((prev) => ({
      ...prev,
      [studentId]: {
        ...prev[studentId],
        internal_marks: {
          ...prev[studentId].internal_marks,
          [criterionId]: parseFloat(value) || 0,
        },
      },
    }));
  };

  const handleExternalMarkChange = (studentId, value) => {
    setEvaluationData((prev) => ({
      ...prev,
      [studentId]: {
        ...prev[studentId],
        external_total: parseFloat(value) || 0,
      },
    }));
  };

  const handleAttendanceChange = (studentId, value) => {
    setEvaluationData((prev) => ({
      ...prev,
      [studentId]: {
        ...prev[studentId],
        attendance_percent: value !== '' ? parseFloat(value) : null,
      },
    }));
  };

  const handleEvaluate = async () => {
    if (!selectedSubject || !selectedBatch) {
      alert('Please select subject and batch');
      return;
    }

    if (criteria.length === 0) {
      alert('Please add at least one criterion');
      return;
    }

    setLoading(true);
    try {
      const studentEvaluations = students.map((student) => {
        const studentData = evaluationData[student.id] || {};
        const internalMarks = criteria.map((criterion) => ({
          criterion_id: criterion.id,
          marks_obtained: studentData.internal_marks?.[criterion.id] || 0,
        }));

        return {
          student_id: student.id,
          internal_marks: internalMarks,
          external_total: studentData.external_total || 0,
          attendance_percent: studentData.attendance_percent !== null && studentData.attendance_percent !== undefined
            ? studentData.attendance_percent
            : null,
        };
      });

      const requestData = {
        subject_id: selectedSubject,
        batch: selectedBatch,
        internal_weight: internalWeight,
        evaluation_date: evaluationDate,
        student_evaluations: studentEvaluations,
      };

      const response = await evaluateStudents(requestData);
      alert(`Successfully evaluated ${response.data.length} students!`);
      
      // Update existing evaluations with new data
      const newEvaluationsMap = {};
      response.data.forEach((evaluation) => {
        newEvaluationsMap[evaluation.student_id] = evaluation;
      });
      setExistingEvaluations(newEvaluationsMap);
      
      // Preserve the evaluation data so marks don't disappear after evaluation
      // Restore marks from the response to ensure they're visible
      setEvaluationData((prev) => {
        const updated = { ...prev };
        response.data.forEach((evaluation) => {
          const internalObj = Array.isArray(evaluation.internal_marks)
            ? evaluation.internal_marks.reduce((acc, item) => {
                if (item && item.criterion_id != null) {
                  acc[item.criterion_id] = item.marks_obtained || 0;
                }
                return acc;
              }, {})
            : (evaluation.internal_marks || {});
          if (updated[evaluation.student_id]) {
            // Restore marks from evaluation response to keep them visible
            updated[evaluation.student_id] = {
              internal_marks: Object.keys(internalObj).length > 0 ? internalObj : (updated[evaluation.student_id].internal_marks || {}),
              external_total: updated[evaluation.student_id].external_total || evaluation.external_total || 0,
              attendance_percent: evaluation.attendance_percent,
            };
          } else {
            // Initialize with evaluation data
            updated[evaluation.student_id] = {
              internal_marks: internalObj,
              external_total: evaluation.external_total || 0,
              attendance_percent: evaluation.attendance_percent,
            };
          }
        });
        return updated;
      });
      
      // Reload evaluations to show updated grades (but don't reload students to preserve marks)
      loadExistingEvaluations();
    } catch (error) {
      console.error('Error evaluating students:', error);
      alert('Error evaluating students: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const getGradeColor = (grade) => {
    const colors = {
      O: '#28a745',
      'A+': '#17a2b8',
      A: '#007bff',
      'B+': '#ffc107',
      B: '#fd7e14',
      U: '#dc3545',
      SA: '#6c757d',
    };
    return colors[grade] || '#000000';
  };

  const computeFinalScore = (student) => {
    const data = evaluationData[student.id] || {};
    const internal = data.internal_marks || {};
    let internalSum = 0;
    let internalMax = 0;
    criteria.forEach((c) => {
      internalSum += Number(internal[c.id] ?? 0);
      internalMax += Number(c.max_score ?? 0);
    });
    const internalScaled = internalMax > 0 ? (internalSum / internalMax) * internalWeight : 0;
    const externalScaled = ((data.external_total ?? 0) / 100) * (100 - internalWeight);
    const total = internalScaled + externalScaled;
    return Math.round((total + Number.EPSILON) * 100) / 100;
  };

  return (
    <div className="grade-evaluation-container">
      <div className="controls-section">
        <h1>Grade Manager</h1>
        
        <div className="controls-row">
          <div className="control-group">
            <label htmlFor="subject-select">Subject:</label>
            <select
              id="subject-select"
              value={selectedSubject || ''}
              onChange={(e) => setSelectedSubject(e.target.value ? parseInt(e.target.value) : null)}
              className="subject-select"
            >
              <option value="">Select Subject</option>
              {subjects.map((subject) => (
                <option key={subject.id} value={subject.id}>
                  {subject.code} - {subject.name}
                </option>
              ))}
            </select>
          </div>

          <BatchSelector value={selectedBatch} onChange={setSelectedBatch} />
          
          <MarkSettingsSelector value={internalWeight} onChange={setInternalWeight} />

          <div className="control-group">
            <label htmlFor="evaluation-date">Evaluation Date:</label>
            <input
              type="date"
              id="evaluation-date"
              value={evaluationDate}
              onChange={(e) => setEvaluationDate(e.target.value)}
              className="date-input"
            />
          </div>
        </div>

        <SearchBar value={searchTerm} onChange={setSearchTerm} />

        <CriteriaManager
          subjectId={selectedSubject}
          onCriteriaChange={handleCriteriaChange}
        />

        <EvaluateButton
          onEvaluate={handleEvaluate}
          disabled={!selectedSubject || !selectedBatch || criteria.length === 0 || loading}
        />
      </div>

      <div className="table-section">
        {loading ? (
          <div className="loading">Loading...</div>
        ) : students.length === 0 ? (
          <div className="no-data">No students found. Select a subject and batch to view students.</div>
        ) : (
          <div className="table-wrapper">
            <table className="evaluation-table">
              <thead>
                <tr>
                  <th>Reg No</th>
                  <th>Name</th>
                  {criteria.map((criterion) => (
                    <th key={criterion.id}>
                      {criterion.name} (Max: {criterion.max_score})
                    </th>
                  ))}
                  <th>External</th>
                  <th>Attendance %</th>
                  <th>Final (100)</th>
                  <th>Grade</th>
                </tr>
              </thead>
              <tbody>
                {students.map((student) => {
                  const studentData = evaluationData[student.id] || {};
                  return (
                    <tr key={student.id}>
                      <td>{student.regno}</td>
                      <td>{student.name}</td>
                      {criteria.map((criterion) => (
                        <td key={criterion.id}>
                          <input
                            type="number"
                            min="0"
                            max={criterion.max_score}
                            step="0.01"
                            value={studentData.internal_marks?.[criterion.id] ?? ''}
                            onChange={(e) =>
                              handleInternalMarkChange(
                                student.id,
                                criterion.id,
                                e.target.value
                              )
                            }
                            className="marks-input"
                          />
                        </td>
                      ))}
                      <td>
                        <input
                          type="number"
                          min="0"
                          step="0.01"
                          value={studentData.external_total ?? ''}
                          onChange={(e) =>
                            handleExternalMarkChange(student.id, e.target.value)
                          }
                          className="marks-input"
                        />
                      </td>
                      <td>
                        <input
                          type="number"
                          min="0"
                          max="100"
                          step="0.01"
                          value={
                            studentData.attendance_percent !== null && studentData.attendance_percent !== undefined
                              ? studentData.attendance_percent
                              : existingEvaluations[student.id]?.attendance_percent !== undefined
                              ? existingEvaluations[student.id].attendance_percent
                              : ''
                          }
                          onChange={(e) =>
                            handleAttendanceChange(student.id, e.target.value)
                          }
                          placeholder="%"
                          className="marks-input"
                        />
                      </td>
                      <td>
                        {computeFinalScore(student)}
                      </td>
                      <td 
                        className="grade-cell"
                        style={{
                          color: existingEvaluations[student.id] 
                            ? getGradeColor(existingEvaluations[student.id].grade) 
                            : '#666',
                          fontWeight: 'bold'
                        }}
                      >
                        {existingEvaluations[student.id]?.grade || '-'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default GradeEvaluationTable;

