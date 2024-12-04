from AI import AI
from Action import Action
from heapq import heappush, heappop
import random


class MyAI(AI):
    ACTION_UNCOVER = "UNCOVER"
    ACTION_FLAG = "FLAG"

    def __init__(self, rowDimension, colDimension, totalMines, startX, startY):
        self.row_dimension = rowDimension
        self.col_dimension = colDimension
        self.total_mines = totalMines
        self.total_cells = rowDimension * colDimension
        self.x = startX  # Column index
        self.y = startY  # Row index

        # Initialize the board with covered cells
        self.board = [["?" for _ in range(self.col_dimension)] for _ in range(self.row_dimension)]
        self.queue = []
        self.deferred_queue = []
        self.uncovered = set()
        self.bombs = set()
        self.covered = dict()
        self.uncovered_count = 0
        self.processed_patterns = set()

    def getAdjacentCells(self, col, row):
        """gets surrounding cells"""
        directions = [(-1, -1), (-1, 0), (-1, 1),
                      (0, -1), (0, 1),
                      (1, -1), (1, 0), (1, 1)]
        return [(col + dc, row + dr) for dc, dr in directions if self.inBounds(col + dc, row + dr)]

    def inBounds(self, x, y):
        """bounds check"""
        return 0 <= x < self.col_dimension and 0 <= y < self.row_dimension

    def checkCells(self, directions, number):
        """returns uncovered cells and known bomb cells"""
        adj_bombs = []
        adj_covered = []

        for cell in directions:
            new_col, new_row = cell
            if self.inBounds(new_col, new_row):
                if (new_col, new_row) in self.bombs:
                    adj_bombs.append((new_col, new_row))
                elif (new_col, new_row) not in self.uncovered:
                    adj_covered.append((new_col, new_row))

        # updating cells probability
        if adj_covered:
            probability_of_mine = (number - len(adj_bombs)) / len(adj_covered)

            for cell in adj_covered:
                if cell not in self.covered:
                    self.covered[cell] = (probability_of_mine, 1)
                else:
                    current_prob, count = self.covered[cell]
                    new_prob = (current_prob * count + probability_of_mine) / (count + 1)
                    self.covered[cell] = (new_prob, count + 1)

        return adj_covered, adj_bombs

    def zero_action(self):
        """adds to queue to uncover all adjacent cells if n is 0"""
        cells = self.getAdjacentCells(self.x, self.y)
        self.addActionsToQueue(0, self.ACTION_UNCOVER, cells)

    def hint_action(self, number, col, row, deferred=False):
        """adds to queue when n > 0, flags cells if known bombs + cells = num or uncovers cells if known bombs = num"""
        directions = self.getAdjacentCells(col, row)
        uncovered, bombs = self.checkCells(directions, number)

        if len(uncovered) + len(bombs) == number:
            self.addActionsToQueue(number, self.ACTION_FLAG, uncovered)
        elif len(bombs) == number:
            self.addActionsToQueue(number, self.ACTION_UNCOVER, uncovered)
        else:
            if not deferred:
                heappush(self.deferred_queue, (number, (col, row)))

    def bomb_action(self, number, col, row):
        """adds to deferred queue when n is -1, adds adjacent cells"""
        directions = self.getAdjacentCells(col, row)
        for cell in directions:
            new_col, new_row = cell
            if (new_col, new_row) in self.uncovered:
                # Get the number from the board for the uncovered cell
                cell_number = self.board[new_row][new_col]
                if isinstance(cell_number, int):
                    heappush(self.deferred_queue, (cell_number, (new_col, new_row)))

    def action_decider(self, number, col, row, deferred=False):
        """do action based on n"""
        if number == 0:
            self.zero_action()
        elif number > 0:
            self.hint_action(number, col, row, deferred)
        else:
            self.bomb_action(number, col, row)

    def addActionsToQueue(self, priority, action, directions):
        """bounds check + add action to queue"""
        for cell in directions:
            new_col, new_row = cell
            if self.inBounds(new_col, new_row) and (new_col, new_row) not in self.uncovered:
                heappush(self.queue, (priority, (action, new_col, new_row)))
                if action == self.ACTION_UNCOVER:
                    self.uncovered.add((new_col, new_row))
                elif action == self.ACTION_FLAG:
                    self.bombs.add((new_col, new_row))

    def runQueue(self):
        """completes action in queue based on priority of n (0 has highest)"""
        if self.queue:
            priority, (action, col, row) = heappop(self.queue)
            if action == self.ACTION_UNCOVER:
                self.uncovered_count += 1
            self.x, self.y = col, row
            return Action(AI.Action[action], col, row)
        return None

    def processDeferredQueue(self):
        """Revisits deferred cells with potential new information."""
        revisited = []

        while self.deferred_queue:
            deferred_number, (col, row) = heappop(self.deferred_queue)
            directions = self.getAdjacentCells(col, row)
            if any((c, r) in self.uncovered for c, r in directions):
                self.action_decider(deferred_number, col, row, True)
                action = self.runQueue()
                if action:
                    return action
            else:
                revisited.append((deferred_number, (col, row)))

        for item in revisited:
            heappush(self.deferred_queue, item)

        return None

    def exploreUnexploredCells(self):
        """finds all unexplored cells and adds to deferred queue"""
        unexplored_cells = [(col, row) for row in range(self.row_dimension)
                            for col in range(self.col_dimension) if self.board[row][col] == "?"]

        # adds hints near unexplored cells to deferred queue
        for col, row in unexplored_cells:
            adj_cells = self.getAdjacentCells(col, row)
            if any((adj_col, adj_row) in self.uncovered for adj_col, adj_row in adj_cells):
                for adj_col, adj_row in adj_cells:
                    if (adj_col, adj_row) in self.uncovered:
                        cell_number = self.board[adj_row][adj_col]
                        if isinstance(cell_number, int):
                            heappush(self.deferred_queue, (cell_number, (adj_col, adj_row)))

    def educated_guess(self):
        to_delete = []

        for coord in self.covered:
            if coord in self.uncovered or coord in self.bombs:
                to_delete.append(coord)

        for coord in to_delete:
            del self.covered[coord]

        if self.covered:
            guess = min(self.covered, key=self.covered.get)
            return guess

    def one_one_and_variations(self):
        for row in range(self.row_dimension):
            for col in range(self.col_dimension):
                if self.board[row][col] == 1:
                    # Get adjacent cells
                    adj_cells = self.getAdjacentCells(col, row)
                    unexplored = [cell for cell in adj_cells if cell not in self.uncovered]

                    # Skip if the pattern for this cell has already been processed
                    if len(unexplored) == 2:
                        pattern_id = (row, col, tuple(sorted(unexplored)))
                        if pattern_id in self.processed_patterns:
                            continue

                        # Mark pattern as processed
                        self.processed_patterns.add(pattern_id)

                        for adj_col, adj_row in adj_cells:
                            hint_number = self.board[adj_row][adj_col]
                            other_adj_cells = self.getAdjacentCells(adj_col, adj_row)
                            other_unexplored = [cell for cell in other_adj_cells if cell not in self.uncovered]

                            if (len(other_unexplored) >= 3
                                    and len(set(other_unexplored).intersection(set(unexplored))) == 2):
                                if hint_number == 1:
                                    safe = set(other_unexplored).difference(set(unexplored))

                                    self.addActionsToQueue(
                                        priority=1, action=self.ACTION_UNCOVER, directions=safe
                                    )
                                else:
                                    if hint_number != "?":
                                        bombs = set(other_unexplored).difference(set(unexplored))
                                        if len(bombs) == hint_number - 1:
                                            self.addActionsToQueue(
                                                priority=1, action=self.ACTION_FLAG, directions=bombs
                                            )

    def getAction(self, number: int) -> "Action Object":
        # World Complete Check
        if self.total_cells - self.total_mines == self.uncovered_count:
            return Action(AI.Action.LEAVE)

        # Update board with the current cell's number
        self.board[self.y][self.x] = number

        # Decide next actions based on the number hint
        self.action_decider(number, self.x, self.y)

        # Run actions from the main queue
        action = self.runQueue()
        if action:
            return action

        # If main queue is empty, try deferred actions
        action = self.processDeferredQueue()
        if action:
            return action

        self.exploreUnexploredCells()
        action = self.processDeferredQueue()
        if action:
            return action

        self.one_one_and_variations()
        action = self.runQueue()
        if action:
            return action

        # Explore remaining cells if no actions are queued
        if len(self.bombs) < self.total_mines:
            min_guess = self.educated_guess()
            if min_guess:
                del self.covered[min_guess]
                self.addActionsToQueue(0, self.ACTION_UNCOVER, [min_guess])

        # uncover rest of cells if no mines
        else:
            unexplored_cells = [(col, row) for row in range(self.row_dimension)
                                for col in range(self.col_dimension) if self.board[row][col] == "?"]

            for col, row in unexplored_cells:
                heappush(self.queue, (0, (self.ACTION_UNCOVER, col, row)))

        action = self.runQueue()
        if action:
            return action

        return Action(AI.Action.LEAVE)