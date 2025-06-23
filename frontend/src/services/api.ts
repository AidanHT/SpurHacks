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
    tagTypes: ['User', 'Session', 'Node', 'File'],
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

        // Session endpoints (corrected paths)
        getSessions: builder.query<any[], void>({
            query: () => '/sessions',
            providesTags: ['Session'],
        }),

        getSession: builder.query<any, string>({
            query: (sessionId) => `/sessions/${sessionId}`,
            providesTags: (_result, _error, sessionId) => [{ type: 'Session', id: sessionId }],
        }),

        // Session management endpoints
        createSession: builder.mutation<any, {
            title?: string;
            metadata?: Record<string, any>;
            starter_prompt: string;
            max_questions: number;
            target_model: string;
            settings: Record<string, any>;
        }>({
            query: (sessionData) => ({
                url: '/sessions',
                method: 'POST',
                body: sessionData,
            }),
            invalidatesTags: ['Session'],
        }),

        answerQuestion: builder.mutation<any, {
            sessionId: string;
            nodeId: string;
            selected: string[];
            isCustomAnswer?: boolean;
            cancel?: boolean;
        }>({
            query: ({ sessionId, ...answerData }) => ({
                url: `/sessions/${sessionId}/answer`,
                method: 'POST',
                body: answerData,
            }),
            invalidatesTags: (_result, _error, { sessionId }) => [
                { type: 'Session', id: sessionId },
                'Session',
                'Node'
            ],
        }),

        // Node endpoints
        getSessionNodes: builder.query<any[], string>({
            query: (sessionId) => `/sessions/${sessionId}/nodes`,
            providesTags: (_result, _error, sessionId) => [
                { type: 'Node', id: sessionId },
                'Node'
            ],
        }),

        // File upload endpoints
        uploadFile: builder.mutation<any, {
            file: File;
            sessionId?: string;
        }>({
            query: ({ file, sessionId }) => {
                const formData = new FormData();
                formData.append('file', file);

                const url = sessionId
                    ? `/files?session_id=${sessionId}`
                    : '/files';

                return {
                    url,
                    method: 'POST',
                    body: formData,
                };
            },
            invalidatesTags: ['File'],
        }),

        getFileInfo: builder.query<any, string>({
            query: (fileId) => `/files/${fileId}`,
            providesTags: (_result, _error, fileId) => [{ type: 'File', id: fileId }],
        }),
    }),
});

// Export hooks for usage in functional components
export const {
    usePingQuery,
    useGetCurrentUserQuery,
    useGetSessionsQuery,
    useGetSessionQuery,
    useCreateSessionMutation,
    useAnswerQuestionMutation,
    useGetSessionNodesQuery,
    useUploadFileMutation,
    useGetFileInfoQuery,
} = api; 