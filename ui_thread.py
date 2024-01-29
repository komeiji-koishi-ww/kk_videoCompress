from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from better_ffmpeg_progress import FfmpegProcess
import signal

class ui_thread(QThread):

    progress_signal = pyqtSignal(float, float, float, float)
    success_signal = pyqtSignal()
    error_signal = pyqtSignal()

    def __init__(self):
        super(ui_thread, self).__init__()


    def setValue(self, input_file, output_file, crf, target_file_size):
        self.input_file = input_file
        self.output_file = output_file
        self.crf = crf
        self.target_file_size = target_file_size


    def run(self):

        compress_cmd = ['ffmpeg', '-i', self.input_file, '-crf', f'{self.crf}', '-b:v', '1M', '-r', '24', '-fs', f'{self.target_file_size}MB',
                        self.output_file]
        self.process = FfmpegProcess(compress_cmd)
        self.process.run(progress_handler=self.progressInfo, success_handler=self.handle_success,
                         error_handler=self.handle_error)

    def progressInfo(self, percentage, speed, eta, estimated_filesize):
        print(percentage, speed, eta, estimated_filesize)

        if percentage is not None and speed is not None and eta is not None and estimated_filesize is not None:
            self.progress_signal.emit(percentage, speed, eta, estimated_filesize)


    def handle_success(self):
        self.success_signal.emit()


    def handle_error(self):
        self.error_signal.emit()
