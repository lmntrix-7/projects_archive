import math
from games4e import *

GS = namedtuple('GS', 'state, utility, move, count')  # Namedtuple GS containing state, utility, move played, and count of move

def is_legal(tapping_hand, tapped_hand, state):
  # Return a list   
    if tapping_hand == tapped_hand: return False # must tap a different hand
    if state[tapping_hand] == 0: return False # tapping hand cannot be busted
    if state[tapped_hand] == 0 and not {tapping_hand, tapped_hand} == {'A', 'B'}: return False # split only allowed for own hands
    if state[tapped_hand] == 0 and state[tapping_hand] < 4: return False # split only allowed for hands with >=4 fingers
    return True

def actions(tup, player):   # gives all possible actions for the player
 # Return a list of the allowable moves at this point
    f_moves = []            # stores all the possible legal moves for the player
    
    if player == 'P1':                 # checks whether player is P1 and gives the possible moves for P1
        if (tup.state['A'] == 0 or tup.state['B'] == 0):
            pos_moves = ['AB', 'AC', 'AD', 'BA', 'BC', 'BD']      # possible moves if splitting is an option for the bot
        else:
            pos_moves = ['AC', 'AD', 'BC', 'BD']                  # makes the bot more attacking when splitting is not an option
    
    if player == 'P2':                # checks whether player is P2 and gives the possible moves for P2
        pos_moves = ['CA', 'CB', 'CD', 'DA', 'DB', 'DC']
        
    
    for x in pos_moves:               # runs a loop to get only the moves which are legal and returns a list of possible mmoves
        if is_legal(x[0], x[1], tup.state):
            f_moves.append(x)
    
    return f_moves

def to_move(player):                 # function to toggle player
  # Return the player whose move it is in the current state
    if player == 'P1':
        player = 'P2'
    else:
        player = 'P1'
        
    return player

def terminal_test(tup, player):
  # Return True if this is a final state for the game
    return (tup.state.get('C') == 0 and tup.state.get('D') == 0) or (tup.state.get('A') == 0 and tup.state.get('B') == 0) or (tup.utility == 1000)

def result(tup, move):
  # Return the state that results from making a move in the previous state  
    tapping_hand = move[0]        # gets tapping hand from the move
    tapped_hand = move[1]         # gets tapped hand from the move
    fin = tup.state.copy()

    if is_legal(tapping_hand, tapped_hand, tup.state):     # if move is legal then it changes the state and gives new state after the move is played
        
        if fin[tapped_hand] == 0:             #  used for splitting
            fin[tapped_hand] = math.floor(fin[tapping_hand] / 2)      # gives floor value of tapping hand
            fin[tapping_hand] = math.ceil(fin[tapping_hand] / 2)      # gives ceiling value of tapping hand
        
        elif fin[tapped_hand] + fin[tapping_hand] <= 5:               # adds the value of the tapping hand to the value in the tapped hand
            fin[tapped_hand] += fin[tapping_hand]
                
        else:
            fin[tapped_hand] = 0         # if tapped hand value is more than 5 then hand is busted
            
    else:
        return tup                       # if move is not legal it return the original state and does not cause any effect
    
    #player = to_move(player)
    
    tup = GS(state = fin, utility = compute_utility(fin, tup.move), move = move, count = tup.count + 1)  

    return tup
    
def utility(tup, player):     # utility function
  #  Returns a utility value to the player; positive value for win, negative value for loss, 0 otherwise
    tup = tup(state = tup.state, utility = tup.utility, move = tup.move, count = tup.count)
    
    if player == 'P1':
        return tup.utility
    
    elif player == 'P2':
        return -tup.utility
    
    else:
        return 0

def eval_fn(tup, player):      # evaluation function
  #  Returns an evaluation score to the player; positive value for win, negative value for loss, 0 otherwise    
    if player == 'P1':
        return tup.utility
    
    elif player == 'P2':
        return -tup.utility

    else:
        return 0
    
def compute_utility(state, move):
 # Computes the utility of a particular state based on the number of fingers and returns the score based on a formula   
    util = 0      # utility value
    bf = 0        # balancing factor
    rf = 0        # risk factor
    opp_fing = 0  # opponents fingers
    
    if ((state['C'] == 0) & (state['D'] == 0)):   # if opponents hands are busted gives very high utility value
        util = 1000
    
    if ((state['C'] == 0) or (state['D'] == 0)):   # if one of the opponents hands are busted gives medium utility value
        util = 100
        
    opp_fing = state['C'] + state['D']     # calculates the number of fingers in the opponents hands
    
    bf = (state['A'] + state['B']) - (state['C'] + state['D'])    # factor to see a balanced distribution of fingers in the state
    
    rf = state['A'] + state['B']     # factor to penalize a move that increases the risk for P1
    
    score = (util) + (3 * opp_fing) + (1 * bf) - (1.5 * rf)    # weighted score based on the multiple factors
    
    return score

def ab_cutoff_search(tup, d = 20, eval_fn = eval_fn, cutoff_test = None):   # has depth = 20
    player = 'P1'    # setting player as P1 when the function is called
    
    # Functions used by alpha_beta
    def max_value(tup, alpha, beta, player, depth):

        if cutoff_test(tup, player, depth):
            return eval_fn(tup, player)
        v = -np.inf
        player = to_move(player)
        for a in actions(tup, player):
            tup = GS(state = tup.state, utility = tup.utility, move = a, count = tup.count)
            v = max(v, min_value(result(tup, a), alpha, beta, player, depth + 1))
            if v >= beta:
                return v
            alpha = max(alpha, v)
        return v

    def min_value(tup, alpha, beta, player, depth):
        if cutoff_test(tup, player, depth):
            return eval_fn(tup, player)
        v = np.inf
        player = to_move(player)
        for a in actions(tup, player):
            tup = GS(state = tup.state, utility = tup.utility, move = a, count = tup.count)
            v = min(v, max_value(result(tup, a), alpha, beta, player, depth + 1))
            if v <= alpha:
                return v
            beta = min(beta, v)
        return v

    # Body of alpha_beta_search:
    # The default test cuts off at depth d or at a terminal state
    cutoff_test = (cutoff_test or (lambda tup, player, depth: depth > d or terminal_test(tup, player)))
    eval_fn = eval_fn or (lambda tup, player: utility(tup, player))
    best_score = -np.inf
    beta = np.inf
    best_action = None
    
    for a in actions(tup, player):
        tup = GS(state = tup.state, utility = 0, move = a, count = 0)
        v = min_value(result(tup, a), best_score, beta, player, 1)
        if v > best_score:
            best_score = v
            best_action = a
    return best_action

def generate_move(state_str):
    state = {'A': int(state_str[1]), 'B': int(state_str[3]), 'C': int(state_str[5]), 'D': int(state_str[7])}
    possible_moves = ['AB', 'AC', 'AD', 'BA', 'BC', 'BD']   # list of possible moves for the bot
    
    tup = GS(state = state,  utility = 0, move = '', count = 0)  # defines named tuple with state which is given, utility = 0, move and count
    best_move = ab_cutoff_search(tup)    # calls AB_Cutoff Search to produce best move
    
    if (best_move in possible_moves):    # checks whether best move is in the possible moves and returns best move
        return best_move
    
    else:                                # else returns NA
        return NA    
    
