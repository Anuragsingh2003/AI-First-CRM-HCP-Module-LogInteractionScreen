import { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { setFormData, addInteraction, updateInteraction, setInteractions, deleteInteraction } from './redux/interactionsSlice';

function App() {
  const [chatMessage, setChatMessage] = useState('');
  const [chatResponse, setChatResponse] = useState('');
  const dispatch = useDispatch();
  const formData = useSelector(state => state.interactions.formData);
  const interactions = useSelector(state => state.interactions.interactions);
  const [editingId, setEditingId] = useState(null);

  // Fetch interactions on load
  useEffect(() => {
    fetchInteractions();
  }, []);

  const fetchInteractions = async () => {
    try {
      const response = await fetch('http://localhost:8000/interactions');
      if (!response.ok) throw new Error(await response.text());
      const data = await response.json();
      dispatch(setInteractions(data));
    } catch (error) {
      console.error('Error fetching interactions:', error);
    }
  };

  const handleFormSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingId) {
        // Edit existing interaction
        const response = await fetch(`http://localhost:8000/interactions/${editingId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(formData),
        });
        if (!response.ok) throw new Error(await response.text());
        const data = await response.json();
        dispatch(updateInteraction(data));
        setEditingId(null);
      } else {
        // Save new interaction
        const response = await fetch('http://localhost:8000/interactions', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(formData),
        });
        if (!response.ok) throw new Error(await response.text());
        const data = await response.json();
        dispatch(addInteraction(data));
      }
      dispatch(setFormData({
        hcp_id: '',
        hcp_name: '',
        specialty: '',
        interaction_type: '',
        date: '',
        time: '',
        attendees: '',
        topic_discussed: '',
        materials_shared: '',
        hcp_sentiment: '',
        outcomes: '',
        follow_up_action: ''
      }));
    } catch (error) {
      console.error('Error saving interaction:', error);
    }
  };

  const handleChatSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: chatMessage,
          ...formData,
          interaction_id: editingId ? String(editingId) : "0"
        }),
      });
      if (!response.ok) throw new Error(await response.text());
      const data = await response.json();
      setChatResponse(data.response);
      // Update form with AI-filled data
      if (data.form_data) {
        const updatedFormData = {
          hcp_id: data.form_data.hcp_id || formData.hcp_id,
          hcp_name: data.form_data.hcp_name || formData.hcp_name,
          specialty: data.form_data.specialty || formData.specialty,
          interaction_type: data.form_data.interaction_type || formData.interaction_type,
          date: data.form_data.date ? data.form_data.date.split('T')[0] : formData.date,
          time: data.form_data.time || formData.time,
          attendees: data.form_data.attendees || formData.attendees,
          topic_discussed: data.form_data.topic_discussed || formData.topic_discussed,
          materials_shared: data.form_data.materials_shared || formData.materials_shared,
          hcp_sentiment: data.form_data.hcp_sentiment || formData.hcp_sentiment,
          outcomes: data.form_data.outcomes || formData.outcomes,
          follow_up_action: data.form_data.follow_up_action || formData.follow_up_action,
        };
        dispatch(setFormData(updatedFormData));
      }
    } catch (error) {
      console.error('Error in chat:', error);
      setChatResponse('Error processing your request. Please try again.');
    }
    setChatMessage('');
  };

  const handleEdit = (interaction) => {
    dispatch(setFormData({
      hcp_id: interaction.hcp_id,
      hcp_name: interaction.hcp_name || '',
      specialty: interaction.specialty || '',
      interaction_type: interaction.interaction_type || '',
      date: interaction.date ? interaction.date.split('T')[0] : '',
      time: interaction.time || '',
      attendees: interaction.attendees || '',
      topic_discussed: interaction.topic_discussed || '',
      materials_shared: interaction.materials_shared || '',
      hcp_sentiment: interaction.hcp_sentiment || '',
      outcomes: interaction.outcomes || '',
      follow_up_action: interaction.follow_up_action || ''
    }));
    setEditingId(interaction.id);
  };

  const handleDelete = async (id) => {
    try {
      const response = await fetch(`http://localhost:8000/interactions/${id}`, {
        method: 'DELETE',
      });
      if (!response.ok) throw new Error(await response.text());
      dispatch(deleteInteraction(id));
    } catch (error) {
      console.error('Error deleting interaction:', error);
    }
  };

  const handleChange = (e) => {
    dispatch(setFormData({ ...formData, [e.target.name]: e.target.value }));
  };

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '20px', fontFamily: "'Inter', sans-serif", color: '#333' }}>
      <h1 style={{ fontSize: '28px', fontWeight: 'bold', marginBottom: '20px', color: '#1f2937' }}>
        Log HCP Interaction
      </h1>
      <div style={{ display: 'flex', flexDirection: 'row', gap: '20px', flexWrap: 'wrap' }}>
        {/* Left Side: Structured Form */}
        <div style={{ flex: '1', minWidth: '300px', backgroundColor: '#fff', padding: '20px', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
          <h2 style={{ fontSize: '22px', fontWeight: '600', marginBottom: '15px', color: '#374151' }}>
            Interaction Form
          </h2>
          <form onSubmit={handleFormSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
            <div>
              <label htmlFor="hcp_name" style={{ display: 'block', fontSize: '14px', fontWeight: '500', color: '#4b5563', marginBottom: '5px' }}>
                HCP Name
              </label>
              <input
                type="text"
                id="hcp_name"
                name="hcp_name"
                value={formData.hcp_name}
                onChange={handleChange}
                placeholder="Enter HCP Name (e.g., Dr. Davis)"
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid #d1d5db',
                  borderRadius: '4px',
                  fontSize: '14px',
                  outline: 'none',
                  transition: 'border-color 0.2s',
                }}
                onFocus={(e) => (e.target.style.borderColor = '#3b82f6')}
                onBlur={(e) => (e.target.style.borderColor = '#d1d5db')}
              />
            </div>
            <div>
              <label htmlFor="hcp_id" style={{ display: 'block', fontSize: '14px', fontWeight: '500', color: '#4b5563', marginBottom: '5px' }}>
                HCP ID (Auto-generated if new)
              </label>
              <input
                type="text"
                id="hcp_id"
                name="hcp_id"
                value={formData.hcp_id}
                onChange={handleChange}
                placeholder="Auto-generated or enter existing ID"
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid #d1d5db',
                  borderRadius: '4px',
                  fontSize: '14px',
                  outline: 'none',
                  transition: 'border-color 0.2s',
                }}
                onFocus={(e) => (e.target.style.borderColor = '#3b82f6')}
                onBlur={(e) => (e.target.style.borderColor = '#d1d5db')}
                disabled
              />
            </div>
            <div>
              <label htmlFor="specialty" style={{ display: 'block', fontSize: '14px', fontWeight: '500', color: '#4b5563', marginBottom: '5px' }}>
                Specialty
              </label>
              <input
                type="text"
                id="specialty"
                name="specialty"
                value={formData.specialty}
                onChange={handleChange}
                placeholder="Enter HCP Specialty (e.g., Cardiologist)"
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid #d1d5db',
                  borderRadius: '4px',
                  fontSize: '14px',
                  outline: 'none',
                  transition: 'border-color 0.2s',
                }}
                onFocus={(e) => (e.target.style.borderColor = '#3b82f6')}
                onBlur={(e) => (e.target.style.borderColor = '#d1d5db')}
              />
            </div>
            <div>
              <label htmlFor="interaction_type" style={{ display: 'block', fontSize: '14px', fontWeight: '500', color: '#4b5563', marginBottom: '5px' }}>
                Interaction Type
              </label>
              <select
                id="interaction_type"
                name="interaction_type"
                value={formData.interaction_type}
                onChange={handleChange}
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid #d1d5db',
                  borderRadius: '4px',
                  fontSize: '14px',
                  outline: 'none',
                  transition: 'border-color 0.2s',
                }}
                onFocus={(e) => (e.target.style.borderColor = '#3b82f6')}
                onBlur={(e) => (e.target.style.borderColor = '#d1d5db')}
              >
                <option value="">Select Type</option>
                <option value="meeting">Meeting</option>
                <option value="call">Call</option>
                <option value="email">Email</option>
                <option value="visit">Visit</option>
              </select>
            </div>
            <div>
              <label htmlFor="date" style={{ display: 'block', fontSize: '14px', fontWeight: '500', color: '#4b5563', marginBottom: '5px' }}>
                Date
              </label>
              <input
                type="date"
                id="date"
                name="date"
                value={formData.date}
                onChange={handleChange}
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid #d1d5db',
                  borderRadius: '4px',
                  fontSize: '14px',
                  outline: 'none',
                  transition: 'border-color 0.2s',
                }}
                onFocus={(e) => (e.target.style.borderColor = '#3b82f6')}
                onBlur={(e) => (e.target.style.borderColor = '#d1d5db')}
              />
            </div>
            <div>
              <label htmlFor="time" style={{ display: 'block', fontSize: '14px', fontWeight: '500', color: '#4b5563', marginBottom: '5px' }}>
                Time
              </label>
              <input
                type="time"
                id="time"
                name="time"
                value={formData.time}
                onChange={handleChange}
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid #d1d5db',
                  borderRadius: '4px',
                  fontSize: '14px',
                  outline: 'none',
                  transition: 'border-color 0.2s',
                }}
                onFocus={(e) => (e.target.style.borderColor = '#3b82f6')}
                onBlur={(e) => (e.target.style.borderColor = '#d1d5db')}
              />
            </div>
            <div>
              <label htmlFor="attendees" style={{ display: 'block', fontSize: '14px', fontWeight: '500', color: '#4b5563', marginBottom: '5px' }}>
                Attendees
              </label>
              <input
                type="text"
                id="attendees"
                name="attendees"
                value={formData.attendees}
                onChange={handleChange}
                placeholder="Enter attendees (e.g., John Doe, Jane Smith)"
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid #d1d5db',
                  borderRadius: '4px',
                  fontSize: '14px',
                  outline: 'none',
                  transition: 'border-color 0.2s',
                }}
                onFocus={(e) => (e.target.style.borderColor = '#3b82f6')}
                onBlur={(e) => (e.target.style.borderColor = '#d1d5db')}
              />
            </div>
            <div>
              <label htmlFor="topic_discussed" style={{ display: 'block', fontSize: '14px', fontWeight: '500', color: '#4b5563', marginBottom: '5px' }}>
                Topic Discussed
              </label>
              <textarea
                id="topic_discussed"
                name="topic_discussed"
                value={formData.topic_discussed}
                onChange={handleChange}
                placeholder="Enter topic discussed"
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid #d1d5db',
                  borderRadius: '4px',
                  fontSize: '14px',
                  height: '100px',
                  resize: 'none',
                  outline: 'none',
                  transition: 'border-color 0.2s',
                }}
                onFocus={(e) => (e.target.style.borderColor = '#3b82f6')}
                onBlur={(e) => (e.target.style.borderColor = '#d1d5db')}
              />
            </div>
            <div>
              <label htmlFor="materials_shared" style={{ display: 'block', fontSize: '14px', fontWeight: '500', color: '#4b5563', marginBottom: '5px' }}>
                Materials Shared / Samples Distributed
              </label>
              <textarea
                id="materials_shared"
                name="materials_shared"
                value={formData.materials_shared}
                onChange={handleChange}
                placeholder="Enter materials shared or samples distributed"
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid #d1d5db',
                  borderRadius: '4px',
                  fontSize: '14px',
                  height: '100px',
                  resize: 'none',
                  outline: 'none',
                  transition: 'border-color 0.2s',
                }}
                onFocus={(e) => (e.target.style.borderColor = '#3b82f6')}
                onBlur={(e) => (e.target.style.borderColor = '#d1d5db')}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', color: '#4b5563', marginBottom: '5px' }}>
                HCP Sentiment
              </label>
              <div style={{ display: 'flex', gap: '15px' }}>
                <label style={{ display: 'flex', alignItems: 'center', fontSize: '14px', color: '#4b5563' }}>
                  <input
                    type="radio"
                    name="hcp_sentiment"
                    value="positive"
                    checked={formData.hcp_sentiment === 'positive'}
                    onChange={handleChange}
                    style={{ marginRight: '5px' }}
                  />
                  Positive
                </label>
                <label style={{ display: 'flex', alignItems: 'center', fontSize: '14px', color: '#4b5563' }}>
                  <input
                    type="radio"
                    name="hcp_sentiment"
                    value="neutral"
                    checked={formData.hcp_sentiment === 'neutral'}
                    onChange={handleChange}
                    style={{ marginRight: '5px' }}
                  />
                  Neutral
                </label>
                <label style={{ display: 'flex', alignItems: 'center', fontSize: '14px', color: '#4b5563' }}>
                  <input
                    type="radio"
                    name="hcp_sentiment"
                    value="negative"
                    checked={formData.hcp_sentiment === 'negative'}
                    onChange={handleChange}
                    style={{ marginRight: '5px' }}
                  />
                  Negative
                </label>
              </div>
            </div>
            <div>
              <label htmlFor="outcomes" style={{ display: 'block', fontSize: '14px', fontWeight: '500', color: '#4b5563', marginBottom: '5px' }}>
                Outcomes
              </label>
              <textarea
                id="outcomes"
                name="outcomes"
                value={formData.outcomes}
                onChange={handleChange}
                placeholder="Enter outcomes"
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid #d1d5db',
                  borderRadius: '4px',
                  fontSize: '14px',
                  height: '100px',
                  resize: 'none',
                  outline: 'none',
                  transition: 'border-color 0.2s',
                }}
                onFocus={(e) => (e.target.style.borderColor = '#3b82f6')}
                onBlur={(e) => (e.target.style.borderColor = '#d1d5db')}
              />
            </div>
            <div>
              <label htmlFor="follow_up_action" style={{ display: 'block', fontSize: '14px', fontWeight: '500', color: '#4b5563', marginBottom: '5px' }}>
                Follow-Up Action
              </label>
              <textarea
                id="follow_up_action"
                name="follow_up_action"
                value={formData.follow_up_action}
                onChange={handleChange}
                placeholder="Enter follow-up action"
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid #d1d5db',
                  borderRadius: '4px',
                  fontSize: '14px',
                  height: '100px',
                  resize: 'none',
                  outline: 'none',
                  transition: 'border-color 0.2s',
                }}
                onFocus={(e) => (e.target.style.borderColor = '#3b82f6')}
                onBlur={(e) => (e.target.style.borderColor = '#d1d5db')}
              />
            </div>
            <div style={{ display: 'flex', gap: '10px' }}>
              <button
                type="submit"
                style={{
                  backgroundColor: '#3b82f6',
                  color: '#fff',
                  padding: '8px 16px',
                  borderRadius: '4px',
                  border: 'none',
                  fontSize: '14px',
                  cursor: 'pointer',
                  transition: 'background-color 0.2s',
                }}
                onMouseOver={(e) => (e.target.style.backgroundColor = '#2563eb')}
                onMouseOut={(e) => (e.target.style.backgroundColor = '#3b82f6')}
              >
                {editingId ? 'Update' : 'Save'} Interaction
              </button>
              {editingId && (
                <button
                  type="button"
                  onClick={() => {
                    dispatch(setFormData({
                      hcp_id: '',
                      hcp_name: '',
                      specialty: '',
                      interaction_type: '',
                      date: '',
                      time: '',
                      attendees: '',
                      topic_discussed: '',
                      materials_shared: '',
                      hcp_sentiment: '',
                      outcomes: '',
                      follow_up_action: ''
                    }));
                    setEditingId(null);
                  }}
                  style={{
                    backgroundColor: '#6b7280',
                    color: '#fff',
                    padding: '8px 16px',
                    borderRadius: '4px',
                    border: 'none',
                    fontSize: '14px',
                    cursor: 'pointer',
                    transition: 'background-color 0.2s',
                  }}
                  onMouseOver={(e) => (e.target.style.backgroundColor = '#4b5563')}
                  onMouseOut={(e) => (e.target.style.backgroundColor = '#6b7280')}
                >
                  Cancel
                </button>
              )}
            </div>
          </form>
          {/* Interaction List */}
          <div style={{ marginTop: '30px' }}>
            <h2 style={{ fontSize: '22px', fontWeight: '600', marginBottom: '15px', color: '#374151' }}>
              Interactions
            </h2>
            {interactions.length === 0 ? (
              <p style={{ color: '#6b7280', fontSize: '14px' }}>No interactions found.</p>
            ) : (
              <ul style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {interactions.map((interaction) => (
                  <li
                    key={interaction.id}
                    style={{
                      padding: '15px',
                      border: '1px solid #e5e7eb',
                      borderRadius: '4px',
                      backgroundColor: '#f9fafb',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'flex-start',
                    }}
                  >
                    <div>
                      <p style={{ fontSize: '14px', marginBottom: '5px' }}>
                        <strong style={{ color: '#374151' }}>HCP ID:</strong> {interaction.hcp_id}
                      </p>
                      <p style={{ fontSize: '14px', marginBottom: '5px' }}>
                        <strong style={{ color: '#374151' }}>Interaction Type:</strong> {interaction.interaction_type || 'N/A'}
                      </p>
                      <p style={{ fontSize: '14px', marginBottom: '5px' }}>
                        <strong style={{ color: '#374151' }}>Date:</strong> {interaction.date ? interaction.date.split('T')[0] : 'N/A'}
                      </p>
                      <p style={{ fontSize: '14px', marginBottom: '5px' }}>
                        <strong style={{ color: '#374151' }}>Time:</strong> {interaction.time || 'N/A'}
                      </p>
                      <p style={{ fontSize: '14px', marginBottom: '5px' }}>
                        <strong style={{ color: '#374151' }}>Attendees:</strong> {interaction.attendees || 'N/A'}
                      </p>
                      <p style={{ fontSize: '14px', marginBottom: '5px' }}>
                        <strong style={{ color: '#374151' }}>Topic Discussed:</strong> {interaction.topic_discussed || 'N/A'}
                      </p>
                      <p style={{ fontSize: '14px', marginBottom: '5px' }}>
                        <strong style={{ color: '#374151' }}>Materials Shared:</strong> {interaction.materials_shared || 'N/A'}
                      </p>
                      <p style={{ fontSize: '14px', marginBottom: '5px' }}>
                        <strong style={{ color: '#374151' }}>HCP Sentiment:</strong> {interaction.hcp_sentiment || 'N/A'}
                      </p>
                      <p style={{ fontSize: '14px', marginBottom: '5px' }}>
                        <strong style={{ color: '#374151' }}>Outcomes:</strong> {interaction.outcomes || 'N/A'}
                      </p>
                      <p style={{ fontSize: '14px', marginBottom: '5px' }}>
                        <strong style={{ color: '#374151' }}>Follow-Up Action:</strong> {interaction.follow_up_action || 'N/A'}
                      </p>
                      <p style={{ fontSize: '14px', marginBottom: '5px' }}>
                        <strong style={{ color: '#374151' }}>Summary:</strong> {interaction.summary || 'N/A'}
                      </p>
                      <p style={{ fontSize: '14px' }}>
                        <strong style={{ color: '#374151' }}>Outcome:</strong> {interaction.outcome || 'N/A'}
                      </p>
                    </div>
                    <div style={{ display: 'flex', gap: '10px' }}>
                      <button
                        onClick={() => handleEdit(interaction)}
                        style={{
                          backgroundColor: '#f59e0b',
                          color: '#fff',
                          padding: '6px 12px',
                          borderRadius: '4px',
                          border: 'none',
                          fontSize: '14px',
                          cursor: 'pointer',
                          transition: 'background-color 0.2s',
                        }}
                        onMouseOver={(e) => (e.target.style.backgroundColor = '#d97706')}
                        onMouseOut={(e) => (e.target.style.backgroundColor = '#f59e0b')}
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDelete(interaction.id)}
                        style={{
                          backgroundColor: '#ef4444',
                          color: '#fff',
                          padding: '6px 12px',
                          borderRadius: '4px',
                          border: 'none',
                          fontSize: '14px',
                          cursor: 'pointer',
                          transition: 'background-color 0.2s',
                        }}
                        onMouseOver={(e) => (e.target.style.backgroundColor = '#dc2626')}
                        onMouseOut={(e) => (e.target.style.backgroundColor = '#ef4444')}
                      >
                        Delete
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
        {/* Right Side: Chat Interface */}
        <div style={{ flex: '1', minWidth: '300px', backgroundColor: '#fff', padding: '20px', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
          <h2 style={{ fontSize: '22px', fontWeight: '600', marginBottom: '15px', color: '#374151' }}>
            AI Assistant
          </h2>
          <div
            style={{
              border: '1px solid #e5e7eb',
              borderRadius: '4px',
              padding: '15px',
              height: '250px',
              overflowY: 'auto',
              marginBottom: '15px',
              backgroundColor: '#f9fafb',
            }}
          >
            {chatResponse && (
              <p style={{ fontSize: '14px', color: '#1f2937' }}>
                <strong>AI:</strong> {chatResponse}
              </p>
            )}
          </div>
          <form onSubmit={handleChatSubmit} style={{ display: 'flex', gap: '10px' }}>
            <input
              type="text"
              value={chatMessage}
              onChange={(e) => setChatMessage(e.target.value)}
              placeholder="e.g., 'met dr.davis, call, date today, time 09:30, discussed product Z pricing, neutral sentiment, follow-up: send pricing details'"
              style={{
                flexGrow: '1',
                padding: '8px',
                border: '1px solid #d1d5db',
                borderRadius: '4px 0 0 4px',
                fontSize: '14px',
                outline: 'none',
                transition: 'border-color 0.2s',
              }}
              onFocus={(e) => (e.target.style.borderColor = '#3b82f6')}
              onBlur={(e) => (e.target.style.borderColor = '#d1d5db')}
            />
            <button
              type="submit"
              style={{
                backgroundColor: '#3b82f6',
                color: '#fff',
                padding: '8px 16px',
                borderRadius: '0 4px 4px 0',
                border: 'none',
                fontSize: '14px',
                cursor: 'pointer',
                transition: 'background-color 0.2s',
              }}
              onMouseOver={(e) => (e.target.style.backgroundColor = '#2563eb')}
              onMouseOut={(e) => (e.target.style.backgroundColor = '#3b82f6')}
            >
              Send
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default App;