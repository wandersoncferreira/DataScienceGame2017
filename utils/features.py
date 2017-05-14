import sys
import multiprocessing as mp
import pandas as pd
import requests
import numpy as np
from time import sleep
import os

def number_musics_listened(df_user, user_id):
    list_feats = ["nmidia_with_flow", "nmidia_regular", "nmidia_with_flow_listened",
                  "nmidia_regular_listened", "nmidia_max_repeat"]
    max_repeat = df_user["media_id"].value_counts().values[0]
    with_flow = len(df_user[(df_user["listen_type"] == 1)]["media_id"].unique())
    regular = len(df_user[(df_user["listen_type"] == 0)]["media_id"].unique())
    with_flow_listened = len(df_user[(df_user["listen_type"] == 1) & (df_user["is_listened"] == 1)]["media_id"].unique())
    regular_listened = len(df_user[(df_user["listen_type"] == 0) & (df_user["is_listened"] == 1)]["media_id"].unique())

    df_user[list_feats] = df_user.apply(lambda row: pd.Series([with_flow, regular, with_flow_listened, regular_listened, max_repeat]), axis=1)
    df_user.set_index("user_id", inplace=True)
    return df_user[list_feats].iloc[0:1]

def number_artists_listened(df_user, user_id):
    list_feats = ["nartist_with_flow", "nartist_regular", "nartist_with_flow_listened", "nartist_regular_listened"]
    with_flow = len(df_user[(df_user["listen_type"] == 1)]["artist_id"].unique())
    regular = len(df_user[(df_user["listen_type"] == 0)]["artist_id"].unique())
    # case where is_listened equals to 1
    with_flow_listened = len(df_user[(df_user["listen_type"] == 1) & (df_user["is_listened"] == 1)]["artist_id"].unique())
    regular_listened = len(df_user[(df_user["listen_type"] == 0) & (df_user["is_listened"] == 1)]["artist_id"].unique())
    df_user[list_feats] = df_user.apply(lambda row: pd.Series([with_flow, regular, with_flow_listened, regular_listened]), axis=1)
    list_return = list_feats + ["user_id"]
    df_user.set_index("user_id", inplace=True)
    return df_user[list_feats].iloc[0:1]


def number_platform(df_user, user_id):
    list_feats = ["nplatform_with_flow", "nplatform_regular", "nplatform_with_flow_listened", "nplatform_regular_listened"]
    # case where is_listened was not fixed
    with_flow = len(df_user[(df_user["listen_type"] == 1)]["platform_name"].unique())
    regular = len(df_user[(df_user["listen_type"] == 0)]["platform_name"].unique())

    # case where is_listened equals to 1
    with_flow_listened = len(df_user[(df_user["listen_type"] == 1) & (df_user["is_listened"] == 1)]["platform_name"].unique())
    regular_listened = len(df_user[(df_user["listen_type"] == 0) & (df_user["is_listened"] == 1)]["platform_name"].unique())
    df_user[list_feats] = df_user.apply(lambda row: pd.Series([with_flow, regular, with_flow_listened, regular_listened]), axis=1)
    list_return = list_feats + ["user_id"]
    df_user.set_index("user_id", inplace=True)
    return df_user[list_feats].iloc[0:1]


