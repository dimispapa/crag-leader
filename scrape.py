import gspread
from google.oauth2.service_account import Credentials

class GoogleSheetsClient:
    def __init__(self, creds_file, scope):
        self.creds_file = creds_file
        self.scope = scope
        self.client = self._authorize_client()

    def _authorize_client(self):
        creds = Credentials.from_service_account_file(self.creds_file)
        scoped_creds = creds.with_scopes(self.scope)
        return gspread.authorize(scoped_creds)

    def open_sheet(self, sheet_name):
        return self.client.open(sheet_name)

    def get_sheet_data(self, sheet_name, worksheet_name):
        sheet = self.open_sheet(sheet_name)
        worksheet = sheet.worksheet(worksheet_name)
        return worksheet.get_all_values()

def main():
    # Define the scope and credentials file
    SCOPE = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive"
    ]
    CREDS_FILE = "creds.json"

    # Create an instance of GoogleSheetsClient
    gsc = GoogleSheetsClient(CREDS_FILE, SCOPE)

    # Access and print data from boulders, routes, and ascents sheets
    boulder_data = gsc.get_sheet_data("boulders", "data")
    print("Boulder Data:", boulder_data)

    route_data = gsc.get_sheet_data("routes", "data")
    print("Route Data:", route_data)

    ascent_data = gsc.get_sheet_data("ascents", "data")
    print("Ascent Data:", ascent_data)

if __name__ == "__main__":
    main()
