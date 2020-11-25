import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

"""
The team class is the parent class of some of the more sophisticated draft algorithms.
It is designed to mimic an auto-draft in that it takes what it thinks is the best player
available every time unless it has run out of opportunities to fill out its staring lineup
or has met the league cap for players of a certian type.

ATTRIBUTES:
name:          String that reperesents the team name

pos_counts:    Dictionary that keeps track of how many players are on the team at QB,RB,WR, and TE
               it has keys for FLX and bench but they are not used

starter_cap:   Dictionary containing the max amount of starters allowed by the league

picks:         List containing the slots of all of the remaining draft picks for the player. The
               length of this list is often used to find out how many picks are left

selected:      List of tuples in the format (selection number, player name)

roster_caps:   Dictionary containing the max amount of players allowed at each position
               (QB,RB,WR, and TE). In children the caps are reduced to allow more realistic
               drafting

wins:          Float containing the number of expected regular season wins as calculted by league


METHODS:
set_pos_counts:  Sets the amount of players at each position to 0

set_roster:      Empties the roster

add_pick:        Invoked by league to assign the pick number to the team during the predraft
                 process

add_wins:        Invoked by league to update the regular season win total of the team

draft_player:    Contains the logic for selecting a player. Is overwritten in children. It assigns the selected
                 player to a roster spot and updates the position count

set_lineup:      Called by league each week to return the total points from the optimal lineup of
                 players on the team based on their performance that week

"""



import copy
class Team:
    def __init__(self, positions,roster_caps,name):
        self.name = name
        self.pos_counts = self.set_pos_counts(positions)
        self.roster = self.set_roster(positions)
        self.starter_cap = positions
        self.picks = []
        self.selected = []
        self.roster_caps = roster_caps
        self.wins = 0


    def set_pos_counts(self, positions):
        p = positions.copy()
        for k in p.keys():
            p[k] = 0
        return p

    def set_roster(self, positions):
        p = positions.copy()
        for k in p.keys():
            p[k] = []
        return p

    def add_pick(self, pick):
        self.picks.append(pick)

    def add_wins(self, n):
        self.wins += n

    # TAKES THE DRAFT BAORD AVAIABLABLE AND RETURNS THE ANME OF THE PLAYER TO BE DRAFTED
    def draft_player(self, board):


        # MAKES SURE STARTERS ARE FILLED AT END
        starter_num = sum(self.starter_cap.values()) - self.starter_cap["BEN"]
        starters_filled = sum([len(x) for x in self.roster.values()])- len(self.roster["BEN"])
        open_slots = starter_num - starters_filled


        # RESTRICT POSITIONS TO FILL STARTING LINEUP OF NEEDED
        if open_slots >= len(self.picks): # try to fill lineup
            must_draft = [pos for pos in ["QB","RB","WR","TE"] if self.starter_cap[pos] > len(self.roster[pos])]
            new_board = board.loc[board["Position"].isin(must_draft)]


        #NEXT PRIORITY IS TO PREVENT OVERLOADING ON A POSITION IF STARTERS ARE ALL FILLED
        else:
            capped = [pos for pos in ["QB","RB","WR","TE"] if self.pos_counts[pos] >= self.roster_caps[pos]]
            draftable = [pos for pos in self.pos_counts.keys() if pos not in capped]
            new_board = board.loc[board["Position"].isin(draftable)]

        #BEST PLAYER FROM AVAILABLE
        best = new_board.Overall.idxmin()
        position = new_board.loc[best].Position


        # HANDELS CASES WITH DUPLICATE IDS IF PLAYER CHAGED TEAMS (POSSIBLY REDUNDANT)
        if type(position) != str:
            position = position[0]


        #UPDATES THE POSITION COUNTS AND ROSTER BASED ON THE SELECTION NAME AND POSITION
        self.pos_counts[position] += 1

        #ADD PLAYER TO LINEUP IN STARTING SPOT IF POSSIBLE
        if len(self.roster[position]) < self.starter_cap[position]:
            self.roster[position].append(best)

        #ADD TO FLEX SPOT IF STARTING SLOTS FOR POSITION ARE FILLED AND THERE IS A FLEX SPOT AVAILABLE
        elif (len(self.roster["FLX"]) < self.starter_cap["FLX"]) and (position in ["RB","WR","TE"]):
            self.roster["FLX"].append(best)

        else:
            self.roster["BEN"].append(best)

        #UPDATES THE REMAING PICKS AND PLAYERS CHOSEN ATTRIBUTES
        self.selected.append((self.picks[0], board.loc[best].Name))
        self.picks = self.picks[1:]

        return best

    #RETURNS THE TOTAL POINTS OF THE OPTIMAL LINEUP FOR A WEEK GIVEN DATA FOR THAT WEEK
    def set_lineup(self,data,scoring):

        #GETS THE PLAYERS ON THE TEAM FROM THE SELECTED ATTRIBUTE AND RETURNS WEEKLY DATA FROM THEM
        players = [x[1] for x in self.selected]
        players = data.loc[data["Player"].isin(players)]

        # SOME CLEANING TO THE WEEKLY DATA
        players = players.set_index("Player")
        players["Pos"]= players.apply(lambda row: "RB" if row.Pos in ["FB","HB", "RB/K", "FB/R","RB/F", "FB/T"]
                                      else row.Pos, axis = 1)


        # GETS THE SCORES FROM THE BEST PLAYERS THIS WEEK AT QB, RB, WR, AND TE FROM THE DATA BASED ON LINEUP REQUIREMENTS
        total_points = 0 # stores the  total points of the optimal lineup
        for pos in ["QB","RB", "WR","TE",]:
            cap = self.starter_cap[pos]
            if scoring == "standard":
                best = players.loc[players["Pos"] == pos].StandardFantasyPoints.nlargest(cap)

            # ADDS TOTAL POINTS FROM THE BEST PLAYERS AND REMOVES THEM FROM CONSIDERATION FOR FLX
            total_points += best.sum()
            players = players.drop(best.index)

        # GETS BEST REMAINING PLAYER/S FOR FLX AND ADDS THEIR POINT TO TOTAL
        players = players.loc[players["Pos"].isin(["RB", "WR","TE"])]
        if scoring == "standard":
            total_points += sum(players.StandardFantasyPoints.nlargest(self.starter_cap["FLX"]))


        return total_points

