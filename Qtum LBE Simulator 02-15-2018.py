version = "02-15-2018"
'''
Qtum LBE Simulator (LBE = Long Block Eradicator)

Copyright (c) 2017 Jackson Belove
Beta software, use at your own risk
MIT License, free, open software for the Qtum Community

A program to use the SHA-256 hash function and algorithms from qtum mainnet
wallet software to explore retargeting, the network weight calculation and block spacing.
Runs a simulation using "steps" to replicate 16 second granularity in the PoS algorithm.
Uses SHA-265 hash and identical logic for block-by-block retargeting. Simulates wallet 
populations from 500 up, and can run for any amount of blocks.

Also may run a replay of mainnet block spacing by reading in a file containing
the block spacing and difficulty for a number of blocks. In the case of running
a replay, simulated variables are not used. The replay is used mainly to tune
parameters and logic related to calculating network weight.

Logs the peak number of steps (x 16 seconds for nActualSpacing) and the number
of blocks with 5x target spacing (>= 640 seconds or ten minutes 40 seconds).

Can be set to make multiple runs while adjusting a parameter. Set paramValue to
the parameter being adjusted in each run. For example, to do 10 runs adjusting
the target scaling starting at 1.0 with a step of 0.005 on each run, override
the targetScalingFactor at the top of the parameter loop, and assign that value
to paramValue for print/logging. Each of these conditions must be setup before the top
and at the bottom of the parameter loop. Some example outputs:

Adjusting the target scaling factor after n steps (within a block):
  Run | trgtScFactr | ave secs | >=640 blks | max secs | collisns
    0 |       1.000 |   134.53 |        146 |    1,280 |    1,278
    1 |       1.005 |   130.37 |         83 |    1,232 |    1,309
    2 |       1.010 |   131.93 |         84 |    1,040 |    1,263

Adjusting the target multiplier value (for the next block difficulty):
  Run | tgt multplr | ave secs | >=640 blks | max secs | collisns
    0 |  35,000.000 |   128.16 |          0 |      512 |       16
    1 |  37,500.000 |   112.64 |          0 |      560 |       19
    2 |  40,000.000 |   128.40 |          1 |      784 |       19

"Long block" is a block with a long spacing, > 20 minutes.

Program Summary

    set switches & parameters for simuation complexity
    if doing replay, read file for spacing and difficulty
    initialize log file
    set starting target, based on network weight
    load the wallets: uniform, random, mainnet, testnet

    parameter loop - - - - - - - - - - - - - - - - - - - - - -
   /
   |   initialize variables for a single run 
   |
   |    block loop - - - - - - - - - - - - - - - - - - - - - -
   |   /
   |   |   adjust wallet weight or number of wallets, if desired
   |   |  
   |   |    step loop - - - - - - - - - - - - - - - - - - - -
   |   |   /
   |   |   |    target scaling after XX steps, if configured
   |   |   |
   |   |   |    wallet loop - - - - - - - - - - - - - - - - -
   |   |   |   /
   |   |   |   |    if doing simulation
   |   |   |   |        if target < SHA256 hash of random variable * wallet weight
   |   |   |   |            block reward
   |   |   |   |
   |   |   |   |        else if long steps can configure for 2nd check for target < SHA256
   |   |   |   |            
   |   |   |   |        (loop through all wallets, check for collisions)
   |   |   |   |
   |   |   |   |    else doing replay
   |   |   |   |        use block spacing and difficulty from file
   |   |   |   \_
   |   |   |  
   |   |   |    adjust the target based on target multiplier and previous spacing
   |   |   |    print and log (if desired)   
   |   |   \_
   |   \_
   |
   |     print and log results for a run
   |     increment paramValue for next run
   \_

Revisions
02/14/2018 Cleaned up comments
12/18/2017 Updated Mainnet wallet weights with current numbers, 1,500 wallets, 25 million network weight
12/18/2017 Added wallet growth capability, moved network weight calculation to function
12/14/2017 Added Complexity 5: second bite of the apple (2nd SHA-256 hash check) after nn steps 
12/13/2017 Added dynamic wallet chaos mode (random n% changes in network weight)
12/05/2017 Use calculation to set starting target (and difficulty) based on true network weight. 
12/04/2017 Added Testnet wallets (31) and network weight 3.8 million
12/04/2017 Renamed from SBE to LBE "Long Block Eradicator"
12/02/2017 Set target multiplier to 45000, this seems to be a good value
11/28/2017 Fixed off by one error in retargeting (144 seconds vs. 144 seconds)
11/28/2017 Correcting retargeting calculation to agree with mainnet actuals
11/23/2017 4x121 expotential moving average to replace Network Weight
11/18/2017 Set default values into averaging arrays at startup
11/15/2017 Added import of block spacing and difficulty times for replay of mainnet
11/13/2017 Fixing target and Network Weight calculation
11/08/2017 Added parameter (outer) loop for multiple runs
11/07/2017 Added print formatting, Network Weight as a adjustable SMA
11/06/2017 Added expotential adjustment of target between blocks
11/03/2017 Added block spacing offset and normal distribution within steps.
11/02/2017 Added logging to .csv file.
11/01/2017 Added block-by-block retargeting per PeerCoin/Qtum
10/31/2017 All new, revised from Qtum PoS Simuator 10/20/2017

- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

To help understandability, the simulator tries to use variable names (and provide
source code file name/line of code references) from the qtum-master clone.

The simiulator can calculate the true values of various numbers, for comparison
to the values calculated by algorithms. Examples of these are true network weight
(the sum of all wallet weights) and true wallet weight, which is a moving
average of the weights of recent wallet winners, for comparision to the
network weight calculation derived from the target, which is literally a
"moving target".

- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

Simulation Complexity

The simulator may be set to run with different levels of complexity, from
simple fixed default parameters, then adding various improvements, adding 
input data measured from mainnet, and trying various soft fork scenarios
(to come). Simulation complexity is set next, along with the relevant
simulation parameters.

'''

import random                           # for pseudo-random numbers

# 0. Baseline: use wallets of uniform weight for a total network weight of
#    n million coins, a fixed target, use Python random module with
#    useFixedSeed = True to give repeatable outputs, or useFixedSeed = False
#    to give different random inputs each run.

useFixedSeed = True  # has no effect for the Python secrets module

if useFixedSeed == True:                                  # COMPLEXITY SWITCH 0
    random.seed("The Blockchain Made Ready for Business") # for repeatability, if desired

# 1. Use the Python secrets module to generate cryptographically secure random numbers
#    to be hashed. Set useSecretsModule = True to use this module, False to use the Python
#    random module. Used in the wallet loop. useFixedSeed has no effect if
#    useSecretsModule = True

useSecretsModule = True

# 2. Retarget with each block based on the PeerCoin/Qtum dynamics. Set
#    useRetarget = True to adjust the difficulty for each new block.
#    Otherwise, use a fixed difficulty, which was manually tweaked in for
#    an approximate average of 8 steps (128 seconds). Used in the wallet
#    loop.

useRetarget = True    # retarget difficulty with each block

# 3. Offset sets block timing within the 16 second steps.  This gives a
#    normal distribution from the start of the 16 second steps,
#    based on measured mainnet behavior. Set useNormalDistributionForOffset = True.
#    Otherwise the block spacing is set the end of the 16 second steps (rounding up,
#    I think, which causes an off-by-one error in the block spacing). Normally this is
#    set to false, because that is how the software works with mainet wallets.
#    Used in the wallet loop.