def qtd_success_flow_noflow(df_user, user_id):
    list_feats = ["nmidia_noflow", "nmidia_noflow_sucess", "nmidia_noflow_sucess_PROP",
                  "nmodia_flow", "nmidia_flow_success", "midia_flow_success_PROP",
                  "PROP_flow_PROP_noflow", "qtd_flow_noflow_PROP"]

    # reproducoes com sucesso em nao-flow
    qtd_musics_noflow = df_user[(df_user["listen_type"] == 0)].__len__()
    qtd_musics_noflow_success = df_user[(df_user["is_listened"] == 1) & (df_user["listen_type"] == 0)].__len__()
    prop_musics_noflow_success = qtd_musics_noflow_success / qtd_musics_noflow

    # reproducoes em modo flow
    df_flow = df_user[(df_user["listen_type"] == 1)].copy()
    qtd_musics_flow = len(df_flow)
    qtd_musics_flow_success = df_flow[(df_flow["is_listened"] == 1)].__len__()
    prop_musics_flow_success = qtd_musics_flow_success / qtd_musics_flow

    # prop qtd_noflow / qtd_flow
    prop_qtd_flow_noflow = qtd_musics_flow / qtd_musics_noflow

    # proporcao entre flow_success e noflow_successs
    prop_prop = prop_musics_flow_success / prop_musics_noflow_success

    df_user[list_feats] = df_user.apply(lambda row: pd.Series([qtd_musics_noflow,
                                                               qtd_musics_noflow_success,
                                                               prop_musics_noflow_success,
                                                               qtd_musics_flow,
                                                               qtd_musics_flow_success,
                                                               prop_musics_flow_success,
                                                               prop_prop,
                                                               prop_qtd_flow_noflow]), axis=1)
    df_user.set_index("user_id", inplace=True)
    return df_user[list_feats].iloc[0:1]


class DataGame(object):

    def __init__(self, filepath, nrows=None, nusers=None):
        self.filepath = filepath
        self.nrows = nrows
        self.nusers = nusers
        self.df = None
        self.status_user_features = None
        self.prepare_data()

    def prepare_data(self):
        from pandas import read_csv
        if self.nrows:
            self.df = read_csv(self.filepath, nrows=self.nrows)
        else:
            self.df = read_csv(self.filepath)
        return True

    @property
    def user_ids(self):
        user_ids = self.df["user_id"].unique().tolist()
        return user_ids


    def combine_user_features(self, result_df_users, features):
        if self.status_user_features:
            df_tmp = result_df_users.copy()

            if "nmidia" in features:
                df_tmp["nmidia_with_flow_listened_PROP"] = df_tmp["nmidia_with_flow_listened"] / df_tmp["nmidia_with_flow"]
                df_tmp["nmidia_regular_listened_PROP"] = df_tmp["nmidia_regular_listened"] / df_tmp["nmidia_regular"]
                df_tmp["nmidia_PROP_diff"] = df_tmp["nmidia_with_flow_listened_PROP"] / df_tmp["nmidia_regular_listened_PROP"]

            if "nartist" in features:
                df_tmp["nartist_with_flow_listened_PROP"] = df_tmp["nartist_with_flow_listened"] / df_tmp["nartist_with_flow"]
                df_tmp["nartist_regular_listened_PROP"] = df_tmp["nartist_regular_listened"] / df_tmp["nartist_regular"]
                df_tmp["nartist_PROP_diff"] = df_tmp["nartist_with_flow_listened_PROP"] / df_tmp["nartist_regular_listened_PROP"]

            return df_tmp
        else:
            return False

    def __multiprocessing(self, feature):
        __dict_features__ = {"nmidia": number_musics_listened,
                             "nartist": number_artists_listened,
                             "nplatform": number_platform,
                             "flow_noflow": qtd_success_flow_noflow}
        results = []
        pool = mp.Pool(processes=mp.cpu_count() - 1)
        func = __dict_features__[feature]

        if self.nusers:
            list_of_users = self.user_ids[0:self.nusers]
        else:
            list_of_users = self.user_ids

        for user_id in list_of_users:
            df_user = self.df[(self.df["user_id"] == user_id)].copy()
            results.append(pool.apply_async(func, [df_user, user_id]))
        pool.close()
        pool.join()

        df_res = []
        for r in results:
            try:
                df_res.append(r.get())
            except:
                pass
        result_df_user = pd.concat(df_res)
        return result_df_user

    def compute_features(self, features, feature_combinations=True):

        res_list = []
        for feature in features:
            res_list.append(self.__multiprocessing(feature))

        final = pd.concat(res_list, axis=1)
        self.status_user_features = True

        if feature_combinations:
            df_final = self.combine_user_features(final, features)
        else:
            df_final = final

        return df_final



