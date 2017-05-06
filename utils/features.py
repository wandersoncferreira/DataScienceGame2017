import multiprocessing as mp
import pandas as pd


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

    def number_musics_listened(self, user_id):
        df_user = self.df[(self.df["user_id"] == user_id)].copy()
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

    def number_artists_listened(self, user_id):
        df_user = self.df[(self.df["user_id"] == user_id)].copy()
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


    def number_platform(self, user_id):
        df_user = self.df[(self.df["user_id"] == user_id)].copy()
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
        __dict_features__ = {"nmidia": self.number_musics_listened,
                             "nartist": self.number_artists_listened,
                             "nplatform": self.number_platform}
        results = []
        pool = mp.Pool(processes=mp.cpu_count() - 1)
        func = __dict_features__[feature]

        if self.nusers:
            list_of_users = self.user_ids[0:self.nusers]
        else:
            list_of_users = self.user_ids

        for user_id in list_of_users:
            results.append(pool.apply_async(func, [user_id]))
        pool.close()
        pool.join()

        df_res = []
        for r in results:
            df_res.append(r.get())
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
