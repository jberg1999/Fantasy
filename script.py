import pandas as pd
import matplotlib.pyplot as plt
df = pd.read_csv("data/yearly/2010.csv", index_col=0)
df["Year"] = "2010"
#df["Id"] = df["Player"] + " " + df["Year"]
#df.set_index("Id")
#print(df)
print(df.columns)
#df["ReceivingTD"].plot.hist()
#plt.show()


path = "data/yearly/2019.csv"
for year in range(2011,2020):
    newpath = path.replace("2019", str(year))
    new_df = pd.read_csv(newpath, index_col=0)
    new_df["Year"] = str(year)
    #new_df["Id"] = new_df["Player"] + " " + new_df["Year"]
    #print(new_df)
    df = df.merge(new_df,how="outer")

df["Id"] = df["Player"] + " " + df["Year"]
df = df.set_index("Id")
print(df)