useNormalDistributionForOffset = False
offsetFromStartOfStep = 5.0          # based on mainnet averages
standardDeviationWithinStep = 0.7    # based on mainnet timing

# 4. Wallet weights can be set for three different approaches:
#
#    "Uniform" - all wallets receive identical weights for a total true network
#        weight of 25,000,000, or whatever.
#
#    "Random" - normal distribution random weights between 100 and 29545 for
#        total true network weight of 25,000,000.
#
#    "Mainnet" - distribution of the 200 largest wallet on mainnet, plus
#         200 small wallets 1 to 200, with the rest mid-sized wallets for
#         total true network weight of 25 million.
#
#    "Testnet" - distribution of 31 wallets with a true network weight of 3,864,113.
#         Also override numWallets and set to 31.
#  

walletWeightDistribution = "Mainnet"  # "Uniform", "Random", "Mainnet", or "Testnet"
numUniformDistbnWallets = 1500
numRandomDistbnWallets = 1500
numMainnetWallets = 1500
numTestnetWallets = 31

# 5. Second bite of the apple: if secondSHA256Check == True make a second check for
#    a SHA256 hash solution after secondCheckStep steps. In this case (on the blockchain)
#    set the nonce to 1 (?)

secondSHA256Check = False
secondCheckStep = 16

# 6. Setting useDynamicWeights = "Once" allows changing the wallet
#    weights one time during the simulation run to show some "big guys" joining and leaving
#    at preset blocks, to observe retargeting algorithm behavior and network response,
#    in particular, to check response time for various retargeting multipliers and
#    the response for "network weight" derived from an inverse moving average of the
#    target. Setting useDynamicWeights = "Multi" allows changing the Network Weight
#    every changeAfterBlocks blocks by dynamicWeightChange percent, randomly up or down.
#    Setting useDymanicWeights = "No" (or anything else) will keep the
#    wallet weights fixed during the simulation run. Used at the top of the block loop.

useDynamicWeights = "No"        # "No", "Once" or "Multi"
dynamicWeightChangeOnce = 100   # change in percent network weight in Once mode, could be negative
changeOnBlock = 2000            # change once on this block, in Once mode
dynamicWeightChangeMulti = 33   # change in percent network weight in Multi mode
changeAfterBlocks = 2000        # in Multi mode, change after this many blocks

# 7. The setting useSpacingDifficultyFile = True allows replaying block spacing and
#   difficulty ripped from the blockchain, or files otherwise created to test
#   spacing and difficulty sequences.
#   If useSpacingDifficultyFile is set to True, then random timing from SHA-256 hash and
#   Normal Distribution for Offset are disabled. Searh for the text "7777A" to see where
#   spacing is set from the file, and search for the text "7777B" to see where difficulty
#   is set from the file. If both of these are active, then there is a full replay of mainnet
#   actions, which can be used for testing Network Weight calculations, but says nothing about
#   the probablity response of the simulator. Otherwise, either the spacing or difficulty
#   input can be commented out to use one or the other for various test scenarios. numBlocks is
#   set by the number of rows in the file. The file also sets the starting block number.

useSpacingDifficultyFile = False
spacing_difficulty_file_name = "spacing_difficulty.txt"       # file name

# 8. Set useTargetScaling = True to dynamically increase the target during a block.
#    Starting with step 16 (or other values), multiply the target by targetScalingFactor,
#    set below. This gives a gradual expotential increase in the target if the blocks are
#    getting too long. You can also set the targetScalingFactor to 1.0 to disable scaling.
#    Used at the top of the step loop to reset the target for that step.

useTargetScaling = False
targetScalingFactor = 1.05
startingStep = 16

# 9. Reserved

# 10. Set useWalletGrowth = True to add wallets during a simulation run.
#    Uses parameters as described below. Network weight will grow by
#    walletGrowthNumWallets * walletGrowthWeight * walletGrowthNumIncrements 
#    with total wallet growth given by walletGrowthNumWallets * walletGrowthNumIncrements

useWalletGrowth = False            # set to cause the number of wallets to grow during the simulation run
walletGrowthStartBlock = 1000      # block to start wallet growth
walletGrowthBlockIncrement = 500   # spacing between blocks of wallet growth
walletGrowthNumWallets = 5000      # number of wallets to grow in each increment
walletGrowthNumIncrements = 10     # number of times to grow wallets
walletGrowthWeight = 500           # weight of each new wallet

numBlocks = 2000          # unless set by spacing difficulty file
                          # 675 blocks a day, 4725 a week, 20250 month, 246375 a year
startingBlock = 0         # unless set in spacing difficulty file

                          # setup here for multiple runs
run = 0                   # set the number of runs, the outer parameter loop 
runMax = 5                # set the number of runs, while paramValue can be changed for
                          # each run. Set to 1 for a single run, or n for multiple runs

                          # paramValue is incremented at the end of a run at the bottom
                          # of the parameter loop, to iterate through the values and
                          # display the results
numWallets = 0            # will set below
                          
paramValue = 15000         # paramValue must placed into the code, as appropriate

                          # the increment value for paramValue, added to paramValue at 
paramIncrement = 5000     # the bottom of the parameter loop

           # "abcdefghijk"
paramLabel = "target mplr" # up to 11 charactrers column label in the printed output to identify the parameter

targetMultiplier = 832     # for retargeting, default = 832, proposed = 25000

'''
targetScalingFactor = 1.000
paramValue = targetScalingFactor
paramIncrement = 0.005              # increment at the bottom of the parameter loop
paramLabel = "trgtScFactr"          # limit to 11 characters, prints on display and logs
'''

'''
startingStep = 16                   # step to start the target scaling
paramValue = startingStep
paramIncrement = 2                  # increment at the bottom of the parameter loop
paramLabel = "startngStep"          # limit to 11 characters, prints on display and logs
'''

# consensus parameters, or constants from the bitcoin source code- - - - - - - - - - - - - - - 

nPowTargetTimespan = 16 * 60            # from chainparams.cpp, line 89
nPowTargetSpacing = 2 * 64              # from chainparams.cpp, line 90
nPoSInterval = 72                       # for GetPoSKernelPS() in blockchain.cpp line 111, default 72
COIN = 100000000                        # from amount.h line 17: static const CAmount COIN = 100000000;

                                        # // To decrease granularity of timestamp, Supposed to be 2^n-1
STAKE_TIMESTAMP_MASK = 15               # pos.h line 21: static const uint32_t STAKE_TIMESTAMP_MASK = 15; 

EASIEST_DIFFICULTY = 26959000000000000000000000000000000000000000000000000000000000000000
                                        # = ffff0000000000000000000000000000000000000000000000000000 in hex

# printing and logging switches - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

enableLogging = True         # control logging of settings and final results
printBlockByBlock = False    # print out each new block, doubles the simulation duration
logBlockByBlock = False      # log each new block, turn this off if just interested in end summary

import hashlib                          # for SHA-256 hash algorithm
import secrets				# for cryptographically strong random numbers
from timeit import default_timer as timer
import os, sys                          # for file operations
from array import *                     # for arrays
import time
from time import localtime, strftime, sleep
from datetime import datetime
import winsound                         # change on linux machines

