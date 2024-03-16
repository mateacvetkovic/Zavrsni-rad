import pandas as pd
import os

devices = ['Aparat za kavu', 'Perilica rublja', 'Uticnice', 'Napa', 'Mikrovalna',
           'Rasvjeta', 'Podno grijanje', 'Rolete', 'Drobilica', 'Elektricni bojler',
           'Å\xa0tednjak', 'Frizider', 'Pecnica', 'Klima', 'Perilica posuda',
           'Susilica rublja', 'Led rasvjeta', 'Uticnica']
columns = ['energy', 'total_active_power',
           'demand_total_active_power', 'maximum_demand_total_active_power', 'i1',
           'i2', 'i3', 'u12', 'u23', 'u13', 'v1', 'v2', 'v3',
           'total_power_factor', 'total_apparent_power']


def obrada(file, filename):
    """
        Razdvajanje uredaja u različite csvove
            file (string): put do csv-a sa svim uredajima
            filename (string): ime za novodobivene fileove (uredaj_filenam.csv)
    """
    df = pd.read_csv(file, parse_dates=['time'], encoding='latin1')
    # odredivanje svih uredaja
    #global devices, columns
    #devices = df['device'].unique()
    #columns = df.columns
    for device in devices:
        df3 = df[df['device'] == device]
        df2 = df3['time'].duplicated()
        # print(device)
        # print(df2)
        num = int(df2[df2 == True].shape[0] / df2[df2 == False].shape[0] + 1)
        df3 = df3.reset_index(drop=True)
        # broj različitih uređaja u jednom df-u
        for i in range(num):
            df2 = df3[df3.index % num == i]
            if num == 1:
                df2.to_csv("{}/{}_{}.csv".format(filename, device, filename), index=False)
            else:
                df2.to_csv("{}/{}{}_{}.csv".format(filename, device, i + 1, filename), index=False)
    return


def spajanje(file1, file2):
    df = pd.read_csv(file1, parse_dates=['time'], encoding='latin1')
    df2 = pd.read_csv(file2, parse_dates=['time'], encoding='latin1')
    # df2['energy'] = df2['energy'] * 1000
    df.drop(columns=['id'], inplace=True)
    df2.drop(columns=['id'], inplace=True)

    df = df.sort_values(['time', 'energy'])
    df2 = df2.sort_values(['time', 'energy'])
    df = df.rename(columns={'time': 'time_dev', 'energy': 'energy_dev'})
    df2 = df2.rename(columns={'time': 'time_prod', 'energy': 'energy_prod'})

    merged = pd.merge_asof(df, df2, left_on="time_dev", right_on='time_prod', tolerance=pd.to_timedelta('00:00:01'),
                           suffixes=('_dev', '_prod'), direction='nearest')
    merged = merged.sort_index(axis=1)
    return merged


def usporedba(file):
    df = pd.read_csv(file, parse_dates=['time_dev', 'time_prod'], encoding='latin1')
    lst = []
    for i, row in df.iterrows():
        for column in columns:
            new_row = False
            value1 = row['{}_dev'.format(column)]
            value2 = row['{}_prod'.format(column)]
            if not pd.isna(value1) or not pd.isna(value2):
                # ako je bar jedna od vrijednosti razlicita od null
                if pd.isna(value1) or pd.isna(value2):
                    # ako je neka od njih nan automatski znaci da druga nije pa se moze odmah upisat
                    new_row = True
                else:
                    if row['{}_dev'.format(column)] != row['{}_prod'.format(column)]:
                        new_row = True
                """elif column == 'demand_total_active_power' or column == 'v1' or column == 'maximum_demand_total_active_power' or column == 'u13' or column == 'u12' or column == 'u23':
                    # ako value1 nije null i ako je zaokruzena na 6 dec. razlicita od v2
                    if round(value1, 6) != value2:
                        new_row = True
                elif column == 'i1':
                    if round(value1, 2) != value2:
                        new_row = True
                elif column == 'energy':
                    if value1 != round(value2):
                        new_row = True
                elif column == 'total_power_factor':
                    if round(value1, 2) != value2:
                        new_row = True
                """
            if new_row:
                # podatak nije isti, upisujem ga u novu tablicu
                diff = abs(value1 - value2)
                lst.append({'time_dev': row['time_dev'], 'time_prod': row['time_prod'], 'column': column,
                            'value_dev': row['{}_dev'.format(column)], 'value_prod': row['{}_prod'.format(column)],
                            'diff': diff})

    final = pd.DataFrame(lst, columns=['time_dev', 'time_prod', 'column', 'value_dev', 'value_prod', 'diff'])
    return final


def main():
    #obrada(r'postgres_public_measurements_dev.csv', 'dev')
    #obrada(r'postgres_public_measurements_prod.csv', 'prod')

    dev_dir = sorted(os.listdir('dev'))
    prod_dir = sorted(os.listdir('prod'))
    for dev, prod in zip(dev_dir, prod_dir):
        df = spajanje('dev/' + dev, 'prod/' + prod)
        df.to_csv('merge/{}_merged.csv'.format(dev.split('_')[0]), index=False)

    for file in os.listdir('merge'):
        df = usporedba('merge/' + file)
        df.to_csv('diff/{}_diff.csv'.format(file.split('_')[0]), index=False)
    return


main()
