import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  formData: {
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
  },
  interactions: []
};

const interactionsSlice = createSlice({
  name: 'interactions',
  initialState,
  reducers: {
    setFormData: (state, action) => {
      state.formData = action.payload;
    },
    addInteraction: (state, action) => {
      state.interactions.push(action.payload);
    },
    updateInteraction: (state, action) => {
      const index = state.interactions.findIndex(i => i.id === action.payload.id);
      if (index !== -1) state.interactions[index] = action.payload;
    },
    setInteractions: (state, action) => {
      state.interactions = action.payload;
    },
    deleteInteraction: (state, action) => {
      state.interactions = state.interactions.filter(i => i.id !== action.payload);
    }
  }
});

export const { setFormData, addInteraction, updateInteraction, setInteractions, deleteInteraction } = interactionsSlice.actions;
export default interactionsSlice.reducer;