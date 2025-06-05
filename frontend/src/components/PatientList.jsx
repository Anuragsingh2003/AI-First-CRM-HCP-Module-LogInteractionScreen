import React from 'react';

function PatientList({ patients, onEdit, onDelete }) {
  return (
    <div>
      <h2 className="text-2xl font-semibold mb-2">Patients</h2>
      {patients.length === 0 ? (
        <p>No patients found.</p>
      ) : (
        <ul className="space-y-2">
          {patients.map((patient) => (
            <li key={patient.patient_id} className="p-4 border rounded flex justify-between">
              <div>
                <p><strong>Name:</strong> {patient.name}</p>
                <p><strong>Age:</strong> {patient.age}</p>
                <p><strong>Condition:</strong> {patient.condition}</p>
              </div>
              <div>
                <button
                  onClick={() => onEdit(patient)}
                  className="bg-yellow-500 text-white p-2 rounded mr-2 hover:bg-yellow-600"
                >
                  Edit
                </button>
                <button
                  onClick={() => onDelete(patient.patient_id)}
                  className="bg-red-500 text-white p-2 rounded hover:bg-red-600"
                >
                  Delete
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default PatientList;