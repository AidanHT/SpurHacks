import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { PayloadAction } from '@reduxjs/toolkit';

// Types
export interface User {
    id: string;
    email: string;
    is_active: boolean;
    is_superuser: boolean;
    is_verified: boolean;
    created_at: string;
    updated_at: string;
}

export interface AuthState {
    accessToken: string | null;
    refreshToken: string | null;
    profile: User | null;
    status: 'idle' | 'loading' | 'refreshing' | 'failed';
    error: string | null;
}

// Initial state
const initialState: AuthState = {
    accessToken: null,
    refreshToken: null,
    profile: null,
    status: 'idle',
    error: null,
};

// Async thunks
export const loginAsync = createAsyncThunk(
    'auth/login',
    async (credentials: { username: string; password: string }, { rejectWithValue }) => {
        try {
            const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/auth/jwt/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams(credentials),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Login failed');
            }

            const data = await response.json();
            return {
                accessToken: data.access_token,
                refreshToken: data.refresh_token,
            };
        } catch (error) {
            return rejectWithValue(error instanceof Error ? error.message : 'Login failed');
        }
    }
);

export const refreshTokenAsync = createAsyncThunk(
    'auth/refreshToken',
    async (_, { getState, rejectWithValue }) => {
        const state = getState() as { auth: AuthState };
        const refreshToken = state.auth.refreshToken;

        if (!refreshToken) {
            return rejectWithValue('No refresh token available');
        }

        try {
            const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/auth/jwt/refresh`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${refreshToken}`
                },
                body: JSON.stringify({ refresh_token: refreshToken }),
            });

            if (!response.ok) {
                throw new Error('Token refresh failed');
            }

            const data = await response.json();
            return { accessToken: data.access_token };
        } catch (error) {
            return rejectWithValue(error instanceof Error ? error.message : 'Token refresh failed');
        }
    }
);

// Auth slice
const authSlice = createSlice({
    name: 'auth',
    initialState,
    reducers: {
        // Action to set tokens
        setTokens: (state, action: PayloadAction<{ accessToken: string; refreshToken?: string }>) => {
            state.accessToken = action.payload.accessToken;
            if (action.payload.refreshToken) {
                state.refreshToken = action.payload.refreshToken;
            }
            state.error = null;
        },

        // Action to clear auth state (logout)
        logout: (state) => {
            state.accessToken = null;
            state.refreshToken = null;
            state.profile = null;
            state.status = 'idle';
            state.error = null;
            // Clear localStorage
            localStorage.removeItem('promptly_access_token');
            localStorage.removeItem('promptly_refresh_token');
            localStorage.removeItem('promptly_user_profile');
        },

        // Action to hydrate state from localStorage
        rehydrateAuth: (state) => {
            const accessToken = localStorage.getItem('promptly_access_token');
            const refreshToken = localStorage.getItem('promptly_refresh_token');
            const profileData = localStorage.getItem('promptly_user_profile');

            if (accessToken) {
                state.accessToken = accessToken;
            }
            if (refreshToken) {
                state.refreshToken = refreshToken;
            }
            if (profileData) {
                try {
                    state.profile = JSON.parse(profileData);
                } catch {
                    // Ignore invalid JSON
                }
            }
        },

        // Clear error state
        clearError: (state) => {
            state.error = null;
        },
    },
    extraReducers: (builder) => {
        // Login
        builder
            .addCase(loginAsync.pending, (state) => {
                state.status = 'loading';
                state.error = null;
            })
            .addCase(loginAsync.fulfilled, (state, action) => {
                state.status = 'idle';
                state.accessToken = action.payload.accessToken;
                state.refreshToken = action.payload.refreshToken;
                state.error = null;

                // Persist to localStorage
                localStorage.setItem('promptly_access_token', action.payload.accessToken);
                localStorage.setItem('promptly_refresh_token', action.payload.refreshToken);
            })
            .addCase(loginAsync.rejected, (state, action) => {
                state.status = 'failed';
                state.error = action.payload as string;
            })
            // Token refresh
            .addCase(refreshTokenAsync.pending, (state) => {
                state.status = 'refreshing';
                state.error = null;
            })
            .addCase(refreshTokenAsync.fulfilled, (state, action) => {
                state.status = 'idle';
                state.accessToken = action.payload.accessToken;
                state.error = null;

                // Persist new token to localStorage
                localStorage.setItem('promptly_access_token', action.payload.accessToken);
            })
            .addCase(refreshTokenAsync.rejected, (state, action) => {
                state.status = 'failed';
                state.error = action.payload as string;
                // Clear tokens on refresh failure (likely expired)
                state.accessToken = null;
                state.refreshToken = null;
                localStorage.removeItem('promptly_access_token');
                localStorage.removeItem('promptly_refresh_token');
                localStorage.removeItem('promptly_user_profile');
            });
    },
});

export const { setTokens, logout, rehydrateAuth, clearError } = authSlice.actions;

export default authSlice.reducer; 