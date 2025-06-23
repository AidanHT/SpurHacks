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
            console.log('Attempting login with:', { username: credentials.username });

            const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/auth/jwt/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams(credentials),
            });

            if (!response.ok) {
                const errorData = await response.json();
                console.error('Login error response:', errorData);
                throw new Error(errorData.detail || `Login failed: ${response.status}`);
            }

            const data = await response.json();
            console.log('Login successful, received token');

            return {
                accessToken: data.access_token,
                refreshToken: data.refresh_token || null,
            };
        } catch (error) {
            console.error('Login error:', error);
            return rejectWithValue(error instanceof Error ? error.message : 'Login failed');
        }
    }
);

// Note: FastAPI Users doesn't support refresh tokens by default
// This is a placeholder for future implementation or custom JWT refresh logic
export const refreshTokenAsync = createAsyncThunk(
    'auth/refreshToken',
    async (_, { rejectWithValue }) => {
        // For now, just reject since FastAPI Users doesn't support refresh tokens
        return rejectWithValue('Token refresh not supported. Please log in again.');
    }
);

export const fetchUserProfileAsync = createAsyncThunk(
    'auth/fetchProfile',
    async (_, { getState, rejectWithValue }) => {
        const state = getState() as { auth: AuthState };
        const accessToken = state.auth.accessToken;

        if (!accessToken) {
            return rejectWithValue('No access token available');
        }

        try {
            const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/users/me`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                throw new Error('Failed to fetch user profile');
            }

            const profile = await response.json();
            return profile;
        } catch (error) {
            return rejectWithValue(error instanceof Error ? error.message : 'Failed to fetch user profile');
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
            // Clear localStorage with error handling
            try {
                localStorage.removeItem('promptly_access_token');
                localStorage.removeItem('promptly_refresh_token');
                localStorage.removeItem('promptly_user_profile');
            } catch (error) {
                console.warn('Failed to clear localStorage:', error);
            }
        },

        // Action to hydrate state from localStorage
        rehydrateAuth: (state) => {
            try {
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
                    } catch (error) {
                        console.warn('Failed to parse user profile from localStorage:', error);
                    }
                }
            } catch (error) {
                console.warn('Failed to rehydrate auth state from localStorage:', error);
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

                // Persist to localStorage with error handling
                try {
                    localStorage.setItem('promptly_access_token', action.payload.accessToken);
                    localStorage.setItem('promptly_refresh_token', action.payload.refreshToken);
                } catch (error) {
                    console.warn('Failed to save auth tokens to localStorage:', error);
                }
            })
            .addCase(loginAsync.rejected, (state, action) => {
                state.status = 'failed';
                state.error = action.payload as string;
            })
            // Token refresh (placeholder - not supported by FastAPI Users)
            .addCase(refreshTokenAsync.pending, (state) => {
                state.status = 'refreshing';
                state.error = null;
            })
            .addCase(refreshTokenAsync.fulfilled, (state) => {
                // This case won't be reached with current implementation
                state.status = 'idle';
                state.error = null;
            })
            .addCase(refreshTokenAsync.rejected, (state, action) => {
                state.status = 'failed';
                state.error = action.payload as string;
                // Clear tokens on refresh failure
                state.accessToken = null;
                state.refreshToken = null;
                localStorage.removeItem('promptly_access_token');
                localStorage.removeItem('promptly_refresh_token');
                localStorage.removeItem('promptly_user_profile');
            })
            // Fetch profile
            .addCase(fetchUserProfileAsync.pending, (state) => {
                state.status = 'loading';
            })
            .addCase(fetchUserProfileAsync.fulfilled, (state, action) => {
                state.status = 'idle';
                state.profile = action.payload;
                state.error = null;

                // Persist profile to localStorage
                localStorage.setItem('promptly_user_profile', JSON.stringify(action.payload));
            })
            .addCase(fetchUserProfileAsync.rejected, (state, action) => {
                state.status = 'failed';
                state.error = action.payload as string;
            });
    },
});

export const { setTokens, logout, rehydrateAuth, clearError } = authSlice.actions;

export default authSlice.reducer; 