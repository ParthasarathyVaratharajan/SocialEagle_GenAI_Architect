import win32com.client

# Step 1: Launch Outlook
outlook = win32com.client.Dispatch("Outlook.Application")

# Step 2: Create a new mail item
mail = outlook.CreateItem(0)  # 0 = olMailItem

# Step 3: Compose the email
mail.To = "hiring.manager@example.com"
mail.Subject = "Application for Sr. Technical Architect Role"
mail.Body = """Dear Hiring Manager,

I am writing to express my interest in the Sr. Technical Architect position.

With over 23 years of experience in data architecture, Power BI, and Azure Synapse, I bring a wealth of expertise.

Attached is my resume for your review.

Warm regards,
Parthasarathy Varatharajan
Sr. Technical Architect | Hexaware Technologies
"""

# Step 4: Attach a file
mail.Attachments.Add(r"Parthasarathy_Resume.pdf")  # Update path

# Step 5: Save as draft
mail.Save()