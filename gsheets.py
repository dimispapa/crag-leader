import gspread
from google.oauth2.service_account import Credentials


class GoogleSheetsClient:
    """
    A client to interact with Google Sheets using gspread and Google OAuth2.

    Attributes:
        creds_file (str): Path to the JSON file with Google service account credentials.
        scope (list): List of OAuth2 scope for accessing Google Sheets and Drive.
        client (gspread.Client): Authorized gspread client.
    """

    def __init__(self, creds_file, scope):
        """
        Initialize the GoogleSheetsClient with the given credentials file and scope.

        Args:
            creds_file (str): Path to the JSON file with Google service account credentials.
            scope (list): List of OAuth2 scope for accessing Google Sheets and Drive.
        """
        self.creds_file = creds_file
        self.scope = scope
        self.client = self._authorize_client()

    def _authorize_client(self):
        """
        Authorize the gspread client using the provided credentials and scope.

        Returns:
            gspread.Client: Authorized gspread client.
        """
        creds = Credentials.from_service_account_file(self.creds_file)
        scoped_creds = creds.with_scopes(self.scope)
        return gspread.authorize(scoped_creds)

    def open_sheet(self, sheet_name):
        """
        Open a Google Sheet by its name.

        Args:
            sheet_name (str): The name of the Google Sheet to open.

        Returns:
            gspread.Spreadsheet: The opened Google Sheet.
        """
        return self.client.open(sheet_name)

    def get_sheet_data(self, sheet_name, worksheet_name):
        """
        Retrieve all values from a specific worksheet in a Google Sheet.

        Args:
            sheet_name (str): The name of the Google Sheet.
            worksheet_name (str): The name of the worksheet within the Google Sheet.

        Returns:
            list: A list of lists containing the worksheet data.
        """
        sheet = self.open_sheet(sheet_name)
        worksheet = sheet.worksheet(worksheet_name)
        return worksheet.get_all_values()


def main():
    """
    Main function to create a GoogleSheetsClient instance and retrieve data from specified sheets.
    """
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
