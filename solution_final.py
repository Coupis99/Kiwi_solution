import pandas as pd 
import json
from datetime import datetime, timedelta 
import argparse

class Flight:
    
    def __init__(self, data, origin, destination, bags = 0, ret = False):
        self.origin = origin
        self.destination = destination
        self.data = pd.read_csv(data)

        # all unique possible combinations between origin and destination
        self.data_c = self.data[["origin", "destination"]].drop_duplicates()

        # all unique cities in a dataframe
        self.data_s = self.data["origin"].drop_duplicates()

        # count of bags
        self.bags = bags
        
        self.ret = ret

    # create a graph from dataframe
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
    
    # find all connections between two cities in a dataframe with respect to the layover rules
    def _find_connection(self, a, b, time = 0, ret = False):
        # no rules
        if time == 0: 
            return self.data[(self.data["origin"] == a) & (self.data["destination"] == b)] 
        else:
            # apply when start looking for flight back 
            if ret == True:
                df = self.data[(self.data["origin"] == a) & (self.data["destination"] == b)]
                adj_df = pd.DataFrame()
                for i in range(df.shape[0]):
                    if self._return_date(df.iloc[i]["departure"]) > self._return_date(time):
                        adj_df = adj_df.append(df.iloc[i])
                return adj_df
            # layover rule
            else:
                df = self.data[(self.data["origin"] == a) & (self.data["destination"] == b)]
                adj_df = pd.DataFrame()
                for i in range(df.shape[0]):
                    if timedelta(seconds=21600) + self._return_date(time) >= self._return_date(df.iloc[i]["departure"]) >= timedelta(seconds=3600) + self._return_date(time):
                        adj_df = adj_df.append(df.iloc[i])
                return adj_df

    # return a datetime from string
    def _return_date(self, s):
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S")
    
    # split dataframe with respect to splt parameter
    def _split_df(self, splt, df):
        df = df.reset_index(drop = True)
        df1 = pd.DataFrame()
        df2 = pd.DataFrame()
        break_rows = 0
        for row in range(len(df)):
            if df.iloc[row]["destination"] == splt:
                break_rows = row + 1
        df1 = df.iloc[range(0, break_rows)]
        df2 = df.iloc[range(break_rows, (len(df)))]
        return [df1, df2]
    
    # parse seconds to HH:MM:SS format
    def _parse_time(self, s):
        hours = int(s / 3600)
        minutes = int((s - hours * 3600) / 60)
        seconds = int(s - hours * 3600 - minutes * 60)
        if hours < 10:
            hours = str(0) + str(hours)
        if minutes < 10:
            minutes = str(0) + str(minutes)
        if seconds < 10:
            seconds = str(0) + str(seconds)
        return  str(hours) + ":" + str(minutes) + ":" + str(seconds)
    
    # return required json format from pandas dataframe
    def _return_dict_format(self, df, end):
        df = df.reset_index(drop = True)
        # direct flight 
        if str(df.iloc[df.shape[0] - 1]["destination"]) == str(end):
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
                                                        - self._return_date(df.iloc[0]["departure"])).total_seconds())
            return ret_dict
        else:
            # return flight - the way to the destination 
            df1 = self._split_df(str(end), df)[0]
            df1 = df1.reset_index(drop = True)
            df2 = self._split_df(str(end), df)[1]
            df2 = df2.reset_index(drop = True)
            
            ret_dict = {"return flights": []}
            dict_to_dest = {"flights to dest.": []}
            dict_from_dest = {"flights from dest.": []}
            
            for row in range(len(df1)):
                dictt = {}
                for col in df1.columns:
                    dictt[col] = df1.iloc[row][col]
                dict_to_dest["flights to dest."].append(dictt) 
    
            dict_to_dest["bags_allowed"] = df1["bags_allowed"].min()
            dict_to_dest["bags_count"] = self.bags
            dict_to_dest["destination"] = df1.loc[df1.index[df1.shape[0] - 1]]["destination"]
            dict_to_dest["origin"] = df1.loc[df1.index[0]]["origin"]
            dict_to_dest["total_price"] = df1["base_price"].sum() + self.bags * df1["bag_price"].sum()
            dict_to_dest["travel_time"] = self._parse_time((self._return_date(df1.iloc[len(df1) - 1]["arrival"]) 
                                                        - self._return_date(df1.iloc[0]["departure"])).total_seconds())
            ret_dict["return flights"].append(dict_to_dest)
            
            # return flight - the way from the destination
            for row in range(len(df2)):
                dictt = {}
                for col in df2.columns:
                    dictt[col] = df2.iloc[row][col]
                dict_from_dest["flights from dest."].append(dictt) 
            dict_from_dest["bags_allowed"] = df2["bags_allowed"].min()
            dict_from_dest["bags_count"] = self.bags
            dict_from_dest["destination"] = df2.loc[df2.index[df2.shape[0] - 1]]["destination"]
            dict_from_dest["origin"] = df2.loc[df2.index[0]]["origin"]
            dict_from_dest["total_price"] = df2["base_price"].sum() + self.bags * df2["bag_price"].sum()
            dict_from_dest["travel_time"] = self._parse_time((self._return_date(df2.iloc[len(df2) - 1]["arrival"]) 
                                                        - self._return_date(df2.iloc[0]["departure"])).total_seconds())
            ret_dict["return flights"].append(dict_from_dest)
            
            ret_dict["bags_allowed"] = min(int(dict_to_dest["bags_allowed"]), int(dict_from_dest["bags_allowed"]))
            ret_dict["bags_count"] = self.bags
            ret_dict["destination"] = df2.loc[df2.index[df2.shape[0] - 1]]["destination"]
            ret_dict["origin"] = df1.loc[df1.index[0]]["origin"]
            ret_dict["total_price"] = int(dict_to_dest["total_price"]) + int(dict_from_dest["total_price"])
            ret_dict["travel_time"] = self._parse_time(((self._return_date(df1.iloc[len(df1) - 1]["arrival"]) 
                                                        - self._return_date(df1.iloc[0]["departure"])).total_seconds())
                                                       + (self._return_date(df2.iloc[len(df2) - 1]["arrival"]) - 
                                                          self._return_date(df2.iloc[0]["departure"])).total_seconds())
            return ret_dict
            
    # sort list on a total_price basis               
    def _sort_function(self, e):
        return e["total_price"]
    
    # find all flights from origin (start) to destination (end)
    # using DFS algorithm 
    def _find_flights(self, start, end, graph, path, all_path, df, all_df, ret, ret_time):
        
        path.append(start)

        if (start == end):
            # direct flight
            if ret == False:
                all_path.append(list(path))
                if df["bags_allowed"].min() >= self.bags:
                    all_df.append(self._return_dict_format(df, self.destination))   
            else:
                # return flight 
                all_path.append(list(path))
                path2 = []
                ret = False
                ret_time = True
                self._find_flights(end, self.origin, graph, path2, all_path, df, all_df, ret, ret_time)  
        else:
            for i in graph[start]:
                if (i not in path):
                    if df.empty == True:
                        # at the beginning 
                        flights = self._find_connection(start, i)
                    else:
                        # at the beginning of the way back 
                        if ret_time == True:
                            flights = self._find_connection(start, i, str(df.iloc[df.shape[0] - 1]["arrival"]), True)
                        else:
                            # using layover rules
                            flights = self._find_connection(start, i, str(df.iloc[df.shape[0] - 1]["arrival"]))                     
                    if flights.empty == False:
                        for flight in range(flights.shape[0]):
                            df = df.append(flights.iloc[flight])
                            self._find_flights(i, end, graph, path, all_path, df, all_df, ret, False)
                            df = df.drop(df.index[df.shape[0] - 1])
        path.pop()
    
    # return all flights from origin to destination available in dataframe and sort the with respect to price
    # return json format 
    def return_all_flights(self):
        graph = self.create_graph()
        path = []
        all_path = []
        df = pd.DataFrame()
        all_df = []
        self._find_flights(self.origin, self.destination, graph, path, all_path, df, all_df, self.ret, False)
        all_df.sort(key = self._sort_function)
        if len(all_df) > 0:
            return json.dumps(all_df, indent = 4)
        else:
            return "No flights found."

# handling inputs from terminal 
def main():
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("data", help="Path to dataset - Required")
        parser.add_argument("origin", help="Origin shortcut in dataset - Required")
        parser.add_argument("destination", help="Destination shortcut in dataset - Required")
        parser.add_argument("--bags", help="Number of requested bags - Optional (defaults to 0)", type=int, default=0)
        parser.add_argument("--returnn", help="Is it a return flight? - Optional (defaults to false)", action="store_true")
        args = parser.parse_args()
        flight = Flight(args.data, args.origin, args.destination,int(args.bags),args.returnn)
        print(flight.return_all_flights())
    except:
        print("Invalid format!")
        print("The correct format is: python -m solution data origin destination --bags=0 --return")
    
# always True
if __name__ == "__main__":
    main()