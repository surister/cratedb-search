import { fileURLToPath, URL } from 'node:url'
import { resolve } from "path";
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),

  ],
    build: {
    lib: {
      entry: resolve(__dirname, "src/index.js"),
      name: "CrateDBSearchComponent",
      fileName: "cratedb-search-component",
    },
    rollupOptions: {
      // make sure to externalize deps that shouldn't be bundled
      // into your library
      external: ["vue"],
      output: {
        // Provide global variables to use in the UMD build
        // for externalized deps
        globals: {
          vue: "Vue",
        },
      },
    },
  },

  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
})
