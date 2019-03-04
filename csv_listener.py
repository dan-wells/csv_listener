import argparse
import csv
import os
import sys
import wave

# gui toolkit
try:
    from PyQt5.QtWidgets import QApplication, QWidget, QTableWidget, QVBoxLayout, \
        QHBoxLayout, QTableWidgetItem, QCheckBox, QPushButton, QLineEdit, \
        QFileDialog, QMessageBox
    from PyQt5.QtCore import Qt
except ImportError:
    from PyQt4.QtGui import QApplication, QWidget, QTableWidget, QVBoxLayout, \
        QHBoxLayout, QTableWidgetItem, QCheckBox, QPushButton, QLineEdit, \
        QFileDialog, QMessageBox
    from PyQt4.QtCore import Qt

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

class CsvListener(QWidget):
    def __init__(self, csv_file, audio_path=None, do_exclude=False, do_comment=False, 
                 utd=False, fn_file_name='File Name', fn_exclude='Exclude', 
                 fn_comment='Comment', *args, **kwargs):
                 #disp_rows=10, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)

        self.csv_file = csv_file
        self.audio_path = audio_path
        self.do_exclude = do_exclude
        self.do_comment = do_comment
        self.utd = utd
        self.fn_file_name = fn_file_name
        self.fn_exclude = fn_exclude
        self.fn_comment = fn_comment
        #self.disp_rows = disp_rows
        # default saving to original file
        self.csv_out = csv_file
        # set title on root window
        self.title = "CSV Listener - {0}".format(self.csv_file)
        self.setWindowTitle(self.title)

        # get various info from csv_file
        self.read_csv()

        self.create_table()

        save_button = QPushButton("Save")
        save_button.clicked.connect(lambda:self.save_dialog())
        save_as_button = QPushButton("Save As")
        save_as_button.clicked.connect(lambda:self.save_dialog(do_save_as=True))
        #load_button = QPushButton("Open")
        #load_button.clicked.connect(lambda:self.load_file())

        button_layout = QHBoxLayout()
        button_layout.addWidget(save_button,0,Qt.AlignLeft)
        button_layout.addWidget(save_as_button,0,Qt.AlignLeft)
        #button_layout.addWidget(load_button,0,Qt.AlignLeft)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(0)
        button_layout.addStretch(1)
        
        layout = QVBoxLayout()
        layout.addWidget(self.table)
        layout.addLayout(button_layout)
        self.setLayout(layout)

        #print(self.sizeHint())
        #self.resize(self.table.sizeHint().width(), self.table.sizeHint().height())
        #self.setGeometry(0,0,self.table.width(),500)
        self.show()
        
        # TODO: set window size according to table width, disp_rows
        # TODO: work out how to clear table and load a new file

    def read_csv(self):
        with open(self.csv_file) as inf:
            if self.utd:
                reader = csv.DictReader(inf, delimiter=':')
            else:
                reader = csv.DictReader(inf)
            self.csv_header = reader.fieldnames
            if (self.do_exclude) and (self.fn_exclude not in self.csv_header):
                self.csv_header.append(self.fn_exclude)
            if (self.do_comment) and (self.fn_comment not in self.csv_header):
                self.csv_header.append(self.fn_comment)
            self.csv_rows = []
            for row in reader:
                # concatenate audio paths
                if self.audio_path is not None:
                    wav_file = os.path.join(self.audio_path, row[self.fn_file_name])
                    row['audio_path'] = wav_file 
                else:
                    row['audio_path'] = row[self.fn_file_name]
                # convert existing exclude column to bools
                if (self.do_exclude) and (row[self.fn_exclude] is not None):
                    if row[self.fn_exclude] == 'True':
                        row[self.fn_exclude] = True
                    else:
                        row[self.fn_exclude] = False
                self.csv_rows.append(row)

    def create_table(self):
        self.table = QTableWidget(len(self.csv_rows), len(self.csv_header) + 1)
        # TODO: try using QTableView or at least horizontalHeader(), could
        # give better informatin/more control for resizing things
        self.table.setHorizontalHeaderLabels(self.csv_header + ['Play Audio'])
        self.exclude_vars = {}
        self.comment_vars = {}
        for i, row in enumerate(self.csv_rows):
            for j, col in enumerate(self.csv_header):
                if (self.do_exclude) and (col == self.fn_exclude):
                    item = QCheckBox()
                    self.exclude_vars[row[self.fn_file_name]] = item
                    if row[col]:
                        item.toggle()
                    self.table.setCellWidget(i, j, item)
                if (self.do_comment) and (col == self.fn_comment):
                    item = QLineEdit()
                    self.comment_vars[row[self.fn_file_name]] = item
                    if row[col]:
                        item.insert(row[col])
                    self.table.setCellWidget(i, j, item)
                else:
                    item = QTableWidgetItem()
                    item.setData(Qt.EditRole, row[col])
                    self.table.setItem(i, j, item) 
            play_button = QPushButton("Play")
            # because we need so many functions (1 per audio), use a factory method
            play_button.clicked.connect(self.play_button_factory(row['audio_path']))
            self.table.setCellWidget(i, len(self.csv_header), play_button)

    def play_button_factory(self, audio):
        def play_button():
            self.play_wav(audio)
        return play_button

    def load_file(self):
        #path = QFileDialog.getOpenFileName()
        ## catch canceled save-as dialogs
        #if path[0] != '':
        #    self.csv_file = path[0]
        #self.read_csv()
        #self.create_table()
        #self.show()
        pass

    def save_dialog(self, do_save_as=False):
        if do_save_as:
            path = QFileDialog.getSaveFileName()
            # in pyqt5, path is a tuple (selected file path, file type e.g. 'All Files (*)')
            # in pyqt4, it is just a string
            # catch canceled save-as dialogs
            if type(path) == tuple:
                if path[0] != '':
                    self.csv_out = path[0]
                    self.save_file()
            elif path:
                self.csv_out = path
                self.save_file()
            else:
                self.csv_out = self.csv_file
        else:
            msg = QMessageBox()
            ret = msg.question(self, "Save", "Save to {0}?".format(self.csv_out), msg.Yes | msg.No)
            if ret == msg.Yes:
                self.save_file()

    def save_file(self):
        with open(self.csv_out, 'w') as outf:
            if self.utd:
                writer = csv.DictWriter(outf, delimiter=':', fieldnames=self.csv_header, 
                                        extrasaction='ignore', lineterminator='\n')
            else:
                writer = csv.DictWriter(outf, fieldnames=self.csv_header, 
                                        extrasaction='ignore', lineterminator='\n')
            writer.writeheader()
            if self.do_exclude:
                x_idx = self.csv_header.index(self.fn_exclude)
            if self.do_comment:
                c_idx = self.csv_header.index(self.fn_comment)
            for i, row in enumerate(self.csv_rows):
                # update any user-added values
                if self.do_exclude:
                    row[self.fn_exclude] = self.exclude_vars[row[self.fn_file_name]].isChecked()
                if self.do_comment:
                    row[self.fn_comment] = self.comment_vars[row[self.fn_file_name]].text()
                writer.writerow(row)

    def play_wav(self, wav_fn):
        if not os.path.exists(wav_fn):
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Warning: File not found")
            msg.setText("Cannot find file {0}".format(wav_fn))
            msg.exec_()
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
    parser.add_argument('-u', '--utd', help="Read and write UTD files rather than CSV", action='store_true')
    parser.add_argument('--fn_file_name', help="Field containing audio file name. Default 'File Name'", default='File Name')
    parser.add_argument('--fn_exclude', help="Field for exclude decisions. Will be added to output CSV if not present in input and in exclude mode. Default 'Exclude'", default='Exclude')
    parser.add_argument('--fn_comment', help="Field for text comments. Will be added to output CSV if not present in input and in comment mode. Default 'Comment'", default='Comment')
    #parser.add_argument('--disp_rows', help="Number of rows visible at once in scrollable field. Default 10", default=10, type=int)
    args = parser.parse_args()
    args_dict = vars(args)

    app = QApplication([])
    csv_listener = CsvListener(**args_dict)
    sys.exit(app.exec_())
    
