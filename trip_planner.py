import json
import re
from functools import lru_cache
from typing import List

from fastapi import APIRouter
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, field_validator

from tools.db_tool import search_hidden_gems
from tools.route_tool import get_route_info
from tools.weather_tool import get_weather

router = APIRouter()


class DayPlan(BaseModel):
    day: int
    activity: str


class TripPlan(BaseModel):
    title: str
    destination: str
    weather: str
    route: str
    itinerary: List[DayPlan]
    tips: List[str]

    @field_validator("itinerary")
    @classmethod
    def enforce_day_limit(cls, value):
        return value[:4]

    @field_validator("tips")
    @classmethod
    def enforce_tip_count(cls, value):
        tips = value[:3]
        defaults = [
            "Respect local communities and nature.",
            "Carry water and basic travel essentials.",
            "Check local conditions before starting your journey.",
        ]
        while len(tips) < 3:
            tips.append(defaults[len(tips)])
        return tips


class UserRequest(BaseModel):
    prompt: str


@lru_cache(maxsize=1)
def get_agent():
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.35)
    tools = [search_hidden_gems, get_weather, get_route_info]

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """You are an AI Trip Planner grounded in the KhojIndia hidden-gem dataset.

NON-NEGOTIABLE RULES:
1. The trip must be within India.
2. The itinerary may contain at most 4 days.
3. Return exactly 3 travel tips.
4. You MUST call search_hidden_gems before selecting any destination.
5. The final destination MUST be one of the MongoDB places returned by search_hidden_gems.
6. Never replace a database result with a famous place from your own knowledge.
7. Choose the returned place that best fits the user's origin, requested vibe, activities and region.
8. After selecting it, call get_weather using the chosen destination.
9. If the user gives or clearly implies an origin, call get_route_info with that origin and destination.
10. If MongoDB returns no usable place, use the no-result JSON. Never fabricate a destination.
11. Output raw valid JSON only. No markdown and no extra explanation.

Required JSON schema:
{
  "title": "...",
  "destination": "Local Name, District, State",
  "weather": "...",
  "route": "...",
  "itinerary": [
    {"day": 1, "activity": "..."}
  ],
  "tips": ["tip1", "tip2", "tip3"]
}

No-result JSON:
{
  "title": "No hidden gem found",
  "destination": "No matching KhojIndia destination",
  "weather": "Not available",
  "route": "Not available",
  "itinerary": [],
  "tips": [
    "Try describing the kind of place you want.",
    "Mention your starting city or region.",
    "Try another travel vibe or activity."
  ]
}
""",
        ),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=False,
        max_iterations=8,
        handle_parsing_errors=True,
    )


def _extract_json(output):
    if isinstance(output, list):
        raw = ""
        for part in output:
            if isinstance(part, dict):
                raw += part.get("text", "")
            elif isinstance(part, str):
                raw += part
    else:
        raw = str(output)

    raw = raw.strip()
    fenced = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", raw, re.IGNORECASE)
    if fenced:
        return json.loads(fenced.group(1))

    match = re.search(r"\{[\s\S]*\}", raw)
    if not match:
        raise ValueError("Gemini did not return a JSON object")
    return json.loads(match.group(0))


@router.post("/api/plan-trip")
async def plan_trip(request: UserRequest):
    try:
        if not request.prompt.strip():
            raise ValueError("Prompt cannot be empty")
        result = await get_agent().ainvoke({"input": request.prompt.strip()})
        parsed = _extract_json(result["output"])
        trip = TripPlan.model_validate(parsed)
        return trip.model_dump()
    except Exception as exc:
        print(f"Planner error: {exc}")
        return {
            "title": "Planner unavailable",
            "destination": "Unable to generate destination",
            "weather": "Not available",
            "route": "Not available",
            "itinerary": [],
            "tips": [
                "Please try again.",
                "Mention your starting city.",
                "Describe the kind of hidden place you want.",
            ],
        }
