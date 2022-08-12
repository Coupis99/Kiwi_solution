import pandas as pd 
import json
from datetime import datetime, timedelta 
import sys

class Flight:
    
    def __init__(self, data, origin, destination, bags = 0):
        self.origin = origin
        self.destination = destination
        self.data = pd.read_csv(data)

        # all unique possible combinations between origin and destination
        self.data_c = self.data[["origin", "destination"]].drop_duplicates()

        # all unique cities in a dataframe
        self.data_s = self.data["origin"].drop_duplicates()

        # count of bags
        self.bags = bags

    # will create a graph from dataframe
    # the output of this function is a dictionary with all unique cities in df as a key
    # every key has list of values (cities), where is possible to fly straight from the key
    def create_graph(self):
        dictt = {}
        for i in self.data_s:
            a = self.data_c[self.data_c["destination"] == i]
            values = []
            for j in a["origin"]:
                values.append(j)
            dictt[i] = values
        return dictt
    
    # Depth-First search algorithm
    # will create list of list from graph above
    # in an outer list are stored all possible combinations how to get from origin (start) to destination (self.destination) with respect to grpah and dataframe
    # each combination is stored as a list
    def _dfs_util(self, graph, start, visited, path, ab, all_path):
        visited[ab.index(start)] = True
        path.append(str(start))
        if start == self.destination:
            all_path.append(list(path))
        else:
            for nextt in graph[start]:
                if visited[ab.index(nextt)] == False:
                    self._dfs_util(graph, nextt, visited, path, ab, all_path)
        path.pop()
        visited[ab.index(start)] = False
        return all_path
    
    # will cal _dfs_util() function
    def dfs(self):
        path = []
        visited = [False] * len(self.data_s)
        ab = [a for a in self.data_s]
        all_path = []
        graph = self.create_graph()
        return self._dfs_util(graph, self.origin, visited, path, ab, all_path)
    
    # will find all connections between two cities in a dataframe
    def _find_connection(self, a, b):
        return self.data[(self.data["origin"] == a) & (self.data["destination"] == b)] 

    # will return a datetime from string
    def _return_date(self, s):
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S")
    
    # will parse seconds to HH:MM:SS format
    def _parse_time(self, s):
        hours = int(s / 3600)
        minutes = int((s - hours * 3600) / 60)
        seconds = (s - hours * 3600 - minutes * 60)
        if hours < 10:
            hours = str(0) + str(hours)
        if minutes < 10:
            minutes = str(0) + str(minutes)
        if seconds < 10:
            seconds = str(0) + str(seconds)
        return  str(hours) + ":" + str(minutes) + ":" + str(seconds)
    
    # will return required json format from pandas dataframe
    def _return_dict_format(self, df):
        ret_dict = {"flights": []}
        for row in range(len(df)):
            dictt = {}
            for col in df.columns:
                dictt[col] = df.iloc[row][col]
            ret_dict["flights"].append(dictt)

        ret_dict["bags_allowed"] = df["bags_allowed"].min()
        ret_dict["bags_count"] = self.bags
        ret_dict["destination"] = df.loc[df.index[df.shape[0] - 1]]["destination"]
        ret_dict["origin"] = df.loc[df.index[0]]["origin"]
        ret_dict["total_price"] = df["base_price"].sum() + self.bags * df["bag_price"].sum()
        ret_dict["travel_time"] = self._parse_time((self._return_date(df.iloc[len(df) - 1]["arrival"]) 
                                                    - self._return_date(df.iloc[0]["departure"])).seconds)
        return ret_dict
    
    # will check if combination given by arr list from dfs() function is available in dataframe with respect to parameters
    # similar logic to DFS algorithm 
    def _find_flights_util(self, arr, first_index, second_index, dff, all_flights):
        if (second_index == (len(arr))) & (dff.empty == False):
            if dff["bags_allowed"].min() >= self.bags:
                all_flights.append(self._return_dict_format(dff)) 
        else:
            flights = self._find_connection(arr[first_index], arr[second_index])
            for i in range(flights.shape[0]):
                if (dff.empty):
                    dff = dff.append(flights.iloc[i])
                    self._find_flights_util(arr, first_index + 1, second_index + 1, dff, all_flights)
                    dff = dff.drop(dff.index[dff.shape[0] - 1])
                elif timedelta(seconds=3600) <= (self._return_date(flights.iloc[i]["departure"]) 
                                                 - self._return_date(dff.loc[dff.index[dff.shape[0] - 1]]["arrival"])) <= timedelta(seconds=21600):
                    dff = dff.append(flights.iloc[i])
                    self._find_flights_util(arr, first_index + 1, second_index + 1, dff, all_flights)
                    dff = dff.drop(dff.index[dff.shape[0] - 1])

    # will sort list on a total_price basis               
    def _sort_function(self, e):
        return e["total_price"]

    # will call _find_flights_util() function              
    def _find_flights(self, arr, all_flights):
        dff = pd.DataFrame()
        self._find_flights_util(arr, 0, 1, dff, all_flights)
    
    # will return all flights from origin to destination available in dataframe
    # it goes through each combination from dfs() function and call _find_flights() function
    def return_all_flights(self):
        all_flights = []
        paths = self.dfs()
        for path in paths:
            self._find_flights(path, all_flights)
        all_flights.sort(key = self._sort_function)
        if len(all_flights) > 0:
            return json.dumps(all_flights, indent = 4)
        else:
            return "No flights found."

# handling inputs from terminal 
def main():
    args = sys.argv[1:]
    try:
        if len(args) == 3:
            flight = Flight(args[0], args[1], args[2])
            print(flight.return_all_flights())  
        elif (len(args) == 4) & (int(args[3]) >= 0):
            flight = Flight(args[0], args[1], args[2], int(args[3]))
            print(flight.return_all_flights())  
        else:
            print("Invalid format!")
            print("The correct format is: python -m solution data origin destination bags_count")
    except:
        print("Invalid format!")
        print("The correct format is: python -m solution data origin destination bags_count")

# always True
if __name__ == "__main__":
    main()