print("Qtum LBE Simulator, version", version)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def getNetworkWeight( ):
    # update the network weight

    newNetworkWeight = 0

    for i in range(numWallets):   
        newNetworkWeight += walletWeight[i]    
    
    return(newNetworkWeight)

# read in the spacing difficulty file - - - - - - - - - - - - - - - - - - - - - - - - - -
# comments line start with a "#"
# the first non-comment line gives the starting block number
# This file can be derived from the blockchain ripper or manually created:

'''
# blocks 35,700 - 35,913
# including 1866 seconds at block 35,753
# and 3246 seconds at block 35,806
# starting block:
35700
13
418
433
748
...
'''

if useSpacingDifficultyFile == True:

    blockSpacing = []              # an array of block spacings in seconds
    blockDifficulty = []           # an array of difficulties
    gotBlockNumber = False
    numBlocks = 0

    try:
        blockSpacingFile = open(spacing_difficulty_file_name, 'r')  # check for success, or exit
    except:
        print("ERROR opening spacing difficulty file")
        print('The configuration file "spacing_difficulty.txt" must be in the same directory with QLBES')
        sys.exit()

    print("useSpacingDifficultyFile = True, loading spacing and difficulty for replay from file", spacing_difficulty_file_name)  

    for line in blockSpacingFile:
        data = line
        # print("data", data)

        if data[0] != "#":                   # skip comments     
            if gotBlockNumber == False:      # get block number from first non-comment line
                startingBlock = int(data)
                print("startingBlock number is", startingBlock)
                gotBlockNumber = True
            else:
                i = 0
                strSpacing = ""
                strDifficulty = ""
                
                while i < len(data):   # just grab the spacing
                    if data[i] != ",":
                        strSpacing += data[i]
                    else:
                        break
                    i += 1

                i += 1    

                while i < len(data):   # just grab the difficulty
                    strDifficulty += data[i]
                    i += 1

                # print(strSpacing, strDifficulty)

                if strSpacing == '\n':   # read to end of file
                    break
                
                spacing = int(strSpacing)
                difficulty = float(strDifficulty)

                # print(spacing, difficulty)
                    
                blockSpacing.append(spacing)
                blockDifficulty.append(difficulty)
                numBlocks += 1                # count the blocks from the file

    blockSpacingFile.close()

# print("useSpacingDifficultyFile 2", useSpacingDifficultyFile)    

start = timer()         # to measure seconds duration for simulation

nNetworkWeightList = array('f',(0.0,) * nPoSInterval) # an array for storing old difficulty moving average values
nStakesTimeList =    array('f',(0.0,) * nPoSInterval) # an array for storing old block spacing moving average values

# load up the wallets - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

def loadMainnetWallets():  # define as a function to allow reset for multiple runs
    
    ''' 
    0 to 199   Big guys, 1.5 million to 11.5k coins, 17529755 subtotal, Mainnet scrape 12/16/2017
    200 to 399   Little guys, 1 to 200 coins, 20100 subtotal
    400 to numWallets - 401 linear distribution, 7448224 subtotal
    numWallets - 1, 1921, top off to 25 million
    '''
    
    global numWallets
    numWallets = numMainnetWallets

    global walletWeight
    walletWeight = array('i',\
        [1540561, 1419648, 817193, 720017, 705309, 635108, 634289, 524979, 501631, 350003,\
          328899, 302864, 294290, 237965, 223800, 190088, 184761, 176591, 162036, 132052,\
          109115, 105678, 100340, 100330, 100306, 100305, 100302, 100302, 100302, 100299,\
          100294, 100294, 100292, 100291, 100290, 100286, 100282, 100278, 100272, 100272,\
          100272, 100271, 100271, 100268, 100268, 100267, 100267, 100261, 100261, 100259,\
          100253, 100252, 100239, 100230, 100230, 100191, 100166, 93021, 81860, 75930,\
          72298, 70566, 65027, 60907, 56020, 55468, 53556, 52114, 50276, 50268,\
          50129, 43915, 42909, 42830, 42651, 40265, 40212, 40188, 40180, 40171,\
          40143, 40028, 39764, 37800, 37559, 37533, 37053, 35017, 33783, 32112,\
          31405, 30489, 30421, 30204, 30167, 29553, 28617, 28123, 28074, 28001,\
          27736, 27732, 27526, 27437, 26784, 25445, 25323, 25225, 25200, 25159,\
          25096, 24324, 24219, 23489, 23088, 22669, 22564, 21995, 21704, 21383,\
          21351, 21203, 21088, 21050, 20947, 20697, 20221, 20192, 20124, 20119,\
          20096, 20061, 20046, 19986, 19967, 19888, 19587, 19480, 19305, 19272,\
          19101, 18802, 18786, 18783, 18639, 18462, 18302, 18283, 18067, 18008,\
          17976, 17891, 17552, 17432, 17430, 16945, 16454, 16443, 16401, 16253,\
          15730, 15722, 15596, 15522, 15402, 15194, 15109, 15038, 14566, 14548,\
          14444, 14137, 14087, 13913, 13631, 13624, 13612, 13611, 13611, 13575,\
          13439, 13261, 13240, 13163, 13147, 12930, 12846, 12833, 12715, 12538,\
          12531, 12509, 12254, 12199, 12146, 12116, 12045, 12029, 11730, 11577])
                   
    # the little guys, just load them up with 1..200, add 20100
    for i in range(200):
        walletWeight.append(i + 1)
    
    for i in range(numWallets - 401):          # add 7448224 more
        walletWeight.append((200 + i * 24) % 14800)

    walletWeight.append(1921)                  # top off to 25 million even    
    
    numWallets = len(walletWeight)             # double check

    return()

if walletWeightDistribution == "Uniform":  #       COMPLEXITY SWITCH 4
    walletWeight = []
    numWallets = numUniformDistbnWallets
    
    for i in range(numWallets): # initialize all wallets for a network weight 25000500
        walletWeight.append(round(25000000/numWallets))   

elif walletWeightDistribution == "Random":  # 24986700
    walletWeight = []
    numWallets = numRandomDistbnWallets
    for i in range(numWallets):
        walletWeight.append(random.randint(100,33535))
    
elif walletWeightDistribution == "Mainnet":
    loadMainnetWallets()
    print("did loadMainnetWallets()")
    
elif walletWeightDistribution == "Testnet":    # testnet wallets as of 12/02/2017
    # wallets 0..30, 3864113 total

    walletWeight = array('i',\
        [143099, 193363, 89341, 128595, 84284, 143694, 77200, 196241, 82733, 208009,\
         134267, 170248, 183450, 116931, 95888, 84865, 159591, 64177, 50450, 241,\
         186143, 180077, 140432, 206759, 52160, 88620, 61543, 61820, 148059, 146921, 184912])
    
    numWallets = len(walletWeight)

else:
    print("ERROR: need to specify Uniform, Random, Mainnet or Testnet for wallet weight distribution")
    sys.exit()

# print("numWallets", numWallets)

trueNetworkWeight = getNetworkWeight()

walletStaking = []
for i in range(numWallets):
    walletStaking.append(1)      # initialize all wallets to be staking   

# print("trueNetworkWeight", trueNetworkWeight)

# sys.exit()     # use if resetting network weight

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# logFileName = "qlbes.csv"  # logging file

if enableLogging == True:
    print("enableLogging = True")
else:
    print("enableLogging = False")

if printBlockByBlock == True:
    print("printBlockByBlock = True")
