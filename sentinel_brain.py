import gspread
from datetime import datetime
import time
import os
from dotenv import load_dotenv
from openai import OpenAI

# --- 1. SETUP & SECURITY ---
load_dotenv()
SHEET_ID = os.getenv("SHEET_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY or not SHEET_ID:
    print("❌ ERROR: Missing keys in .env file!")
    exit()

RISK_THRESHOLD_DAYS = 21
MAU_DROP_THRESHOLD = 0.50
GHOST_THRESHOLD = 2

client = OpenAI(api_key=OPENAI_API_KEY)

# --- 2. HELPER FUNCTIONS ---
def calculate_days_ago(date_string):
    try:
        date_format = "%Y-%m-%d"
        past_date = datetime.strptime(str(date_string), date_format)
        return (datetime.now() - past_date).days
    except ValueError:
        return 0

def get_today_str():
    return datetime.now().strftime("%Y-%m-%d")

# --- 3. THE CORTEX (AI WRITER) ---
def generate_smart_email(company, csm, context, issue_type):
    print(f"   🧠 Thinking of a draft for {company} ({issue_type})...")
    
    if issue_type == "NEWBIE_STALLED":
        system_prompt = "You are an expert Customer Success Manager. Write a short, helpful, low-pressure email to a new client who hasn't logged in. Do not sound salesy."
        user_prompt = f"Client: {company}. CSM: {csm}. Context: Signed up {context['tenure']} days ago, no login for {context['dsll']} days. Ask if stuck on setup."
    elif issue_type == "VETERAN_GHOST":
        system_prompt = "You are a strategic Account Manager. Write a concise, professional email to a long-term client. Use a tone of 'concerned partner'."
        user_prompt = f"Client: {company}. CSM: {csm}. Context: Usage dropped {context['drop_pct']}% and ignored {context['unanswered']} emails. Ask for a 15-min strategy sync."
    else:
        return "Error: Unknown Type"

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating draft: {e}"

# --- 4. THE LOGIC ENGINE (ANALYZER) ---
def analyze_customer(customer):
    name = customer['Company Name']
    csm = customer['CSM Name']
    tenure_days = calculate_days_ago(customer['Account Live Date'])
    dsll = calculate_days_ago(customer['Last Login Date'])
    unanswered = customer['Unanswered Outreach Count']
    
    current_mau = customer['Current MAU']
    avg_mau = customer['Avg MAU (12mo)']
    drop_pct = (avg_mau - current_mau) / avg_mau if avg_mau > 0 else 0

    status = "HEALTHY"
    draft = ""

    # Rule A: Failed Onboard
    if tenure_days < 365:
        if dsll > RISK_THRESHOLD_DAYS:
            status = "RISK"
            context = {"tenure": tenure_days, "dsll": dsll}
            draft = generate_smart_email(name, csm, context, "NEWBIE_STALLED")

    # Rule B: Ghost
    else:
        if drop_pct > MAU_DROP_THRESHOLD and unanswered >= GHOST_THRESHOLD:
            status = "RISK"
            context = {"drop_pct": int(drop_pct*100), "unanswered": unanswered}
            draft = generate_smart_email(name, csm, context, "VETERAN_GHOST")

    return status, draft

# --- 5. THE ACTION ENGINE (EXECUTOR) ---
def execute_send(row_num, customer, worksheet, log_sheet):
    """Simulates sending email and updates the DB."""
    company = customer['Company Name']
    draft_body = customer['Rescue Draft']
    
    # Get the email address from Column L (Column 12)
    contact_email = customer.get('Contact Email', 'NO EMAIL FOUND')
    
    print(f"🚀 [SIMULATION] Sending email to: {contact_email} (Company: {company})...")
    
    time.sleep(1) # Simulate network delay
    
    # 1. Log to 'Sent Log' tab
    try:
        log_sheet.append_row([get_today_str(), company, contact_email, draft_body])
    except:
        print("   (Warning: Could not write to Sent Log tab - check if it exists)")
    
    # 2. Update the Main Sheet
    worksheet.update_cell(row_num, 8, get_today_str()) # Last Outreach Date
    
    new_count = int(customer['Unanswered Outreach Count']) + 1
    worksheet.update_cell(row_num, 9, new_count)       # Unanswered Count
    
    worksheet.update_cell(row_num, 10, "SENT")         # Status
    worksheet.update_cell(row_num, 11, "")             # Clear Draft
    
    print(f"✅ Action logged. Status updated to SENT.")

# --- 6. MAIN EXECUTION LOOP ---
print("🤖 Sentinel Agent Connecting (Master Mode)...")

try:
    gc = gspread.service_account(filename='credentials.json')
    sh = gc.open_by_key(SHEET_ID)
    worksheet = sh.sheet1
    
    # Try to connect to log sheet, if it fails, just warn
    try:
        log_sheet = sh.worksheet("Sent Log")
    except:
        log_sheet = None
        print("⚠️  Warning: 'Sent Log' tab not found. Logging will be skipped.")

    data = worksheet.get_all_records()

    for i, row in enumerate(data):
        row_num = i + 2
        current_status = row.get('Status', '')

        # STATE 1: EXECUTION (Human approved)
        if current_status == "APPROVED":
            execute_send(row_num, row, worksheet, log_sheet)

        # STATE 2: ANALYSIS (Needs checking)
        elif current_status != "SENT" and row.get('Rescue Draft', '') == "":
            new_status, new_draft = analyze_customer(row)
            
            if new_status == "RISK":
                print(f"✍️  Drafting email for {row['Company Name']}...")
                worksheet.update_cell(row_num, 10, new_status)
                worksheet.update_cell(row_num, 11, new_draft)
                time.sleep(1)

    print("\n✅ Master Cycle Complete.")

except Exception as e:
    print(f"❌ CRITICAL FAILURE: {e}")