import os
import time
from playwright.sync_api import sync_playwright

output_dir = "/config/Desktop/BuildWithGemini/demo_video"
os.makedirs(output_dir, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path="/usr/bin/google-chrome",
        headless=True,
        args=["--no-sandbox", "--disable-gpu", "--window-size=1280,840"]
    )
    context = browser.new_context(
        viewport={"width": 1280, "height": 840},
        record_video_dir=output_dir,
        record_video_size={"width": 1280, "height": 840}
    )
    page = context.new_page()
    page.goto("https://traveler-ai-frontend-19506325136.us-east1.run.app")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # -------------------------------------------------------------
    # Scene 1: What Traveler AI does best
    # Real-time weather, attraction discovery, and allergy-aware dining safety
    # -------------------------------------------------------------
    input_box = page.locator("#input")
    input_box.click()
    prompt1 = "What is the weather in Tokyo and find top attractions?"
    for char in prompt1:
        input_box.type(char, delay=35)
    time.sleep(1)
    page.locator("#send-btn").click()

    print("Sent Prompt 1. Waiting for response...")
    # Wait until response bubble exists and is not "…"
    for i in range(75):
        time.sleep(1)
        agents = page.locator(".msg.agent .bubble").all()
        if agents:
            text = agents[0].text_content()
            if text and text.strip() != "…":
                print(f"Prompt 1 response arrived at {i}s!")
                break
    time.sleep(5)

    # -------------------------------------------------------------
    # Scene 2: Richer prompt showing off Firestore DB lookup + Gemini Image Gen + A2UI
    # -------------------------------------------------------------
    input_box.click()
    prompt2 = "Look up our saved destinations in the database and generate a scenic postcard image for Kyoto"
    for char in prompt2:
        input_box.type(char, delay=35)
    time.sleep(1)
    page.locator("#send-btn").click()

    print("Sent Prompt 2. Waiting for response...")
    for i in range(75):
        time.sleep(1)
        agents = page.locator(".msg.agent .bubble").all()
        if len(agents) >= 2:
            text = agents[1].text_content()
            if text and text.strip() != "…":
                print(f"Prompt 2 response arrived at {i}s!")
                break
    time.sleep(7)

    # Smooth scroll down to show the rich A2UI postcard card
    page.evaluate("document.getElementById('log').scrollTo({top: document.getElementById('log').scrollHeight, behavior: 'smooth'})")
    time.sleep(5)

    context.close()
    browser.close()
    print("Demo video recorded successfully!")
