import os
import time
import subprocess
from playwright.sync_api import sync_playwright

RAW_DIR = "/config/Desktop/BuildWithGemini/demo_recording/raw_video"
FINAL_VIDEO = "/config/Desktop/BuildWithGemini/demo_recording/book_concierge_demo.mp4"
os.makedirs(RAW_DIR, exist_ok=True)

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ]
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            record_video_dir=RAW_DIR,
            record_video_size={"width": 1280, "height": 800}
        )
        page = context.new_page()

        print("Navigating to Book Concierge...", flush=True)
        page.goto("http://localhost:8080")
        page.wait_for_selector("#welcome-card", timeout=10000)
        time.sleep(3.0)  # Showcase welcome card and suggestions

        # --- Turn 1: Trending sci-fi recommendation (Core Domain Best Feature) ---
        print("Clicking suggestion: 'Find trending books in science fiction'...", flush=True)
        pills = page.locator(".prompt-pill")
        pills.nth(1).click()

        # Wait for typing indicator to disappear
        print("Waiting for Turn 1 response...", flush=True)
        page.wait_for_selector(".dialogue-row.agent", timeout=15000)
        # Wait until typing indicator is gone from agent bubble
        page.wait_for_function(
            "document.querySelector('.dialogue-row.agent .typing-indicator') === null",
            timeout=60000
        )
        print("Turn 1 received!", flush=True)
        time.sleep(5.0)  # Let viewer read trending books

        # --- Turn 2: Rich prompt triggering custom cover art generation tool ---
        print("Typing prompt for book cover generation tool call...", flush=True)
        input_field = page.locator("#input")
        prompt_text = "Generate custom cover art for a new fantasy novel called The Starlight Alchemist"
        
        # Simulate typing naturally
        input_field.click()
        for char in prompt_text:
            input_field.type(char, delay=35)
        time.sleep(1.2)
        page.locator("button:has-text('Send')").click()

        # Wait for agent row 2 and typing indicator gone
        print("Waiting for Turn 2 response (image generation tool)...", flush=True)
        page.wait_for_function("document.querySelectorAll('.dialogue-row.agent').length >= 2", timeout=20000)
        page.wait_for_function(
            "document.querySelectorAll('.dialogue-row.agent')[1].querySelector('.typing-indicator') === null",
            timeout=90000
        )
        print("Turn 2 received!", flush=True)
        time.sleep(3.5)

        # Showcase the generated book cover & open lightbox modal
        cover_imgs = page.locator(".a2img")
        if cover_imgs.count() > 0:
            cover_img = cover_imgs.last
            print("Scrolling to generated cover image...", flush=True)
            cover_img.scroll_into_view_if_needed()
            time.sleep(1.8)
            print("Opening image modal lightbox...", flush=True)
            cover_img.click()
            time.sleep(4.5)  # Showcase lightbox view & download action
            close_btn = page.locator(".modal-btn.secondary")
            if close_btn.is_visible():
                close_btn.click()
                time.sleep(2.0)

        time.sleep(3.0)
        video_path = page.video.path()
        context.close()
        browser.close()
        print(f"Playwright video recorded to: {video_path}", flush=True)

        # Convert webm to polished high-compatibility mp4
        print(f"Converting video to MP4: {FINAL_VIDEO}...", flush=True)
        cmd = [
            "ffmpeg", "-y", "-i", video_path,
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-preset", "fast", "-crf", "22",
            FINAL_VIDEO
        ]
        subprocess.run(cmd, check=True)
        print("Demo video recording and conversion complete!", flush=True)

if __name__ == "__main__":
    run()
