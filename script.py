import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt



# This data set contains detailed statistics on each player's fantasy statistsics going
# back to 1970, though only 2010 and beyond are used. Each observation in the final dataframe
# is a player's performance in a given year.

# Load first data frame
df = pd.read_csv("data/yearly/2010.csv", index_col=0)
df["Year"] = "2010"


path = "data/yearly/2019.csv"

# get data from csv files from 2011 to 2019
for year in range(2011,2020):
    newpath = path.replace("2019", str(year))
    new_df = pd.read_csv(newpath, index_col=0)
    new_df["Year"] = str(year)
    df = df.merge(new_df,how="outer")

#create ID
df["ID"] = df["Player"] + " " + df["Year"]
df = df.set_index("ID")

#changing column names and changing team names
df.rename(columns = {'Player':'Name', 'Tm':'Team', 'Pos':'Position'}, inplace = True)
df.loc[df.Team == "KAN", ["Team"]] = "KC"
df.loc[df.Team == "OAK", ["Team"]] = "LV"
df.loc[df.Team == "GNB", ["Team"]] = "GB"
df.loc[df.Team == "NWE", ["Team"]] = "NE"
df.loc[df.Team == "STL", ["Team"]] = "LAR"
df.loc[df.Team == "SDG", ["Team"]] = "LAC"
df.loc[df.Team == "TAM", ["Team"]] = "TB"
df.loc[df.Team == "NOR", ["Team"]] = "NO"
df.loc[df.Team == "SFO", ["Team"]] = "SF"

print(df)


path2 = "data/adp/2010.csv"
adp = pd.read_csv(path2, index_col=0)
adp["Year"] = "2010"
adp["ID"] = adp["Name"] + " " + adp["Year"]
adp = adp.set_index("ID")

for year in range(2011,2020):
    newpath = path2.replace("2010", str(year))
    new_adp = pd.read_csv(newpath, index_col=0)

    new_adp["Year"] = str(year)
    new_adp["ID"] = new_adp["Name"] + " " + new_adp["Year"]
    new_adp = new_adp.set_index("ID")
    adp = pd.concat([adp, new_adp])

print(adp)

#merge the two dataframes
data = df.merge(adp, on = ['ID', 'Name', 'Position', 'Team', 'Year'], how = 'outer')
print(data)

print(data.dtypes)
top_10 = data.sort_values(by="FantasyPoints", ascending = False).head(10)
print(top_10[["Position","FantasyPoints"]])
sns.countplot(data=top_10, x= "Position")

averages = data.groupby("Position").FantasyPoints.mean()
