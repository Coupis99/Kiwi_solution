import csv
from datetime import datetime, timedelta 
import json
import argparse

class Flight:
    
    def __init__(self, data, origin, destination, bags = 0, ret = False):
        self.origin = origin
        self.destination = destination
        self.data = self._load_flights(data)[0]
        self.keys = self._load_flights(data)[1]
        self.bags = bags
        self.ret = ret
    
    def _load_flights(self, file):
        """
        - loading data from csv to list
        """
        flights = []
        with open(file, "r") as f:
            f_reader = csv.reader(f)
            for flight in f_reader:
                flights.append(flight)
        keys = flights.pop(0)
        flights.sort(key=lambda x: x[3])
        return [list(flights), keys]

    def create_graph(self):
        """
        - create a graph from dataframe
        - the output of this function is a dictionary with all unique cities in df as a key
        - every key has list of values (cities), where is possible to fly straight from the key
        """
        ret_dict = {}
        for i in self.data:
            if i[1] not in ret_dict:
                ret_dict[i[1]] = []
            if i[2] not in ret_dict[i[1]]:
                ret_dict[i[1]].append(i[2])
        return ret_dict
    
    def _return_datetime_format(self, s):
        """
        - return datetime format from string
        """
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S")

    def _find_connection(self, start, end, time = 0, ret = False):
        """
        - find all connections between two cities in a dataframe with respect to the layover rules
        """
        # no rules
        if time == 0:
            ret_flights = []
            for flight in self.data:
                if flight[1] == str(start) and flight[2] == end:
                    ret_flights.append(flight)
            return ret_flights  
        # apply when start looking for flight back 
        else:
            if ret == True:
                time = self._return_datetime_format(time)
                ret_flights = []
                for flight in self.data:
                    if flight[1] == str(start) and flight[2] == str(end):
                        if time  < self._return_datetime_format(flight[3]):
                            ret_flights.append(flight)
                return ret_flights
            # layover rule
            else:
                time = self._return_datetime_format(time)
                ret_flights = []
                for flight in self.data:
                    if flight[1] == str(start) and flight[2] == end:
                        if time + timedelta(seconds = 3600) <= self._return_datetime_format(flight[3]) <= time + timedelta(seconds = 21600):
                            ret_flights.append(flight)
                return ret_flights
    
    def _parse_time(self, s):
        """
        - parse time from seconds to HH:MM:SS format
        """
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
    
    def _return_right_format(self, lst, end):
        """
        - return required json format from list
        """
        # direct flight
        if end == lst[-1][2]:
            ret_dict = {"flights": []}
            for flight in lst:
                dictt = {}
                i = 0
                for key in self.keys:
                    dictt[key] = flight[i]
                    i += 1
                ret_dict["flights"].append(dictt)
                ret_dict["bags_allowed"] = min([int(a[7]) for a in lst])
                ret_dict["bags_count"] = self.bags
                ret_dict["destination"] = lst[-1][2]
                ret_dict["origin"] = lst[0][1]
                ret_dict["total_price"] = sum([int(float(a[5])) for a in lst]) + self.bags * sum([int(float(a[6])) for a in lst])
                ret_dict["travel_time"] = self._parse_time((self._return_datetime_format(lst[-1][4]) - self._return_datetime_format(lst[0][3])).total_seconds())
            return ret_dict
        else:
            # splitting lst 
            splt_idx = [a[2] for a in lst].index(end) + 1
            fl_to_dest = lst[:splt_idx]
            fl_from_dest = lst[splt_idx:]

            # return flight - the way to the destination 
            ret_dict = {"flights": []}
            dict_to_dest = {"flights_to_destination": []}
            dict_from_dest = {"flights_from_destination": []}
            
            for flight in fl_to_dest:
                dictt = {}
                i = 0
                for key in self.keys:
                    dictt[key] = flight[i]
                    i += 1
                dict_to_dest["flights_to_destination"].append(dictt)
            dict_to_dest["bags_allowed"] = min([int(a[7]) for a in fl_to_dest])
            dict_to_dest["bags_count"] = self.bags
            dict_to_dest["destination"] = fl_to_dest[-1][2]
            dict_to_dest["origin"] = fl_to_dest[0][1]
            dict_to_dest["total_price"] = sum([int(float(a[5])) for a in fl_to_dest]) + self.bags * sum([int(float(a[6])) for a in fl_to_dest])
            travel_time_to_dest = (self._return_datetime_format(fl_to_dest[-1][4]) - self._return_datetime_format(fl_to_dest[0][3])).total_seconds()
            dict_to_dest["travel_time"] = self._parse_time(travel_time_to_dest)
            ret_dict["flights"].append(dict_to_dest)

            # return flight - the way from the destination 
            for flight in fl_from_dest:
                dictt = {}
                i = 0
                for key in self.keys:
                    dictt[key] = flight[i]
                    i += 1
                dict_from_dest["flights_from_destination"].append(dictt)
            dict_from_dest["bags_allowed"] = min([int(a[7]) for a in fl_from_dest])
            dict_from_dest["bags_count"] = self.bags
            dict_from_dest["destination"] = fl_from_dest[-1][2]
            dict_from_dest["origin"] = fl_from_dest[0][1]
            dict_from_dest["total_price"] = sum([int(float(a[5])) for a in fl_from_dest]) + self.bags * sum([int(float(a[6])) for a in fl_from_dest])
            travel_time_from_dest = (self._return_datetime_format(fl_from_dest[-1][4]) - self._return_datetime_format(fl_from_dest[0][3])).total_seconds()
            dict_from_dest["travel_time"] = self._parse_time(travel_time_from_dest)
            ret_dict["flights"].append(dict_from_dest)

            # final summary
            ret_dict["bags_allowed"] = min(int(dict_to_dest["bags_allowed"]), int(dict_from_dest["bags_allowed"]))
            ret_dict["bags_count"] = self.bags
            ret_dict["destination"] = lst[-1][2]
            ret_dict["origin"] = lst[0][1]
            ret_dict["total_price"] = int(dict_to_dest["total_price"]) + int(dict_from_dest["total_price"])
            ret_dict["travel_time"] = self._parse_time(travel_time_to_dest + travel_time_from_dest)
            return ret_dict

    def _find_flights(self, start, end, graph, path, all_path, temp_flights, all_flights, ret, ret_time):
        """
        - find all flights from origin (start) to destination (end) using recursion 
        - using DFS algorithm 
        """
        path.append(start)

        if (start == end):
            # direct flight
            if ret == False:
                all_path.append(list(path))
                if min([int(float(a[7])) for a in temp_flights]) >= self.bags:
                    all_flights.append(self._return_right_format(temp_flights, self.destination))  
            else:
                # return flight
                all_path.append(list(path))
                path2 = []
                ret = False
                ret_time = True
                self._find_flights(end, self.origin, graph, path2, all_path, temp_flights, all_flights, ret, ret_time)   
        else:
            for i in graph[start]:
                if (i not in path):
                    if temp_flights == []:
                        # at the beginning 
                        flights = self._find_connection(start, i)
                    else:
                        # at the beginning of the way back 
                        if ret_time == True:
                            flights = self._find_connection(start, i, temp_flights[-1][4], True) 
                        else:
                            # using layover rules
                            flights = self._find_connection(start, i, temp_flights[-1][4]) 
                    if flights != []:
                        for flight in flights:
                            temp_flights.append(list(flight))
                            self._find_flights(i, end, graph, path, all_path, temp_flights, all_flights, ret, False)
                            temp_flights.pop()
        path.pop()

    def return_all_flights(self):
        """
        - return all flights from origin to destination available in csv and sort them with respect to price
        - return json format 
        """
        graph = self.create_graph()
        path = []
        all_path = []
        temp_flights = [] 
        all_flights = []
        self._find_flights(self.origin, self.destination, graph, path, all_path, temp_flights, all_flights, self.ret, False)
        all_flights.sort(key = lambda x: x["total_price"])
        if len(all_flights) > 0:
            return json.dumps(all_flights, indent = 4)
        else:
            return "No flights found."

def main():
    """
    - handling inputs from terminal
    """
    try: 
        parser = argparse.ArgumentParser()
        parser.add_argument("data", help="Path to dataset - Required")
        parser.add_argument("origin", help="Origin shortcut in dataset - Required")
        parser.add_argument("destination", help="Destination shortcut in dataset - Required")
        parser.add_argument("--bags", help="Number of requested bags - Optional (defaults to 0)", type=int, default=0)
        parser.add_argument("--returnn", help="Is it a return flight? - Optional (defaults to false)", action="store_true")
        args = parser.parse_args()
        flight = Flight(args.data, args.origin, args.destination, int(args.bags), args.returnn)
        print(flight.return_all_flights())
    except:
        print("Invalid format!")
        print("The correct format is: python -m solution data origin destination --bags=0 --return")
       
# always True
if __name__ == "__main__":
    main()