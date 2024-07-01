from gspread import Client
from pandas import DataFrame


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
        volume_bonus['Volume Bonus'] = \
            (volume_bonus['Num Ascents'] //
             self.vol_bonus_incr) * self.vol_bonus_points
        # merge the volume bonus df on the scoring table
        # via a left join
        self.scoring_table = \
            self.scoring_table.merge(
                volume_bonus[['Climber Name', 'Volume Bonus']],
                on='Climber Name', how='left')
        # fill potential na values with zero to allow summation later
        self.scoring_table['Volume Bonus'] = \
            self.scoring_table['Volume Bonus'].fillna(0).astype(int)

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
        self.scoring_table['Unique Ascent Bonus'] = self.scoring_table.apply(
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

        aggregate_table = self.scoring_table.groupby('Climber Name').agg({
            'Base Points': 'sum',
            'Volume Bonus': 'max',
            'Unique Ascent Bonus': 'sum'
        })

        aggregate_table['Total Score'] = aggregate_table['Base Points'] + \
            aggregate_table['Volume Bonus'] + \
            aggregate_table['Unique Ascent Bonus']

        return aggregate_table

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
