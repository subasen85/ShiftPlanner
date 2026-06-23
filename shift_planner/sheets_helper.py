import os
import pickle
import gspread
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from typing import List, Dict, Optional

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_credentials():
    """
    Loads Google API credentials from:
    1. service_account.json (Google Service Account)
    2. token.pickle (Cached user token)
    3. credentials.json (OAuth Client secrets, triggers local browser flow)
    """
    creds = None
    if os.path.exists("service_account.json"):
        return ServiceAccountCredentials.from_service_account_file(
            "service_account.json", scopes=SCOPES
        )
        
    if os.path.exists("token.pickle"):
        try:
            with open("token.pickle", "rb") as token:
                creds = pickle.load(token)
        except Exception:
            pass
            
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None
        
        if not creds:
            if not os.path.exists("credentials.json"):
                return None
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
            
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)
            
    return creds

def get_or_create_folder(drive_service, folder_name: str) -> str:
    """Finds or creates a folder on Google Drive and returns its ID."""
    query = f"mimeType = 'application/vnd.google-apps.folder' and name = '{folder_name}' and trashed = false"
    results = drive_service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get("files", [])
    if files:
        return files[0]["id"]
        
    file_metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder"
    }
    folder = drive_service.files().create(body=file_metadata, fields="id").execute()
    return folder.get("id")

def get_or_create_spreadsheet(drive_service, folder_id: str, sheet_name: str) -> str:
    """Finds or creates a spreadsheet inside a specific Google Drive folder."""
    query = f"mimeType = 'application/vnd.google-apps.spreadsheet' and name = '{sheet_name}' and '{folder_id}' in parents and trashed = false"
    results = drive_service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get("files", [])
    if files:
        return files[0]["id"]
        
    file_metadata = {
        "name": sheet_name,
        "mimeType": "application/vnd.google-apps.spreadsheet",
        "parents": [folder_id]
    }
    file = drive_service.files().create(body=file_metadata, fields="id").execute()
    return file.get("id")

def write_schedule_to_sheets(creds, spreadsheet_id: str, employees: List[str], schedule_records: List[Dict[str, any]]):
    """
    Populates and styles the spreadsheet with pivoted schedule data.
    Sets 'Weekoff' cells to red background and auto-fits columns.
    """
    gc = gspread.Client(auth=creds)
    sh = gc.open_by_key(spreadsheet_id)
    
    # Use the first worksheet
    worksheet = sh.get_worksheet(0)
    
    # Pivot records into a grid format
    employees = sorted(list(set(employees)))
    headers = ["Date", "Day"] + employees
    
    from collections import defaultdict
    pivoted = defaultdict(dict)
    for r in schedule_records:
        date = r["Date"]
        day = r["Day"]
        emp = r["Employee"]
        assignment = r["Assignment"]
        pivoted[(date, day)][emp] = assignment
        
    matrix = [headers]
    for date, day in sorted(pivoted.keys()):
        row = [date, day]
        for emp in employees:
            # Shorten names or keep full text as assigned
            val = pivoted[(date, day)].get(emp, "")
            row.append(val)
        matrix.append(row)
        
    num_rows = len(matrix)
    num_cols = len(headers)
    
    # Clear existing and update data
    worksheet.clear()
    worksheet.update("A1", matrix)
    
    # Set sheet column letter bounds
    def get_col_letter(col_idx):
        letter = ""
        while col_idx > 0:
            col_idx, remainder = divmod(col_idx - 1, 26)
            letter = chr(65 + remainder) + letter
        return letter
        
    last_col_letter = get_col_letter(num_cols)
    
    # Apply global cell alignment (Center/Middle)
    worksheet.format(f"A1:{last_col_letter}{num_rows}", {
        "horizontalAlignment": "CENTER",
        "verticalAlignment": "MIDDLE",
        "textFormat": {"fontFamily": "Inter", "fontSize": 10}
    })
    
    # Style header row (Dark grey background, bold text)
    worksheet.format(f"A1:{last_col_letter}1", {
        "textFormat": {"bold": True, "fontSize": 11},
        "backgroundColor": {"red": 0.85, "green": 0.85, "blue": 0.85}
    })
    
    # Apply batch update for conditional formatting and auto column resize
    sh.batch_update({
        "requests": [
            # Conditional formatting rule to color Weekoff cells RED
            {
                "addConditionalFormatRule": {
                    "rule": {
                        "ranges": [
                            {
                                "sheetId": worksheet.id,
                                "startRowIndex": 1,  # Skip header
                                "endRowIndex": num_rows,
                                "startColumnIndex": 2,  # Employee columns
                                "endColumnIndex": num_cols
                            }
                        ],
                        "booleanRule": {
                            "condition": {
                                "type": "TEXT_CONTAINS",
                                "values": [{"userEnteredValue": "Weekoff"}]
                            },
                            "format": {
                                "backgroundColor": {"red": 1.0, "green": 0.8, "blue": 0.8},
                                "textFormat": {
                                    "foregroundColor": {"red": 0.7, "green": 0.0, "blue": 0.0},
                                    "bold": True
                                }
                            }
                        }
                    },
                    "index": 0
                }
            },
            # Auto-fit column widths
            {
                "autoResizeDimensions": {
                    "dimensions": {
                        "sheetId": worksheet.id,
                        "dimension": "COLUMNS",
                        "startIndex": 0,
                        "endIndex": num_cols
                    }
                }
            }
        ]
    })
    print(f"Spreadsheet '{sh.title}' updated successfully inside folder.")
