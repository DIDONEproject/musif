from ast import List
import csv
import pandas as pd


# def read_dicts_from_csv(file_path: str) -> List[dict]:
#     with open(file_path, "r", encoding='utf8') as file:
#         return [obj for obj in csv.DictReader(file)]

def add_duetos_gender(df_arias):
    for index, value in enumerate(df_arias['RoleType'].dropna()):
        if ',' in value:
            characters = value.split(',')
            df_arias['Gender'].iat[index] = '&'.join(['Female' if str(i).split(' ')[0].startswith('Female') else 'Male' for i in characters])

if __name__ == "__main__":
    #Arias.csv
    base_path = r'../../_Ana/Music Analysis/'
    des_path = r'../musif/metadata/score/'

   # passions
    passions_route= '../../_AlDaniMartiAnni/' + 'Passions.xlsx'
    df_passions = pd.read_excel(passions_route, header=0)
    df_passions.to_csv('musif/internal_data/Passions.csv',  index=False)

    # arias.csv
    arias_route = base_path+'Arias_change.xlsx'
    df_arias = pd.read_excel(arias_route, header=2)
    df_arias.rename(columns={'ID': 'AriaId', 'Country':'Territory', 'Type': 'RoleType'}, inplace=True)
    
    df_arias['Gender'] = ['Female' if str(i).split(' ')[0].startswith('Female') else 'Male' for i in df_arias['RoleType']]
    add_duetos_gender(df_arias)
            
    columns=['AriaId','Form','Character','Gender','RoleType','City','Territory']
    df_arias=df_arias[columns]
    df_arias.to_csv(des_path + 'aria.csv', index=False)

    # clefs.csv
    clefs_route=base_path + 'Arias_clefs.xlsx'
    df_clefs = pd.read_excel(clefs_route, header=1)
    df_clefs.rename(columns={'ID': 'AriaId', 'Clef 1': 'Clef1', 'Clef 2': 'Clef2',  'Clef 3': 'Clef3'}, inplace=True)
    columns=['AriaId','Character','Clef1', 'Clef2', 'Clef3']
    df_clefs=df_clefs[columns]
    df_clefs.to_csv(des_path + 'clefs.csv', index=False)
    
    # themeA
    themeA_route = base_path + 'Arias_proportions.xlsx'
    df_themeA = pd.read_excel(themeA_route, header=1)

    df_themeA.rename(columns={'ID': 'AriaId', ' A1': 'EndOfThemeA'}, inplace=True)
    columns=['AriaId', 'EndOfThemeA']
    df_themeA=df_themeA[columns]
    df_themeA.to_csv(des_path + 'theme_a_per_aria.csv', index=False)


 