# RECORDS THE LINEUP CONFIGURATIONS FOR TEAMS IN THE LEAGUE. THESE VALUES ARE FAIRLY STANDARD
positions = {
    "QB": 1,
    "RB": 2,
    "WR": 2,
    "TE": 1,
    "FLX": 1,
    "BEN": 6
}

# RECORDS THE MAX AMOUNT OF PLAYERS AT EACH POSITION ALLOWED. THESE ARE CLOSE TO UNIVERSAL IF THE ABOVE LINUP
# CONFIGURATION IS USED
roster_caps = {
    "QB": 4,
    "RB": 8,
    "WR": 8,
    "TE": 3,
}

'''
descended from Team object'
will fill all startering positions first and then will maintain some balance using smart roster caps
'''
class Smart_ADP(Team):
    def draft_player(self,board):

        #FINDS OUT IF THERE ARE ANY STARTERS LEFT
        starter_num = sum(self.starter_cap.values()) - self.starter_cap["BEN"]
        starters_filled = sum([len(x) for x in self.roster.values()])- len(self.roster["BEN"])
        open_slots = starter_num - starters_filled

        # DETERMINES THE POSITIONS IN THE LINEUP THAT HAVENT BEEN FILLED YET
        if open_slots > 0:
            must_draft = [pos for pos in ["QB","RB","WR","TE"] if self.starter_cap[pos] > len(self.roster[pos])]

            #NOT GONNA DRAFT A TIGHT END AS A FLEX SO IT WON'T BE AN OPTION UNLESS CAUGHT ABOVE
            if self.roster["FLX"]==[]:
                for pos in ["RB","WR"]:
                    if pos not in must_draft:
                        must_draft.append(pos)


            new_board = board.loc[board["Position"].isin(must_draft)]

        #NEXT PRIORITY IS TO PREVENT OVERLOADING ON A POSITION IF STARTERS ARE ALL FILLED
        else:
            capped = [pos for pos in ["QB","RB","WR","TE"] if self.pos_counts[pos] >= self.roster_caps[pos]]
            draftable = [pos for pos in self.pos_counts.keys() if pos not in capped]
            new_board = board.loc[board["Position"].isin(draftable)]


        #BEST PLAYER FROM AVAILABLE AFTER RESTRICTIONS FROM ABOVE
        best = new_board.Overall.idxmin()
        position = new_board.loc[best].Position

        # HANDELS BROKEN DATAFRAME
        if type(position) != str:
            position = position[0]

        #UPDATES THE POSITION COUNTS AND ROSTER BASED ON THE SELECTION NAME AND POSITION
        self.pos_counts[position] += 1

        #ADD PLAYER TO LINEUP IN STARTING SPOT IF POSSIBLE
        if len(self.roster[position]) < self.starter_cap[position]:
            self.roster[position].append(best)

        #ADD TO FLEX SPOT IF STARTING SLOTS FOR POSITION ARE FILLED AND THERE IS A FLEX SPOT AVAILABLE
        elif (len(self.roster["FLX"]) < self.starter_cap["FLX"]) and (position in ["RB","WR","TE"]):
            self.roster["FLX"].append(best)

        else:
            self.roster["BEN"].append(best)

        #UPDATES THE REMAING PICKS AND PLAYERS CHOSEN ATTRIBUTES
        self.selected.append((self.picks[0], board.loc[best].Name))
        self.picks = self.picks[1:]

        return best

