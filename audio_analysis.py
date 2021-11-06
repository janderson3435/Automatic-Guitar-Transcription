import librosa
from scipy.signal.signaltools import wiener
from math import log2, pow
import numpy as np
import scipy as sp
import matplotlib.pyplot as plt
import pandas as pd
import librosa as lr
from librosa.display import waveplot, specshow
from scipy.signal import butter, lfilter 
from moviepy.editor import *


def get_audio(path):

    vid_file_path = path
    aud_file_path = "audio.wav"

    video = VideoFileClip(vid_file_path)
    audio = video.audio 
    audio.write_audiofile(aud_file_path) 

    samples, sampling_rate = librosa.load(aud_file_path, sr = None, mono = True, offset = 0.0, duration = None)
    
    return samples, sampling_rate

def get_rhythm(samples, sampling_rate, visualise):

    hop_length = 1024
    oenv = librosa.onset.onset_strength(y=samples, sr=sampling_rate, aggregate=np.mean, fmax=11025,n_mels= 128) 
    wienered = wiener(oenv)  #Filter the signal
    onsets = librosa.onset.onset_detect(y=samples, sr=sampling_rate, onset_envelope=wienered, delta=0.15, wait= 50) #original
    #onsets = librosa.onset.onset_detect(y=samples, sr=sampling_rate, onset_envelope=wienered, delta=0.15, wait= 20)  # experimental
    times = librosa.times_like(oenv, sr=sampling_rate, hop_length=hop_length)
    beat_times = times[onsets]

    if (visualise):
        plt.figure(figsize=(10, 4))
        plt.plot(times, oenv, label='Onset strength')
        plt.plot(times[onsets], oenv[onsets], 'o', color = 'red')
        plt.xticks(np.arange(0,np.ceil(times[times.size-1])+1))
        #plt.show()

    return beat_times

def get_notes(samples, sampling_rate, beat_times, visualise):
    flags = [] # in case any notes detected are outside of range
    notes = []
    i = 0
    for time in beat_times:    
        freq = get_freq_at_beat_time(samples, sampling_rate, time/2, time/2+0.5)
        if (freq < 60): # likely from noise at start and end, so discard
            flags.append(True) 
        else:
            flags.append(False)
        notes.append(pitch(freq))  # convert frequency to pitch
        i += 1
    
    if (visualise):
        print(notes)

    return notes, flags

def pitch(freq):
    A4 = 440
    C0 = A4*pow(2, -4.75)
    name = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    h = round(12*log2(freq/C0))
    octave = h // 12
    n = h % 12
    return name[n] + str(octave)
    
    
def get_freq_hps(signal, fs):
    signal = np.asarray(signal) + 0.0

    N = len(signal)
    signal -= np.mean(signal)  # remove DC offset

    #  fourier transform windowed signal
    windowed = signal * np.kaiser(N, 100)

    # get harmonic spectrum
    X = np.log(abs(np.fft.rfft(windowed)))
    X -= np.mean(X)

    # downsample sum logs of spectra instead of multiplying
    hps = np.copy(X)
    for h in range(2, 9):  
        dec = sp.signal.decimate(X, h, zero_phase=True)
        hps[:len(dec)] += dec

    # find the peak and interpolate to get a more accurate peak
    i_peak = np.argmax(hps[:len(dec)])
    i_interp = quad_interpolate(hps, i_peak)[0]

    # Convert to equivalent frequency
    return fs * i_interp / N  # Hz

def get_freq_at_beat_time(samples, sampling_rate, beat_start, beat_end):
    # high pass filter
    desired = (0, 0, 1, 1)
    bands = (0, 70, 100, sampling_rate/2.)
    filter_coefs = sp.signal.firls(1001, bands, desired, nyq=sampling_rate/2.)
    filtered_audio = sp.signal.filtfilt(filter_coefs, [1], samples)

    # analyze the audio between time_start and time_end
    time_seconds = np.arange(filtered_audio.size, dtype=float) / sampling_rate
    audio_to_analyze = filtered_audio[(time_seconds >= beat_start) &
                                    (time_seconds <= beat_end)]

    frequency = get_freq_hps(audio_to_analyze, sampling_rate)

    return(frequency)

def quad_interpolate(f, x):
    # interpolation function
    x = int(x)
    xv = 1/2. * (f[x-1] - f[x+1]) / (f[x-1] - 2 * f[x] + f[x+1]) + x
    yv = f[x] - 1/4. * (f[x-1] - f[x+1]) * (xv - x)
    return (xv, yv)