# ==============================CS-199==================================
# FILE:            MyAI.py
#
# AUTHOR:         Justin Chung
#
# DESCRIPTION:     This file contains the MyAI class. You will implement your
#                  agent in this file. You will write the 'getAction' function,
#                  the constructor, and any additional helper functions.
#
# NOTES:          - MyAI inherits from the abstract AI class in AI.py.
#
#                  - DO NOT MAKE CHANGES TO THIS FILE.
# ==============================CS-199==================================

from AI import AI
from Action import Action
from heapq import heappush, heappop


class MyAI(AI):

    def __init__(self, rowDimension, colDimension, totalMines, startX, startY):
        self.row_dimension = rowDimension
        self.col_dimension = colDimension
        self.total_mines = totalMines
        self.x = startX
        self.y = startY

        # Initialize the board with covered cells
        self.board = [["#" for _ in range(self.col_dimension)] for _ in range(self.row_dimension)]
        self.queue = []
        self.uncovered = set()
        self.bombs = set()

    def addActionsToQueue(self, x, y, priority, action, directions):
        for cell in directions:
            new_x, new_y = cell
            if self.inBounds(new_x, new_y) and (new_x, new_y) not in self.uncovered:
                heappush(self.queue, (priority, (action, new_x, new_y)))
                if action == "UNCOVER":
                    self.uncovered.add((new_x, new_y))
                elif action == "FLAG":
                    self.bombs.add((new_x, new_y))

    def inBounds(self, x, y):
        return (0 <= x < self.row_dimension and
                0 <= y < self.col_dimension)

    def checkBombs(self, directions):

        bombs = []

        for cell in directions:
            new_x, new_y = cell
            if self.inBounds(new_x, new_y) and (new_x, new_y) not in self.uncovered:
                bombs.append((new_x, new_y))

        return bombs

    def getAdjacentCells(self, x, y):
        directions = [(-1, -1), (-1, 0), (-1, 1),
                      (0, -1), (0, 1),
                      (1, -1), (1, 0), (1, 1)]

        adj_cells = []

        for dx, dy in directions:
            new_x, new_y = x + dx, y + dy
            adj_cells.append((new_x, new_y))

        return adj_cells

    def getAction(self, number: int) -> "Action Object":

        # update board
        self.board[self.x][self.y] = number
        print(f'CURRENT CELL: {self.x, self.y}')
        for row in self.board:
            print(row)

        print(f'QUEUE: {self.queue}')

        # zero queue
        if number == 0:
            cells = self.getAdjacentCells(self.x, self.y)

            self.addActionsToQueue(self.x, self.y, 0, "UNCOVER", cells)

        # n queue
        elif number > 0:
            directions = self.getAdjacentCells(self.x, self.y)

            potential_bombs = self.checkBombs(directions)
            if len(potential_bombs) == number:
                self.addActionsToQueue(self.x, self.y, number, "FLAG", potential_bombs)

        elif number < 0:
            directions = self.getAdjacentCells(self.x, self.y)


        # do the priority action
        if self.queue:
            priority, cell = heappop(self.queue)
            self.x = cell[1]
            self.y = cell[2]

            print(f'CELL: {cell}')

            if cell[0] == "UNCOVER":
                return Action(AI.Action.UNCOVER, cell[1], cell[2])
            elif cell[0] == "FLAG":
                return Action(AI.Action.FLAG, cell[1], cell[2])

        # no actions left
        return Action(AI.Action.LEAVE)
