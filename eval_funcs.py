import os,sys,re
import numpy as np
from munkres import Munkres
#### PITCH ####
insertion_pen = -1
deletion_pen = -25
match_reward = 100
mismatch_pen = -25

def max(matchCost, delCost, inCost, mismatchCost):
    Max = matchCost
    index = 0 
    if(mismatchCost > Max):
        Max = mismatchCost
        index = 3
    if(delCost > Max):
        Max = delCost
        index = 1
    if(inCost > Max):
        Max = inCost
        index = 2
   
    return index   

def globalAlignment(seq1, seq2):
   
    lenSeq1 = len(seq1)
    lenSeq2 = len(seq2)

    score = [[0 for i in range(lenSeq2+1)] for j in range(lenSeq1+1)] # represent score matrix
    
    backtrace = [[' ' for x in range(lenSeq2+1)] for y in range(lenSeq1+1)]  # contains information about which operation is chosen

    score[0][0] = 0
    #backtrace[0][0] = 'N'

    for i in range(lenSeq1+1):
    
        score[i][0] = deletion_pen
        backtrace[i][0] = 'D'       # 'D' is used for delete operation
    
    for i in range(lenSeq2+1):
    
        score[0][i] = insertion_pen
        backtrace[0][i] = 'I'       # 'I' represents insertion

    for i in range(1,lenSeq1+1):
        for j in range(1,lenSeq2+1):
            matchScore = 0
            if seq1[i-1] == seq2[j-1]:  
                matchScore = score[i-1][j-1] + match_reward
                backtrace[i][j] = 'M'  # 'M' represents match  
        
            delScore = score[i-1][j] + deletion_pen
            inScore = score[i][j-1] + insertion_pen
            mismatchScore = score[i-1][j-1] + mismatch_pen
            maxScore = max(matchScore, delScore, inScore, mismatchScore)
            if( maxScore == 1):
                score[i][j] = delScore
                backtrace[i][j] = 'D'
            elif( maxScore == 2):
                score[i][j] = inScore
                backtrace[i][j] = 'I'
            elif( maxScore == 3):
                score[i][j] = mismatchScore
                backtrace[i][j] = 'N'
            elif maxScore == 0:
                score[i][j] = matchScore
                backtrace[i][j] = 'M'
            else:
                print ("Problem in scoring")


    row = lenSeq1
    col = lenSeq2
    alSeq1 = ""
    alSeq2 = ""
    while row > -1 and col > -1:
        opCode = backtrace[row][col]
        if opCode == 'I':
            if col > 0: 
                alSeq2 = alSeq2 + seq2[col-1]
            else: 
                alSeq2 = alSeq2 + "-"
      
            alSeq1 = alSeq1 + "-"    
            col = col - 1
        elif opCode == 'D':

            if row > 0:
                alSeq1 = alSeq1 + seq1[row-1]
            else: 
                alSeq1 = alSeq1 + "-"
            alSeq2 = alSeq2 + "-"
            row = row - 1
        elif opCode == 'N':
            alSeq1 = alSeq1 + seq1[row-1]
            alSeq2 = alSeq2 + seq2[col-1]
            row = row - 1
            col = col - 1
        elif opCode == 'M':
            if row > 0:
                alSeq1 = alSeq1 + seq1[row-1]
            else: 
                alSeq1 = alSeq1 + "-"
            if col > 0:    
                alSeq2 = alSeq2 + seq2[col-1]
            else:
                alSeq2 = alSeq2 + "-"
            row = row - 1
            col = col - 1            
        else:
            print ("Problem in backtracing")
    
  
    alSeq1 = alSeq1[::-1]
    alSeq1 = alSeq1[1:]
    alSeq2 = alSeq2[::-1]
    alSeq2 = alSeq2[1:]
   
    return (score[lenSeq1][lenSeq2], alSeq1, alSeq2)

def format_line(line):

    newline = []
    for i in range(len(line)):
        if not(line[i] == '-' or line[i] == '|' or line[i] == ' ' or line[i] == '\n'):
            newline.append(line[i])

    return newline


def linewiseAlignment(correct_path, output_path):
    note_num = 0
    total = 0
    output = open(output_path, 'r')
    output_lines = output.readlines()

    correct_file = open(correct_path, 'r')
    correct_lines = correct_file.readlines()

    for i, line in enumerate(output_lines):  # get score for each individual string, sum together
        correct = correct_lines[i]
        line1 = format_line(line)# format both tabs so dashes are ignored (only care about pitch not rhythm)
        correct1 = format_line(correct)

        note_num += len(correct1)
        score, aligned1, aligned2 = globalAlignment(line1, correct1)
        total += score
        i += 1

    correct_file.close()
    output.close()
    return total, note_num


#### RHYTHM ####
def squash(lines):
    # squash tab into single line to make it easier to work with
    new = []
    length_lines = len(lines) - ((len(lines)+1) % 7)
 
    for i in range(0, length_lines, 7):
        
        for k in range(0, len(lines[i])):
            flag = True
            for j in range(0,6):
                if not(lines[i+j][k] == '-'or lines[i+j][k] == '|' or lines[i+j][k] == ' ' or lines[i+j][k] == '\n'):
                    new.append('1')
                    flag = False  
                    
            if flag:
                if not(lines[i+j][k] == '|' or lines[i+j][k] == ' ' or lines[i+j][k] == '\n'):
                    new.append('-')

    return new

def rhythm_score(correct_path, output_path):
    output = open(output_path, 'r')
    output_lines = output.readlines()

    correct_file = open(correct_path, 'r')
    correct_lines = correct_file.readlines()

    correct1 = squash(correct_lines)
    output1 = squash(output_lines)

    correct_indices = []
    for i in range(len(correct1)):
        if correct1[i] == '1':
            correct_indices.append(i)

    output_indices = []
    for i in range(len(output1)):
        if output1[i] == '1':
            output_indices.append(i)

    # Assign one index to another such that the distance between them is minimised
    # First compute distance table
    distances = np.empty((len(correct_indices), len(output_indices)))
    for i in range(len(correct_indices)):
        for j in range(len(output_indices)):
            distances[i][j] = abs(correct_indices[i]-output_indices[j])

    # Use munkres/hungarian algorithm to solve assignment problem
    m = Munkres() 
    
    if(distances.shape[0] > distances.shape[1]):
        indices = m.compute(distances.T)
    else:
        indices = m.compute(distances)

    # Compute rhythm score
    tot = 0
    for (i,j) in indices:
        score = 5 - abs(i-j)
        if (score < 0):
            score = 0
        
        tot += score

    len_difference =  len(correct_indices) - len(output_indices) 
    # Penalise if it predicts too many, as then score higher

    diff_pen = 1 + len_difference/10
    if diff_pen < 0:
        diff_pen = 0
    if (len_difference < 0):
        tot *= diff_pen
    
    
    return(tot, len_difference)