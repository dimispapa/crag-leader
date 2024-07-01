"""
A module containg classes and method used for calculating the scores, bonuses,
based on the ascent log and aggregating the scores in a leaderboard.
"""
from gspread import Client
from pandas import DataFrame


def rank_leaderboard(leaderboard: DataFrame, ranking_column: str):
    """
    Sort and rank the leaderboard based on the selected column.

    Args:
        leaderboard (pandas.DataFrame): The leaderboard to be ranked.
        ranking_column (str): The column name to rank it by.

    Returns:
        pandas.DataFrame: The sorted and ranked leaderboard.
    """
    # sort and rank the leaderboard before printing to the terminal
    ranked_leaderboard = leaderboard.sort_values(
        ranking_column, ascending=False)
    ranked_leaderboard['Rank'] = \
        ranked_leaderboard[ranking_column].rank(
            method='min', ascending=False).astype(int)

    return ranked_leaderboard


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
            'Volume Bonus': 'max',
            'Unique Ascent Bonus': 'sum'
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
        while True:
            # Present the options to the user
            print("Please choose a leaderboard to view:")
            print("1 - Total Score leaderboard")
            print("2 - Volume leaderboard")
            print("3 - Unique Ascents leaderboard")
            print("4 - Master Grade leaderboard")
            print("5 - Exit")

            choice = input("Enter your choice (1-5): ").strip()

            if choice == '1':
                # Total Score leaderboard
                total_score_leaderboard = rank_leaderboard(
                    self.aggregate_table, 'Total Score')
                print("Total Score Leaderboard:")
                print(total_score_leaderboard)

            elif choice == '2':
                # Volume leaderboard
                volume_leaderboard = rank_leaderboard(
                    self.aggregate_table[['Climber Name', 'Volume Score']],
                    'Volume Score')
                print("Volume Leaderboard:")
                print(volume_leaderboard)

            elif choice == '3':
                # Unique ascent leaderboard
                unique_ascent_leaderboard = rank_leaderboard(
                    self.aggregate_table[['Climber Name',
                                          'Unique Ascent Score']],
                    'Volume Score')
                print("Unique Ascents Leaderboard:")
                print(unique_ascent_leaderboard)

            elif choice == '4':
                # Grade leaderboard
                # ask user to input a grade
                grade = input(
                    "Enter the grade (e.g., 3, 6A, 9A): ").strip().upper()
                # filter the scoring table based on that grade
                grade_leaderboard = \
                    self.scoring_table[self.scoring_table['Grade'] == grade]
                # group by the climber and count the ascents per that grade
                grade_leaderboard = grade_leaderboard.groupby(
                    'Climber Name').size().reset_index(
                        name=f'Num of {grade} Ascents')
                # sort and rank the leaderboard
                grade_leaderboard = rank_leaderboard(
                    grade_leaderboard[['Climber Name',
                                      f'Num of {grade} Ascents']],
                    f'Num of {grade} Ascents'
                )
                # print the leaderborad to the terminal
                print(f"Master Grade Leaderboard for {grade}:")
                print(grade_leaderboard)

            elif choice == '5':
                # Exit the loop
                print("Exiting the leaderboard menu.")
                break

            else:
                print("Invalid choice. Please enter a number between 1 and 5.")

    def calculate_scores(self):
        """
        Calculate all scores and bonuses for each climber.

        Returns:
            pandas.DataFrame: A DataFrame with the total score for each
                                climber.
        """
        self.calc_base_points()
        self.calc_volume_bonus()
        self.calc_unique_ascent()
        aggregate_table = self.aggregate_scores()

        return aggregate_table
