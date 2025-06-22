import { createSlice } from '@reduxjs/toolkit';
import type { PayloadAction } from '@reduxjs/toolkit';

// Session type - simplified for now
export interface Session {
    id: string;
    title: string;
    description?: string;
    created_at: string;
    updated_at: string;
    user_id: string;
    is_archived: boolean;
}

export interface SessionsState {
    sessions: Session[];
    currentSession: Session | null;
    loading: boolean;
    error: string | null;
}

const initialState: SessionsState = {
    sessions: [],
    currentSession: null,
    loading: false,
    error: null,
};

const sessionsSlice = createSlice({
    name: 'sessions',
    initialState,
    reducers: {
        setSessions: (state, action: PayloadAction<Session[]>) => {
            state.sessions = action.payload;
        },
        setCurrentSession: (state, action: PayloadAction<Session | null>) => {
            state.currentSession = action.payload;
        },
        addSession: (state, action: PayloadAction<Session>) => {
            state.sessions.unshift(action.payload);
        },
        updateSession: (state, action: PayloadAction<Session>) => {
            const index = state.sessions.findIndex(s => s.id === action.payload.id);
            if (index !== -1) {
                state.sessions[index] = action.payload;
            }
        },
        removeSession: (state, action: PayloadAction<string>) => {
            state.sessions = state.sessions.filter(s => s.id !== action.payload);
        },
        setLoading: (state, action: PayloadAction<boolean>) => {
            state.loading = action.payload;
        },
        setError: (state, action: PayloadAction<string | null>) => {
            state.error = action.payload;
        },
    },
});

export const {
    setSessions,
    setCurrentSession,
    addSession,
    updateSession,
    removeSession,
    setLoading,
    setError,
} = sessionsSlice.actions;

export default sessionsSlice.reducer; 