else:
    print("printBlockByBlock = False")
        
if logBlockByBlock == True:
    print("logBlockByBlock = True")
else:
    print("logBlockByBlock = False")

if useSpacingDifficultyFile == False:      # running a simulation with all these parameters
 
    if useSecretsModule == True:
        print("Using Python secrets module for cryptographically strong random numbers")
    else:
        if useFixedSeed == True:
            print("Using Python random module with fixed seed for repeatable pseudo-random numbers")
        else:
            print("Using Python random module with random seed for pseudo-random numbers")

    if useRetarget == True:
        print("useRetarget = True, retarget on every block")
    else:
        print("useRetarget = False, use fixed target")
        
    if useNormalDistributionForOffset == True:
        print("useNormalDistributionForOffset = True, use block times within the 16 second steps")
    else:
        print("useNormalDistributionForOffset = False, use fixed block times at the start of the 16 second steps")
        
    if useTargetScaling == True:
        print("Using target scaling, targetScalingFactor", targetScalingFactor, "starting on step", startingStep)

if walletWeightDistribution == "Uniform":
    print("Loading wallets with uniform weights based on total network weight")
elif walletWeightDistribution == "Random":
    print("Loading wallets with random weights based on total network weight")
elif walletWeightDistribution == "Mainnet":
    print("Loading wallets with Mainnet distribuition")
elif walletWeightDistribution == "Testnet":
    print("Loading wallets with Testnet distribution")
else:
    print('ERROR: wallet weight distribution must be set to "Uniform", "Random", "Mainnet", or "Testnet"')
    sys.exit()

if secondSHA256Check == True:
    print("secondSHA256 = True, secondCheckStep", secondCheckStep)
else:
    print("secondSHA256 = False, do not make 2nd SHA-256 check")
    
if useDynamicWeights == "No":
    print("useDynamicWeights = No, keep wallet weights constant during the simulation run")
elif useDynamicWeights == "Once":
    print("useDynamicWeights = Once, make one change in wallet of", dynamicWeightChangeOnce, "percent in network weight at block", changeOnBlock)
elif useDynamicWeights == "Multi":
    print("useDynamicWeights = Multi, make a random direction change of", dynamicWeightChangeMulti, "percent in network weight every", changeAfterBlocks, "blocks")
else:
    print("ERROR useDynamicWeights = Unknown - should be No Once or Multi - keep wallet weights constant during the simulation run")

if useWalletGrowth == True:
    print("useWalletGrowth = True, start block", walletGrowthStartBlock, "block increment", walletGrowthBlockIncrement, "num each increment", walletGrowthNumWallets, "num increments", walletGrowthNumIncrements, "wallet size", walletGrowthWeight)                 

# initialize log file - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

if enableLogging == True:    
    GMT = strftime("%a, %d %b %Y %H:%M:%S", time.gmtime())  # GMT
    # open log file in the format "QM_Log_DD_MMM_YYYY.csv"
    out_file_name_QLBES = 'QLBES_Log_'+GMT[5]+GMT[6]+'_'+GMT[8]+GMT[9]+GMT[10]+\
                    '_'+GMT[12]+GMT[13]+GMT[14]+GMT[15]+'.csv'
    
    print("Log file name =", out_file_name_QLBES) 
        
    try:
        outFileQLBES = open(out_file_name_QLBES, 'a')   # create or open log file for appending
        tempStr = 'QLBES version' + version
        outFileQLBES.write(tempStr)
        outFileQLBES.write('\n')
        
        # log starting time:
        tempStr = 'Starting' + '_' + GMT[17]+GMT[18]+GMT[20]+GMT[21]+',hours,GMT,'+\
                  GMT[5]+GMT[6]+'_'+GMT[8]+GMT[9]+GMT[10]+GMT[12]+GMT[13]+GMT[14]+GMT[15]
        outFileQLBES.write(tempStr)
        outFileQLBES.write('\n')
        time.sleep(0.01)
        tempStr = "wallets" + "," + str(numWallets) + "," + "blocks," + str(numBlocks) + ",targetMultiplier," + str(targetMultiplier)
        outFileQLBES.write(tempStr)
        outFileQLBES.write('\n')
        time.sleep(0.01)

    except IOError:   # NOT WORKING
        print("QLBES ERROR: File didn't exist, open for appending")

# log simulation parameters - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# gonna run a whole lot of simulations, better log the simulation complexity settings
# be sure to close Excel before running the simulator, or the log file won't open (on a PC)

if enableLogging == True:

    if useSpacingDifficultyFile == False:      # doing simulation, not replay
    
        if useSecretsModule == True:
            tempStr = "Using Python secrets module for cryptographically strong random numbers\n"
        else:
            if useFixedSeed == True:
                tempStr = "Using Python random module with fixed seed for repeatable pseudo-random numbers\n"
            else:
                tempStr = "Using Python random module with random seed for pseudo-random numbers\n"

        outFileQLBES.write(tempStr)
        time.sleep(0.01)            

        if useRetarget == True:
            tempStr = "useRetarget = True, retarget on every block\n"
        else:
            tempStr = "useRetarget = False, use fixed target\n"
            
        outFileQLBES.write(tempStr)
        time.sleep(0.01)

        if useNormalDistributionForOffset == True:
            tempStr = "useNormalDistributionForOffset = True, use block times within the 16 second steps\n"
        else:
            tempStr = "useNormalDistributionForOffset = False, use fixed block times at the start of the 16 second steps\n"

        if useTargetScaling == True:
            tempStr = "Using target scaling, targetScalingFactor" + "," + str(targetScalingFactor) + "," + "starting step" + "," + str(startingStep) + "\n"
            outFileQLBES.write(tempStr)
            time.sleep(0.01)
    else:     # using spacing difficulty file for replay
        
        tempStr = "useSpacingDifficultyFile = True, loading spacing and difficulty for replay from file," + spacing_difficulty_file_name + "\n"
        outFileQLBES.write(tempStr)
        time.sleep(0.01)
        
    if walletWeightDistribution == "Uniform":
        tempStr = "Loading wallets with uniform weights based on total network weight\n"
    elif walletWeightDistribution == "Random":
        tempStr = "Loading wallets with random weights based on total network weight\n"
    elif walletWeightDistribution == "Mainnet":
        tempStr = "Loading wallets with Mainnet distribuition\n"
    elif walletWeightDistribution == "Testnet":
        tempStr = "Loading wallets with Testnet distribuition\n"
    else:
        tempStr = "ERROR Unknown wallet distribution\n"

    outFileQLBES.write(tempStr)
    time.sleep(0.01)

    if secondSHA256Check == True:
        tempStr = "secondSHA256 = True, secondCheckStep" + str(secondCheckStep) + "\n"
    else:
        tempStr = "secondSHA256 = False\n"

    outFileQLBES.write(tempStr)
    time.sleep(0.01)

    if useDynamicWeights == "No":
        tempStr = "useDynamicWeights = No, keep wallet weights constant during the simulation run\n"
    elif useDynamicWeights == "Once":
        tempStr = "useDynamicWeights = Once, make one change in wallet weight of" + str(dynamicWeightChangeOnce) + "percent in network weight at block", str(changeOnBlock) + "\n"
    elif useDynamicWeights == "Multi":
        tempStr = "useDynamicWeights = Multi - make a random direction change of," + str(dynamicWeightChangeMulti) + ", percent in network weight every," + str(changeAfterBlocks) + ",blocks\n"
    else:
        tempStr = "ERROR useDynamicWeights = Unknown - should be No Once or Multi, keep wallet weights constant during the simulation run\n"  

    outFileQLBES.write(tempStr)
    time.sleep(0.01)

    if useWalletGrowth == True:
        tempStr = "useWalletGrowth = True, start block," + str(walletGrowthStartBlock) + ",block increment," + str(walletGrowthBlockIncrement) + ",num each increment," + str(walletGrowthNumWallets) + ",num increments," + str(walletGrowthNumIncrements) + ",size," + str(walletGrowthWeight) + "\n"      
        outFileQLBES.write(tempStr)
        time.sleep(0.01)

