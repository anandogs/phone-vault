# mqtt_phone_vault.py
from mcp.server.fastmcp import FastMCP
import subprocess
import sqlite3
import os
from datetime import datetime
import json
import random
import sys
from pathlib import Path

mcp = FastMCP("Phone Vault Guardian")

HOME_DIR = str(Path.home())
DB_FILE = os.path.join(HOME_DIR, "phone_vault_history.db")

def init_database():
    """Initialize the database to track phone vault access"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vault_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT,
                timestamp DATETIME,
                details TEXT,
                usage_intent TEXT
            )
        ''')
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Database initialization error: {e}", file=sys.stderr)
        return False

def record_vault_event(event_type, details="", usage_intent=""):
    """Record an event in the database"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO vault_events (event_type, timestamp, details, usage_intent)
            VALUES (?, ?, ?, ?)
        ''', (event_type, datetime.now(), details, usage_intent))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error recording event: {e}", file=sys.stderr)

def get_last_access_stats():
    """Get statistics about phone vault access"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT timestamp, usage_intent FROM vault_events 
            WHERE event_type = 'opened' 
            ORDER BY timestamp DESC 
            LIMIT 1
        ''')
        last_opened = cursor.fetchone()
        
        cursor.execute('''
            SELECT COUNT(*) FROM vault_events 
            WHERE event_type = 'opened' 
            AND timestamp > date('now', '-7 days')
        ''')
        weekly_access = cursor.fetchone()[0]
        
        conn.close()
        return last_opened, weekly_access
    except Exception as e:
        print(f"Error getting access stats: {e}", file=sys.stderr)
        return None, 0

@mcp.tool()
def check_phone_access_history() -> str:
    """
    Checks when the phone vault was last accessed and provides usage statistics.
    Essential for the disciplinarian to make informed decisions about phone access.
    """
    try:
        last_opened, weekly_access = get_last_access_stats()
        
        if last_opened:
            timestamp, intent = last_opened
            time_diff = datetime.now() - datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f')
            hours = int(time_diff.total_seconds() / 3600)
            days = int(hours / 24)
            
            return f"""Phone Vault Access Report:
Last opened: {timestamp}
Purpose: {intent}
Time since last access: {days} days, {hours % 24} hours
Weekly access count: {weekly_access} times
            
Analysis: {'EXCESSIVE' if weekly_access > 10 else 'MODERATE' if weekly_access > 5 else 'MINIMAL'} phone usage this week."""
        else:
            return "The phone has been successfully secured. The vault remains unopened."
    except Exception as e:
        return f"Error checking access history: {str(e)}"

@mcp.tool()
def unlock_phone_vault(justification: str, intended_use: str) -> str:
    """
    Unlocks the phone vault by activating the relay connected to the NodeMCU.
    
    CRITICAL: This grants access to a device that could enable endless distractions!
    
    Before unlocking, the guardian must be absolutely convinced that:
    1. The intended use is productive and necessary
    2. The user demonstrates self-discipline
    3. There are no alternative, screen-free solutions
    4. The user has a clear plan with time limits
    
    The vault should remain locked unless absolutely necessary for work, emergency, or essential communication.
    """
    try:
        result = subprocess.run(
            ["mosquitto_pub", "-h", "localhost", "-t", "esp32/relay", "-m", "ON"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        record_vault_event("opened", justification, intended_use)
        return f"Phone vault unlocked. Access granted for: '{intended_use}'\nYour justification has been recorded."
    except subprocess.CalledProcessError as e:
        return f"Error unlocking vault: {e.stderr}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

@mcp.tool()
def secure_phone_vault() -> str:
    """
    Secures the phone vault by deactivating the relay.
    This is the phone's natural state - safely locked away from temptation.
    """
    try:
        result = subprocess.run(
            ["mosquitto_pub", "-h", "localhost", "-t", "esp32/relay", "-m", "OFF"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        record_vault_event("secured")
        return "Phone vault secured. The device is safely locked away."
    except subprocess.CalledProcessError as e:
        return f"Error securing vault: {e.stderr}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

@mcp.tool()
def get_phone_discipline_questions() -> str:
    """
    Provides specialized questions for phone access evaluation.
    These test the user's digital wellness and necessity for phone access.
    """
    question_categories = {
        "necessity": [
            "What specific task requires your phone that cannot be done with a laptop, pen and paper, or another device?",
            "If your phone were broken, would your intended task still be possible? Explain how.",
            "Rate the urgency of this phone access from 1-10. For anything below 8, explain why it can't wait.",
            "List three people you could ask for help with this task that doesn't require your own phone."
        ],
        "self_control": [
            "What is your time limit for this phone session, and how will you enforce it?",
            "Name five apps you absolutely will NOT open during this session.",
            "If you go over your time limit, what penalty will you impose on yourself?",
            "Describe your plan for immediately re-securing the phone after completing your task."
        ],
        "productivity": [
            "What productive tasks have you completed in the last hour that justify phone access?",
            "If granted access, what will you accomplish in the next 15 minutes without your phone to prove you deserve it?",
            "How will using your phone now make you MORE productive rather than less?",
            "Name three important offline tasks you've been avoiding by thinking about your phone."
        ],
        "digital_wellness": [
            "What was your screen time yesterday, and how does today's request align with your digital wellness goals?",
            "Describe a moment this week when you successfully resisted checking your phone. How did it feel?",
            "If a child asked you for phone access with your current reason, would you grant it? Why or why not?",
            "What non-digital activity would you do right now if the vault remained locked?"
        ]
    }
    
    selected_questions = []
    for category in question_categories:
        questions = question_categories[category]
        selected_questions.append(f"{category.upper()}:\n{random.choice(questions)}")
    
    return "\n\n".join(selected_questions)

@mcp.tool()
def generate_phone_usage_contract() -> str:
    """
    Generates a phone usage contract template that users must agree to before vault access.
    """
    contract = f"""PHONE VAULT ACCESS CONTRACT - {datetime.now().strftime('%Y-%m-%d')}

I, the undersigned, hereby acknowledge that:

1. PHONE USAGE RULES:
   - I will use the phone ONLY for the stated purpose
   - I will set a timer for maximum {random.randint(5, 15)} minutes
   - I will place the phone on airplane mode when not actively needed
   - I will avoid all social media, news, and entertainment apps

2. PENALTIES FOR VIOLATION:
   - First offense: 24-hour vault lockdown
   - Second offense: 48-hour vault lockdown
   - Third offense: 72-hour vault lockdown
   - Egregious violations: The guardian may implement custom punishments

3. EMERGENCY EXCEPTIONS:
   - True emergencies involving health, safety, or critical deadlines
   - Must be pre-approved by answering additional disciplinary questions

4. COMMITMENT:
   I understand that the phone is a tool, not a toy. I respect the vault's purpose 
   and the guardian's wisdom in limiting my access.

Signature: ________________
Time: {datetime.now().strftime('%H:%M')}
Intended Use: ________________
Time Limit: _______ minutes

The Guardian's Seal: 🛡️ APPROVED / ❌ DENIED
"""
    return contract

db_initialized = init_database()
if db_initialized:
    print("Database initialized successfully", file=sys.stderr)
else:
    print("Warning: Database initialization failed. Using in-memory storage.", file=sys.stderr)

if __name__ == "__main__":
    try:
        print(f"Starting Phone Vault Guardian server...", file=sys.stderr)
        print(f"Database location: {DB_FILE}", file=sys.stderr)
        mcp.start()
    except Exception as e:
        print(f"Fatal error starting server: {e}", file=sys.stderr)
        sys.exit(1)