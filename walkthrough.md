# Walkthrough - ShiftPlanner Implementation

We have successfully built and verified the **ShiftPlanner** application, integrated it with Google Sheets via a Google ADK Agent, and pushed the repository to GitHub.

## Changes Made

### 1. Created Project Structure & Configs
- **[pyproject.toml](file:///f:/Senthil/Projects/SubaPOC/ShiftAllocationProject/pyproject.toml)**: Set up dependencies including `google-adk[gcp]`, `gspread`, `google-auth-oauthlib`, and `pandas`.
- **[requirements.txt](file:///f:/Senthil/Projects/SubaPOC/ShiftAllocationProject/requirements.txt)**: Python package dependency file for standard pip installations.
- **[.gitignore](file:///f:/Senthil/Projects/SubaPOC/ShiftAllocationProject/.gitignore)**: Properly configured to ignore credentials (`.env`, `credentials.json`, `service_account.json`, `token.pickle`) and locally generated outputs.
- **[.env.example](file:///f:/Senthil/Projects/SubaPOC/ShiftAllocationProject/.env.example)**: Added an environment template (removing the real Gemini API key to comply with security rules).
- **[README.md](file:///f:/Senthil/Projects/SubaPOC/ShiftAllocationProject/README.md)**: Documented setup, configuration, and execution commands.

### 2. Implemented Scheduling Solver
- **[shift_planner/solver.py](file:///f:/Senthil/Projects/SubaPOC/ShiftAllocationProject/shift_planner/solver.py)**: Built a deterministic constraint satisfaction solver that generates schedules for any list of employees for the period **6th July 2026 to 2nd August 2026**.
  - **Employee Off Days**: Each employee gets exactly 2 days off per week.
  - **Sunday Shifts**: Exactly 1 employee in Shift 1 (07:00 - 15:00 IST) and exactly 1 employee in Shift 2 (12:00 - 20:00 IST) work, while the remaining employees are off.
  - **Weekday Balance**: Coverage is balanced as evenly as possible.

### 3. Implemented Google Sheets & ADK Agent
- **[shift_planner/sheets_helper.py](file:///f:/Senthil/Projects/SubaPOC/ShiftAllocationProject/shift_planner/sheets_helper.py)**: Integrates Google Drive & Sheets. Searches for or creates a folder named `KaggleCap`, creates the sheet `Shift_Details_jul_2026`, writes the pivoted schedule, auto-adjusts columns, and applies **RED** conditional formatting for all `Weekoff` cells.
- **[shift_planner/agent.py](file:///f:/Senthil/Projects/SubaPOC/ShiftAllocationProject/shift_planner/agent.py)**: Configures the ADK Agent, binding the solver and sheets uploader as tools. If no credentials are found, it saves a local CSV and Markdown backup.
- **[main.py](file:///f:/Senthil/Projects/SubaPOC/ShiftAllocationProject/main.py)**: Entrypoint CLI. Wait for employee names, terminates on `EOE`, and invokes the ADK Agent.

---

## Validation Results

We executed the program locally using the active python virtual environment and verified that:
1. The solver successfully computed a valid schedule for 6 employees (`A`, `B`, `C`, `X`, `Y`, `Z`).
2. The ADK Agent ran successfully, saved local backups:
   - **CSV Backup**: `Shift_Details_jul_2026.csv`
   - **Markdown Backup**: `Shift_Details_jul_2026.md`
3. All constraints were checked and verified week-by-week:
   - Every employee has exactly 2 weekoffs per week.
   - Every Sunday has exactly 1 person in Shift1 and 1 person in Shift2 working.
   - Weekday coverage remains balanced.
4. The Git repository was initialized, and all code was committed and successfully pushed to the GitHub repository: https://github.com/subasen85/ShiftPlanner.
