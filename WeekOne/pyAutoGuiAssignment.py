import pyautogui
import time
import os

# Optional: Enable fail-safe (move mouse to top-left to abort)
pyautogui.FAILSAFE = True

# Step 1: Open Outlook via Windows Search
pyautogui.press('win')
time.sleep(1)
pyautogui.write('Outlook')
time.sleep(1)
pyautogui.press('enter')
time.sleep(8)  # Wait for Outlook to load

# Step 2: Click "New Email" (adjust coordinates for your screen)
#pyautogui.click(x=100, y=200)  # Replace with actual "New Email" button location
#time.sleep(3)

# Step 2: Open "New Email" using Ctrl + N
pyautogui.hotkey('ctrl', 'n')
time.sleep(3)



# Step 3: Type recipient
pyautogui.write("hiring.manager@example.com")
pyautogui.press("tab")  # Move to Subject

# Step 4: Type subject
pyautogui.write("Application for Sr. Technical Architect Role")
pyautogui.press("tab")  # Move to body

# Step 5: Type email body
email_body = [
    "Dear Hiring Manager,",
    "",
    "I hope this message finds you well. I am writing to express my interest in the Sr. Technical Architect position at your esteemed organization.",
    "",
    "With over 23 years of experience in data architecture, Power BI, and Azure Synapse, I bring a blend of technical mastery and ceremonial clarity to every project I undertake.",
    "",
    "Attached is my resume for your review. I would welcome the opportunity to discuss how my background aligns with your team’s goals.",
    "",
    "Thank you for considering my application.",
    "",
    "Warm regards,",
    "Parthasarathy Varatharajan",
    "Sr. Technical Architect | Hexaware Technologies"
]

for line in email_body:
    pyautogui.write(line)
    pyautogui.press("enter")


pyautogui.FAILSAFE = True
time.sleep(2)  # Give time to switch to Outlook

# Locate image on screen
location = pyautogui.locateCenterOnScreen('insert_button.png', confidence=0.9)

if location:
    pyautogui.moveTo(location)
    pyautogui.click()
    print("✅ Clicked on 'Insert' button.")
else:
    print("❌ 'Insert' button not found on screen.")


location = pyautogui.locateCenterOnScreen('Attach_button.png', confidence=0.9)

if location:
    pyautogui.moveTo(location)
    pyautogui.click()
    print("✅ Clicked on 'Attach' button.")
else:
    print("❌ 'Attach' button not found on screen.")

location = pyautogui.locateCenterOnScreen('browse_button.png', confidence=0.9)

if location:
    pyautogui.moveTo(location)
    pyautogui.click()
    print("✅ Clicked on 'Browse' button.")
else:
    print("❌ 'Browse' button not found on screen.")

# Step 6: Attach resume (simulate Alt+N, AF for Attach File)
pyautogui.hotkey("alt", "n")
time.sleep(1)
#pyautogui.press("a")
#pyautogui.press("f")
time.sleep(2)

# Step 7: Type file path and attach
resume_path = r"C:\Sarathy\SocialEagle\WeekOne\Parthasarathy_Resume.pdf"  # Update this path
pyautogui.write(resume_path)
pyautogui.press("enter")
time.sleep(2)

# Step 8: Save as draft (Ctrl + S)
pyautogui.hotkey("ctrl", "s")

# Step 9: Close Outlook (Alt + F4)
pyautogui.hotkey("alt", "f4")
time.sleep(2)

print("✅ Email drafted and saved with ceremonial clarity.")