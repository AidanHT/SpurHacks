import { rootApi } from '@/store';

// Session data types matching backend models
export interface SessionSettings {
  tone: string;
  wordLimit: number;
  contextSources?: string[];
}

export interface SessionCreateRequest {
  title?: string;
  metadata?: Record<string, any>;
  starter_prompt: string;
  max_questions: number;
  target_model: string;
  settings: SessionSettings;
}

export interface SessionResponse {
  id: string;
  user_id: string;
  created_at: string;
  updated_at: string;
  title?: string;
  metadata?: Record<string, any>;
  starter_prompt?: string;
  max_questions: number;
  target_model: string;
  settings: SessionSettings;
  status: string;
}

// Extend the rootApi with sessions endpoints
export const sessionsApi = rootApi.injectEndpoints({
  endpoints: (builder) => ({
    createSession: builder.mutation<SessionResponse, SessionCreateRequest>({
      query: (sessionData) => ({
        url: '/sessions',
        method: 'POST',
        body: sessionData,
      }),
      invalidatesTags: ['Session'],
    }),
    getSession: builder.query<SessionResponse, string>({
      query: (sessionId) => `/sessions/${sessionId}`,
      providesTags: (result, error, id) => [{ type: 'Session', id }],
    }),
    listSessions: builder.query<SessionResponse[], { limit?: number; skip?: number }>({
      query: ({ limit = 50, skip = 0 } = {}) => 
        `/sessions?limit=${limit}&skip=${skip}`,
      providesTags: ['Session'],
    }),
  }),
});

export const {
  useCreateSessionMutation,
  useGetSessionQuery,
  useListSessionsQuery,
} = sessionsApi; 