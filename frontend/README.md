# BhuDrishti 3D — Master Frontend

Professional 3D cadastral dashboard for BhuDrishti 3D.

## Setup

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start dev server (port 5173) |
| `npm run build` | TypeScript check + production build |
| `npm run test` | Run test suite |
| `npm run preview` | Preview production build |

## Backend

The frontend proxies `/api/*` and `/health` to `http://localhost:8000`.
If the backend is unavailable, the app runs in demo mode with local mock data.

## Tech Stack

- React 18 + TypeScript
- Vite
- Three.js + React Three Fiber + Drei
- Zustand (state)
- Tailwind CSS 3
- Vitest + Testing Library
