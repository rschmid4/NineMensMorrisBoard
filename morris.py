#!/usr/bin/env python
# Modified code from: https://github.com/asrivat1/DeepLearningVideoGames and http://programarcadegames.com/index.php?chapter=introduction_to_graphics
# which is in turn Modified from http://www.pygame.org/project-Very+simple+Pong+game-816-.html

import numpy as np
import pygame
from threading import Thread
from time import sleep

GUI = True
BACKGROUND = (90, 90, 90) # gray
PLAYER1 = (240, 240, 240) # almost white
PLAYER2 = (10, 10, 10) # almost black
LINES = (255, 255, 255) # white

TAKE_PIECE_REWARD = 0.2
WIN_REWARD = 1

# Lookup table for what fields are above others, nicer and more readable than if's
above_arr = [-1, -1, -1,    -1, 1, -1,    -1, 4, -1,    0, 3, 6,    8, 5, 2,    11, -1, 12,    10, 16, 13,    9, 19, 14]
# Lookup table for coordinates
coord_arr = np.array([(1,1), (7,1), (13,1),    (3,3), (7,3), (11,3),    (5,5), (7,5), (9,5),    (1,7), (3,7), (5,7),
                    (9,7), (11,7), (13,7),    (5,9), (7,9), (9,9),    (3,11), (7,11), (11,11),    (1,13), (7,13), (13,13)], dtype=[('x', 'i4'),('y', 'i4')])

def indexAbove(i):
    return above_arr[i]
def indexBelow(i):
    try:
        return above_arr.index(i)
    except ValueError:
        return -1
def indexLeft(i):
    if i % 3 == 0:
        return -1
    else:
        return i-1
def indexRight(i):
    if i % 3 == 2:
        return -1
    else:
        return i+1
def getCoords(i):
    return [coord_arr['x'][i], coord_arr['y'][i]]
        
