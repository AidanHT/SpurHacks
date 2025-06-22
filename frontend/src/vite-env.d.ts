/// <reference types="vite/client" />

interface ImportMetaEnv {
    readonly VITE_API_URL: string;
    readonly VITE_APP_NAME: string;
    readonly VITE_DEV_MODE: string;
    readonly VITE_JWT_STORAGE_KEY: string;
    readonly VITE_THEME_STORAGE_KEY: string;
}

interface ImportMeta {
    readonly env: ImportMetaEnv;
} 