import { defineConfig } from '@playwright/test'
import { resolve } from 'node:path'
const python = process.env.SENTINEL_PYTHON || resolve(process.platform === 'win32' ? '../.venv/Scripts/python.exe' : '../.venv/bin/python')
export default defineConfig({
  testDir: './e2e', fullyParallel: false, workers: 1, timeout: 30000,
  use: {baseURL:'http://127.0.0.1:5174', browserName:'chromium', trace:'retain-on-failure'},
  reporter: [['list']],
  webServer: [
    {command: `"${python}" "${resolve('../scripts/e2e_server.py')}"`, url:'http://127.0.0.1:8001/ready', timeout:60000, reuseExistingServer:false},
    {command: 'npm run dev -- --port 5174 --strictPort', url:'http://127.0.0.1:5174', timeout:30000, reuseExistingServer:false, env:{VITE_API_PROXY:'http://127.0.0.1:8001'}},
  ],
})