'''child of Team. It will elavuate the best player at curent pick and projected best player
at the next time it will pick at each position and will draft the best player at the position
where the gap is the largest. In cases where the team owns consecutive selections, the first
of these will look ahead two picks instead of one. It also has smart roster caps'''
class Perfect(Team):

    def draft_player(self, board):

        #DETERMINES WHICH PLAYERS ARE NOT LIKELY TO BE AVAILABLE THE NEXT TIME PICKING

        #CAN ONLY CALCULATE FOR THE NEXT TIME UP IF THERE IS GONNA BE A NEXT TIME UP!
        if len(self.picks) > 1:
            pick_gap = (self.picks[1]- self.picks[0])-1 # stores the number of picks between selections


            #THE FIRST OF CONSECUTIVE PICKS LOOKS AHEAD 2 PICKS NOT ONE
            if pick_gap == 0:

                # THIS ONLY WORKS IF THERE IS ANOTHER PICK AFTER THE CONSECUTIVE ONES
                if len(self.picks) >3:
                    next_pick = self.picks[2]
                    effective_gap = (next_pick - self.picks[1]) - 1
                    next_board = board.drop(board.Overall.nsmallest(effective_gap).index)

                # IF THE SECOND OF CONSECUTIVE PICKS IS THE LAST ROUND JUST MOVE ON
                else:
                    next_board = board.copy()

            # IF PICK ARE NOT CONSECUTIVE, FIND AND DROP THE N BEST PLAYERS BASED ON THE DISTANCE BETWEEN PICKS
            else:
                next_board = board.drop(board.Overall.nsmallest(pick_gap).index)



        # IF THIS IS THE LAST ROUND JUST MOVE ON
        else:
            next_board = board.copy()


        # CACLUTATES THE GAPS IN POSITIONAL VALUE BASED ON WHO IS REMOVED ABOVE
        groups_1 = board.groupby("Position")
        options = {} # stores the names of the best players at each position
        diffs = {} # stores the projected lost value at each position

        #BEST FOR EACH POSITION CURRENTLY AVIABLABLE
        for name, group in groups_1:
            best = group.FantasyPoints.nlargest(1)
            diffs[name] = best[0]
            options[name] = best.idxmax()


        # PROJECTED BEST FOR EACH POSITION THE NEXT TIME YOU DRAFT
        groups_2 = next_board.groupby("Position")
        for name, group in groups_2:
            best = group.FantasyPoints.nlargest(1)
            diffs[name] -= best[0]



        #PREVENTS OVERLAODING ON A POSITION REMOVING POSITIONS WITH TOO MANY PLAYERS FROM CONSIDERATION
        capped = [pos for pos in ["QB","RB","WR","TE"] if self.pos_counts[pos] >= self.roster_caps[pos]]
        for pos in capped:
            del diffs[pos]


        #EXTRACTS THE BEST PICK FROM AVAIALABLE POSITIONS
        position = max(diffs, key=diffs.get)
        best = options[position]


        #UPDATES THE POSITION COUNTS AND ROSTER BASED ON THE SELECTION NAME AND POSITION
        self.pos_counts[position] += 1


        #ADD PLAYER TO LINEUP IN STARTING SPOT IF POSSIBLE
        if len(self.roster[position]) < self.starter_cap[position]:
            self.roster[position].append(best)


        #ADD TO FLEX SPOT IF STARTING SLOTS FOR POSITION ARE FILLED AND THERE IS A FLEX SPOT AVAILABLE
        elif (len(self.roster["FLX"]) < self.starter_cap["FLX"]) and (position in ["RB","WR","TE"]):
            self.roster["FLX"].append(best)

        else:
            self.roster["BEN"].append(best)


        #UPDATES THE REMAING PICKS AND PLAYERS CHOSEN ATTRIBUTES
        self.selected.append((self.picks[0], board.loc[best].Name))
        self.picks = self.picks[1:]



        return best

