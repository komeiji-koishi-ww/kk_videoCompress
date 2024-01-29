
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

import time
import os

class ProgressDialog(QDialog):

    closeSignal = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("转码进度")
        self.setFixedSize(400, 150)

        self.total_duration = None  # 初始化时将总时长设置为None

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setGeometry(20, 20, 260, 30)

        self.time_label = QLabel(self)
        self.time_label.setGeometry(20, 60, 260, 30)
        self.time_label.setText("waiting...")

        layout = QVBoxLayout(self)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.time_label)

        self.start_time = None
        self.timerDidStarted = False

    def update_progress(self, percentage, speed, eta, estimated_filesize):
        self.progress_bar.setValue(percentage)
        hms = self.convert_seconds_to_hms(eta)
        if self.timerDidStarted == False:
            self.start_time = time.time()
            self.timerDidStarted = True
        currentTime = self.get_elapsed_time()
        self.time_label.setText(f"已用时间：{currentTime}  预计剩余时间：{hms}  速度: {speed}x \n 预计文件大小: {round(estimated_filesize/(1024.0 ** 2), 2)}MB")

    def get_elapsed_time(self):
        if self.start_time is None:
            return "Timer not started"
        current_time = time.time()
        elapsed_time = current_time - self.start_time
        formatted_time = self.convert_seconds_to_hms(elapsed_time)
        return formatted_time

    def closeEvent(self, event):
        """Shuts down application on close."""
        reply = QMessageBox.question(self, '警告', '<font color=red><b>窗口关闭后，将终止本次运行</b></font>',
                                     QMessageBox.Yes|QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:

            self.closeSignal.emit(True)

            event.accept()
            if os.path.exists(self.outputPath):
                try:
                    os.remove(self.outputPath)
                    print(f"成功删除文件: {self.outputPath}")
                except OSError as e:
                    print(f"删除文件时出错: {e}")
            else:
                print(f"文件不存在: {self.outputPath}")
        else:
            event.ignore()


    def setStatus(self, outpath):
        self.outputPath = outpath


    @staticmethod
    def convert_seconds_to_hms(seconds):
        if not isinstance(seconds, (int, float)):
            return "Invalid"  # 或者返回其他默认值或采取其他处理方式
        try:
            hms = time.strftime("%H:%M:%S", time.gmtime(float(seconds)))
        except:
            return "00:00:00"
        return hms