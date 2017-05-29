import sqlite3 as lite
import sys
import pandas as pd
from tqdm import tqdm
from numpy import arange

con = lite.connect("deezer.db")

def split_list(input_list, size):
    from itertools import islice
    iterator_list = iter(input_list)
    item = list(islice(iterator_list, size))

    while item:
        yield item
        item = list(islice(iterator_list, size))

with con:
    cur = con.cursor()
    cur.execute("DROP TABLE IF EXISTS DeezerTreino")
    cur.execute('''
    CREATE TABLE DeezerTreino(id INT, genre_id INT, ts_listen INT, media_id INT,
    album_id INT, context_type INT, release_date INT, platform_name INT,
    platform_family INT, media_duration INT, listen_type INT, user_gender INT, user_id INT,
    artist_id INT, user_age INT, is_listened INT)
    ''')

    # reading CSV with files
    df_treino = pd.read_csv("github/DataScienceGame2017/data/train.csv")
    list_indx = arange(0, len(df_treino) - 1)

    for sub_list in tqdm(split_list(list_indx, size=50000)):
        df_tmp = df_treino.iloc[sub_list].copy()
        df_tmp = df_tmp.reset_index()
        tuples = [tuple(row) for row in df_tmp.values]

        cur.executemany('''
        INSERT INTO DeezerTreino(id, genre_id, ts_listen, media_id, album_id,
        context_type, release_date, platform_name, platform_family,
        media_duration, listen_type, user_gender, user_id, artist_id, user_age, is_listened)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''', tuples)
        con.commit()

    print("Fim!")
