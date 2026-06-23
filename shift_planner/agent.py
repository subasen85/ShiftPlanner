import os
import datetime
from google.adk.agents import Agent
from google.adk.models import Gemini
from google.genai import types
from dotenv import load_dotenv

from shift_planner.solver import ShiftSolver
from shift_planner.sheets_helper import (
    get_credentials,
    get_or_create_folder,
    get_or_create_spreadsheet,
    write_schedule_to_sheets,
)

# Load environment variables
load_dotenv()

# Setup Gemini model configuration for ADK
model_name = os.environ.get("GEMINI_MODEL_NAME", "gemini-2.5-flash")

# Define tools for the agent

def generate_shift_schedule(employees: list[str]) -> list[dict]:
    """
    Generates a balanced shift schedule for the period from 6th July 2026 to 2nd August 2026
    satisfying all constraints:
    - 2 off days (weekoffs) per week per employee.
    - Exactly 1 person in Shift1 (07:00-15:00 IST) and 1 person in Shift2 (12:00-20:00 IST) on Sundays.
    - Balanced weekday coverage.

    Args:
        employees: List of employee names.

    Returns:
        List of daily schedule records containing Date, Day, Employee name, and Assignment.
    """
    start_date = datetime.date(2026, 7, 6)
    end_date = datetime.date(2026, 8, 2)
    solver = ShiftSolver(employees)
    return solver.generate_schedule(start_date, end_date)

def upload_schedule_to_sheets(employees: list[str], schedule: list[dict]) -> str:
    """
    Attempts to upload the generated schedule to a Google Sheet named 'Shift_Details_jul_2026'
    inside the folder 'KaggleCap' on Google Drive. If credentials are not present,
    it saves local CSV and Markdown backup files and returns instructions for setup.

    Args:
        employees: List of employee names.
        schedule: List of daily schedule records.

    Returns:
        A string message describing the outcome.
    """
    # 1. Generate local backup files first
    csv_file = "Shift_Details_jul_2026.csv"
    md_file = "Shift_Details_jul_2026.md"
    
    # Generate CSV
    import csv
    # Pivot for CSV
    employees_sorted = sorted(list(set(employees)))
    headers = ["Date", "Day"] + employees_sorted
    
    from collections import defaultdict
    pivoted = defaultdict(dict)
    for r in schedule:
        pivoted[(r["Date"], r["Day"])][r["Employee"]] = r["Assignment"]
        
    try:
        with open(csv_file, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for (date, day) in sorted(pivoted.keys()):
                row = [date, day]
                for emp in employees_sorted:
                    row.append(pivoted[(date, day)].get(emp, ""))
                writer.writerow(row)
                
        # Generate Markdown
        with open(md_file, mode="w", encoding="utf-8") as f:
            f.write("# Shift Details July 2026\n\n")
            f.write("| " + " | ".join(headers) + " |\n")
            f.write("| " + " | ".join(["---"] * len(headers)) + " |\n")
            for (date, day) in sorted(pivoted.keys()):
                row = [date, day]
                for emp in employees_sorted:
                    val = pivoted[(date, day)].get(emp, "")
                    if val == "Weekoff":
                        row.append(f"**{val}**")  # Bold weekoff locally
                    else:
                        row.append(val)
                f.write("| " + " | ".join(row) + " |\n")
    except Exception as e:
        print(f"Error saving local backup files: {e}")

    # 2. Check credentials
    creds = get_credentials()
    if creds is None:
        return (
            f"Local backup files saved successfully:\n"
            f"- CSV: `{csv_file}`\n"
            f"- Markdown: `{md_file}`\n\n"
            f"**Google Sheets integration was skipped** because no credentials were found.\n"
            f"To enable direct Google Sheets upload, please place either `credentials.json` "
            f"(OAuth Client) or `service_account.json` (Service Account) in the project directory."
        )
        
    try:
        # Build drive service
        from googleapiclient.discovery import build
        drive_service = build("drive", "v3", credentials=creds)
        
        # Get or create folder
        folder_id = get_or_create_folder(drive_service, "KaggleCap")
        
        # Get or create spreadsheet
        spreadsheet_id = get_or_create_spreadsheet(drive_service, folder_id, "Shift_Details_jul_2026")
        
        # Populate sheet
        write_schedule_to_sheets(creds, spreadsheet_id, employees, schedule)
        
        return (
            f"Successfully uploaded schedule to Google Sheet named 'Shift_Details_jul_2026' "
            f"inside the Google Drive folder 'KaggleCap'.\n"
            f"Local backups also saved as `{csv_file}` and `{md_file}`."
        )
    except Exception as e:
        return (
            f"Failed to upload to Google Sheets due to an error: {e}.\n"
            f"However, local backups were successfully saved to `{csv_file}` and `{md_file}`."
        )

# Define the root agent
root_agent = Agent(
    name="shift_planner_agent",
    model=Gemini(
        model=model_name,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=(
        "You are an AI shift planning assistant. Given a list of employee names:\n"
        "1. Run the 'generate_shift_schedule' tool to calculate the shift schedule for the period (6th July 2026 to 2nd August 2026).\n"
        "2. Run the 'upload_schedule_to_sheets' tool to save it locally and upload it to Google Sheets.\n"
        "3. Present the resulting schedule back to the user in a beautiful format and explain briefly how it satisfies the required constraints:\n"
        "   - Shift1 (07:00 - 15:00 IST) and Shift2 (12:00 - 20:00 IST).\n"
        "   - Each employee gets exactly 2 weekoff days per week.\n"
        "   - On Sundays, exactly 1 employee works Shift1 and 1 works Shift2, and the other employees are on weekoff.\n"
        "   - Weekday coverage is balanced."
    ),
    tools=[generate_shift_schedule, upload_schedule_to_sheets],
)
