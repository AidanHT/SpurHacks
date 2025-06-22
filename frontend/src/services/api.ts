import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import type { RootState } from '../store';

// Base query with auth headers
const baseQuery = fetchBaseQuery({
    baseUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000',
    prepareHeaders: (headers, { getState }) => {
        const state = getState() as RootState;
        const token = state.auth.accessToken;

        if (token) {
            headers.set('Authorization', `Bearer ${token}`);
        }

        return headers;
    },
});

// Main API slice
export const api = createApi({
    reducerPath: 'api',
    baseQuery,
    tagTypes: ['User', 'Session', 'Node'],
    endpoints: (builder) => ({
        // Health check endpoint
        ping: builder.query<{ ok: boolean }, void>({
            query: () => '/ping',
        }),

        // Get current user profile
        getCurrentUser: builder.query<any, void>({
            query: () => '/users/me',
            providesTags: ['User'],
        }),

        // Basic session endpoints
        getSessions: builder.query<any[], void>({
            query: () => '/api/sessions',
            providesTags: ['Session'],
        }),

        getSession: builder.query<any, string>({
            query: (sessionId) => `/api/sessions/${sessionId}`,
            providesTags: (_result, _error, sessionId) => [{ type: 'Session', id: sessionId }],
        }),
    }),
});

// Export hooks for usage in functional components
export const {
    usePingQuery,
    useGetCurrentUserQuery,
    useGetSessionsQuery,
    useGetSessionQuery,
} = api; 