# THESE SMARTER POSITION CONSTRAINTS ARE DESIGNED TO MIMIC HOW A HUMAN WOULD BALACNCE THEIR ROSTER COMPOSTION
# IT IS USED FOR PERFECT, SMART_ADP AND PREDICTIVE ALGORTHMS
smart_caps = {
    "QB": 2,
    "RB": 6,
    "WR": 6,
    "TE": 2,
}
"""This class is identical to the perfect class but instead of using actual known fantasy points, it uses the
projected points that were calculated from"""
class Predictive(Team):

    def draft_player(self, board):


        #DETERMINES WHICH PLAYERS ARE NOT LIKELY TO BE AVAILABLE THE NEXT TIME PICKING

        #CAN ONLY CALCULATE FOR THE NEXT TIME UP IF THERE IS GONNA BE A NEXT TIME UP!
        if len(self.picks) > 1:
            pick_gap = (self.picks[1]- self.picks[0])-1 # stores the number of picks between selections


            #THE FIRST OF CONSECUTIVE PICKS LOOKS AHEAD 2 PICKS NOT ONE
            if pick_gap == 0:

                # THIS ONLY WORKS IF THERE IS ANOTHER PICK AFTER THE CONSECUTIVE ONES
                if len(self.picks) >3:
                    next_pick = self.picks[2]
                    effective_gap = (next_pick - self.picks[1]) - 1
                    next_board = board.drop(board.Overall.nsmallest(effective_gap).index)

                # IF THE SECOND OF CONSECUTIVE PICKS IS THE LAST ROUND JUST MOVE ON
                else:
                    next_board = board.copy()

            # IF PICK ARE NOT CONSECUTIVE, FIND AND DROP THE N BEST PLAYERS BASED ON THE DISTANCE BETWEEN PICKS
            else:
                next_board = board.drop(board.Overall.nsmallest(pick_gap).index)



        # IF THIS IS THE LAST ROUND JUST MOVE ON
        else:
            next_board = board.copy()


        # CACLUTATES THE GAPS IN POSITIONAL VALUE BASED ON WHO IS REMOVED ABOVE
        groups_1 = board.groupby("Position")
        options = {} # stores the names of the best players at each position
        diffs = {} # stores the projected lost value at each position

        #BEST FOR EACH POSITION CURRENTLY AVIABLABLE
        for name, group in groups_1:
            best = group.projScore.nlargest(1)
            diffs[name] = best[0]
            options[name] = best.idxmax()


        # PROJECTED BEST FOR EACH POSITION THE NEXT TIME YOU DRAFT
        groups_2 = next_board.groupby("Position")
        for name, group in groups_2:
            best = group.projScore.nlargest(1)
            diffs[name] -= best[0]



        #PREVENTS OVERLAODING ON A POSITION REMOVING POSITIONS WITH TOO MANY PLAYERS FROM CONSIDERATION
        capped = [pos for pos in ["QB","RB","WR","TE"] if self.pos_counts[pos] >= self.roster_caps[pos]]
        for pos in capped:
            del diffs[pos]


        #EXTRACTS THE BEST PICK FROM AVAIALABLE POSITIONS
        position = max(diffs, key=diffs.get)
        best = options[position]


        #UPDATES THE POSITION COUNTS AND ROSTER BASED ON THE SELECTION NAME AND POSITION
        self.pos_counts[position] += 1


        #ADD PLAYER TO LINEUP IN STARTING SPOT IF POSSIBLE
        if len(self.roster[position]) < self.starter_cap[position]:
            self.roster[position].append(best)


        #ADD TO FLEX SPOT IF STARTING SLOTS FOR POSITION ARE FILLED AND THERE IS A FLEX SPOT AVAILABLE
        elif (len(self.roster["FLX"]) < self.starter_cap["FLX"]) and (position in ["RB","WR","TE"]):
            self.roster["FLX"].append(best)

        else:
            self.roster["BEN"].append(best)


        #UPDATES THE REMAING PICKS AND PLAYERS CHOSEN ATTRIBUTES
        self.selected.append((self.picks[0], board.loc[best].Name))
        self.picks = self.picks[1:]



        return best

