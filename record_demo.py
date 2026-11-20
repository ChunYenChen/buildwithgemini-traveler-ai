import os
import time
from playwright.sync_api import sync_playwright

output_dir = "/config/Desktop/BuildWithGemini/demo_frames"
os.makedirs(output_dir, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path="/usr/bin/google-chrome",
        headless=True,
        args=["--no-sandbox", "--disable-gpu", "--window-size=1280,800"]
    )
    context = browser.new_context(
        viewport={"width": 1280, "height": 800},
        record_video_dir="/config/Desktop/BuildWithGemini/demo_raw",
        record_video_size={"width": 1280, "height": 800}
    )
    page = context.new_page()
    page.goto("http://localhost:8080")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # Demo Part 1: What the app does best - Allergy-aware personalized travel itinerary
    # Type user prompt
    input_box = page.locator("#input")
    input_box.click()
    prompt1 = "I am planning a 3-day trip to Tokyo. I love historic shrines and ramen, but I have a severe peanut allergy. Can you suggest a personalized day-by-day plan?"
    for char in prompt1:
        input_box.type(char, delay=25)
    time.sleep(1)
    page.locator("#send-btn").click()

    # Wait for the agent to reply (up to 45 seconds)
    print("Waiting for response 1...")
    page.wait_for_selector(".msg.agent:nth-of-type(1) .bubble:not(:empty)", timeout=60000)
    # Wait until it is not "…"
    for _ in range(60):
        content = page.locator(".msg.agent:nth-of-type(1) .bubble").text_content()
        if content and content.strip() != "…":
            break
        time.sleep(1)
    print("Response 1 received!")
    time.sleep(4)

    # Demo Part 2: Richer prompt showing off tool call / database lookup / generated image
    input_box = page.locator("#input")
    input_box.click()
    prompt2 = "Can you look up our saved destinations in the database and generate a scenic postcard image for Kyoto?"
    for char in prompt2:
        input_box.type(char, delay=25)
    time.sleep(1)
    page.locator("#send-btn").click()

    print("Waiting for response 2...")
    page.wait_for_selector(".msg.agent:nth-of-type(2) .bubble:not(:empty)", timeout=60000)
    for _ in range(60):
        content = page.locator(".msg.agent:nth-of-type(2) .bubble").text_content()
        if content and content.strip() != "…":
            break
        time.sleep(1)
    print("Response 2 received!")
    time.sleep(6)

    context.close()
    browser.close()
    print("Demo recording complete!")
