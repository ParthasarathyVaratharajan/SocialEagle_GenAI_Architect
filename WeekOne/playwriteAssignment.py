import asyncio
from playwright.async_api import async_playwright
from dotenv import load_dotenv
from pathlib import Path
import os
import pyautogui
import time


# Load environment variables from requirements.env
env_path = Path(__file__).parent / 'requirements.env'
load_dotenv(dotenv_path=env_path)

OUTLOOK_EMAIL = os.getenv("OUTLOOK_EMAIL")
OUTLOOK_PASSWORD = os.getenv("OUTLOOK_PASSWORD")

async def delete_junk_emails():
    if not OUTLOOK_EMAIL or not OUTLOOK_PASSWORD:
        print("❌ Environment variables not loaded. Check requirements.env.")
        return

    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=False, slow_mo=50)
        context = await browser.new_context()
        page = await context.new_page()

        print("🔐 Navigating to Outlook Web...")
        await page.goto("https://outlook.office.com/mail/")
        await page.wait_for_load_state('networkidle')

        print("📧 Entering email...")
        await page.fill('input[type="email"]', OUTLOOK_EMAIL)
        await page.click('input[type="submit"]')
        await page.wait_for_timeout(2000)

        print("🔑 Entering password...")
        await page.fill('input[type="password"]', OUTLOOK_PASSWORD)
        #await page.click('input[type="submit"]')
        await page.get_by_role("button", name="Next").click()
        await page.wait_for_timeout(3000)

        try:
            await page.wait_for_selector('input[id="idBtn_Back"]', timeout=1000)
            await page.click('input[id="idBtn_Back"]')  # Clicks "No"
            print("🚪 Skipped 'Stay signed in' prompt.")
        except:
            print("⚠️ 'Stay signed in' prompt not found—continuing.")

        no_button_location = pyautogui.locateCenterOnScreen('no_button.png', confidence=0.8)
        if no_button_location:
            pyautogui.click(no_button_location)
            print("🖱️ Clicked 'No' using pyautogui.")
        else:
            print("⚠️ 'No' button not found on screen.")

        # Handle "Stay signed in?" prompt
        if await page.is_visible('input[id="idBtn_Back"]'):
            await page.click('input[id="idBtn_Back"]')
            await page.wait_for_timeout(2000)

        print("📬 Waiting for mailbox to load...")
        await page.wait_for_selector('div[role="treeitem"]')

        print("🧭 Navigating to Junk Email folder...")
        await page.locator('text=Junk Email').click()
        await page.wait_for_timeout(3000)

        print("📌 Selecting all emails...")
        if await page.is_visible('button[aria-label="Select all"]'):
            await page.click('button[aria-label="Select all"]')
            await page.wait_for_timeout(1000)

            print("🗑️ Deleting selected emails...")
            if await page.is_visible('button[aria-label="Delete"]'):
                await page.click('button[aria-label="Delete"]')
                print("✅ Junk emails deleted successfully.")
            else:
                print("⚠️ Delete button not found.")
        else:
            print("⚠️ No emails found in Junk folder.")

        await page.screenshot(path="junk_cleanup_firefox.png")
        await browser.close()

asyncio.run(delete_junk_emails())