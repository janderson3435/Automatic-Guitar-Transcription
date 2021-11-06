import matplotlib
import numpy as np
from eval_funcs import *
from main import *
import timeit

start = timeit.default_timer()

vid_path = "source videos/c major scale slow.mov"
main(vid_path,'E,A,D,G,B,E', False)             # comment out if anthemscore, saves time

tab_path = 'Correct tabs/c major.txt'
output_path = 'output.txt'
#output_path = 'anthemscore tabs/anthem octaves.txt'

score, num = linewiseAlignment(tab_path, output_path)
print('Pitch Score: ', score)
print('Pitch score per note: ', score/num)

r_score, diff = rhythm_score(tab_path, output_path)
print('\nRhythm Score: ', r_score)
print('Rhythm Score per note: ', r_score/num)
print('Difference: ', diff)

print('\nNumber of notes: ', num)
stop = timeit.default_timer()

print('\nTime: ', stop - start)  