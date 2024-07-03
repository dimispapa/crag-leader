"""
A module containg classes and method used for calculating the scores, bonuses,
based on the ascent log and aggregating the scores in a leaderboard.
"""
from time import sleep
from gspread import Client
from pandas import DataFrame
from rich.prompt import Prompt
from modules.helper import clear, rank_leaderboard
from modules.rich_utils import console, display_table, show_help


class ScoreCalculator():
    """
    A class module containing methods for the purpose of calculating
    the various scores and leaderboards from the ascent logs.

    Attributes:
        ascent_data (pd.DataFrame): A DataFrame containing ascent logs.
        gsc (gspread.Client): An authorized gspread client instance.
        base_points_dict (dict): A dictionary mapping grades to base points.
        vol_bonus_incr (int): The increment value for volume bonuses.
        vol_bonus_points (int): The points awarded per volume bonus increment.
        unique_asc_bonus (float): A bonus factor for unique ascents.
    """

    def __init__(self, gs_client: Client, ascent_data: DataFrame):
        """
        Initialize the ScoreCalculator class instance.

        Args:
            gs_client (gspread.Client): An authorized gspread client instance.
            ascent_data (pandas.DataFrame): A DataFrame containing ascent logs.
        """
        self.scoring_table = ascent_data
        self.gsc = gs_client
        # get the scoring system parameters
        self.base_points_dict, self.vol_bonus_incr, \
            self.vol_bonus_points, self.unique_asc_bonus = \
            self.get_scoring_params('scoring_system')
        # init empty agg table df
        self.aggregate_table = DataFrame()

    def get_scoring_params(self, file_name: str):
        """
        Retrieve scoring system parameters from Google Sheets
        and reformat them for easier use.

        Args:
            file_name (str): The name of the Google Sheets file containing the
                                scoring system parameters.

        Returns:
            tuple: A tuple containing the following elements:
                - base_points_dict (dict): A dictionary mapping grades to base
                                            points.
                - vol_bonus_incr (int): The increment value for
                                        volume bonuses.
                - vol_bonus_points (int): The points awarded per
                                            volume bonus increment.
                - unique_asc_bonus (float): A bonus factor for unique ascents.
        """
        # get scoring system parameters
        base_points_data = self.gsc.get_sheet_data(file_name,
                                                   'base_points')
        volume_bonus_data = self.gsc.get_sheet_data(file_name,
                                                    'volume_bonus')
        unique_ascent_data = self.gsc.get_sheet_data(file_name,
                                                     'unique_ascent_bonus')

        # reformat scoring system params into variables for easier use
        base_points_dict = {str(row['Grade']): int(row['Points'])
                            for row in base_points_data}

        vol_bonus_incr = int(
            volume_bonus_data[0].get('Bonus_increment'))

        vol_bonus_points = int(
            volume_bonus_data[0].get('Points_per_increment'))

        unique_asc_bonus = float(
            unique_ascent_data[0].get('Bonus_factor'))

        return (base_points_dict,
                vol_bonus_incr,
                vol_bonus_points,
                unique_asc_bonus)

    def calc_base_points(self):
        """
        Calculate the base points for each ascent and add it to the DataFrame.
        If the ascent type is "flash", the base points are doubled.

        Returns:
            pandas.DataFrame: A DataFrame with the calculated base points for
                                each ascent.
        """
        # define a mappping function to apply on the dataframe
        def get_base_points(row):
            base_points = self.base_points_dict.get(row['Grade'], 0)
            if row['Ascent Type'] == 'flash':
                base_points *= 2
            return base_points

        # apply the mapping function to get the base points for each ascent
        self.scoring_table['Base Points'] = self.scoring_table.apply(
            get_base_points, axis=1).astype(int)

        return self.scoring_table

    def calc_volume_bonus(self):
        """
        Calculate the volume bonus for each climber based on the number of
        ascents.

        Returns:
            pandas.DataFrame: A DataFrame with the volume bonus for each
                                climber.
        """
        # group the scoring table by the climber and count numbers of ascents
        volume_bonus = self.scoring_table.groupby(
            'Climber Name').size().reset_index(name='Num Ascents')
        # calculate the volume bonus by getting the increments
        # through floor division and multiplying by the bonus points
        volume_bonus['Volume Score'] = \
            (volume_bonus['Num Ascents'] //
             self.vol_bonus_incr) * self.vol_bonus_points
        # merge the volume bonus df on the scoring table
        # via a left join
        self.scoring_table = \
            self.scoring_table.merge(
                volume_bonus[['Climber Name', 'Volume Score']],
                on='Climber Name', how='left')
        # fill potential na values with zero to allow summation later
        self.scoring_table['Volume Score'] = \
            self.scoring_table['Volume Score'].fillna(0).astype(int)

    def calc_unique_ascent(self):
        """
        Calculate the unique ascent bonus for each ascent if applicable.

        Returns:
            pandas.DataFrame: A DataFrame with the unique ascent bonus for
                                ascent applied if applicable.
        """
        # Group by route name and count the number of unique ascents
        ascent_counts = self.scoring_table.groupby(
            'Route Name').size().reset_index(name='Ascent Count')

        # Merge the ascent counts with the scoring table
        self.scoring_table = self.scoring_table.merge(
            ascent_counts, on='Route Name', how='left')

        # Calculate the unique ascent bonus
        self.scoring_table['Unique Ascent Score'] = self.scoring_table.apply(
            lambda row: row['Base Points'] +
            (row['Base Points'] * self.unique_asc_bonus)
            if row['Ascent Count'] == 1 else 0,
            axis=1
        ).astype(int)

    def aggregate_scores(self):
        """
        Aggregates the scoring columns by Climber Name, summing the
        Base Points and Unique Ascent while getting the max of Volume Bonus.

        Returns:
            pandas.DataFrame: The aggregated scoring table.
        """
        # group by climber and aggregate the scoring columns
        self.aggregate_table = self.scoring_table.groupby('Climber Name').agg({
            'Base Points': 'sum',
            'Volume Score': 'max',
            'Unique Ascent Score': 'sum'
        })
        # get the total tally based on the various scoring components
        self.aggregate_table['Total Score'] = \
            self.aggregate_table['Base Points'] + \
            self.aggregate_table['Volume Score'] + \
            self.aggregate_table['Unique Ascent Score']

        return self.aggregate_table

    def leaderboard_mode(self):
        """
        Present the user with different leaderboard options and display the
        selected leaderboard.
        """
        # parse aggregate table in variable for readability
        agg_table = self.aggregate_table

        # Dictionary to map user choices to leaderboard columns and
        # descriptions
        leaderboard_options = {
            '1': ('Total Score', 'Overall leaderboard - ranks climbers '
                  'after summing up the Base Points based on grade (double '
                  'points for flash), Volume Score and Unique Ascent Score.'),
            '2': ('Volume Score', 'Volume leaderboard - ranks climbers based '
                  'on number of ascents counting 25 points every 5 ascents.'),
            '3': ('Unique Ascent Score', 'Unique Ascents leaderboard - ranks '
                  'climbers by only counting unique ascents and awarding for'
                  'double the normal base points for the grade.')
        }

        # keep looping until user decides to exit
        while True:
            # Present the options to the user
            console.print("\nPlease choose a leaderboard to view or type "
                          "'help' for more information:",
                          style="bold cyan")
            console.print("1 - Total Score leaderboard", style="bold cyan")
            console.print("2 - Volume leaderboard", style="bold cyan")
            console.print("3 - Unique Ascents leaderboard", style="bold cyan")
            console.print("4 - Master Grade leaderboard", style="bold cyan")
            console.print("5 - Exit", style="bold cyan")

            choice = Prompt.ask("[bold cyan]Enter your choice (1-5)").strip()

            # if choice is 1, 2 or 3
            if choice in leaderboard_options:
                # Clear the terminal
                clear()
                # process the leaderboard
                lead_option, description = leaderboard_options[choice]
                leaderboard = rank_leaderboard(agg_table, lead_option)
                # display the leaderboard
                display_table(description, leaderboard)

            # Grade leaderboard
            elif choice == '4':
                # clear the terminal
                clear()
                # ask user to input a grade
                grade = Prompt.ask("[bold cyan]"
                                   "Enter the grade (e.g., 3, 6A, 9A): "
                                   ).strip().upper()
                # filter the scoring table based on that grade
                grade_leaderboard = \
                    self.scoring_table.loc[
                        self.scoring_table['Grade'] == grade]
                # group by the climber and count the ascents per that grade
                grade_leaderboard = grade_leaderboard.groupby(
                    'Climber Name').size().reset_index(
                        name=f'Num of {grade} Ascents'
                ).set_index('Climber Name')
                # sort and rank the leaderboard
                grade_leaderboard = rank_leaderboard(
                    grade_leaderboard[f'Num of {grade} Ascents'],
                    f'Num of {grade} Ascents'
                )
                # display the leaderboard
                display_table(f"\nMaster Grade Leaderboard for {grade}",
                              leaderboard)

            # Exit the loop
            elif choice == '5':
                clear()
                console.print("\nExiting...\n", style="bold red")
                break

            # display help options
            elif choice == 'help':
                clear()
                show_help()

            # Invalidate choice
            else:
                clear()
                console.print(f"\nInvalid choice. You've entered '{choice}'."
                              " Please enter a number between 1 and 5.\n",
                              style="bold red")

            # introduce slight delay to allow user to view output before
            # prompting again
            sleep(1)

    def calculate_scores(self):
        """
        Calculate all scores and bonuses for each climber.

        Returns:
            pandas.DataFrame: An aggregate DataFrame with the scores
                                for each climber.
        """
        self.calc_base_points()
        self.calc_volume_bonus()
        self.calc_unique_ascent()
        aggregate_table = self.aggregate_scores()

        return aggregate_table