class DeezerFeatures(object):


    def __init__(self, media_ids=None, album_ids=None, artist_ids=None, create_csv=False, file_number=0, ntimes=4):
        self.media_ids = media_ids
        self.album_ids = album_ids
        self.file_number = file_number
        self.artist_ids = artist_ids
        self.create_csv = True
        self.track_link = "https://api.deezer.com/track/TRACK_ID"
        self.album_link = "https://api.deezer.com/album/ALBUM_ID"
        self.artist_link = "https://api.deezer.com/artist/ARTIST_ID"
        self.finished = False
        self.ntimes = ntimes


    def track_features(self, media_id):
        track = self.track_link.replace("TRACK_ID", str(media_id))
        response = requests.get(track)
        rjson = response.json()
        try:
            error = rjson["error"]
            media_bpm = None
            media_rank = None
        except:
            media_bpm = rjson["bpm"]
            media_rank = rjson["rank"]

        dict_resp = {"media_id": media_id, "media_bpm": media_bpm, "media_rank": media_rank}
        return dict_resp

    def album_features(self, album_id):
        album = self.album_link.replace("ALBUM_ID", str(album_id))
        response = requests.get(album, proxies=proxies)
        rjson = response.json()
        try:
            error = rjson["error"]
            rating = None
            fans = None
            ids_genre = None
        except:
            rating = rjson["rating"]
            fans = rjson["fans"]
            ids_genre = [genre["id"] for genre in rjson["genres"]["data"]]

        dict_resp = {"album_id": album_id, "album_rating": rating, "album_fans": fans,
                     "album_genres": ids_genre}
        return dict_resp

    def artist_features(self, artist_id):
        artist = self.artist_link.replace("ARTIST_ID", str(artist_id))
        sleep(2)
        response = requests.get(artist)
        rjson = response.json()
        try:
            error = rjson["error"]
            nb_fans = None
            nb_albuns = None
            radio = None
        except:
            nb_fans = rjson["nb_fan"]
            nb_albuns = rjson["nb_album"]
            radio = rjson["radio"]

        dict_resp = {"artist_id": artist_id, "artist_fans": nb_fans, "artist_albuns": nb_albuns, "artist_radio": radio}
        return dict_resp

    def __multiprocessing(self, ids, func_ids):
        import random

        results = []
        pool = mp.Pool(processes=30)


        for _id in ids:
            results.append(pool.apply_async(func_ids, [_id]))
        pool.close()
        pool.join()

        tmp_list = []
        for r in results:
            tmp_list.append(r.get())

        df_final = pd.DataFrame(tmp_list)
        return df_final


    def compute_features(self):
        df_artist = None
        df_media = None
        df_album = None
        n = 0

        if self.artist_ids:
            artist_ids = self.artist_ids
            number = self.file_number
            while self.finished == False and n <= self.ntimes:
                df_artist = self.__multiprocessing(artist_ids, self.artist_features)

                if self.create_csv:
                    df_artist.to_csv("artist_features_from_deezer_{}.csv".format(number), sep=";", index=False)
                    check_df = pd.read_csv("artist_features_from_deezer_{}.csv".format(number), sep=";")
                    artist_ids = check_df[(pd.isnull(check_df["artist_albuns"]))]["artist_id"].tolist()

                    if len(artist_ids) > 0:
                        n += 1
                        number += 1
                        print("Ainda restam {} tentativas e {} valores NULL \n\n\n".format(self.ntimes - n, len(artist_ids)))
                    else:
                        self.finished = True
                        print("Terminou!!\n\n")



        if self.media_ids:
            df_media = self.__multiprocessing(self.media_ids, self.track_features)
            if self.create_csv:
                df_media.to_csv("media_features_from_deezer.csv", sep=";", index=False)

        if self.album_ids:
            df_album = self.__multiprocessing(self.album_ids, self.album_features)
            if self.create_csv:
                df_album.to_csv("album_features_from_deezer.csv", sep=";", index=False)

        return df_artist, df_media, df_album
