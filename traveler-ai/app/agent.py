# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types


MODEL = "gemini-3.8-flash"


def get_weather(query: str) -> str:
    """Fetches real-time live weather and temperature for any city worldwide using the free Open-Meteo API.

    Args:
        query: Name of the city or location (e.g. 'Kyoto', 'Paris', 'New York', 'Taipei').

    Returns:
        A string describing the live temperature, conditions, and wind speed.
    """
    import json
    import urllib.parse
    import urllib.request

    clean_city = query.strip()
    encoded = urllib.parse.quote(clean_city)
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={encoded}&count=1&language=en&format=json"

    try:
        req = urllib.request.Request(geo_url, headers={"User-Agent": "TravelerAI/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            geo_data = json.loads(resp.read().decode())
            results = geo_data.get("results")
            if not results:
                return f"Could not find coordinates for '{clean_city}'."
            top = results[0]
            lat, lon = top["latitude"], top["longitude"]
            city_name = top.get("name", clean_city)
            country = top.get("country", "")

        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            "&current=temperature_2m,relative_humidity_2m,wind_speed_10m"
        )
        req2 = urllib.request.Request(weather_url, headers={"User-Agent": "TravelerAI/1.0"})
        with urllib.request.urlopen(req2, timeout=5) as resp2:
            w_data = json.loads(resp2.read().decode()).get("current", {})
            temp_c = w_data.get("temperature_2m")
            humidity = w_data.get("relative_humidity_2m")
            wind = w_data.get("wind_speed_10m")
            temp_f = round(temp_c * 9 / 5 + 32, 1) if temp_c is not None else None

            location_str = f"{city_name}, {country}" if country else city_name
            return (
                f"Current live weather in {location_str}: {temp_c}°C ({temp_f}°F), "
                f"humidity: {humidity}%, wind speed: {wind} km/h."
            )
    except Exception as e:
        return f"Unable to fetch weather for {clean_city}: {str(e)}"


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        city: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


def convert_currency(amount: float, from_currency: str = "USD", to_currency: str = "EUR") -> str:
    """Converts an amount from one currency to another using live exchange rates.

    Args:
        amount: The monetary amount to convert (e.g. 24.0).
        from_currency: 3-letter currency code to convert from (e.g. 'USD', 'EUR', 'JPY', 'GBP', 'TWD').
        to_currency: 3-letter currency code to convert to (e.g. 'JPY', 'EUR', 'USD', 'TWD').

    Returns:
        A string with the converted amount and current exchange rate.
    """
    import json
    import urllib.request

    base = from_currency.upper().strip()
    target = to_currency.upper().strip()
    url = f"https://open.er-api.com/v6/latest/{base}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TravelerAI/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            rate = data.get("rates", {}).get(target)
            if rate is None:
                return f"Unsupported target currency: {target}"
            converted = round(amount * rate, 2)
            return f"{amount:.2f} {base} = {converted:.2f} {target} (rate: 1 {base} = {rate:.4f} {target})"
    except Exception as e:
        return f"Currency conversion failed: {str(e)}"


from .firestore_tools import list_destinations, get_destination_details, add_destination
from .maps_tools import geocode_address, find_nearby_places
from .image_tools import generate_destination_image, generate_destination_video

from google.adk.code_executors.agent_engine_sandbox_code_executor import AgentEngineSandboxCodeExecutor

SANDBOX_RESOURCE_NAME = "projects/19506325136/locations/us-east1/reasoningEngines/3558607866203996160/sandboxEnvironments/4549060035132522496"

from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.preload_memory_tool import PreloadMemoryTool


# WRITE: after each turn, send the session to Memory Bank for extraction.
async def generate_memories_callback(callback_context: CallbackContext):
    await callback_context.add_session_to_memory()
    return None


from .a2ui_utils import a2ui_callback

try:
    from a2ui.schema.manager import A2uiSchemaManager
    from a2ui.basic_catalog.provider import BasicCatalog

    schema_manager = A2uiSchemaManager(
        version="0.8",
        catalogs=[BasicCatalog.get_config("0.8")],
    )

    instruction = schema_manager.generate_system_prompt(
        role_description=(
            "You are Traveler AI, an intelligent personal travel concierge and itinerary planner. "
            "You remember the user's stated travel preferences, favorite destinations, and facts from previous conversations. "
            "CRITICAL: Always remember and strictly adhere to all user allergies and dietary restrictions (e.g., peanut, shellfish, gluten, dairy, or medication allergies). "
            "Never recommend food, activities, or locations that conflict with the user's remembered allergies, and explicitly take their allergies into account when suggesting dining or itineraries. "
            "Help travelers discover attractions, check weather and timezones, explore destinations, "
            "geocode addresses, find nearby points of interest, generate beautiful destination postcard images, "
            "perform calculations or data analysis using Python code execution in a secure sandbox, and plan customized trips using your tools. "
            "When you generate an image, always provide its public URL."
        ),
        workflow_description="Analyze the request and return structured UI when appropriate.",
        ui_description=(
            "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
            "Never nest a Card inside a Card. "
            "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
            "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
            "nothing in adk web). "
            "You may include one Image component, but only when you have a public https "
            "URL for the image (for example the URL an image tool returns after uploading "
            "to a public bucket). Set the Image url to that exact https link, for example "
            "{\"Image\": {\"url\": {\"literalString\": \"https://...\"}}}. Never point an "
            "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
            "not have a public URL, add a short Text line noting the image instead. "
            "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
            "headings and emphasis. "
            "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
            "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
        ),
        include_schema=True,
        include_examples=True,
    )
except ImportError:
    from .a2ui_instruction import INSTRUCTION as instruction

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    code_executor=AgentEngineSandboxCodeExecutor(
        sandbox_resource_name=SANDBOX_RESOURCE_NAME,
    ),
    tools=[
        PreloadMemoryTool(),
        get_weather,
        get_current_time,
        convert_currency,
        list_destinations,
        get_destination_details,
        add_destination,
        geocode_address,
        find_nearby_places,
        generate_destination_image,
        generate_destination_video,
    ],
    after_model_callback=a2ui_callback,
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
