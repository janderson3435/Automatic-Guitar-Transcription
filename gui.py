import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from tkinter import filedialog
from main import *

root= tk.Tk()

canvas1 = tk.Canvas(root, width = 800, height = 800)
canvas1.pack()

label1 = tk.Label(root, text='Guitar To Tab Transcriber')
label1.config(font=('calibri', 20))
canvas1.create_window(400, 50, window=label1)

# Function for opening the
# file explorer window
def browseFiles():
    entry1.delete(0, 'end')
    filename = filedialog.askopenfilename(initialdir = "/",title = "Select a File",filetypes =(("Video files", "*.mov*"), ("all files", "*.*")))
    entry1.insert(tk.END, filename) 


label_e1 = tk.Label(root, text='Path to video: ')
canvas1.create_window(400, 80, window=label_e1)   
entry1 = tk.Entry (root)
canvas1.create_window(400, 100, window=entry1) 

button_explore = tk.Button(root, text = "Browse Files", command = browseFiles)
canvas1.create_window(510, 100, window=button_explore)

label_e2 = tk.Label(root, text='Tuning: ')
canvas1.create_window(400, 120, window=label_e2)   
entry2 = tk.Entry (root)
entry2.insert(0, 'E,A,D,G,B,E')
canvas1.create_window(400, 140, window=entry2) 

visualise = tk.BooleanVar()
visualise.set(False)

check1 = tk.Checkbutton(root, text='Visualise',variable=visualise)
canvas1.create_window(510, 180, window=check1)

def transcribe():
    tuning = entry2.get()
    path = entry1.get()
    v = visualise.get()
    main(path, tuning, v)
    f = open('output.txt','r')
    t.delete("1.0",tk.END)
    lines = f.readlines()

    i=1
    for line in lines:
        t.insert(str(i) + '.0', line)
        i+=1
    f.close()


button_transcribe = tk.Button (root, text='Perform transcription',command=transcribe, bg='lightsteelblue2', font=('calibri', 11, 'bold')) 
canvas1.create_window(400, 180, window=button_transcribe)

button_quit = tk.Button (root, text='Exit Application', command=root.destroy, bg='red', font=('calibri', 11, 'bold'))
canvas1.create_window(400, 220, window=button_quit)

t = tk.Text(root)
canvas1.create_window(400, 450, window=t)

root.mainloop()