import { configureStore } from '@reduxjs/toolkit';
import { setupListeners } from '@reduxjs/toolkit/query';
import { api } from './services/api';
import authReducer from './slices/authSlice';
import sessionsReducer from './slices/sessionsSlice';
import nodesReducer from './slices/nodesSlice';

export const store = configureStore({
    reducer: {
        [api.reducerPath]: api.reducer,
        auth: authReducer,
        sessions: sessionsReducer,
        nodes: nodesReducer,
    },
    middleware: (getDefaultMiddleware) =>
        getDefaultMiddleware({
            serializableCheck: {
                ignoredActions: [api.util.resetApiState.type],
            },
        }).concat(api.middleware),
    devTools: import.meta.env.DEV || import.meta.env.VITE_DEV_MODE === 'true',
});

// Setup listeners for refetchOnFocus/refetchOnReconnect behaviors
setupListeners(store.dispatch);

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