import random
'''
This class us used to simulate an entire fantasy season. it assigns draftpicks to teams, simulates a draft,
simulates the regular fantasy season using an expected wins per week model and then simulate a head to
head postseason amoung the 4 best teams. It takes a list of team objects, lineup composition requirements,
they year to be simulated, and a scoring system. Its simulate method returns the standings as well as how many
regular season points each team scored

ATTRIBUTES:

num_teams:      Int that stores the number of teams in the league

year:           Int storing the year in which the league takes place

board:          Data Frame storing the available players in the league. It is updated when teams make draft selections

positions:      Dictionary storing the lineup requirements of the league

rounds:         Int storing the number of rounds in the draft

picks:          List that stores refrences to team objects in the order they will draft. It is used to call
                on those teams to make selections in the correct order. After each pick is make, the reference is
                replaced with the player selected

weekly_scores:  Dictionary that keeps track of the scores of each team each week during the entire season

scoring:        String that indentifies what scoring rules are in place for the league


METHODS:

set_board:    Filters the data input into the league object to be only in the year of interest and only players who are
              a QB, RB, WR or TE.

set_picks :   maps each selection in the upcoming draft to a team based on the order of the teams in the list. The draft
              is a snake draft so picks are mapped in a snaking order.

draft:        Simulates the draft by calling each team to select a player in order. Is invoked by simulate method

simulate:     Used to run the entire league process from the draft through the post season. Is invoked outside of the
              class

sim_season:   Called by simulate method to simulate the season. It uses an expected wins week by week model for the regular
              season for simplicity and to avoid any luck of drawing favorable matchups. It simulates the postseason using the


'''

