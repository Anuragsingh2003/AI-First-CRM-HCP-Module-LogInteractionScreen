import React, { useState, useEffect } from 'react';

function PatientForm({ onSubmit, editingPatient, setEditingPatient }) {
  const [formData, setFormData] = useState({ name: '', age: '', condition: '' });

  useEffect(() => {
    if (editingPatient) {
      setFormData({
        name: editingPatient.name,
        age: editingPatient.age,
        condition: editingPatient.condition,
        patient_id: editingPatient.patient_id,
      });
    } else {
      setFormData({ name: '', age: '', condition: '' });
    }
  }, [editingPatient]);

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit({
      ...formData,
      age: parseInt(formData.age),
      ...(editingPatient && { patient_id: editingPatient.patient_id }),
    });
    if (!editingPatient) {
      setFormData({ name: '', age: '', condition: '' });
    }
  };

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  return (
    <div className="mb-8">
      <h2 className="text-2xl font-semibold mb-2">
        {editingPatient ? 'Edit Patient' : 'Add Patient'}
      </h2>
      <div className="space-y-4">
        <input
          type="text"
          name="name"
          value={formData.name}
          onChange={handleChange}
          placeholder="Name"
          className="w-full p-2 border rounded"
          required
        />
        <input
          type="number"
          name="age"
          value={formData.age}
          onChange={handleChange}
          placeholder="Age"
          className="w-full p-2 border rounded"
          required
        />
        <input
          type="text"
          name="condition"
          value={formData.condition}
          onChange={handleChange}
          placeholder="Condition"
          className="w-full p-2 border rounded"
          required
        />
        <div>
          <button
            onClick={handleSubmit}
            className="bg-blue-500 text-white p-2 rounded hover:bg-blue-600"
          >
            {editingPatient ? 'Update' : 'Add'}
          </button>
          {editingPatient && (
            <button
              onClick={() => setEditingPatient(null)}
              className="ml-2 bg-gray-500 text-white p-2 rounded hover:bg-gray-600"
            >
              Cancel
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default PatientForm;