/// <reference types="vite/client" />

declare global {
  interface ImportMetaEnv {
    // Set at build time (VITE_DEMO=1) to serve the embedded demo dataset with no
    // backend, for the standalone artifact build.
    readonly VITE_DEMO?: string
  }
}

export {}
