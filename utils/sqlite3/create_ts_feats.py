import sqlite3 as lite
import sys
import pandas as pd
from tqdm import tqdm
from datetime import datetime, timedelta
import numpy as np
import multiprocessing

def time_offset_rolling_df_count(data_df_ser, window_i_s, min_periods_i=1, center_b=False):
    def calculate_count_ts(ts):
        """Function (closure) to apply that actually computes the rolling mean"""
        if center_b == False:
            dslice_df_ser = data_df_ser[
                ts-pd.datetools.to_offset(window_i_s).delta+timedelta(0,0,1):
                ts
            ]
            # adding a microsecond because when slicing with labels start and endpoint
            # are inclusive
        else:
            dslice_df_ser = data_df_ser[
                ts-pd.datetools.to_offset(window_i_s).delta/2+timedelta(0,0,1):
                ts+pd.datetools.to_offset(window_i_s).delta/2
            ]
        if  (isinstance(dslice_df_ser, pd.DataFrame) and dslice_df_ser.shape[0] < min_periods_i) or \
            (isinstance(dslice_df_ser, pd.Series) and dslice_df_ser.size < min_periods_i):
            return dslice_df_ser.count()*np.nan   # keeps number format and whether Series or DataFrame
        else:
            return dslice_df_ser.count()

    idx_ser = pd.Series(data_df_ser.index.to_pydatetime(), index=data_df_ser.index)
    count_df_ser = idx_ser.apply(calculate_count_ts)
    return count_df_ser


def time_offset_rolling_df_sum(data_df_ser, window_i_s, min_periods_i=1, center_b=False):
    def calculate_sum_ts(ts):
        """Function (closure) to apply that actually computes the rolling mean"""
        if center_b == False:
            dslice_df_ser = data_df_ser[
                ts-pd.datetools.to_offset(window_i_s).delta+timedelta(0,0,1):
                ts
            ]
            # adding a microsecond because when slicing with labels start and endpoint
            # are inclusive
        else:
            dslice_df_ser = data_df_ser[
                ts-pd.datetools.to_offset(window_i_s).delta/2+timedelta(0,0,1):
                ts+pd.datetools.to_offset(window_i_s).delta/2
            ]
        if  (isinstance(dslice_df_ser, pd.DataFrame) and dslice_df_ser.shape[0] < min_periods_i) or \
            (isinstance(dslice_df_ser, pd.Series) and dslice_df_ser.size < min_periods_i):
            return dslice_df_ser.sum()*np.nan   # keeps number format and whether Series or DataFrame
        else:
            return dslice_df_ser.sum()

    idx_ser = pd.Series(data_df_ser.index.to_pydatetime(), index=data_df_ser.index)
    sum_df_ser = idx_ser.apply(calculate_sum_ts)
    return sum_df_ser


# cur.execute("SELECT id, ts_listen, is_listened FROM DeezerTreino where user_id=?", (str(users[0]),))
# records = cur.fetchall()
# df_user = pd.DataFrame.from_records(records, columns=["id", "ts_listen", "is_listened"])
# df_user["ts_datetime"] = df_user.apply(lambda x: datetime.fromtimestamp(x["ts_listen"]), axis=1)
# df_user = df_user.set_index("ts_datetime")
# df_user = df_user.sort_index()
# df_rolling_count = time_offset_rolling_df_count(df_user, window_i_s=last_x_min)
# df_rolling_sum = time_offset_rolling_df_sum(df_user, window_i_s=last_x_min)
# df_user["count_listened_{}".format(last_x_min)] = df_rolling_count["is_listened"]
# df_user["sum_listened_{}".format(last_x_min)] = df_rolling_sum["is_listened"]
# df_user = df_user.reset_index()

# # creating the list of items to commit
# tuples = [(row[-1], row[-2], row[1]) for row in df_user.values]
# # each tuple is composed by SUM_LISTENED_120min, COUNT_LISTENED_120min, ID

# cur.executemany('''
# UPDATE DeezerTreino SET sum_listened_120min=?, count_listened_120min=? WHERE Id=?
# ''', tuples)

# con.commit()
# con.close()
# print("Fim")

def compute_ts_feat(user_id, cur):
    cur.execute("SELECT id, ts_listen, is_listened FROM DeezerTreino where user_id=?", (str(user_id),))
    records = cur.fetchall()
    df_user = pd.DataFrame.from_records(records, columns=["id", "ts_listen", "is_listened"])
    df_user["ts_datetime"] = df_user.apply(lambda x: datetime.fromtimestamp(x["ts_listen"]), axis=1)
    df_user = df_user.set_index("ts_datetime")
    df_user = df_user.sort_index()
    df_rolling_count = time_offset_rolling_df_count(df_user, window_i_s=last_x_min)
    df_rolling_sum = time_offset_rolling_df_sum(df_user, window_i_s=last_x_min)
    df_user["count_listened_{}".format(last_x_min)] = df_rolling_count["is_listened"]
    df_user["sum_listened_{}".format(last_x_min)] = df_rolling_sum["is_listened"]
    df_user = df_user.reset_index()

    # creating the list of items to commit
    tuples = [(row[-1], row[-2], row[1]) for row in df_user.values]
    # each tuple is composed by SUM_LISTENED_120min, COUNT_LISTENED_120min, ID
    cur.executemany('''
    UPDATE DeezerTreino SET sum_listened_120min=?, count_listened_120min=? WHERE Id=?
    ''', tuples)
    return True

if __name__ == "__main__":
    con = lite.connect("deezer.db")
    last_x_min = "120min"
    cur = con.cursor()

    cur.execute('''
    SELECT distinct(user_id) FROM DeezerTreino
    ''')
    users = cur.fetchall()
    users = [user[0] for user in users]

    for userid in tqdm(users):
        compute_ts_feat(userid, cur)

    # pool = multiprocessing.Pool(processes=8)
    # with tqdm(total=30) as pbar:
    #     for i, _ in tqdm(enumerate(pool.map(compute_ts_feat, users))):
    #         pbar.update()
    # pbar.close()
    # pool.close()
    # pool.join()
    con.close()
