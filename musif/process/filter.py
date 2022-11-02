from typing import Dict, Union

from pandas import DataFrame
import pandas as pd
import os
from musif.extract.features.core.constants import FILE_NAME
# from musif.extract.features.intervals.constants import FILE_NAME
import matplotlib.pyplot as plt

from musif.logs import perr, pinfo
import numpy as np

class DataFilter:
    """Processor class that treats columns and information of a DataFrame

    This operator processes information from a DataFrame or a .csv file. 
    It deletes unseful columns and merges those that are required to clean the data.
    The main method .process() returns a DataFrame and saves it into a .csv file.
    Requires to have a Passions.csv file in the current working directory containing each passion
    for each aria.
    ...

    Attributes
    ----------
    data : DataFrame
        DataFrame extracted with FeaturesExtractor containing all info.
    info: str
        Path to .csv file or Dataframe containing the information from FeaturesExtractor

    Methods
    -------

    """

    def __init__(self, info: Union[str, DataFrame], *args, **kwargs):
        """
        Parameters
        ----------
        *args:  str
            Could be a path to a .yml file, a PostProcess_Configuration object or a dictionary. Length zero or one.
        *kwargs : str
            Key words arguments to construct 
        kwargs[info]: Union[str, DataFrame]
            Either a path to a .csv file containing the information either a DataFrame object fromm FeaturesExtractor
        """
        # self._post_config=PostProcess_Configuration(*args, **kwargs)
        self.info=info
        self.data = self._process_info(self.info)

    def _process_info(self, info: Union[str, DataFrame]) -> DataFrame:  
        """
        Extracts the info from a directory to a csv file or from a Dataframe object. 
        
        Parameters
        ------
        info: str
            Info in the from of str (path to csv file) or DataFrame
        
        Raises
        ------
        FileNotFoundError
            If path to the .csv file is not found.

        Returns
        ------
            Dataframe with the information from either the file or the previous DataFrame.
        """
        
        try:
            if isinstance(info, str):
                pinfo('\nReading csv file...')
                if not os.path.exists(info):
                    raise FileNotFoundError
                self.destination_route=info.replace('.csv','')
                df = pd.read_csv(info, low_memory=False, sep=',', encoding_errors='replace')
                if df.empty:
                    raise FileNotFoundError
                return df
            
            elif isinstance(info, DataFrame):
                pinfo('\nProcessing DataFrame...')
                return info
            else:
                perr('Wrong info type! You must introduce either a DataFrame either the name of a .csv file.')
                return pd.DataFrame()
            
        except FileNotFoundError:
            perr('Data could not be loaded. Either wrong path or an empty file was found.')
            return pd.DataFrame()
    
    def filter_data(self, by:str=None, equal_to: list = [],instrument: str='') -> DataFrame:
        data = self.data.loc[self.data[by].isin(equal_to)]
        percentages_intervals=pd.DataFrame()
        
        for aria in sorted(set(data[by])):
            aria_data=data[data[by]==aria]
            percentages=self._filter_intervals(aria_data, instrument)
            # percentages=self._filter_stepwise(aria_data, instrument)
            # percentages_intervals[aria]=percentages
            percentages[by] = aria
            percentages_intervals = percentages_intervals.append(percentages, ignore_index=True)
        percentages_intervals = self.post_process_intervals(by, instrument, percentages_intervals)

        print(percentages_intervals)
        return percentages_intervals

    def post_process_intervals(self, by, instrument, percentages_intervals: DataFrame):
        for column in percentages_intervals.filter(like='Interval').columns:
            if max(percentages_intervals[column])==0.0:
                del percentages_intervals[column] 
        percentages_intervals=percentages_intervals.reindex(sorted(percentages_intervals.columns), axis=1)
        percentages_intervals.columns = [i.replace(instrument, '').replace('_Percentage','').replace('_',' ').replace('Interval','') for i in percentages_intervals.columns]
        excel_name = 'intervals_per_aria.xlsx'
        percentages_intervals.to_excel(excel_name)
        pinfo(f'File saved succesfully as: {excel_name}')
        percentages_intervals.plot(x=by,kind='bar')
        plt.savefig('intervals.png')
        plt.show()
        return percentages_intervals
    
    def _filter_intervals(self, aria_data, instrument) -> Dict[str, float]:
        
        # interval_types = [i for i in aria_data if 'Intervals' in i and instrument in i]
        interval = [i for i in aria_data if '_Interval' in i and instrument in i and not 'Intervals' in i]
        interval_counts = [i for i in interval if 'Count' in i]
        intervals_dataframe=aria_data[interval_counts]
        total=intervals_dataframe.sum(axis=0).sum()
        totals={}
        for column in intervals_dataframe:
            totals[column.replace('_Count','')+'_Percentage'] = (np.nansum(intervals_dataframe[column]) / total) * 100
        return totals
    
    def _filter_stepwise(self, aria_data, instrument)-> Dict[str, float]:
        # interval_types = [i for i in aria_data if 'Intervals' in i and instrument in i]
        stepwise = [i for i in aria_data if 'stepwise' in i.lower() and instrument in i]
        stepwise_counts = [i for i in stepwise if 'Count' in i]
        steps_dataframe=aria_data[stepwise_counts]
        total=steps_dataframe.sum(axis=0).sum()
        totals={}
        for column in steps_dataframe:
            totals[column.replace('_Count','')+'_Percentage'] = (np.nansum(steps_dataframe[column]) / total) * 100
        return totals