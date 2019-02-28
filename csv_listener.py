import argparse
import csv
import sys
import wave
import os
if sys.version_info[0] == 3:
    import tkinter as tk
    from tkinter import filedialog
elif sys.version_info[0] == 2:
    import Tkinter as tk
    import tkFileDialog as filedialog
if os.name == 'nt':
    import winsound
elif os.name == 'posix':
    try:
        import pyaudio
    except ImportError as impe:
        sys.stderr.write(str(impe) + '\n' \
        'Module pyaudio not available, audio playback will not work on Linux.\n' + \
        'Audio playback available on Windows through standard library module winsound.\n')

#script, csv_file, out_file  = sys.argv
#script, csv_file = sys.argv

class CsvListener(tk.Tk):
    def __init__(self, csv_file, csv_out=None, disp_rows=10, fn_exclude='Exclude', fn_file_name='File Name', audio_path=None, win_title="CSV Listener", *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        self.win_title = win_title
        self.csv_file = csv_file
        self.csv_out = csv_out
        self.disp_rows = disp_rows
        self.fn_exclude = fn_exclude
        self.fn_file_name = fn_file_name
        self.audio_path = audio_path

        # set title on root window
        self.title("{0} - {1}".format(self.win_title, self.csv_file))
        # make floating window
        self.attributes('-type', 'utility')

        master_frame = tk.Frame(self)
        master_frame.pack(anchor=tk.NW)

        # get various info from csv_file
        self.read_csv()

        frame1 = tk.Canvas(master_frame)
        frame1.pack(anchor=tk.NW)

        # draw header row into frame1
        self.draw_header(frame1)

        frame2 = tk.Frame(master_frame)
        frame2.pack(anchor=tk.NW, fill=tk.X)

        # want to be able to scroll through many rows but always see
        # header: next bunch of tk objects is setting that up
        vsbar = tk.Scrollbar(frame2)
        vsbar.pack(side=tk.RIGHT, fill=tk.Y)

        canvas = tk.Canvas(frame2, yscrollcommand=vsbar.set)
        canvas.pack(anchor=tk.NW, fill=tk.X)

        vsbar.config(command=canvas.yview)

        frame = tk.Frame(canvas)
        frame.rowconfigure(1, weight=1)
        frame.columnconfigure(1, weight=1)

        # this puts data into the frame
        self.draw_rows(frame)

        # this creates the scrollable view over canvas in frame
        canvas.create_window(0, 0, anchor=tk.NW, window=frame)
        frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))
        
        num_rows = len(self.csv_rows)
        if num_rows > self.disp_rows:
            canvas_height = (frame.winfo_height() / num_rows) * self.disp_rows
        else:
            canvas_height = frame.winfo_height()
        canvas.configure(height=canvas_height)

        ### File operations
        frame3 = tk.Frame(master_frame)
        frame3.pack(anchor=tk.NW, fill=tk.X)

        load_button = tk.Button(frame3, text="Load file", command=self.load_file, state=tk.DISABLED)
        load_button.pack(anchor=tk.NW)
        
        save_button = tk.Button(frame3, text="Save file", command=self.save_dialog)
        save_button.pack(anchor=tk.NW)

        # make sure window shows all frames
        master_frame.update_idletasks()
        self.minsize(master_frame.winfo_width(), master_frame.winfo_height())

    def read_csv(self):
        with open(self.csv_file) as inf:
            reader = csv.DictReader(inf)
            self.csv_header = reader.fieldnames
            self.csv_rows = []
            #self.csv_rows = [i for i in reader]
            for row in reader:
                # concatenate audio paths
                if self.audio_path is not None:
                    wav_file = os.path.join(self.audio_path, row[self.fn_file_name])
                    row[self.fn_file_name] = wav_file 
                # convert existing exclude column to bools
                if self.fn_exclude in self.csv_header:
                    if row[self.fn_exclude] == 'True':
                        row[self.fn_exclude] = True
                    else:
                        row[self.fn_exclude] = False
                self.csv_rows.append(row)
        self.col_max_lens = {}
        for col in self.csv_header:
            self.col_max_lens[col] = max(max([len(str(i[col])) for i in self.csv_rows]), len(col))

    def draw_header(self, frame):
        for i, col in enumerate(self.csv_header):
            col_val = tk.Label(frame, width=self.col_max_lens[col], padx=7, pady=7, relief=tk.RIDGE, text=col)
            col_val.pack(anchor=tk.NW, side=tk.LEFT)
        if self.fn_exclude not in self.csv_header:
            exclude_idx = len(self.csv_header) + 1
            col_val = tk.Label(frame, padx=7, pady=7, relief=tk.RIDGE, text=self.fn_exclude)
            col_val.pack(anchor=tk.NW, side=tk.LEFT)
            self.exclude_width = col_val.winfo_width()
            play_idx = exclude_idx + 1
        else:
            play_idx = len(self.csv_header) + 1
        col_val = tk.Label(frame, padx=7, pady=7, relief=tk.RIDGE, text='Play audio')
        col_val.pack(anchor=tk.NW, side=tk.LEFT)
        self.play_width = col_val.winfo_width()

    def draw_rows(self, frame):
        # this keeps state of all exclude checkbuttons
        self.exclude_vars = {}
        for r, row in enumerate(self.csv_rows):
            full_row = tk.Canvas(frame)
            full_row.pack(anchor=tk.NW)
            # TODO add warning about any duplicated rows: would need to have checkbutton
            # selected for every instance to have any of them excluded in the end
            exclude_var = tk.BooleanVar()
            self.exclude_vars[row[self.fn_file_name]] = exclude_var
            exclude_button = tk.Checkbutton(full_row, padx=7, pady=7, relief=tk.RIDGE, variable=exclude_var, width=3)
            for c, col in enumerate(row):
                if col == self.fn_exclude:
                    exclude_button.pack(anchor=tk.NW, side=tk.LEFT)
                    if row[self.fn_exclude]:
                        exclude_button.select()
                else:
                    col_val = tk.Label(full_row, width=self.col_max_lens[col], padx=7, pady=7, relief=tk.RIDGE, text=row[col])
                    col_val.pack(anchor=tk.NW, side=tk.LEFT)
            if self.fn_exclude not in self.csv_header:
                exclude_button.pack(anchor=tk.NW, side=tk.LEFT)
            play_button = tk.Button(full_row, padx=7, pady=7, relief=tk.RIDGE, text='Play', 
                                    command=lambda x=row[self.fn_file_name]: self.play_wav(x))
            play_button.pack(anchor=tk.NW, side=tk.LEFT)

    def load_file(self):
        load_fn = filedialog.askopenfilename(initialdir=".", title="Select CSV file")
        pass

    def save_file(self, window=None):
        with open(self.csv_out, 'w') as outf:
            if self.fn_exclude not in self.csv_header:
                self.csv_header.append(self.fn_exclude)
            writer = csv.DictWriter(outf, fieldnames=self.csv_header, lineterminator='\n')
            writer.writeheader()
            for row in self.csv_rows:
                row[self.fn_exclude] = self.exclude_vars[row[self.fn_file_name]].get()
                writer.writerow(row)
        if window is not None:
            window.destroy()

    def save_as(self, window=None):
        self.csv_out = filedialog.asksaveasfilename(initialdir=".", title="Save to CSV file")
        # hitting cancel returns an empty tuple, handle that
        if self.csv_out:
            self.save_file(window)
        else:
            self.csv_out = None

    def save_dialog(self):
        if self.csv_out is None:
            self.save_as()
        else:
            # popup to confirm saving over named csv_out
            save_confirm = tk.Toplevel()
            save_confirm.wm_title("Confirm save")
            save_confirm.attributes('-type', 'dialog')
            l = tk.Label(save_confirm, text="Save to {0}?".format(self.csv_out))
            l.pack()
            button_frame = tk.Frame(save_confirm)
            button_frame.pack()
            y_btn = tk.Button(button_frame, text="Save", command=lambda x=save_confirm:self.save_file(x))
            y_btn.pack(side=tk.LEFT)
            s_btn = tk.Button(button_frame, text="Save As", command=lambda x=save_confirm:self.save_as(x))
            s_btn.pack(side=tk.LEFT)
            n_btn = tk.Button(button_frame, text="Cancel", command=save_confirm.destroy)
            n_btn.pack(side=tk.LEFT)

    def play_wav(self, wav_fn, chunk_size=1024):
        '''
        Play (on the attached system sound device) the WAV file
        named wav_fn.
        '''
        # windows playback through winsound in standard library
        if os.name == 'nt':
            try:
                winsound.PlaySound(wav_fn, winsound.SND_ASYNC)
            except IOError as ioe:
                sys.stderr.write('IOError on file ' + wav_fn + '\n' + \
                str(ioe) + '. Skipping.\n')
                return
        # or stereotypically obnoxious linux audio solution
        elif os.name == 'posix':
            try:
                print('Trying to play file ' + wav_fn)
                wf = wave.open(wav_fn, 'rb')
            except IOError as ioe:
                sys.stderr.write('IOError on file ' + wav_fn + '\n' + \
                str(ioe) + '. Skipping.\n')
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
    parser = argparse.ArgumentParser(description="GUI tool for auditing lists of audio files.")
    parser.add_argument('csv_file', help="CSV file listing audio files to audit")
    parser.add_argument('--csv_out', help="Output filename for modified CSV", default=None)
    parser.add_argument('--disp_rows', help="Number of rows to show at once", default=10, type=int)
    parser.add_argument('--fn_exclude', help="Field for exclude decisions. Will be added if not present", default='Exclude')
    parser.add_argument('--fn_file_name', help="Field containing file name", default='File Name')
    parser.add_argument('--audio_path', help="Path to audio files, use if full path not in CSV", default=None)
    args = parser.parse_args()
    args_dict = vars(args)

    csv_listener = CsvListener(**args_dict)
    csv_listener.mainloop()
    