class League:
    def __init__(self, teams, positions, year, data, scoring, weekly):
        self.num_teams = len(teams)
        self.teams = teams
        self.year = year
        self.board = self.set_board(data)
        self.positions = positions
        self.rounds = sum(self.positions.values())
        self.picks = self.set_picks()
        self.weekly_scores = {}
        for team in self.teams:
            self.weekly_scores[team] = []
        self.scoring = scoring
        self.weekly = weekly


    def set_board(self, data):
        df = data.loc[data["Year"]== str(self.year)]
        df = df.loc[df["Position"].isin(["QB",'RB','WR','TE'])]
        df["Overall"]= df.apply(lambda x: x["Overall"] if x["Overall"] > 0 else 999999, axis = 1)
        return(df)


    #SETS DRAFT ORDER BY INVERTING ORDER OF ODD ROUNDS
    def set_picks(self):
        d = []
        for r in range(self.rounds):
            for i in range(self.num_teams):
                pick_num =(r * self.num_teams) + i # 'i'th pick of round r
                if r % 2 == 0:
                    d.append(self.teams[i])
                    self.teams[i].add_pick(pick_num)
                else:
                    d.append(self.teams[(self.num_teams - i) -1]) # -1 becuase indexing starts at 0
                    self.teams[(self.num_teams - i) -1].add_pick(pick_num) # adds pick to the team's list

        return d

    def draft(self):
        for i in range(len(self.picks)):
            selection = self.picks[i].draft_player(self.board)
            self.picks[i] = selection
            self.board.drop(selection, inplace=True)

    def simulate(self):
        self.draft()
        return self.sim_season()

    # SIMULATES REGULAR AND POST SEASONS
    def sim_season(self):

        # SIMULATE THE REGULAR SEASON WEEK BE WEEK BY RANKING OPTIMAL LINUPS OF EACH TEAM AND ASSIGNING PARTIAL WINS
        # BASED ON WHAT FRACTION OF OTHER TEAMS EACH TEAM BEAT


        #RUNS FOR EACH WEEK IN REGULAR SEASON
        for week in range(1,15):
            data = self.weekly.loc[(self.weekly["Year"]== str(self.year)) & (self.weekly["Week"] == str(week))]
            scores = []
            # GETS OPTIMAL LINUP OF EACH TEAM AND RANKS THEM
            for team in self.teams:
                score = team.set_lineup(data, self.scoring)
                scores.append((score,team,team.name))
                self.weekly_scores[team].append(score)
            week_rank = sorted(scores, key=lambda x: x[0]) # sorts the scores

            # ASSIGNS PARTIAL WINS TO EACH TEAM BY DIVIDING THE RANK BY THE TOTAL NUMBER OF TEAMS IN THE LEAGUE
            for i in range(len(week_rank)):
                wins = i / self.num_teams
                week_rank[i][1].add_wins(wins)


        #COMPUTES WHICH TEAMS BELONG IN THE POSTSEASON
        standings = []
        for team in self.teams:
            standings.append((team.wins, team))
        standings = sorted(standings, key=lambda x: x[0], reverse=True) # sorts the standings according to wins
        playoffs = standings[0:4]
        non_playoffs = standings[4:]



        # SIMULATES THE POSTSEASON USING HEAD TO HEAD


        #CALCULATES THE ROUND 1 SCORES OF EACH TEAM IN THE POSTSEASON
        scores=[]
        data = self.weekly.loc[(self.weekly["Year"]== str(self.year)) & (self.weekly["Week"] == "15")]
        for i in range(len((playoffs))):
            team = playoffs[i][1]
            score = playoffs[i][1].set_lineup(data, self.scoring)
            scores.append((score,team))

        #WINNERS OF EACH ROUND 1 MATCHUP (1 VS 4 AND 2 VS 3) WILL PLAY IN THE CHAMPIONSHIP
        f1 = max([scores[0],scores[3]], key=lambda x: x[0] )[1]
        f2 = max([scores[1],scores[2]], key=lambda x: x[0] )[1]

        #LOSERS OF EACH ROUND ONE MATCHUP PLAY IN THE CONSOLATION GAME
        l1 = min([scores[0],scores[3]], key=lambda x: x[0] )[1]
        l2 = min([scores[1],scores[2]], key=lambda x: x[0] )[1]

        # CALCULATE FINAL ROUND SCORES FOR PLAYOFF TEAMS
        data = self.weekly.loc[(self.weekly["Year"]== str(self.year)) & (self.weekly["Week"] == '16')]
        scores=[(team.set_lineup(data, self.scoring),team) for team in [f1,f2,l1,l2]]

        # FINAL POSITIONS FOR EACH OF THE TEAMS AS DETERMINED BY THIS ROUND
        first = max(scores[0:2], key=lambda x: x[0] )[1]
        second = min(scores[0:2], key=lambda x: x[0] )[1]
        third = max(scores[2:], key=lambda x: x[0] )[1]
        fourth = min(scores[2:], key=lambda x: x[0] )[1]

        # ADD WEEKLY SCORES FOR ALL TEAMS DURING THE POSTSEASON TO GET BETTER MEASURE OF POINTS AT SEASON'S END
        for team in self.teams:
            for x in [15,16]:
                data = self.weekly.loc[(self.weekly["Year"]== str(self.year)) & (self.weekly["Week"] == str(x))]
                self.weekly_scores[team].append(team.set_lineup(data, self.scoring))


        # BUILD FINAL STANDINGS USING POSTSEASON AND WINS FOR THE NON PLAYOFF TEAMS
        playoffs = [x[1] for x in playoffs]
        non_playoffs = [x[1] for x in non_playoffs]
        standings[0] = (first, sum(self.weekly_scores[first]))
        standings[1] = (second, sum(self.weekly_scores[second]))
        standings[2] = (third, sum(self.weekly_scores[third]))
        standings[3] = (fourth, sum(self.weekly_scores[fourth]))
        for x in range(4,self.num_teams):
            standings[x] = (standings[x][1], sum(self.weekly_scores[standings[x][1]]))

        return standings

