import argparse
import csv
import os
import sys
import wave

# gui toolkit
if sys.version_info[0] == 3:
    import tkinter as tk
    from tkinter import filedialog
    from tkinter import messagebox
elif sys.version_info[0] == 2:
    import Tkinter as tk
    import tkFileDialog as filedialog
    import tkMessageBox as messagebox

# audio modules
if os.name == 'nt':
    import winsound
elif os.name == 'posix':
    try:
        import pyaudio
    except ImportError as impe:
        sys.stderr.write(str(impe) + '\n' \
        'Module pyaudio not available, audio playback will not work on Linux.\n' + \
        'Audio playback available on Windows through standard library module winsound.\n')

class CsvListener(tk.Tk):
    def __init__(self, csv_file, audio_path=None, do_exclude=False, do_comment=False, 
                 fn_file_name='File Name', fn_exclude='Exclude', fn_comment='Comment',
                 disp_rows=10, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        self.csv_file = csv_file
        self.audio_path = audio_path
        self.do_exclude = do_exclude
        self.do_comment = do_comment
        self.fn_file_name = fn_file_name
        self.fn_exclude = fn_exclude
        self.fn_comment = fn_comment
        self.disp_rows = disp_rows
        # default saving to original file
        self.csv_out = csv_file
        # set title on root window
        self.title("CSV Listener - {0}".format(self.csv_file))

        master_frame = tk.Frame(self)
        master_frame.pack(anchor=tk.NW)

        # get various info from csv_file
        self.read_csv()

        #header_frame = tk.Canvas(master_frame)
        #header_frame.pack(anchor=tk.NW)

        # draw header row into header_frame
        self.draw_header(master_frame)

        rows_frame = tk.Frame(master_frame)
        rows_frame.pack(anchor=tk.NW, fill=tk.X)

        # want to be able to scroll through many rows but always see
        # header: next bunch of tk objects is setting that up
        vsbar = tk.Scrollbar(rows_frame)
        vsbar.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_canvas = tk.Canvas(rows_frame, yscrollcommand=vsbar.set)
        scroll_canvas.pack(anchor=tk.NW, fill=tk.X)
        vsbar.config(command=scroll_canvas.yview)
        scroll_frame = tk.Frame(scroll_canvas)

        # this puts data into the frame
        self.draw_rows(scroll_frame)

        # this creates the scrollable view over scroll_frame in scroll_canvas
        scroll_canvas.create_window(0, 0, anchor=tk.NW, window=scroll_frame)
        scroll_frame.update()
        scroll_canvas.config(scrollregion=scroll_canvas.bbox("all"))
        
        # limit view to disp_rows at once
        num_rows = len(self.csv_rows)
        if num_rows > self.disp_rows:
            canvas_height = (scroll_frame.winfo_height() / num_rows) * self.disp_rows
        else:
            canvas_height = scroll_frame.winfo_height()
        scroll_canvas.configure(height=canvas_height)

        # adding buttons for file operations
        button_frame = tk.Frame(master_frame)
        button_frame.pack(anchor=tk.NW, fill=tk.X)

        save_button = tk.Button(button_frame, text="Save", command=self.save_dialog)
        save_button.pack(anchor=tk.NW, side=tk.LEFT)

        save_as_button = tk.Button(button_frame, text="Save As", command=lambda x=True: self.save_dialog(do_save_as=x))
        save_as_button.pack(anchor=tk.NW, side=tk.LEFT)

        # TODO work out how to clear frames and load a new file
        #load_button = tk.Button(button_frame, text="Load", 
        #        command=lambda x=header_frame, y=scroll_frame:self.load_file(x, y), state=tk.ACTIVE)
        #load_button.pack(anchor=tk.NW, side=tk.LEFT)
        
        # make sure window shows all frames
        master_frame.update()
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
                    row['audio_path'] = wav_file 
                else:
                    row['audio_path'] = row[self.fn_file_name]
                # convert existing exclude column to IntVar values
                if self.fn_exclude in self.csv_header:
                    row[self.fn_exclude] = int(row[self.fn_exclude])
                self.csv_rows.append(row)
        self.col_max_lens = {}
        for col in self.csv_header:
            self.col_max_lens[col] = max(max([len(str(i[col])) for i in self.csv_rows]), len(col))
            # need wider for comment field: defaults 20 chars
            self.col_max_lens[self.fn_comment] = 20

    def draw_header(self, frame):
        header_frame = tk.Canvas(frame)
        header_frame.pack(anchor=tk.NW)
        for i, col in enumerate(self.csv_header):
            col_val = tk.Label(header_frame, width=self.col_max_lens[col], padx=7, pady=7, relief=tk.RIDGE, text=col)
            col_val.pack(anchor=tk.NW, side=tk.LEFT)
        if (self.fn_exclude not in self.csv_header) and (self.do_exclude):
            col_val = tk.Label(header_frame, padx=7, pady=7, relief=tk.RIDGE, text=self.fn_exclude)
            col_val.pack(anchor=tk.NW, side=tk.LEFT)
        if (self.fn_comment not in self.csv_header) and (self.do_comment):
            col_val = tk.Label(header_frame, padx=7, pady=7, relief=tk.RIDGE, text=self.fn_comment, width=20)
            col_val.pack(anchor=tk.NW, side=tk.LEFT)
        col_val = tk.Label(header_frame, padx=7, pady=7, relief=tk.RIDGE, text='Click to play')
        col_val.pack(anchor=tk.NW, side=tk.LEFT)

    def draw_rows(self, frame):
        # these keep state of all exclude checkbuttons and comment text boxes
        self.exclude_vars = {}
        self.comment_vars = {}
        for r, row in enumerate(self.csv_rows):
            full_row = tk.Canvas(frame)
            full_row.pack(anchor=tk.NW)
            # TODO add warning about any duplicated rows: would need to have checkbutton
            # selected for every instance to have any of them excluded in the end
            if self.do_exclude:
                exclude_var = tk.IntVar()
                self.exclude_vars[row[self.fn_file_name]] = exclude_var
                exclude_button = tk.Checkbutton(full_row, padx=7, pady=7, relief=tk.RIDGE, variable=exclude_var, width=3)
            if self.do_comment:
                comment_var = tk.StringVar()
                self.comment_vars[row[self.fn_file_name]] = comment_var
                comment_box = tk.Entry(full_row, relief=tk.RIDGE, textvariable=comment_var)
            for col in self.csv_header:
                if (self.do_exclude) and (col == self.fn_exclude):
                    exclude_button.pack(anchor=tk.NW, side=tk.LEFT)
                    if row[self.fn_exclude]:
                        exclude_button.select()
                elif (self.do_comment) and (col == self.fn_comment):
                    comment_box.pack(anchor=tk.NW, side=tk.LEFT)
                    if row[self.fn_comment]:
                        comment_var.set(row[self.fn_comment])
                else:
                    col_val = tk.Label(full_row, width=self.col_max_lens[col], padx=7, pady=7, relief=tk.RIDGE, text=row[col])
                    col_val.pack(anchor=tk.NW, side=tk.LEFT)
            if (self.do_exclude) and (self.fn_exclude not in self.csv_header):
                exclude_button.pack(anchor=tk.NW, side=tk.LEFT)
            if (self.do_comment) and (self.fn_comment not in self.csv_header):
                comment_box.pack(anchor=tk.NW, side=tk.LEFT)
            play_button = tk.Button(full_row, padx=7, pady=7, relief=tk.RIDGE, text='Play', 
                                    command=lambda x=row['audio_path']: self.play_wav(x))
            play_button.pack(anchor=tk.NW, side=tk.LEFT)

    def load_file(self, header_frame, rows_frame):
        load_fn = filedialog.askopenfilename(initialdir=".", title="Select CSV file")
        self.csv_file = load_fn
        self.read_csv()
        for frame in [header_frame, rows_frame]:
            for child in frame.winfo_children():
                child.destroy()
        #header_frame.destroy()
        #rows_frame.destroy()
        self.draw_header(header_frame)
        header_frame.update()
        self.draw_rows(rows_frame)
        rows_frame.update()
        #pass

    def save_dialog(self, do_save_as=False):
        if do_save_as:
            self.csv_out = filedialog.asksaveasfilename(title="Save CSV file", 
                    initialdir=os.path.dirname(self.csv_out), initialfile=os.path.basename(self.csv_out), 
                    defaultextension='.csv', filetypes=(('CSV', '*.csv'), ('All Files', '*.*')))
            # catch canceled save-as dialogs
            if not self.csv_out:
                self.csv_out = self.csv_file
            else:
                self.save_file()
        elif messagebox.askokcancel(title="Save", message="Save to {0}?".format(self.csv_out)):
            self.save_file()

    def save_file(self):
        with open(self.csv_out, 'w') as outf:
            if (self.do_exclude) and (self.fn_exclude not in self.csv_header):
                self.csv_header.append(self.fn_exclude)
            if (self.do_comment) and (self.fn_comment not in self.csv_header):
                self.csv_header.append(self.fn_comment)
            writer = csv.DictWriter(outf, fieldnames=self.csv_header, extrasaction='ignore', lineterminator='\n')
            writer.writeheader()
            for row in self.csv_rows:
                # update any user-added values
                row[self.fn_exclude] = self.exclude_vars[row[self.fn_file_name]].get()
                row[self.fn_comment] = self.comment_vars[row[self.fn_file_name]].get()
                writer.writerow(row)

    def play_wav(self, wav_fn):
        if not os.path.exists(wav_fn):
            messagebox.showwarning("Warning: File not found", "Cannot find file {0}".format(wav_fn))
            return
        # windows playback through winsound in standard library
        if os.name == 'nt':
            winsound.PlaySound(wav_fn, winsound.SND_ASYNC)
        # or stereotypically obnoxious linux audio solution
        elif os.name == 'posix':
            wf = wave.open(wav_fn, 'rb')
            p = pyaudio.PyAudio()
            stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True)
            chunk_size = 1024
            data = wf.readframes(chunk_size)
            while len(data) > 0:
                stream.write(data)
                data = wf.readframes(chunk_size)
            stream.stop_stream()
            stream.close()
            p.terminate()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GUI tool for auditing lists of audio files.")
    parser.add_argument('csv_file', help="CSV file listing audio files to audit")
    parser.add_argument('-a', '--audio_path', help="Path to audio files, use if full path not in CSV", default=None)
    parser.add_argument('-x', '--do_exclude', help="Configure tool for excluding audio files", action='store_true')
    parser.add_argument('-c', '--do_comment', help="Configure tool for adding comments to audio files", action='store_true')
    parser.add_argument('--fn_file_name', help="Field containing audio file name. Default 'File Name'", default='File Name')
    parser.add_argument('--fn_exclude', help="Field for exclude decisions. Will be added to output CSV if not present in input and in exclude mode. Default 'Exclude'", default='Exclude')
    parser.add_argument('--fn_comment', help="Field for text comments. Will be added to output CSV if not present in input and in comment mode. Default 'Comment'", default='Comment')
    parser.add_argument('--disp_rows', help="Number of rows visible at once in scrollable field. Default 10", default=10, type=int)
    args = parser.parse_args()
    args_dict = vars(args)

    csv_listener = CsvListener(**args_dict)
    csv_listener.mainloop()
    
