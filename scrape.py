import gspread
from google.oauth2.service_account import Credentials

# list APIs that the program has access to
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]

# create scoped credentials from json file
CREDS = Credentials.from_service_account_file("creds.json")
SCOPED_CREDS = CREDS.with_scopes(SCOPE)

# create gspread authorized client
GSPREAD_CLIENT = gspread.authorize(SCOPED_CREDS)

# access google sheets
BOULDERS_GSHEET = GSPREAD_CLIENT.open("boulders")
ROUTES_GSHEET = GSPREAD_CLIENT.open("routes")
ASCENTS_GSHEET = GSPREAD_CLIENT.open("ascents")

# test that access works
boulders_sheet = BOULDERS_GSHEET.worksheet("data")
boulder_data = boulders_sheet.get_all_values()
print(boulder_data)

routes_sheet = ROUTES_GSHEET.worksheet("data")
route_data = routes_sheet.get_all_values()
print(route_data)

ascents_sheets = ASCENTS_GSHEET.worksheet("data")
ascent_data = ascents_sheets.get_all_values()
print(ascent_data)