class GameState:
    def isInMill(self, i):
        if i == -1:
            return False
        else:
            return      (self.safeGet(indexAbove(i)) == self.safeGet(indexAbove(indexAbove(i))) == self.board[i] != 2) or \
                        (self.safeGet(indexAbove(i)) == self.safeGet(indexBelow(i)) == self.board[i] != 2) or \
                        (self.safeGet(indexBelow(i)) == self.safeGet(indexBelow(indexBelow(i))) == self.board[i] != 2) or \
                        (self.safeGet(indexLeft(i)) == self.safeGet(indexLeft(indexLeft(i))) == self.board[i] != 2)  or \
                        (self.safeGet(indexLeft(i)) == self.safeGet(indexRight(i)) == self.board[i] != 2)  or \
                        (self.safeGet(indexRight(i)) == self.safeGet(indexRight(indexRight(i))) == self.board[i] != 2)
    def safeGet(self, i):
        if i < 0 or i >= len(self.board):
            return 2
        try:
            return self.board[i]
        except IndexError:
            return 2
    
    def reset(self):
        self.board = np.zeros(24)
        self.opponent_num_pieces = 9
        self.player_num_pieces = 9
        
    def __init__(self):
        self.reset()
        if GUI:
            self.init_gui()
        
    def init_gui(self):
        # Create thread to update gui
        thread = Thread(target = self.update_gui)
        thread.start()
        
    def update_gui(self):
        done = False
        # Init pygame
        pygame.init()
        self.screen = pygame.display.set_mode((700, 700))
        pygame.display.set_caption("Nine Men's Morris")
        self.screen.fill(BACKGROUND)
        self.clock = pygame.time.Clock()
        
        while not done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    done = True
            
            self.screen.fill(BACKGROUND)
            # Upper horizontal lines
            self.draw_line([1, 1], [13, 1])
            self.draw_line([3, 3], [11, 3])
            self.draw_line([5, 5], [9, 5])
            # Lower horizontal lines
            self.draw_line([5, 9], [9, 9])
            self.draw_line([3, 11], [11, 11])
            self.draw_line([1, 13], [13, 13])
            # Middle horizontal lines
            self.draw_line([1, 7], [5, 7])
            self.draw_line([9, 7], [13, 7])
            # Draw board
            for i in range(len(self.board)):
                self.draw_piece(getCoords(i), self.board[i])
            
            # Update display
            pygame.display.flip()
            # Update GUI with 60 FPS
            self.clock.tick(60)
        pygame.quit()
    def draw_line(self, start, end):
        pygame.draw.line(self.screen, LINES, [x*50 for x in start], [x*50 for x in end], 10)
        pygame.draw.line(self.screen, LINES, [x*50 for x in start[::-1]], [x*50 for x in end[::-1]], 10)
    def draw_piece(self, pos, value):
        if value != 0:
            color = None
            if value > 0:
                color = PLAYER1
            else:
                color = PLAYER2
            pygame.draw.circle(self.screen, color, [x*50 for x in pos], 30)
            pygame.draw.circle(self.screen, [x-10 for x in color], [x*50 for x in pos], 30, 5)
    
    def frame_step(self, input_vect, execute_opponent=True, color=1):
        if color == 1:
            num_pieces = self.player_num_pieces
        else:
            num_pieces = self.opponent_num_pieces
        
        enemy_reward = 0
        reward = 0
        terminal = False
        
        start = -1
        dest = -1
        
        # -------------------- FIGURE OUT MOVE --------------------
        if num_pieces > 0: # Set down piece
            print('can set down a piece') # DEBUG
            x = np.argsort(input_vect) # list of indices, sorted 0 -> max
            i = -1
            while self.board[x[i]] != 0:
                i-=1
            dest = x[i]
            
            if color == 1:
                self.player_num_pieces -= 1
            else:
                self.opponent_num_pieces -= 1
        else: # Move piece
            # Find best moves according to input_vect
            if len(self.board[self.board == color]) == 3: # Can jump
                print('can jump') # DEBUG
                x = np.argsort(input_vect)
                # start = worst own field
                i = 0
                while self.board[x[i]] != color:
                    i+=1
                start = x[i]
                # dest = best free field
                i = -1
                while self.board[x[i]] != 0:
                    i-=1
                dest = x[i]
            else: # Can't jump
                print('can\'t jump') # DEBUG
                # Functions to get neighbouring positions
                fs = [indexAbove, indexBelow, indexLeft, indexRight]
                # Map to hold scores
                map_type = [('start', 'i4'),('dest', 'i4'), ('score', 'f4')]
                map = np.array([], dtype=map_type)
                # Loop to check all possible moves
                for s in range(0,24):
                    if self.board[s] == color:
                        for f in fs:
                            d = f(s)
                            if d != -1 and self.board[d] == 0:
                                score = input_vect[d] - input_vect[s]
                                map = np.append(map, np.array((s,d,score), dtype=map_type))
                # Find best move
                best = np.argmax(map['score'])
                start = map['start'][best]
                dest = map['dest'][best]
        
        # -------------------- EXECUTE MOVE --------------------
        if dest == -1: # Stuck
            print('is stuck') # DEBUG
            reward = -WIN_REWARD
            terminal = True
            self.reset()
        else:
            # Execute
            if start != -1: # If we'Re still setting up
                self.board[start] = 0
            self.board[dest] = color
            if GUI: # sleep after move
                sleep(1)
            
            # If mill closed, remove best opponent piece
            if self.isInMill(dest):
                print('closed mill') # DEBUG
                x = np.argsort(input_vect)
                # best = best enemy field not in mill
                i = -1
                while self.board[x[i]] != -color or self.isInMill(x[i]):
                    i-=1
                best = x[i]
                # Remove best piece
                self.board[best] = 0
                reward = TAKE_PIECE_REWARD
                if GUI: # sleep after capture
                    sleep(1)
                
                # Check if gameOver
                if len(self.board[self.board == -color]) < 3:
                    terminal = True
                    reward = WIN_REWARD
                    self.reset()
        
        if execute_opponent:
            self.board, enemy_reward, terminal = self.frame_step(np.random.rand(24), execute_opponent=False, color=-1)

        return self.board, reward - enemy_reward, terminal