#teams = {
    #"Predictive": 1,
    #"Team": 9
#}


def full_sim(team_dict, start, end, repeats, scoring, positions, data, weekly):
    d = pd.DataFrame({
    "Name": [""],
    "Year": [0],
    "Draft_Pos": [0],
    "Rank": [0],
    "Points": [0],
    })

    teams= []
    for k in team_dict.keys():
        for i in range(team_dict[k]):
            if k == "Team":
                team = Team(positions, roster_caps, "team"+str(i + 1))
            elif k == "Smart_ADP":
                team = Team(positions, smart_caps, "smart"+str(i + 1))
            elif k=="Predictive":
                team = Predictive(positions, smart_caps, "predictive"+str(i + 1))
            elif k=="Perfect":
                team = Perfect(positions, smart_caps, "perfect"+str(i + 1))
            else:
                "something went wrong"
                return
            teams.append(team)

    for year in range(start, end+1):
        for i in range(len(teams)):
            for j in range(0,repeats):
                dat = data.loc[data["Year"]== str(year)]
                league = League(teams, positions, year,  dat, scoring, weekly)
                results =league.simulate()
                new_teams = []
                for team in teams:
                    if "team" in team.name:
                        team = Team(positions, roster_caps, team.name)
                    elif "smart" in team.name:
                        team = Team(positions, smart_caps, team.name)
                    elif "predictive" in team.name:
                        team = Predictive(positions, smart_caps, team.name)
                    elif 'perfect' in team.name:
                        team = Perfect(positions, smart_caps, team.name)
                    else:
                        print("error!!")
                    new_teams.append(team)
                    teams = new_teams

                for x in range(len(results)):
                    team = results[x][0]
                    d = d.append({"Name": team.name, "Year": str(year), "Draft_Pos": team.selected[0][0],
                    "Rank": x, 'Points':results[x][1]}, ignore_index = True)


            # shifts all teams by one
            teams.insert(0,teams[-1])
            teams = teams[:-1]
    d=d.iloc[1:]
    return d
