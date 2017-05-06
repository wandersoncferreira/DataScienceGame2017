import multiprocessing as mp
import pandas as pd


class DataGame(object):

    def __init__(self, filepath, nrows=None):
        self.filepath = filepath
        self.nrows = nrows
        self.df = None
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
        list_return = list_feats + ["user_id"]
        return df_user[list_return]

    def compute_features(self, features):
        __dict_features__ = {"number_musics": self.number_musics_listened}

        pool = mp.Pool(processes = mp.cpu_count() - 1)
        results = []

        for user_id in self.user_ids[0:2]:
            for feature in features:
                func = __dict_features__[feature]
                results.append(pool.apply_async(func, [user_id]))
        pool.close()
        pool.join()

        df_res = []
        for r in results:
            df_res.append(r.get())
        result_df_users = pd.concat(df_res)

        return result_df_users