if enableLogging == True:
    tempStr = "trueNetworkWeight," + str(trueNetworkWeight)
    outFileQLBES.write(tempStr)
    outFileQLBES.write('\n')
    time.sleep(0.01)

    if logBlockByBlock == True:  # print some column labels
        tempStr = "block,wallet,wallet weight,true network weight,new network weight,network weight,target,difficulty,spacing\n"
        outFileQLBES.write(tempStr)
        time.sleep(0.01) 

# sys.exit()

print("Wallets", numWallets, "blocks", numBlocks, "startingBlock", startingBlock, "targetMultiplier", targetMultiplier)

# calculate the starting target and difficulty - - - - - - - - - - - - - - - - - - - - - - - - - - -

dDiff = trueNetworkWeight / 5.86        # slope from chart of simulated results, uniform wallets
target = EASIEST_DIFFICULTY / dDiff

# print("target", target, "dDiff", dDiff)

startingDifficulty = dDiff                                                     
pFirst121EMA = startingDifficulty       # expotential moving average of difficulty
pSecond121EMA = startingDifficulty      # expotential moving average of pFirst121EMA
pThird121EMA = startingDifficulty       # expotential moving average of pSecond121EMA
pFourth121EMA = startingDifficulty      # expotential moving average of pThird121eEMA
EMAScalingFactor = 5.59                 # simulated value for 20 million network weight
                                        # 29943463, 5.08
                                        # 20026263, 5.59
                                        # 15008923, 5.14
                                        # not 5.86, based on slope?

savedTarget = target                   # used to reset the target if scaling

# go ahead and preload these averaging arrays with default values, this is a KLUDGE
# since we don't really have the blockchain to read like "real" wallets
# but gets to a normal value sooner in the simulation or replay

for i in range(nPoSInterval):   
    dDiff = EASIEST_DIFFICULTY / target
    nNetworkWeightList[i] = dDiff * 4294967296
    nStakesTimeList[i] = nPowTargetSpacing           # nominally 128 seconds
    
if useSpacingDifficultyFile == True:
    print("Running replay - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -")
else:    
    print("Running simulation - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -")

# walletStaking[0] = 0  # turn off the big guy

# parameter loop - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# note, targets, and the simple moving averages lists are not reset between runs

