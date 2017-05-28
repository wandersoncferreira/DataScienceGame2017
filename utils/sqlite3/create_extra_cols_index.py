import sqlite3 as lite


con = lite.connect("deezer.db")
cur = con.cursor()

SQL1 = ("ALTER TABLE DeezerTreino ADD COLUMN count_listened_120min INTEGER")
SQL2 = ("ALTER TABLE DeezerTreino ADD COLUMN sum_listened_120min INTEGER")
SQL3 = ("CREATE INDEX index_id ON DeezerTreino (id)")

cur.execute(SQL1)
cur.execute(SQL2)
cur.execute(SQL3)
con.commit()
con.close()
print("Col count_120min and sum_120min added!")
print("The indexes were created aswell!")
