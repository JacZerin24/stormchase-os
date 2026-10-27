import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
export default defineConfig({
  plugins: [react()],
  base: process.env.GITHUB_PAGES === 'true' ? '/stormchase-os/' : '/',
  test: { include: ['src/**/*.test.ts'], environment: 'node' }
});
