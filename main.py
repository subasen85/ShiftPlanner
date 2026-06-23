import sys
import os
from dotenv import load_dotenv

# Load env variables from .env file
load_dotenv()

# Setup correct import path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from shift_planner.agent import root_agent

def main():
    print("=" * 60)
    print("        WELCOME TO THE GOOGLE ADK SHIFT PLANNER")
    print("=" * 60)
    print("Please feed in the employee names one by one.")
    print("Type 'EOE' (End of Employees) and press Enter when you are done.\n")
    
    employees = []
    while True:
        try:
            line = input(f"Enter employee {len(employees) + 1} name (or EOE): ").strip()
            if not line:
                continue
            if line.upper() == "EOE":
                break
            employees.append(line)
        except (KeyboardInterrupt, EOFError):
            print("\nExiting planner.")
            return

    if not employees:
        print("No employees provided. Exiting.")
        return

    print("\nPlease enter the schedule date range.")
    start_date_str = ""
    while not start_date_str:
        try:
            val = input("Enter Start Date (DD-MMM-YYYY, e.g. 06-Jul-2026): ").strip()
            if val:
                start_date_str = val
        except (KeyboardInterrupt, EOFError):
            print("\nExiting planner.")
            return

    end_date_str = ""
    while not end_date_str:
        try:
            val = input("Enter End Date (DD-MMM-YYYY, e.g. 02-Aug-2026): ").strip()
            if val:
                end_date_str = val
        except (KeyboardInterrupt, EOFError):
            print("\nExiting planner.")
            return

    print(f"\nCollected employees: {', '.join(employees)}")
    print(f"Date Range: {start_date_str} to {end_date_str}")
    print("Initializing ADK Shift Planner Agent and generating schedule...\n")
    
    try:
        # Initialize ADK runner and session
        session_service = InMemorySessionService()
        session = session_service.create_session_sync(user_id="user", app_name="shift-planner")
        runner = Runner(agent=root_agent, session_service=session_service, app_name="shift-planner")
        
        # Define user message
        prompt_text = (
            f"Please generate the shift schedule for the following employees: {', '.join(employees)} "
            f"from {start_date_str} to {end_date_str}. "
            f"Then save it locally and upload it to Google Sheets in folder 'KaggleCap'."
        )
        message = types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt_text)]
        )
        
        # Run agent stream
        events = runner.run(
            new_message=message,
            user_id="user",
            session_id=session.id,
            run_config=RunConfig(streaming_mode=StreamingMode.SSE)
        )
        
        # Process and display output stream
        print("Agent Response:")
        print("-" * 60)
        for event in events:
            if hasattr(event, "content") and event.content:
                if hasattr(event.content, "parts") and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            print(part.text, end="", flush=True)
        print("\n" + "-" * 60)
        print("ShiftPlanner completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nAn error occurred during execution: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
