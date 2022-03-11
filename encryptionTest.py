import math

def shannonEntropy(seen,length):
    '''
    Performs Shannon entropy analysis on given data
    '''
    entropy = 0
    
    #Entropy formula
    for x in range(0, 256):            
        p_x = float(seen[chr(x)]) / length
        if p_x > 0:
            entropy += - p_x*math.log(p_x, 2)
    
    #Return entropy value for given data
    return math.ceil(entropy)

def entropyEncryptionTest(memory):
    '''
    Performs encryption test on provided data. It grabs the characters of the given data and then it calculates
    the data's entropy and returns that value as a result.
    '''
   
    #Create a dictionary with all possible characters and values set to 0
    seen = dict(((chr(x), 0) for x in range(0, 256)))
    
    #Amount of characters in the page
    count = 0
    
    #Count all the characters and count the apparition of each character in the data to use in entropy formula.
    for line in memory:
        for x in line:
            for x in line:
                seen[chr(x)] += 1
                count += 1

    #Perform entropy analysis on the data and return results
    return shannonEntropy(seen,count)