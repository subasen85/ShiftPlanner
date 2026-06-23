# ShiftPlanner

A Google ADK-powered shift planner that generates a monthly shift schedule (from 6th July 2026 to 2nd August 2026) for offshore employees and writes it to Google Sheets.

## Features
- **Deterministic Solver**: Allocates shifts satisfying the following constraints:
  - Shifts: **Shift1 (07:00 - 15:00 IST)** and **Shift2 (12:00 - 20:00 IST)**.
  - Each employee has exactly **2 days off** (weekoffs/leave) per week.
  - **Sundays** have exactly **1 employee in Shift1** and **1 employee in Shift2** working (other employees are off).
  - Weekday coverage is balanced as evenly as possible.
- **Google Sheets Integration**: Creates a new sheet named `Shift_Details_jul_2026` inside the `KaggleCap/` folder on Google Drive and styles off-days/holidays in **RED**.
- **Local Fallback**: If Google Sheets credentials are not set up, it automatically prints the schedule in markdown and saves it to local CSV and Markdown files.

## Prerequisites
Ensure you have `uv` installed, or use standard `pip` with Python 3.11+.

## Installation
Run the following command to install dependencies:
```bash
uv pip install -e .
```

## Running the Planner
Run the entry point `main.py` using `uv`:
```bash
uv run python main.py
```
You will be prompted to enter employee names one by one. Enter `EOE` when finished:
```
Enter employee name (or EOE to finish): A
Enter employee name (or EOE to finish): B
Enter employee name (or EOE to finish): C
Enter employee name (or EOE to finish): X
Enter employee name (or EOE to finish): Y
Enter employee name (or EOE to finish): Z
Enter employee name (or EOE to finish): EOE
```

## Google Sheets Credentials Setup
To enable Google Sheets uploads, place either of the following in the project root:
- `credentials.json`: For OAuth Web flow (opens a browser window for login).
- `service_account.json`: For a Google Cloud Service Account.
