import numpy as np
import librosa as lr
import midiutil
from midiutil import MIDIFile

def create_tab(beat_times, tempo_track, note_positions, length, time_sig):

    if (time_sig == 1):
        bar_div = 5 # notes in bar + 1  

    tab_size  = int(length*6+length/bar_div) # 6 = max beats per second 
    tablature = np.full((6,tab_size), '-')       # create with space for bars, check for clashes later
    
    for i in range(0,tab_size):
        if (i % bar_div == 0):
            for j in range(0,6): 
                tablature[j][i] = '|'

    i = 0    
    for beat in beat_times:
        index = int(beat*6/2)               # divide by two since beats double time precision
        offset = int(beat/(2*bar_div))        #offset by number of bar divs to this point
        index = index+offset
        note = note_positions[i]
        string = note[0]
        fret = note[1]
        if (tablature[string][index] == '|'): 
            tablature[string][index + 1] = fret
        else:
            tablature[string][index] = fret
        i += 1
    
    return (tablature)

def print_tab(tab, length):
    line_size = 60
    file = open('output.txt', 'w')
    for i in range (line_size, int(length*6*2), line_size): 
        for string in tab:
            for j in string[i-line_size:i]:
                file.write(j)
            file.write('\n')
        file.write('\n')
        print()
    file.close()
    return

# tab array will be as follows:
#1  ----|-------
#2  3---|-------
#3  ----|-4-----
#4  ----|------2
#5  ----|-------
#6  ----|-------
#  each dash representing minimum time between notes - 6 beats per second, | representing bars

def create_midi(beat_times, tempo_track, notes, length, time_sig):
    midi = MIDIFile(1)
    i = 0
    for note in notes:
        note = lr.note_to_midi(note)
        midi.addNote(track=0, channel=0, pitch=note, time=beat_times[i], duration=4, volume=64)
        i += 1
    with open("midi_out.mid", "wb") as output_file:
        midi.writeFile(output_file)