while run < runMax:

    targetMultiplier = paramValue   # if changing the targetMultiplier on successive runs
    
    block = startingBlock
    stepTotal = 0          # number of 16 second steps to a solution

    maxSteps = 0           # the maximum steps for a solution, all blocks
    collisionCount = 0     # the number of collisions we get
    fiveXSpacingBlocks = 0 # number of blocks with >= 40 steps
    nNetworkWeight = 0.0   # used to calculate a moving average of difficulty, for network weight
    nNetworkWeightListIndex = 0 # the index into the moving average arrays
    nStakesTime = 0.0      # used to calculate a moving average for block spacing, for network weight
    numTargetDoubles = 0   # if using target scaling, how many times?
    numTwoBites = 0        # if using 2nd SHA256 check, how many times successful?
    nextWeightChangeBlock = changeAfterBlocks  # set first weight change block
    nextWalletGrowthBlock = walletGrowthStartBlock # if growing wallets, set for starting block

    if walletWeightDistribution == "Mainnet" and useDynamicWeights != "No":  # for Once or Multi reset wallet weights
        loadMainnetWallets()                                                 # will run twice on startup
        trueNetworkWeight = getNetworkWeight()
        # print("reset mainnet wallets, trueNetworkWeight", trueNetworkWeight)
  
    # block loop - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

    while block < numBlocks + startingBlock:

        step = 1             # 16 second steps
        had5xSteps = False   # had 40 steps or more in this block
        # target = savedTarget # in case scaling the target below   what to do? 
        
        if useDynamicWeights == "Once":                               # COMPLEXITY SETTING 6
            
            if block == changeOnBlock:

                changeAmount = trueNetworkWeight * dynamicWeightChangeOnce / 1000

                for i in range(10,20):
                    walletWeight[i] += int(changeAmount)
                
                trueNetworkWeight = getNetworkWeight()            # update true network weight 

        elif useDynamicWeights == "Multi" and block == nextWeightChangeBlock:

            nextWeightChangeBlock += changeAfterBlocks  # set next weight change block

            # change amount based on percent for 10 wallets
            changeAmount = trueNetworkWeight * dynamicWeightChangeMulti / 1000
            
            # determine whether increase or decrease
            if random.randrange(0, 99) <= 33:  # decrease 33% of the time
                changeAmount *= -1
                
            for i in range(10,20):
                    walletWeight[i] += int(changeAmount)
                
            trueNetworkWeight = getNetworkWeight()    # update true network weight
            
        # wallet growth - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
                                                                  # COMPLEXITY SETTING 10
                                               
        if useWalletGrowth == True:             # wallets grow during the simulation run

            if block == nextWalletGrowthBlock and walletGrowthNumIncrements > 0:

                nextWalletGrowthBlock += walletGrowthBlockIncrement # set for next growth block
                walletGrowthNumIncrements -= 1

                for i in range(0, walletGrowthNumWallets):          # add this many wallets
                    walletWeight.append(walletGrowthWeight)         # add a wallet
                    walletStaking.append(1)                         # set for staking

                numWallets += walletGrowthNumWallets    
                trueNetworkWeight = getNetworkWeight()    # update true network weighttrue

                print("numWallets", numWallets, "trueNetworkWeight", trueNetworkWeight)
        
        # step loop - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

        while True:  # loop on step until we have a solution
            
            wallet = 0
            SHA256Solutions = 0
                                                                     # COMPLEXITY SWITCH 8
            # if useTargetScaling == True:  # increase the target if the block is getting too long
            #     if step >= startingStep:            # starting step for scaling  
            #         target *= targetScalingFactor

            # loop through all the wallets and check for a solution and find
            # SHA-256 collisions, orphans
            # on a live blockchain all the wallets would be checking simultaneously
            
            # wallet loop - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
            
            while wallet < numWallets:  # loop through all the wallets

                if walletStaking[wallet] == 1:   # this wallet is staking

                    # get a 256 bit random number to use as the digest for SHA-256
                    # use either the Python random module of the secrets module
                    
                    if useSecretsModule == True:                        # COMPLEXITY SWITCH 1
                        temp = str(secrets.randbits(256)).encode('utf-8')   # using secrets module
                    else:
                        temp = str(random.getrandbits(256)).encode('utf-8') # using random module
                    
                    hash_object = hashlib.sha256(temp)    # get SHA-256 hash
                    hex_dig = hash_object.hexdigest()
                                      # random module, fixed seed, first time through, 1,000 mainnet wallets
                    # print(hex_dig)  # 0df34ba99348c61d540586b516925d2836103625268c6387e33f3b3a89174f9f

                    hashProofOfStake = int(hex_dig, 16) # convert hex string to a really big decimal int
                    # print(hashProofOfStake) # 6309933071041450796822743352002321870736073756553388285190011991562795831199
                                              # or 6.30993307104145E+75
                                              
                    if useTargetScaling == True: # add 100% target at 17 steps
                        
                        if step >= paramValue:
                            if hashProofOfStake < (target * 2.0) * walletWeight[wallet] * COIN:
                                SHA256Solutions += 1      # found a solution
                                walletWinner = wallet     # the block reward winner, last one in this block
                                numTargetDoubles += 1     # count the number of times the target doubles

                                if SHA256Solutions >= 2:
                                    collisionCount+= 1  # count of collisions over all blocks
                                    # print("Collision block", block, "wallet", wallet)
                                    
                        else:
                            if hashProofOfStake < target * walletWeight[wallet] * COIN:
                                SHA256Solutions += 1      # found a solution
                                walletWinner = wallet     # the block reward winner, last one in this block

                                if SHA256Solutions >= 2:
                                    collisionCount+= 1  # count of collisions over all blocks
                                    # print
                    else:        
                        if hashProofOfStake < target * walletWeight[wallet] * COIN:
                            SHA256Solutions += 1      # found a solution
                            walletWinner = wallet     # the block reward winner, last one in this block

                            if SHA256Solutions >= 2:
                                collisionCount+= 1  # count of collisions over all blocks

                        else:                                            # COMPLEXITY SWITCH 5
                            if secondSHA256Check == True and step >= secondCheckStep:   # if the step count is getting long, take a second bite of the applehash_object = hashlib.sha256(temp)    # get SHA-256 hash

                                # nonce += 1
                                if useSecretsModule == True:                        # COMPLEXITY SWITCH 1
                                    temp = str(secrets.randbits(256)).encode('utf-8')   # using secrets module
                                else:
                                    temp = str(random.getrandbits(256)).encode('utf-8') # using random module
                    
                                hash_object = hashlib.sha256(temp)    # get SHA-256 hash
                                hex_dig = hash_object.hexdigest()
                                hashProofOfStake = int(hex_dig, 16) # convert hex string to a really big decimal int
                                
                                if hashProofOfStake < target * walletWeight[wallet] * COIN:
                                    SHA256Solutions += 1      # found a solution
                                    walletWinner = wallet     # the block reward winner, last one in this block
                                    numTwoBites += 1
                                    # print("SECOND BITE")

                                    if SHA256Solutions >= 2:
                                        collisionCount+= 1  # count of collisions over all blocks    

                wallet += 1
                
                # end of wallet loop

            if SHA256Solutions >= 1:  # at least one solution found
       
                stepTotal += step         # total steps across all blocks

                if step > maxSteps:       # save largest step
                    maxSteps = step
                                    
                stepOffset = random.normalvariate(offsetFromStartOfStep, standardDeviationWithinStep)
                if stepOffset < 1.5:
                    stepOffset = 1.5   # lop off low end
                    
                if stepOffset > 10.0:
                    stepOffset = 10.0   # lop off high end

                # print(stepOffset)
                
                if useSpacingDifficultyFile == False:   # use SHA-256 results   COMPLEXITY SWITCH 7

                    if useNormalDistributionForOffset == True:                 # COMPLEXITY SWITCH 3
                        nActualSpacing = step * 16 + stepOffset
                    else:                                 # increase spacing here to reduce block time
                        nActualSpacing = step * 16        # step starts from 1

                    # limit adjustment step

                    nTargetSpacing = nPowTargetSpacing         # pow.cpp, line 78
                    
                    if nActualSpacing > nTargetSpacing * 10:   # pow.cpp, line 82, default 1280
                        # print("hit limit")
                        nActualSpacing = nTargetSpacing * 10

                    # if step <= 2: # this one is interesting, no need to adjust for short spacings
                    #   step = 8    # leave unchanged
                        
                else:                              # use block spacing from the file - 7777A
                    nActualSpacing = blockSpacing[block - startingBlock]

                # print("nActualSpacing", nActualSpacing)

                '''
                adjust the difficulty nBits for the next block
                  
                from pow.cpp line 92 - 93
                bnNew *= ((nInterval - 1) * nTargetSpacing + nActualSpacing + nActualSpacing);
                bnNew /= ((nInterval + 1) * nTargetSpacing);

                where nInterval = nPowTargetTimespan / nPowTargetSpacinng
                nPosTargetTimeSpan = 16 * 60, set in chainparams.cpp line 89
                nTargetSpacing = nPowTargetSpacing = 2 * 64, set in chainparams.cpp line 90
                
                the formula (converting steps to 16 seconds) for default values gives:
                
                target *= ((6.5) * 128 + 2 * step * 16)/8.5 * 128)
                or
                target *= 832 + 2 * step * 16 / 1088

                Some values from Excel:
                
                 ActualSpacing  Target	     Difficulty
                   Seconds      Multiplier   Multiplier   
                     16	        0.794   
                    128	        1.000  
                    144	        1.029  
                    160	        1.059 
                    256	        1.235
                    512	        1.706
                    640         3.118   (limit value)

                '''
             
                # carry offset time across blocks, 1st solution or orphans?
                
                if useRetarget == True:                                    # COMPLEXITY SWITCH 2
                    nInterval = nPowTargetTimespan / nPowTargetSpacing
                    # target *= ((nInterval - 1) * nTargetSpacing + nActualSpacing + nActualSpacing)
                    # target /= ((nInterval + 1) * nTargetSpacing)
                    target *= targetMultiplier + nActualSpacing + nActualSpacing # must be divisor - (128 + 128)
                    target /= targetMultiplier + 256
                    
                    savedTarget = target             # save it for reset if doing target scaling

                # print(target)    

                # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
     
                # calculate the network weight as a moving average of difficulty divided by a
                # moving average of the total spacing for the last 72 blocks

                # convert target to difficulty, divide easiest difficulty 0x00000000ffff by target

                if useSpacingDifficultyFile == False:       # use simulation values COMPLEXITY SWITCH 7
                    dDiff = EASIEST_DIFFICULTY / target
                else:                                                  # 7777B
                    dDiff = blockDifficulty[block - startingBlock]
                                  
                # print("dDiff", dDiff)                 # 3000723.7886220054

                # sys.exit()

                # subtract old moving average contribution, after initialization
                if block > nPoSInterval + startingBlock - 1:
                    # print("subtracting old...")
                    nNetworkWeight -= nNetworkWeightList[nNetworkWeightListIndex]
                    nStakesTime -= nStakesTimeList[nNetworkWeightListIndex]

                # add new value to sum, and save on list

                # blockDifficulty

                nNetworkWeight += dDiff * 4294967296
                nNetworkWeightList[nNetworkWeightListIndex] = dDiff * 4294967296
                nStakesTime += nActualSpacing
                nStakesTimeList[nNetworkWeightListIndex] = nActualSpacing
                
                # get old moving average contribution value nPoSInterval blocks ago
                if nNetworkWeightListIndex == 0:
                    oldMovingAverageIndex = nPoSInterval - 1 # wrap to top of list
                else:
                    oldMovingAverageIndex = nNetworkWeightListIndex - 1

                nNetworkWeightResult = nNetworkWeight / nStakesTime  # or just plug in 9216

                nNetworkWeightResult *= STAKE_TIMESTAMP_MASK + 1       # multiply by 16

                # print("dDiff", dDiff, "nNetworkWeightListIndex", nNetworkWeightListIndex, "nNetworkWeightResult", nNetworkWeightResult, "nStakesTime", nStakesTime)
                # print(nStakesTimeList[0], nStakesTimeList[1], nStakesTimeList[2], nStakesTimeList[3], nStakesTimeList[4], nStakesTimeList[5], nStakesTimeList[6], nStakesTimeList[7], nStakesTimeList[8], nStakesTimeList[9])
                # time.sleep(0.1)
                
                nNetworkWeightListIndex += 1
                if nNetworkWeightListIndex >= nPoSInterval: # wrap
                    nNetworkWeightListIndex = 0

                # compute network weight using four 121 block expotential moving averages

                # print("pFirst121EMA before", pFirst121EMA)
                # EMA multiplier = 2 / (period + 1)
                # 121 = 0.0164, 91 = 0.0217, 71 = 0.0278, 51 = 0.0385, 31 = 0.0625

                pFirst121EMA = 0.0164 * dDiff + 0.9836 * pFirst121EMA
                pSecond121EMA = 0.0164 * pFirst121EMA + 0.9836 * pSecond121EMA
                pThird121EMA = 0.0164 * pSecond121EMA + 0.9836 * pThird121EMA
                pFourth121EMA = 0.0164 * pThird121EMA + 0.9836 * pFourth121EMA

                # print(pFirst121EMA, pSecond121EMA, pThird121EMA, pFourth121EMA)

                # time.sleep(0.5)

                # new network weight is the fourth EMA times a scaling factor
                nNewNetworkWeight = EMAScalingFactor * pFourth121EMA
                nNewNetworkWeight -= nNewNetworkWeight % 250  # round down to nearest 250, to elliminate noise
                
                # print("block", block, "nNewNetworkWeight", nNewNetworkWeight)    

                # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -       

                break # found a SHA-256 hash solution, done with this block
            
            if step >= 40:
                had5xSteps = True # had 40 or more steps in this block

            step += 1  # end of step loop
                
        if had5xSteps == True:            
            fiveXSpacingBlocks += 1
            # print("longer block, steps", step)

        if printBlockByBlock == True:
            
            '''
            display key
            
            block is the block number

            wallet is the wallet number, like an address

            weight is the weight of the winning wallet (or the highest # wallet for a collision)

            trueNetworkWeight "true netwt" is the sum of all wallet weights. This is fixed during the simulation
            unless some dybnamic changes are introduced with useDynamicWeights (commented out)

            nNewNetworkWeight is the new network weight calculated using three expotential moving averages
            
            target is the target for each block, no moving average

            nNetworkWeightResult is the nPoSInterval moving average of the difficulty divided by
            the nPoSInterval moving average of the block spacing, divide by COIN for display in millions
            
            spacing is the time between blocks
            
            Format the data for printing on a display. Calculate the pads to keep 
            the columns aligned. Numbers are right justified:
            
                Block |  wallet |    weight   | true netwt |  new netwt |   target  | network wt | spacing
                    1 |      1  |           1 |  1,234,567 |  1,234,567 |   234,567 | 12,456,789 |     3
            9,999,999 | 99,999  | 9,999,999.9 | 99,999,999 | 99,999,999 |   999,999 | 99,999,999 | 9,999
            \ pads go here                                                 
             
            '''

            if block <= 9999999:
                blockWithCommas = "{:,d}".format(int(block))
                pad = " " * (9 - len(blockWithCommas))
                blockPadCommas = pad + blockWithCommas
            else:
                blockPadCommas = "xxxxxxxxx"

            if walletWinner <= 99999:
                walletWinnerWithCommas = "{:,d}".format(int(walletWinner))
                pad = " " * (7 - len(walletWinnerWithCommas))
                walletWinnerPadCommas = pad + walletWinnerWithCommas
            else:
                walletWinnerPadCommas = "xxxxxxx"
                
            if walletWeight[walletWinner] <= 9999999:
                weightWithCommas = ("{:,f}".format(round(walletWeight[walletWinner], 1)))[:-5]
                pad = " " * (11 - len(weightWithCommas))
                weightPadCommas = pad + weightWithCommas
            else:
                weightPadCommas = "xxxxxxxxxxx"
           
            if trueNetworkWeight <= 99999999:
                trueNetworkWeightWithCommas =  "{:,d}".format(int(trueNetworkWeight))
                pad = " " * (10 - len(trueNetworkWeightWithCommas))
                trueNetworkWeightPadCommas = pad + trueNetworkWeightWithCommas
            else:
                trueNetworkWeightPadCommas = "xxxxxxxxxx"
                
            if nNewNetworkWeight <= 99999999:
                nNewNetworkWeightWithCommas =  "{:,d}".format(int(nNewNetworkWeight))
                pad = " " * (10 - len(nNewNetworkWeightWithCommas))
                nNewNetworkWeightPadCommas = pad + nNewNetworkWeightWithCommas
            else:
                nNewNetworkWeightPadCommas = "xxxxxxxxxx"

           # target scaling factor, for printing
            printTarget = target / 10000000000000000000000000000000000000000000000000000000  # print scaling factor ???
            
            if printTarget <= 9999999:
                printTargetWithCommas = "{:,d}".format(int(printTarget))
                pad = " " * (9 - len(printTargetWithCommas))
                printTargetPadCommas = pad + printTargetWithCommas
            else:
                printTargetPadCommas = "xxxxxxxxx"
                
            if (block >= nPoSInterval + startingBlock):   # nNetworkWeight or "Network Weight"
                                          # is a simple moving average for nPoSInterval
                                          # blocks of the reciprocal of the target divided by
                                          # the block spacing for nPosInterval blocks

                nNetworkWeightResultMillions = nNetworkWeightResult / COIN              
                if nNetworkWeightResultMillions <= 99999999:
                    nNetworkWeightResultMillionsWithCommas =  "{:,d}".format(int(nNetworkWeightResultMillions))
                    pad = " " * (10 - len(nNetworkWeightResultMillionsWithCommas))
                    nNetworkWeightResultMillionsPadCommas = pad + nNetworkWeightResultMillionsWithCommas
                else:
                    nNetworkWeightResultMillionsPadCommas = "xxxxxxxxx"
                    
            else:
                nNetworkWeightResultMillionsPadCommas = "   not yet"  # no pseudoNetworkWeight for the first nPoSInterval blocks  
       
            if nActualSpacing <= 9999:
                nActualSpacingWithCommas = ("{:,f}".format(round(nActualSpacing, 1)))[:-5]
                pad = " " * (7 - len(nActualSpacingWithCommas))
                nActualSpacingPadCommas = pad + nActualSpacingWithCommas
            else:
                nActualSpacingPadCommas = "xxxxx"

            if dDiff <= 9999999:
                dDiffWithCommas = ("{:,f}".format(round(dDiff, 1)))[:-5]
                pad = " " * (10 - len(dDiffWithCommas))
                dDiffPadCommas = pad + dDiffWithCommas
            else:
                dDiffPadCommas = "xxxxxxxx"
                
            if block % 20 == 0: # print column labels
                print("    Block |  wallet |    weight   | true netwt |  new netwt | network wt |   target  |  difficulty | spacing")

            print(blockPadCommas, "|", walletWinnerPadCommas, "|", weightPadCommas, "|", trueNetworkWeightPadCommas, "|", nNewNetworkWeightPadCommas, "|", nNetworkWeightResultMillionsPadCommas, "|", printTargetPadCommas, "|", dDiffPadCommas, "|", nActualSpacingPadCommas)

        if logBlockByBlock == True:

            '''
            sample in Excel

                Block |  wallet |    weight   | true netwt |  new netwt | network wt |  target | spacing
                    1 |      1  |           1 |  1,234,567 |  1,234,567 |  1,234,567 |  12,456 |     3
            9,999,999 | 99,999  | 9,999,999.9 | 99,999,999 | 99,999,999 | 99,999,999 | 999,999 | 9,999
            
            block  wallet   weight  target      net weight    spacing
            8473	577	9248	15.88376106	133.4529068
            8474	84	20941	15.89595998	180.6929067
            8475	1	892220	15.9042698	212.8724866
            '''
            
            logTarget = target / 10000000000000000000000000000000000000000000000000000000  # scaling factor for 16 m network weight in logging

            if block >= nPoSInterval + startingBlock:
                nNetworkWeightResultMillions = nNetworkWeightResult / COIN  
                tempStr = str(block) + "," + str(walletWinner) + "," + str(walletWeight[walletWinner]) + "," + str(trueNetworkWeight) + "," + str(nNewNetworkWeight) + "," + str(nNetworkWeightResultMillions) + "," + str(logTarget) + "," + str(dDiff) + "," + str(nActualSpacing)

            else:  # no good values yet for the true wallet and network weight averages
                tempStr = str(block) + "," + str(walletWinner) + "," + str(walletWeight[walletWinner]) + "," + str(trueNetworkWeight) + "," + str(nNewNetworkWeight) + "," + str(0) + "," + str(logTarget) + "," + str(dDiff) + "," + str(nActualSpacing)
             
            outFileQLBES.write(tempStr)
            outFileQLBES.write('\n')
            time.sleep(0.01)

        block += 1  # end of block loop

    '''
    Format the data for printing on a display. Calculate the pads to keep 
    the columns aligned. Numbers are right justified:
        
            Run |  paramValue | ave secs | >=640 blks | max secs | collisns
              1 |           1 |   128.00 |          0 |        0 |        0 
            999 | 999,999,999 | 9,999.00 |    999,999 |  999,999 |   99,999
           \ pads go here
    '''

    if run <= 999:
        runWithCommas = "{:,d}".format(run)
        pad = " " * (5 - len(runWithCommas))
        runPadCommas = pad + runWithCommas
    else:
        runPadCommas = "xxx"

    # parameter value - float
    
    if paramValue <= 999999.999:
        paramValueWithCommas = "{:,f}".format(paramValue)[:-3]  #  xx.xxx
        pad = " " * (11 - len(paramValueWithCommas))
        paramValuePadCommas = pad + paramValueWithCommas
    else:
        paramValuePadCommas = "xxxxxxxxxxx"

    aveSeconds = 16 * stepTotal / numBlocks # is there a better value?
    
    if aveSeconds <= 9999.99:
        aveSecondsWithCommas = ("{:,f}".format(aveSeconds))[:-4]  # xx.xx
        pad = " " * (8 - len(aveSecondsWithCommas))
        aveSecondsPadCommas = pad + aveSecondsWithCommas
    else:
        aveSecondsPadCommas = "xxxxxxxx"
   
    if fiveXSpacingBlocks <= 999999:
        fiveXSpacingBlocksWithCommas =  "{:,d}".format(int(fiveXSpacingBlocks))
        pad = " " * (10 - len(fiveXSpacingBlocksWithCommas))
        fiveXSpacingBlocksPadCommas = pad + fiveXSpacingBlocksWithCommas
    else:
        fiveXSpacingBlocksPadCommas = "  xxxxxxxx"

    maxSeconds = maxSteps * 16 # is there a better number?
    
    if maxSeconds <= 999999:
        maxSecondsWithCommas = "{:,d}".format(int(maxSeconds))
        pad = " " * (8 - len(maxSecondsWithCommas))
        maxSecondsPadCommas = pad + maxSecondsWithCommas
    else:
        maxSecondsPadCommas = "xxxxxxxx"
    
    if collisionCount <= 99999:
        collisionCountWithCommas = "{:,d}".format(int(collisionCount))
        pad = " " * (8 - len(collisionCountWithCommas))
        collisionCountPadCommas = pad + collisionCountWithCommas
    else:
        collisionCountPadCommas = " xxxxxxx"

    if run % 20 == 0: # print column labels

        # brute force centering for the parameter name
        
        lenStr = len(paramLabel)

        if lenStr >= 11:
            printStr =  " " + paramLabel[:11] + " " # chop first 11 characters
        elif lenStr == 10:
            printStr = "  " + paramLabel + " "
        elif lenStr == 9:
            printStr = "  " + paramLabel + "  "
        elif lenStr == 8:
            printStr = "   " + paramLabel + "  "
        elif lenStr == 7:
            printStr = "   " + paramLabel + "   "
        elif lenStr == 6:
            printStr = "    " + paramLabel + "   "
        elif lenStr == 5:
            printStr = "    " + paramLabel + "    "
        elif lenStr == 4:
            printStr = "     " + paramLabel + "    "
        elif lenStr == 3:
            printStr = "     " + paramLabel + "     "
        elif lenStr == 2:
            printStr = "      " + paramLabel + "     "
        else: # len == 1
            printStr = "      " + paramLabel + "      "

        tempStr = "  Run |" + printStr + "| ave secs | >=640 blks | max secs | collisns | num2bites"
        print(tempStr)
        
    print(runPadCommas, "|", paramValuePadCommas, "|", aveSecondsPadCommas, "|", fiveXSpacingBlocksPadCommas, "|", maxSecondsPadCommas, "|", collisionCountPadCommas, "|", numTwoBites)

    if enableLogging == True:

        if run == 0:  # write column labels to log
            tempStr = "Run,paramLabel,ave secs,'>=640 blks,max secs,collisions"
            outFileQLBES.write(tempStr)
            outFileQLBES.write('\n')
            time.sleep(0.01)               
            
        tempStr = str(run) + "," + str(paramValue) + "," + str(aveSeconds) + "," + str(fiveXSpacingBlocks) + "," + str(maxSeconds) + "," + str(collisionCount)

        outFileQLBES.write(tempStr)
        outFileQLBES.write('\n')
        time.sleep(0.01)
  
    # increment the parameter here, some examples

    targetMultiplier += paramIncrement         # for incrementing target multiplier
    paramValue = targetMultiplier

    # startingStep += paramIncrement           # for stepping by 2 the startingStep value
    # paramValue = startingStep

    # paramValue += paramIncrement

    run += 1

    # end of param loop

end = timer()
print("Simulation duration in seconds:", format(end - start, "0.2f"))
print("ending target", target, "ending difficulty", dDiff)
print("true network weight", trueNetworkWeight, "ending new network weight", nNewNetworkWeight)

outFileQLBES.close()
duration = 500                 # millisecond
freq = 880                     # Hz
winsound.Beep(freq, duration)  # sound on a Windows machine
