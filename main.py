from audio_analysis import *
from fretboard_identification import *
from hand_detection import *
from midi import *
import random
import os


def main(path, tuning, visualise):
    
    string_letters = [['E4', 'F4', 'F#4', 'G4', 'G#4', 'A4', 'A#4', 'B4', 'C5', 'C#5', 'D5', 'D#5'],
                ['B3', 'C4', 'C#4','D4','D#4','E4','F4','F#4', 'G4','G#4','A4','A#4'],
                ['G3', 'G#3','A3', 'A#3', 'B3', 'C4', 'C#4','D4','D#4','E4','F4','F#4'],
                ['D3', 'D#3','E3', 'F3', 'F#3', 'G3', 'G#3','A3', 'A#3', 'B3', 'C4', 'C#4'],
                ['A2', 'A#2', 'B2', 'C3', 'C#3', 'D3', 'D#3', 'E3', 'F3', 'F#3', 'G3', 'G#3'],
                ['E2', 'F2', 'F#2', 'G2', 'G#2', 'A2', 'A#2', 'B2', 'C3', 'C#3', 'D3', 'D#3']]
    # EXTENSION
    # Adjust for different tunings
    letters  = tuning.upper().split(',')

    def rotate(l, n):
        return l[n:] + l[:n]

    i = 0
    for letter in letters: # for each inputted letter
        # first flag if there is sharp
        sharp = False
        if len(letter) != 1:
            # check edge case of B# = C and E# = F
            if (not(letter == 'B' or letter == 'E')):
                sharp = True

        # search the relevant string in the database for matching letter
        j = 0
        for s_letter in string_letters[5-i]:
            if (s_letter[0] == letter[0]):
                if sharp:
                    j += 1
                    
                string_letters[5-i] = rotate(string_letters[5-i], j)

                # deal with octaves
                if (j > 6): # if moving down is smaller, presume this has happened
                    for k in range(0, 12-j):
                        length = len(string_letters[5-i][k])
                        octave = chr(ord(string_letters[5-i][k][length-1])-1)
                        string_letters[5-i][k] = string_letters[5-i][k][:length-1] + octave

                else: # tuned up
                    for k in range(12-j, 12):
                        length = len(string_letters[5-i][k])
                        octave = chr(ord(string_letters[5-i][k][length-1])+1)
                        string_letters[5-i][k] = string_letters[5-i][k][:length-1] + octave

                break
            j += 1
        i += 1    


    # Audio analysis
    samples, sampling_rate = get_audio(path)
    beats = get_rhythm(samples, sampling_rate, visualise)
    notes, flags = get_notes(samples, sampling_rate, beats, visualise)


    i=0
    for flag in flags:  # deleting spurious notes
        if (flag):
            if(i >= len(notes)):
                continue
            del notes[i]

            beat_list = beats.tolist()   # np arrays are fixed size
            del beat_list[i]
            del beats
            beats = np.array(beat_list)

        i += 1

    # Video analysis

    cap = cv2.VideoCapture(path)
    tot_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = 30
    length = tot_frames/fps

    frets, strings, transform_pts1, transform_pts2 = find_frets(cap,int(tot_frames/2)) # take middle frame where guitar should be in optimal position
    top, bottom = zip(*strings)

    #transformed_img = perspective_transform(get_img(cap, 0), transform_pts1, transform_pts2)
    k = 0
    final_note_positions = []
    for beat in beats: # get position of hand at each beat from audio phase

        ratio = beat/(2*length)
        frame_num = int(ratio*tot_frames)

        beat_frame = get_img(cap, frame_num)
       
        transformed_img = perspective_transform(beat_frame, transform_pts1, transform_pts2)

        hand_intercepts = get_hand_intercepts(top, bottom, transformed_img)

        #find possible hand postions 
        def find_potential_positions(hand_intercepts):
            positions = []
            hand_top_intercepts, hand_bottom_intercepts = zip(*hand_intercepts)
            lowest_poss_fret = 0
            highest_poss_fret = 11
            for i in range(0,6): # remember 0th is 1st string 
                for j in range(0,11):
                    if (hand_top_intercepts[i] < frets[j]):
                        lowest_poss_fret = j
                        break
                for j in range(0,11):
                    if (hand_bottom_intercepts[i] < frets[j]):
                        highest_poss_fret = j
                        break
                for j in range(lowest_poss_fret, highest_poss_fret):
                    positions.append((i,j))

                positions.append((i,0))

            return (positions)
            
        possible_hand_frets = find_potential_positions(hand_intercepts)
        
        # from this we can work out possible places where notes are being played, from database of notes 
        # Remember: can play note at pos 0 at any point (open string), otherwise can play any note in range hand_top_pos, hand_bot_pos

        note = notes[k]
        possible_note_positions = []
        for (string, fret) in possible_hand_frets:
            if string_letters[string][fret] == note:
                    possible_note_positions.append((string,fret)) # string 0 == 1st string (high E)

        # if not found, try same note different octaves
        if(len(possible_note_positions) == 0):
            flag_found = False
            for octave in range(2,4): # maximum octave differences
                octave_note = note[:len(note)-1] + str(octave)
                for (string, fret) in possible_hand_frets:
                    if string_letters[string][fret] == octave_note:
                        possible_note_positions.append((string,fret))
                        flag_found = True
                        break
                if flag_found:
                    break

        # if still not found, try closest to the previous note found
        if(len(possible_note_positions) == 0):
            if (k == 0):
                # just find first instance 
                for i in range(0,6):
                    for j in range(0,11):
                        if(string_letters[i][j] == note):
                            possible_note_positions.append((i,j))

            else:
                prev_s, prev_f = final_note_positions[k-1]    # within feasible distance so any string but within 4 frets - eliminates all but open string clashes 
                for i in range(0,6):
                    for j  in range(-4, 4):
                        if ((prev_f+j < 0) | (prev_f+j > 11)):
                            continue
                        elif string_letters[i][prev_f+j] == note:
                                possible_note_positions.append((i,prev_f+j))

        
        index = 0
        if(len(possible_note_positions) == 0): # if still not found, brute force search
            found = False
            for i in range(0,6):
                for j in range(0,11):
                    if  string_letters[i][j] == note:
                        final_note_positions.append((i,j))
                        found = True
                        break
            # if still not found, note not in range of guitar, drop it
            if not(found):
                del notes[k]
                beat_list = beats.tolist()   
                del beat_list[k]
                del beats
                beats = np.array(beat_list)
                k -= 1
        else:
            if(len(possible_note_positions) > 1):
                index = random.randint(0, len(possible_note_positions)-1)
                final_note_positions.append(possible_note_positions[index])
            else:
                final_note_positions.append(possible_note_positions[index])

        k += 1
    
    # visualising 
    if(visualise):
        length_pix = 1000
        width_pix = 400


        i = 0
        for centre in bottom: 
            x1 = centre
            x2 = top[i]
            cv2.line(transformed_img, (int(x1), 1000),(int(x2),0), (0,0,255),5)
            i = i+1
        for fret in frets:
            cv2.line(transformed_img,(0,int(fret)),(width_pix,int(fret)),(0,0,255),5)


        plt.imshow(cv2.cvtColor(transformed_img, cv2.COLOR_BGR2RGB))
        
        plt.show()

    tempo, tempo_track = librosa.beat.beat_track(samples, sampling_rate)

    time_sig = 1 # coding time signatures as fractions
    tab = create_tab(beats, tempo_track, final_note_positions, length, time_sig) 
    print_tab(tab, length)
    create_midi(beats, tempo_track, notes, length, time_sig)