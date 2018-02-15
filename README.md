# Qtum-LBE-Simulator

A Qtum wallet simulator to explore target adjustment and block spacing

Qtum LBE Simulator (LBE = Long Block Eradicator) a program to use the SHA-256
hash function and algorithms from qtum mainnet
wallet software to explore retargeting, the network weight calculation and block spacing.
Runs a simulation using "steps" to replicate 16 second granularity in the PoS algorithm.
Uses SHA-265 hash and identical logic for block-by-block retargeting. Simulates wallet 
populations from 500 and up, and can run for any amount of blocks.

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
and at the bottom of the parameter loop. 

"Long block" is a block with a long spacing, > 20 minutes.

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

import random                           # for pseudo-random numbers

0. Baseline: use wallets of uniform weight for a total network weight of
   n million coins, a fixed target, use Python random module with
   useFixedSeed = True to give repeatable outputs, or useFixedSeed = False
   to give different random inputs each run.

useFixedSeed = True  # has no effect for the Python secrets module

if useFixedSeed == True:                                  # COMPLEXITY SWITCH 0
    random.seed("The Blockchain Made Ready for Business") # for repeatability, if desired

1. Use the Python secrets module to generate cryptographically secure random numbers
   to be hashed. Set useSecretsModule = True to use this module, False to use the Python
   random module. Used in the wallet loop. useFixedSeed has no effect if
   useSecretsModule = True

useSecretsModule = False

2. Retarget with each block based on the PeerCoin/Qtum dynamics. Set
   useRetarget = True to adjust the difficulty for each new block.
   Otherwise, use a fixed difficulty, which was manually tweaked in for
   an approximate average of 8 steps (128 seconds). Used in the wallet
   loop.

useRetarget = True    # retarget difficulty with each block

3. Offset sets block timing within the 16 second steps.  This gives a
   normal distribution from the start of the 16 second steps,
   based on measured mainnet behavior. Set useNormalDistributionForOffset = True.
   Otherwise the block spacing is set the end of the 16 second steps (rounding up,
   I think, which causes an off-by-one error in the block spacing). Normally this is
   set to false, because that is how the software works with mainet wallets.
   Used in the wallet loop.

useNormalDistributionForOffset = False
offsetFromStartOfStep = 5.0          # based on mainnet averages
standardDeviationWithinStep = 0.7    # based on mainnet timing

4. Wallet weights can be set for three different approaches:

   "Uniform" - all wallets receive identical weights for a total true network
       weight of 25,000,000, or whatever.

   "Random" - normal distribution random weights between 100 and 29545 for
       total true network weight of 25,000,000.

   "Mainnet" - distribution of the 200 largest wallet on mainnet, plus
        200 small wallets 1 to 200, with the rest mid-sized wallets for
        total true network weight of 25 million.

   "Testnet" - distribution of 31 wallets with a true network weight of 3,864,113.
        Also override numWallets and set to 31.

walletWeightDistribution = "Mainnet"  # "Uniform", "Random", "Mainnet", or "Testnet"
numUniformDistbnWallets = 1500
numRandomDistbnWallets = 1500
numMainnetWallets = 1500
numTestnetWallets = 31

5. Second bite of the apple: if secondSHA256Check == True make a second check for
   a SHA256 hash solution after secondCheckStep steps. In this case (on the blockchain)
   set the nonce to 1 (?)

secondSHA256Check = False
secondCheckStep = 16

6. Setting useDynamicWeights = "Once" allows changing the wallet
   weights one time during the simulation run to show some "big guys" joining and leaving
   at preset blocks, to observe retargeting algorithm behavior and network response,
   in particular, to check response time for various retargeting multipliers and
   the response for "network weight" derived from an inverse moving average of the
   target. Setting useDynamicWeights = "Multi" allows changing the Network Weight
   every changeAfterBlocks blocks by dynamicWeightChange percent, randomly up or down.
   Setting useDymanicWeights = "No" (or anything else) will keep the
   wallet weights fixed during the simulation run. Used at the top of the block loop.

useDynamicWeights = "Multi"     # "No", "Once" or "Multi"
dynamicWeightChangeOnce = 100   # change in percent network weight in Once mode, could be negative
changeOnBlock = 2000            # change once on this block, in Once mode
dynamicWeightChangeMulti = 33   # change in percent network weight in Multi mode
changeAfterBlocks = 2000        # in Multi mode, change after this many blocks

7. The setting useSpacingDifficultyFile = True allows replaying block spacing and
  difficulty ripped from the blockchain, or files otherwise created to test
  spacing and difficulty sequences.
  If useSpacingDifficultyFile is set to True, then random timing from SHA-256 hash and
  Normal Distribution for Offset are disabled. Searh for the text "7777A" to see where
  spacing is set from the file, and search for the text "7777B" to see where difficulty
  is set from the file. If both of these are active, then there is a full replay of mainnet
  actions, which can be used for testing Network Weight calculations, but says nothing about
  the probablity response of the simulator. Otherwise, either the spacing or difficulty
  input can be commented out to use one or the other for various test scenarios. numBlocks is
  set by the number of rows in the file. The file also sets the starting block number.

useSpacingDifficultyFile = False
spacing_difficulty_file_name = "spacing_difficulty.txt"       # file name

8. Set useTargetScaling = True to dynamically increase the target during a block.
   Starting with step 16 (or other values), multiply the target by targetScalingFactor,
   set below. This gives a gradual expotential increase in the target if the blocks are
   getting too long. You can also set the targetScalingFactor to 1.0 to disable scaling.
   Used at the top of the step loop to reset the target for that step.

useTargetScaling = False
targetScalingFactor = 1.05
startingStep = 16

9. Reserved

10. Set useWalletGrowth = True to add wallets during a simulation run.
   Uses parameters as described below. Network weight will grow by
   walletGrowthNumWallets * walletGrowthWeight * walletGrowthNumIncrements 
   with total wallet growth given by walletGrowthNumWallets * walletGrowthNumIncrements
   
   Th
   
   

useWalletGrowth = False            # set to cause the number of wallets to grow during the simulation run
walletGrowthStartBlock = 1000      # block to start wallet growth
walletGrowthBlockIncrement = 500   # spacing between blocks of wallet growth
walletGrowthNumWallets = 5000      # number of wallets to grow in each increment
walletGrowthNumIncrements = 10     # number of times to grow wallets
walletGrowthWeight = 500           # weight of each new wallet

