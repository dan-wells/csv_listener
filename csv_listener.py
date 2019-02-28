import tkinter as tk
import csv
import sys
#from play_wav import play_wav
import pyaudio
import wave
from tkinter import filedialog

script, csv_file = sys.argv

class CsvListener(tk.Tk):
    def __init__(self, title="CSV Listener - {0}".format(csv_file), *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        self.title(title)
        #self.geometry('800x800')

        with open(csv_file) as inf:
            reader = csv.DictReader(inf)
            csv_header = reader.fieldnames
            csv_rows = [i for i in reader]
        col_max_lens = {}
        for col in csv_header:
            col_max_lens[col] = max(max([len(i[col]) for i in csv_rows]), len(col))

        master_frame = tk.Frame(self)
        master_frame.pack(anchor=tk.NW)

        frame1 = tk.Canvas(master_frame)
        frame1.pack(anchor=tk.NW)

        for i, col in enumerate(csv_header):
            col_val = tk.Label(frame1, width=col_max_lens[col], padx=7, pady=7, relief=tk.RIDGE, text=col)
            col_val.pack(anchor=tk.NW, side=tk.LEFT)
        if 'Exclude' not in csv_header:
            exclude_idx = len(csv_header) + 1
            col_val = tk.Label(frame1, padx=7, pady=7, relief=tk.RIDGE, text='Exclude')
            col_val.pack(anchor=tk.NW, side=tk.LEFT)
            exclude_width = col_val.winfo_width()
            play_idx = exclude_idx + 1
        else:
            play_idx = len(csv_header) + 1
        col_val = tk.Label(frame1, padx=7, pady=7, relief=tk.RIDGE, text='Play audio')
        col_val.pack(anchor=tk.NW, side=tk.LEFT)
        play_width = col_val.winfo_width()

        frame2 = tk.Frame(master_frame)
        frame2.pack(anchor=tk.NW, fill=tk.X)

        vsbar = tk.Scrollbar(frame2)
        vsbar.pack(side=tk.RIGHT, fill=tk.Y)

        canvas = tk.Canvas(frame2, yscrollcommand=vsbar.set)
        canvas.pack(anchor=tk.NW, fill=tk.X)

        vsbar.config(command=canvas.yview)

        frame = tk.Frame(canvas)
        frame.rowconfigure(1, weight=1)
        frame.columnconfigure(1, weight=1)

        self.exclude_vars = {}
        for r, row in enumerate(csv_rows):
            full_row = tk.Canvas(frame)
            full_row.pack(anchor=tk.NW)
            # add a warning about any duplicated rows: would need to have checkbutton
            # selected for every instance to have any of them excluded in the end
            exclude_var = tk.BooleanVar()
            self.exclude_vars[row['File Name']] = exclude_var
            exclude_button = tk.Checkbutton(full_row, padx=7, pady=7, relief=tk.RIDGE, variable=exclude_var, width=3)
            for c, col in enumerate(row):
                if col == 'Exclude':
                    exclude_button.pack(anchor=tk.NW, side=tk.LEFT)
                    if row['Exclude'] == 'x':
                        #self.exclude_vars[row['File Name']].set(1)
                        exclude_button.select()
                else:
                    col_val = tk.Label(full_row, width=col_max_lens[col], padx=7, pady=7, relief=tk.RIDGE, text=row[col])
                    col_val.pack(anchor=tk.NW, side=tk.LEFT)
            if 'Exclude' not in csv_header:
                exclude_button.pack(anchor=tk.NW, side=tk.LEFT)
            play_button = tk.Button(full_row, padx=7, pady=7, relief=tk.RIDGE, text='Play', 
                                    command=lambda x=row['File Name']: self.play_wav(x))
            play_button.pack(anchor=tk.NW, side=tk.LEFT)

        canvas.create_window(0, 0, anchor=tk.NW, window=frame)
        frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))
        
        num_rows = len(csv_rows)
        disp_rows = 10
        if num_rows > disp_rows:
            canvas_height = (frame.winfo_height() / num_rows) * disp_rows
        else:
            canvas_height = frame.winfo_height()
        canvas.configure(height=canvas_height)

        ### File operations
        frame3 = tk.Frame(master_frame)
        frame3.pack(anchor=tk.NW, fill=tk.X)

        def load_file():
            load_fn = filedialog.askopenfilename(initialdir=".", title="Select CSV file")
            print(load_fn)
        load_button = tk.Button(frame3, text="Load file", command=load_file)
        load_button.pack(anchor=tk.NW)
        
        def save_file():
            save_fn = filedialog.asksaveasfilename(initialdir=".", title="Save to CSV file")
            with open(save_fn, 'w') as outf:
                if 'Exclude' not in csv_header:
                    csv_header.append('Exclude')
                writer = csv.DictWriter(outf, fieldnames=csv_header)
                writer.writeheader()
                for row in csv_rows:
                    row['Exclude'] = self.exclude_vars[row['File Name']].get()
                    writer.writerow(row)
        save_button = tk.Button(frame3, text="Save file", command=save_file)
        save_button.pack(anchor=tk.NW)

        master_frame.update_idletasks()
        print(f'master_frame: width {master_frame.winfo_width()}, height {master_frame.winfo_height()}')
        self.minsize(master_frame.winfo_width(), master_frame.winfo_height())

    def play_wav(self, wav_filename, chunk_size=1024):
        '''
        Play (on the attached system sound device) the WAV file
        named wav_filename.
        '''

        try:
            print('Trying to play file ' + wav_filename)
            wf = wave.open(wav_filename, 'rb')
        except IOError as ioe:
            sys.stderr.write('IOError on file ' + wav_filename + '\n' + \
            str(ioe) + '. Skipping.\n')
            return
        except EOFError as eofe:
            sys.stderr.write('EOFError on file ' + wav_filename + '\n' + \
            str(eofe) + '. Skipping.\n')
            return

        # Instantiate PyAudio.
        p = pyaudio.PyAudio()

        # Open stream.
        stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
            channels=wf.getnchannels(),
            rate=wf.getframerate(),
            output=True)

        data = wf.readframes(chunk_size)
        while len(data) > 0:
            stream.write(data)
            data = wf.readframes(chunk_size)

        # Stop stream.
        stream.stop_stream()
        stream.close()

        # Close PyAudio.
        p.terminate()

if __name__ == "__main__":
    csv_listener = CsvListener()
    #csv_listener.after(5000, lambda x=csv_listener.exclude_vars:print([i for i in x if x[i].get() == 1]))
    #csv_listener.after(6000, lambda x=csv_listener.exclude_vars:print([i for i in x if x[i].get() == 0]))
    csv_listener.mainloop()
    
    #print([i for i in exclude_vars if exclude_vars[i]==1])
    #print([i for i in csv_listener.exclude_vars if csv_listener.exclude_vars[i].get() == 1])

