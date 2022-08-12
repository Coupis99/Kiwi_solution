Principle:
- At first the solution creates a dictionary (graph) from given data
  with all unique cities as a key
- Every key has list of values (cities) where is possible to fly straight from
  the key
- Example of graph:

{'YOT': ['IUT', 'GXV', 'IUQ', 'LOM'],
'IUQ': ['YOT', 'GXV', 'IUT'],
'IUT': ['YOT', 'IUQ', 'LOM', 'GXV'],
'GXV': ['IUQ', 'YOT', 'IUT', 'LOM'],
'LOM': ['YOT', 'GXV', 'IUT']}

- From the graph above we can see, that except of IUQ <-> LOM, we
  can fly from every city to everywhere
- After that the solution uses the Depth First Search algorithm and looks for
  all possible combinations with respect to the parameters 
- If the solutions finds matching flight in the list, it is stored in a list too, which is
  printed out in the end of program
- The output is sorted by price from lowest to highest

How to run:
- All flights from origin to destination with respect to data, number
  of bags and return: python -m solution data origin destination --bags=0 --return
- Default value for bags is 0 (no need to specify)
- Default value for return is False (no need to specify)
- For example: python -m solution examples/example2.csv YOT LOM --bags=2 --return 
- in case of return flight, there are no time restrictions, which means it finds all possibilities from csv 
  => time consuming: in example3.csv return flight computation takes about 25 seconds