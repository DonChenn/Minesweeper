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
        self.board = [["?" for _ in range(self.col_dimension)] for _ in range(self.row_dimension)]
        self.queue = []
        self.deferred_queue = []
        self.uncovered = set()
        self.bombs = set()

    def addActionsToQueue(self, priority, action, directions):
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

    # finds all uncovered adjacent cells
    def checkUncovered(self, directions):
        uncovered = []
        for cell in directions:
            new_x, new_y = cell
            if self.inBounds(new_x, new_y) and (new_x, new_y) not in self.uncovered:
                uncovered.append((new_x, new_y))
        return uncovered

    # finds all bombs and remaining spaces
    def checkBombs(self, directions):
        adj_bombs = []
        potential_safes = []
        for cell in directions:
            new_x, new_y = cell
            if self.inBounds(new_x, new_y) and (new_x, new_y) in self.bombs:
                adj_bombs.append((new_x, new_y))
            else:
                potential_safes.append((new_x, new_y))
        return potential_safes, adj_bombs

    # returns list of tuples (x, y) of adjacent cells
    def getAdjacentCells(self, x, y):
        directions = [(-1, -1), (-1, 0), (-1, 1),
                      (0, -1), (0, 1),
                      (1, -1), (1, 0), (1, 1)]
        adj_cells = []
        for dx, dy in directions:
            new_x, new_y = x + dx, y + dy
            if self.inBounds(new_x, new_y):
                adj_cells.append((new_x, new_y))
        return adj_cells

    # add queue to uncover all cells around 0
    def zero_action(self):
        cells = self.getAdjacentCells(self.x, self.y)
        self.addActionsToQueue(0, "UNCOVER", cells)

    # logic for current cell number and finding bombs around it
    def hint_action(self, number, x, y, deferred=False):
        directions = self.getAdjacentCells(x, y)
        potential_safes, bombs = self.checkBombs(directions)
        uncovered_cells = self.checkUncovered(directions)

        # known bombs to uncover
        if len(bombs) == number:
            self.addActionsToQueue(number, "UNCOVER", potential_safes)
        # known bombs + spaces to flag
        elif len(uncovered_cells) + len(bombs) == number:
            self.addActionsToQueue(number, "FLAG", uncovered_cells)
        # come back to it for later
        else:
            if not deferred:
                heappush(self.deferred_queue, (number, (x, y)))

    # when on bomb cell, add adjacent cells to come back to
    def bomb_action(self, number, x, y):
        directions = self.getAdjacentCells(x, y)
        for cell in directions:
            new_x, new_y = cell
            if (number, (new_x, new_y)) not in self.deferred_queue and (new_x, new_y) in self.uncovered:
                print(f'Added to heap deferred {x, y, number, (new_x, new_y)}')
                heappush(self.deferred_queue, (number, (new_x, new_y)))

    def runQueue(self, queue):
        if queue:
            priority, cell = heappop(queue)
            # Update x, y to next cell
            self.x, self.y = cell[1], cell[2]

            # Execute action and return it
            if cell[0] == "UNCOVER":
                print(f"UNCOVERED: {cell[1], cell[2]}")
                return Action(AI.Action.UNCOVER, cell[1], cell[2])
            elif cell[0] == "FLAG":
                print(f"FLAGGED: {cell[1], cell[2]}")
                return Action(AI.Action.FLAG, cell[1], cell[2])
        return None

    def getAction(self, number: int) -> "Action Object":
        # Update the board
        self.board[self.x][self.y] = number
        print(f'CURRENT CELL: {self.x, self.y}')
        print(f'NUMBER: {number}')
        for i, row in enumerate(self.board):
            print(i, row)
        print(f'QUEUE: {self.queue}')
        print(f'DEFERRED QUEUE: {self.deferred_queue}')
        print()

        # Determine actions based on the number
        if number == 0:
            self.zero_action()
        elif number > 0:
            self.hint_action(number, self.x, self.y)
        else:
            self.bomb_action(number, self.x, self.y)

        action = self.runQueue(self.queue)
        if action:
            return action

        # Process queues
        for revisit_cells in self.deferred_queue:
            # Process the deferred queue
            deferred_number, (x, y) = heappop(self.deferred_queue)
            self.x, self.y = x, y
            self.hint_action(deferred_number, x, y, True)

        action = self.runQueue(self.queue)
        if action:
            return action

        # No actions left
        return Action(AI.Action.LEAVE)
