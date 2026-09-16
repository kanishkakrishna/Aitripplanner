# AI Trip Planner

Standalone AI itinerary planner rebuilt from the KhojIndia project.

The backend is grounded in the existing KhojIndia MongoDB dataset (`khojindia.Sthan`). It retrieves hidden gems from MongoDB before Gemini builds a maximum four-day itinerary.

## Stack

- FastAPI
- MongoDB Atlas
- MongoDB vector search with lexical fallback
- Gemini 2.5 Flash via LangChain
- Open-Meteo weather
- OpenStreetMap + OSRM routing
- React + Vite frontend

## API

- `GET /health`
- `GET /health/db`
- `POST /api/plan-trip`

Request:

```json
{ "prompt": "Plan a peaceful weekend trip from Jamshedpur near a waterfall" }
```

## Environment variables

Copy `.env.example` and set:

- `GOOGLE_API_KEY`
- `MONGO_URI`
- `MONGO_DB=khojindia`
- `MONGO_COLLECTION=Sthan`
- `MONGO_VECTOR_INDEX=vector_index`

Secrets are never committed to this repository.
