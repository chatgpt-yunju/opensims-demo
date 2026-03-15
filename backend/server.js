import express from 'express'
import cors from 'cors'
import path from 'path'
import { fileURLToPath } from 'url'
import pptRoutes from './src/routes/ppt.js'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

// Load .env manually
import { readFileSync } from 'fs'
try {
  const envContent = readFileSync(path.join(__dirname, '.env'), 'utf-8')
  for (const line of envContent.split('\n')) {
    const trimmed = line.trim()
    if (!trimmed || trimmed.startsWith('#')) continue
    const eqIdx = trimmed.indexOf('=')
    if (eqIdx > 0) {
      const key = trimmed.slice(0, eqIdx).trim()
      const val = trimmed.slice(eqIdx + 1).trim()
      if (!process.env[key]) process.env[key] = val
    }
  }
} catch {}

const app = express()
const PORT = process.env.PORT || 3020

app.use(cors())
app.use(express.json())

// Static files for generated output
app.use('/output', express.static(path.join(__dirname, 'output')))

// API routes
app.use('/api/ppt', pptRoutes)

// Serve frontend in production
const distPath = path.join(__dirname, '..', 'dist')
app.use(express.static(distPath))
app.get('*', (req, res) => {
  res.sendFile(path.join(distPath, 'index.html'))
})

app.listen(PORT, () => {
  console.log(`[AIPPT] Backend running on port ${PORT}`)
})
