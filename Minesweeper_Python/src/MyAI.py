from AI import AI
from Action import Action
from heapq import heappush, heappop


class MyAI(AI):
    ACTION_UNCOVER = "UNCOVER"
    ACTION_FLAG = "FLAG"

    def __init__(self, rowDimension, colDimension, totalMines, startX, startY):
        self.row_dimension = rowDimension
        self.col_dimension = colDimension
        self.total_mines = totalMines
        self.x = startX  # Column index
        self.y = startY  # Row index

        # Initialize the board with covered cells
        self.board = [["?" for _ in range(self.col_dimension)] for _ in range(self.row_dimension)]
        self.queue = []
        self.deferred_queue = []
        self.uncovered = set()
        self.bombs = set()

    def getAdjacentCells(self, col, row):
        directions = [(-1, -1), (-1, 0), (-1, 1),
                      (0, -1), (0, 1),
                      (1, -1), (1, 0), (1, 1)]
        return [(col + dc, row + dr) for dc, dr in directions if self.inBounds(col + dc, row + dr)]

    def inBounds(self, x, y):
        return 0 <= x < self.col_dimension and 0 <= y < self.row_dimension

    def checkCells(self, directions):
        adj_bombs = []
        uncovered = []

        for cell in directions:
            new_col, new_row = cell
            if self.inBounds(new_col, new_row):
                if (new_col, new_row) in self.bombs:
                    adj_bombs.append((new_col, new_row))
                elif (new_col, new_row) not in self.uncovered:
                    uncovered.append((new_col, new_row))  # Collect uncovered spaces
        return uncovered, adj_bombs

    def zero_action(self):
        cells = self.getAdjacentCells(self.x, self.y)
        self.addActionsToQueue(0, self.ACTION_UNCOVER, cells)

    def hint_action(self, number, col, row, deferred=False):
        directions = self.getAdjacentCells(col, row)
        uncovered, bombs = self.checkCells(directions)

        if len(uncovered) + len(bombs) == number:
            self.addActionsToQueue(number, self.ACTION_FLAG, uncovered)
        elif len(bombs) == number:
            self.addActionsToQueue(number, self.ACTION_UNCOVER, uncovered)
        else:
            if not deferred:
                heappush(self.deferred_queue, (number, (col, row)))

    def bomb_action(self, number, col, row):
        directions = self.getAdjacentCells(col, row)
        for cell in directions:
            new_col, new_row = cell
            if (new_col, new_row) in self.uncovered:
                # Get the number from the board for the uncovered cell
                cell_number = self.board[new_row][new_col]
                if isinstance(cell_number, int):
                    heappush(self.deferred_queue, (cell_number, (new_col, new_row)))
                else:
                    # TODO: wtf is going on
                    # print(f"Warning: Invalid cell number found at ({new_col}, {new_row}): {cell_number}")
                    pass

    def action_decider(self, number, col, row, deferred=False):
        """Determine actions based on the number indicating adjacent bombs."""
        if number == 0:
            self.zero_action()
        elif number > 0:
            self.hint_action(number, col, row, deferred)
        else:
            self.bomb_action(number, col, row)

    def addActionsToQueue(self, priority, action, directions):
        for cell in directions:
            new_col, new_row = cell  # new_col is x, new_row is y
            if self.inBounds(new_col, new_row) and (new_col, new_row) not in self.uncovered:
                heappush(self.queue, (priority, (action, new_col, new_row)))
                if action == self.ACTION_UNCOVER:
                    self.uncovered.add((new_col, new_row))
                elif action == self.ACTION_FLAG:
                    self.bombs.add((new_col, new_row))

    def runQueue(self):
        while self.queue:
            priority, (action, col, row) = heappop(self.queue)
            self.x, self.y = col, row
            return Action(AI.Action[action], col, row)
        return None

    def processDeferredQueue(self):
        while self.deferred_queue:
            deferred_number, (col, row) = heappop(self.deferred_queue)
            self.action_decider(deferred_number, col, row, True)
            action = self.runQueue()
            if action:
                return action
        return None

    def exploreUnexploredCells(self):
        unexplored_cells = [(col, row) for row in range(self.row_dimension)
                            for col in range(self.col_dimension) if self.board[row][col] == "?"]

        for col, row in unexplored_cells:
            adj_cells = self.getAdjacentCells(col, row)
            for adj_col, adj_row in adj_cells:
                if (adj_col, adj_row) in self.uncovered:
                    cell_number = self.board[adj_row][adj_col]
                    if isinstance(cell_number, int):
                        heappush(self.deferred_queue, (cell_number, (adj_col, adj_row)))

    def getAction(self, number: int) -> "Action Object":
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

        # Explore remaining cells if no actions are queued
        if len(self.bombs) < self.total_mines:
            self.exploreUnexploredCells()
            action = self.processDeferredQueue()
            if action:
                return action

        # If all options are exhausted, leave the game
        return Action(AI.Action.LEAVE)

