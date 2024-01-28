import os
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QLineEdit, QFileDialog, QDesktopWidget, QMessageBox, QVBoxLayout, QDialog, QProgressBar
from PyQt5.QtGui import QIntValidator, QDesktopServices
from PyQt5.QtCore import QDir, QUrl, pyqtSignal

import threading
from better_ffmpeg_progress import FfmpegProcess
import datetime
import time

class ProgressDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("转码进度")
        self.setFixedSize(300, 150)

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

    def update_progress(self, progress, remaining_time):
        print(progress)
        self.progress_bar.setValue(progress)
        hms = self.convert_seconds_to_hms(remaining_time)
        if self.timerDidStarted == False:
            self.start_time = time.time()
            self.timerDidStarted = True
        currentTime = self.get_elapsed_time()
        self.time_label.setText(f"已用时间：{currentTime}  预计剩余时间：{hms}")

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


    def setoutputPath(self, outpath):
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


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Compression")

        self.file_button = QPushButton("Select File", self)
        self.file_button.clicked.connect(self.select_file)
        self.file_button.setGeometry(50, 50, 100, 30)

        self.file_label = QLabel("Selected File:", self)
        self.file_label.setGeometry(50, 100, 100, 30)

        self.file_path = QLineEdit(self)
        self.file_path.setReadOnly(True)
        self.file_path.setGeometry(150, 100, 300, 30)
        self.file_path.setPlaceholderText("点击按钮选择视频文件")


        self.output_button = QPushButton("Select Output", self)
        self.output_button.clicked.connect(self.select_output)
        self.output_button.setGeometry(50, 150, 100, 30)

        self.output_label = QLabel("Output Path:", self)
        self.output_label.setGeometry(50, 200, 100, 30)

        self.output_path = QLineEdit(self)
        self.output_path.setReadOnly(True)  # 禁止手动输入
        self.output_path.setGeometry(150, 200, 300, 30)
        self.output_path.setPlaceholderText("点击按钮选择存放目录")

        self.target_label = QLabel("Max Size (MB):", self)
        self.target_label.setGeometry(50, 250, 100, 30)

        self.target_size = QLineEdit(self)
        self.target_size.setGeometry(150, 250, 100, 30)
        self.target_size.setValidator(QIntValidator())
        self.target_size.setPlaceholderText("最大体积")

        self.compress_button = QPushButton("Compress", self)
        self.compress_button.clicked.connect(self.openThread)
        self.compress_button.setGeometry(50, 300, 100, 30)

        # 获取屏幕分辨率
        screen_resolution = QDesktopWidget().screenGeometry()
        screen_width = screen_resolution.width()
        screen_height = screen_resolution.height()

        # 计算窗口大小
        window_width = int(screen_width * 0.5)
        window_height = int(screen_height * 0.5)

        # 设置窗口大小
        self.setFixedSize(window_width, window_height)

        self.dialog = ProgressDialog()
        replay = self.dialog.actions()

    def select_file(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFile)

        file_dialog.setNameFilter("Videos (*.mp4 *.avi *.mkv, *.rm, *.rmvb, *.3gp, *.m4v, *.mov, *.fiv, *.vob)")

        if file_dialog.exec_() == QFileDialog.Accepted:
            selected_file = file_dialog.selectedFiles()[0]

            file_path = selected_file
            file_path = QDir.toNativeSeparators(file_path)
            self.file_path.setText(file_path.strip())

    def select_output(self):
        file_dialog = QFileDialog()
        output_path = file_dialog.getExistingDirectory(self, "Select Output")
        output_path = QDir.toNativeSeparators(output_path)
        self.output_path.setText(output_path.strip())

    def openThread(self):

        if self.file_path.text().strip() == "" or self.output_path.text().strip() == "" or self.target_size.text().strip() == "":
            msg_box = QMessageBox()
            msg_box.setWindowTitle("提示")
            msg_box.setText("请完善信息")
            msg_box.setIcon(QMessageBox.Information)
            # 添加确定按钮
            ok_button = msg_box.addButton(QMessageBox.Ok)
            msg_box.setDefaultButton(ok_button)
            msg_box.exec()
        else:

            thread = threading.Thread(target=self.compress_video_ffmpeg2)
            thread.start()

            self.dialog.setModal(True)  # 将对话框设置为模态对话框
            self.dialog.exec_()



    def compress_video_ffmpeg2(self):

        input_file = self.file_path.text()
        output_file = self.output_path.text() + "\\" +os.path.basename(input_file).split(".")[0] + "_compressed" + os.path.splitext(input_file)[-1]
        target_file_size = self.target_size.text()
        self.dialog.setoutputPath(output_file)

        compress_cmd = ['ffmpeg', '-i', input_file, '-b:v', '64k', '-r', '24', '-fs', f'{target_file_size}MB', output_file]

        process = FfmpegProcess(compress_cmd)
        process.run(progress_handler=self.progressInfo, success_handler=self.handle_success, error_handler=self.handle_error)

    def progressInfo(self, percentage, speed, eta, estimated_filesize):
        print(percentage, speed, eta, estimated_filesize)
        self.dialog.update_progress(percentage, eta)


    def handle_success(self):
        print("success")
        msg_box = QMessageBox()
        msg_box.setWindowTitle("提示")
        msg_box.setText("转码完成")
        msg_box.setIcon(QMessageBox.Information)

        # 添加确定按钮
        ok_button = msg_box.addButton(QMessageBox.Ok)
        msg_box.setDefaultButton(ok_button)

        # 设置按钮点击事件
        ok_button.clicked.connect(self.openOutputDir)

        # 显示消息框
        msg_box.exec()


    def handle_error(self):
        msg_box = QMessageBox()
        msg_box.setWindowTitle("提示")
        msg_box.setText("转码失败")
        msg_box.setIcon(QMessageBox.Information)

        # 添加确定按钮
        ok_button = msg_box.addButton(QMessageBox.Ok)
        msg_box.setDefaultButton(ok_button)

        # 显示消息框
        msg_box.exec()

    def openOutputDir(self):
        folder_path = self.output_path.text()  # 替换为您要打开的文件夹路径
        QDesktopServices.openUrl(QUrl.fromLocalFile(folder_path))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())