import pandas as pd
import matplotlib.pyplot as plt


def read_csv(file):
    #čitanje csva

    df = pd.read_csv(file,usecols=['time'], parse_dates=['time'], encoding='latin1')
    #print(df)
    return df

def get_limits(month, year):
    if month!=12:
        end=pd.to_datetime("{}-{}-01 23:59:59".format(year,month+1))-pd.Timedelta(days=1)
    else:
        end=pd.to_datetime("{}-{}-01 23:59:59".format(year+1,1))-pd.Timedelta(days=1)
    beginning=pd.to_datetime("{}-{}-01 00:00:00".format(year,month))
    #print(end,beginning)
    return end, beginning
def calculate_diff(df, column, beginning, end):
    #oduzimanje susjednih redaka
    df['diff']=df[column].diff(periods=1)
     #izračun razmaka između poč. mjeseca i prvog mjerenja
    df.loc[0,'diff']=df.loc[0, column] - beginning
    #izračun razmaka između kraja mjeseca i zadnjeg mjerenja
    df.loc[len(df)] = {'diff':end - df.loc[len(df)-1, column], column: end}

def filter_rows(step,df):
    df['index'] = range(len(df))
    df2=df[df['diff'] > step]
    #filtiranje samo redaka čiji je diff veci od odabranog step-a (i njihovih prethodnika)
    previous_row = df2['index'] - 1
    result = pd.concat([df[df['index'].isin(previous_row) ], df2])
    result.sort_index(inplace=True, ignore_index=True)
    #print(result)
    return result

def make_table(result, beginning,step):
    #print(result)
    if result.loc[0,'index']==0 and result.loc[0,'diff']>step:
        #prvi red ima rupu od poč. mjeseca tj prvi snimljeni trenutak je upao u trenutke s rupom
        new_df=pd.DataFrame({'start-time':[beginning], 'end-time':[result.loc[0,'time']], 'duration':[result.loc[0,'diff']]})
        #print(new_df)
        new_df=pd.concat([new_df,pd.DataFrame({
        'start-time': result['time'].iloc[1::2].reset_index(drop=True),
        'end-time': result['time'].iloc[2::2].reset_index(drop=True),
        'duration': result['diff'].iloc[2::2].reset_index(drop=True)
        })], ignore_index=True)
        #print(new_df)
    else:
        #nema rupe od poč. mjeseca, uzimam parove redaka
        new_df = pd.DataFrame({
            'start-time': result['time'].iloc[0::2].reset_index(drop=True),
            'end-time': result['time'].iloc[1::2].reset_index(drop=True),
            'duration': result['diff'].iloc[1::2].reset_index(drop=True)
        })
    return new_df
def obrada(month, year, step):
    #step definira koja je granica za rupu
    #df = read_csv("bojler\{}\{}_{}.csv".format(year,month,year))
    df = read_csv(r"D:\Users\matea\Documents\3.god\projekt_r\bojler\{}\bojler_{}_{}.csv".format(year,month,year))
    end, beginning = get_limits(month, year)
    #nijedan podatak nije zabiljezen u mjesecu
    if df.empty:
        df=pd.DataFrame({'start-time':[beginning], 'end-time':[end], 'duration':[end-beginning]})
        return df
    #izračun rupa između mjerenja
    calculate_diff(df,'time', beginning, end)
    #print(df)
    #filtriranje rupa vecih od stepa
    result = filter_rows(step,df)
    if(result.empty):
        print("nema rupa")
        return result
    #formiranje tablice u obliku start - end - duration
    final_result = make_table(result, beginning,step)
    print(final_result)
    return final_result

def generate_all_timestamps(beginning, end, frequency):
    all_timestamps = pd.date_range(start=beginning, end=end, freq=frequency)
    return all_timestamps

def check_holes_better(all_timestamps, df, beginning):
    is_within_interval_list = []
    i = 0
    for index, row in df.iterrows():
        while i < len(all_timestamps) and all_timestamps[i] < row['start-time']:
            is_within_interval_list.append(False)
            i += 1
        while i < len(all_timestamps) and all_timestamps[i] >= row['start-time'] and all_timestamps[i] <= row['end-time']:
            is_within_interval_list.append(True)
            i += 1
    while i < len(all_timestamps):
        is_within_interval_list.append(False)
        i += 1
    return is_within_interval_list


def create_graph(ax, all_timestamps, beginning, end, month, interval_list, step, pctg):
    ax.plot(all_timestamps, interval_list, linewidth=1)
    tick_positions = pd.date_range(start=beginning, end=end, freq='2D')
    ax.set_xticks(tick_positions)
    ax.set_xticklabels([timestamp.strftime('%Y-%m-%d') for timestamp in tick_positions], rotation=45, ha='right',
                       fontsize=8)

    ax.set_xlabel('Timestamp', fontsize=10)
    ax.set_ylabel('1 - rupa, 0 - zapis')
    ax.set_title("rupa:>{}s, postotak:{}%".format(int(step.total_seconds()), round(pctg, 2)))

    # fig.set_size_inches(20, 6)  # Adjust the width and height as needed
    # plt.savefig("{}m_graph.png".format(month), dpi=600, bbox_inches='tight')
    return

def make_graph(month,year, steps, save):
    print("{}. mjesec".format(month))
    end, beginning = get_limits(month, year)
    #generiranje svih 'trenutaka' u mjesecu kad bi podaci trebali biti upisani
    all_timestamps = generate_all_timestamps(beginning, end, '1S')
    #stvaranje novog prozora za novi mjesec

    fig, ax = plt.subplots(nrows=1, ncols=len(steps), figsize=(20, 5))
    fig.suptitle("{}. mjesec {}.".format(month,year))
    k=0
    for step in steps:
        df=obrada(month,year,step)
        #true za trenutke koji su u rupi, false za one koji nisu
        interval_list = check_holes_better(all_timestamps, df, beginning)
        percentage = interval_list.count(True)/len(interval_list)*100
        print("Postotak rupa: {} %, rupa: {}".format(round(percentage,2),step))
        #stvaranje grafa
        if len(steps)==1:
            create_graph(ax, all_timestamps, beginning, end, month, interval_list, step, percentage)
        else:
            create_graph(ax[k], all_timestamps, beginning, end, month, interval_list, step, percentage)
        k+=1
    #plt.title("{}. mjesec".format(month))
    if save:
        plt.savefig("{}_{}_graph_popunjen.png".format(month,year), dpi=600, bbox_inches='tight')
    plt.show()
    return

