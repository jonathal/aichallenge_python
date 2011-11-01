#!/usr/bin/env python
import logging
import sys
from optparse import OptionParser
import logging

turn_number = 0
bot_version = 'v0.1'

SUBMISSION=False

class LogFilter(logging.Filter):
  """
  This is a filter that injects stuff like TurnNumber into the log
  """
  def filter(self,record):
    global turn_number,bot_version
    record.turn_number = turn_number
    record.version = bot_version
    return True

from ants import *

# define a class with a do_turn method
# the Ants.run method will parse and update bot input
# it will also run the do_turn method for us
class MyBot:
    def __init__(self):
        pass
    
    # do_setup is run once at the start of the game
    # after the bot has received the game settings
    # the ants class is created and setup by the Ants.run method
    def do_setup(self, ants):
        # initialize data structures after learning the game settings
        self.unseen = []
        for row in range(ants.rows):
            for col in range(ants.cols):
                self.unseen.append((row, col))
                
        self.hills = []
    
    # do turn is run once per turn
    # the ants class has the game state and is updated by the Ants.run method
    # it also has several helper methods to use
    def do_turn(self, ants):
        global turn_number
        turn_number = turn_number+1
        logging.debug("Starting Turn")
        # track all moves, prevent collisions
        orders = {}
        def do_move_direction(loc, direction):
            new_loc = ants.destination(loc, direction)
            if (ants.unoccupied(new_loc) and new_loc not in orders):
                ants.issue_order((loc, direction))
                logging.debug("Going to %s, direction %s" % (loc, direction))
                orders[new_loc] = loc
                return True
            else:
                return False
            
        targets = {}
        def do_move_location(loc, dest):
            #directions = ants.direction(loc, dest)
            path = ants.aStar(loc, dest)
            logging.debug("Path to %s from %s: %s" % (dest, loc, path))
            if not path:
                return False
            location = path[0]
            direction = ants.direction(loc, location)[0]
            if do_move_direction(loc, direction):
                targets[dest] = loc
                return True
            return False
        
        for hill_loc in ants.my_hills():
            orders[hill_loc] = None
            
        # find close food
        logging.debug("Finding food")
        ant_dist = []
        for food_loc in ants.food():
            for ant_loc in ants.my_ants():
                dist = ants.distance(ant_loc, food_loc)
                ant_dist.append((dist, ant_loc, food_loc))
        ant_dist.sort()
        for dist, ant_loc, food_loc in ant_dist:
            if food_loc not in targets and ant_loc not in targets.values():
                do_move_location(ant_loc, food_loc)
                
        
        # unblock own hill
        for hill_loc in ants.my_hills():
            if hill_loc in ants.my_ants() and hill_loc not in orders.values():
                for direction in ('s','e','w','n'):
                    if do_move_direction(hill_loc, direction):
                        break
                    
        logging.debug("Exploring")
        # explore unseen areas
        for loc in self.unseen[:]:
            if ants.visible(loc):
                self.unseen.remove(loc)
        for ant_loc in ants.my_ants():
            if ant_loc not in orders.values():
                unseen_dist = []
                for unseen_loc in self.unseen:
                    dist = ants.distance(ant_loc, unseen_loc)
                    unseen_dist.append((dist, unseen_loc))
                unseen_dist.sort()
                for dist, unseen_loc in unseen_dist:
                    if do_move_location(ant_loc, unseen_loc):
                        break
                    
        logging.debug("Attacking hills")
        # attack hills
        for hill_loc, hill_owner in ants.enemy_hills():
            if hill_loc not in self.hills:
                self.hills.append(hill_loc)        
        ant_dist = []
        for hill_loc in self.hills:
            for ant_loc in ants.my_ants():
                if ant_loc not in orders.values():
                    dist = ants.distance(ant_loc, hill_loc)
                    ant_dist.append((dist, ant_loc))
        ant_dist.sort()
        for dist, ant_loc in ant_dist:
            do_move_location(ant_loc, hill_loc)
            
        logging.debug("End of turn")
            
if __name__ == '__main__':
    # psyco will speed up python a little, but is not needed
    try:
        import psyco
        psyco.full()
    except ImportError:
        pass
    
    if not SUBMISSION:
        logging.basicConfig(filename='bot.log',level=logging.DEBUG,format="%(asctime)s-%(version)s- Turn:%(turn_number)s-%(funcName)25s() - %(message)s")
    else:
        logging.basicConfig(level=logging.ERROR)
        
    log_filter  = LogFilter()
    logging.getLogger().addFilter(log_filter)
    try:
        # if run is passed a class with a do_turn method, it will do the work
        # this is not needed, in which case you will need to write your own
        # parsing function and your own game state class
        Ants.run(MyBot())
    except KeyboardInterrupt:
        print('ctrl-c, leaving ...')
