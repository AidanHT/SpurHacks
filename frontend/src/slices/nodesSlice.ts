import { createSlice } from '@reduxjs/toolkit';
import type { PayloadAction } from '@reduxjs/toolkit';

// Node type matching backend NodeRead model
export interface Node {
    id: string;
    session_id: string;
    parent_id?: string;
    role: string;
    content: string;
    type?: string;
    extra?: Record<string, any>;
    created_at: string;
}

export interface NodesState {
    nodes: Node[];
    currentNode: Node | null;
    loading: boolean;
    error: string | null;
}

const initialState: NodesState = {
    nodes: [],
    currentNode: null,
    loading: false,
    error: null,
};

const nodesSlice = createSlice({
    name: 'nodes',
    initialState,
    reducers: {
        setNodes: (state, action: PayloadAction<Node[]>) => {
            state.nodes = action.payload;
        },
        setCurrentNode: (state, action: PayloadAction<Node | null>) => {
            state.currentNode = action.payload;
        },
        addNode: (state, action: PayloadAction<Node>) => {
            state.nodes.push(action.payload);
        },
        updateNode: (state, action: PayloadAction<Node>) => {
            const index = state.nodes.findIndex(n => n.id === action.payload.id);
            if (index !== -1) {
                state.nodes[index] = action.payload;
            }
        },
        removeNode: (state, action: PayloadAction<string>) => {
            state.nodes = state.nodes.filter(n => n.id !== action.payload);
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
    setNodes,
    setCurrentNode,
    addNode,
    updateNode,
    removeNode,
    setLoading,
    setError,
} = nodesSlice.actions;

export default nodesSlice.reducer; 