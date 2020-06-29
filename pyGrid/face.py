from pyGrid import definition

class FACE:
    nodecoord = dict()
    cellnodes = dict() # references nodes connected to each cell
    nodecells = dict() # references cells associated with each node

    def __init__(self, gdef=None):
        if gdef is None: return

        # collects cell IDs surrounding grid faces

        # EXAMPLE: 4x5 cells = 2*(4x5)+4+5 = 49 faces
        #Dim gd1 As New Grid.Definition("test", 4, 5)
        # o---o---o---o---o---o       o-0-o-1-o-2-o-3-o-4-o      o---o---o---o---o---o
        # | 0 | 1 | 2 | 3 | 4 |       |   |   |   |   |   |     25  26  27  28  29  30        North-east              |
        # o---o---o---o---o---o       o-5-o-6-o-7-o-8-o-9-o      o---o---o---o---o---o     ^   positive          from | to
        # | 5 | 6 | 7 | 8 | 9 |       |   |   |   |   |   |     31  32  33  34  35  36    /|\                         |
        # o---o---o---o---o---o  -->  o-10o-11o-12o-13o-14o  &   o---o---o---o---o---o     |               
        # | 10| 11| 12| 13| 14|       |   |   |   |   |   |     37  38  39  40  41  42     |   +                     to
        # o---o---o---o---o---o       o-15o-16o-17o-18o-19o      o---o---o---o---o---o     |_________\             ------
        # | 15| 16| 17| 18| 19|       |   |   |   |   |   |     43  44  45  46  47  48               /              from 
        # o---o---o---o---o---o       o-20o-21o-22o-23o-24o      o---o---o---o---o---o

        pass