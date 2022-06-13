'''Functions used to calculate entropy of given data'''
import math

def shannon_entropy(seen:dict, length:int) -> int:
    '''
    Performs Shannon entropy analysis on given data
    '''
    entropy = 0

    # Entropy formula
    for char in range(0, 256):
        p_x = float(seen[chr(char)]) / length
        if p_x > 0:
            entropy += - p_x*math.log(p_x, 2)

    # Return entropy value for given data
    return math.ceil(entropy)


def entropy_encryption_test(memory:bytes) -> int:
    '''
    Performs encryption test on provided data.
    It grabs the characters of the given data and then it calculates
    the data's entropy and returns that value as a result.
    '''

    # #Create a dictionary with all possible characters and values set to 0
    seen = dict(((chr(char), 0) for char in range(0, 256)))
    # Amount of characters in the page
    count = 0

    # Count all the characters and count the apparition of each character in the data to use in entropy formula.
    for char in memory:
        seen[chr(char)] = seen.get(chr(char), 0) + 1
        count += 1

    # Perform entropy analysis on the data and return results
    return shannon_entropy(seen, count)
