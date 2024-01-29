import os
import sys

import threading

from ui_thread import *
from progress_dialog import *

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

        self.crf_label = QLabel("CRF:", self)
        self.crf_label.setGeometry(50, 300, 100, 30)

        self.crf_tf = QLineEdit(self)
        self.crf_tf.setGeometry(150, 300, 100, 30)
        self.crf_tf.setValidator(QIntValidator())
        self.crf_tf.setPlaceholderText("压缩比例")
        self.crf_tf.setText("30")

        self.compress_button = QPushButton("Compress", self)
        self.compress_button.clicked.connect(self.openThread)
        self.compress_button.setGeometry(50, 350, 100, 30)

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
        self.dialog.closeSignal.connect(self.handle_dialog_close)


    def select_file(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFile)

        file_dialog.setNameFilter("Videos (*.mp4 *.avi *.mkv *.rm *.rmvb *.3gp *.m4v *.mov *.fiv *.vob)")

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

        if self.file_path.text().strip() == "" or self.output_path.text().strip() == "" or self.target_size.text().strip() == "" or self.crf_tf.text().strip() == "":
            msg_box = QMessageBox()
            msg_box.setWindowTitle("提示")
            msg_box.setText("请完善信息")
            msg_box.setIcon(QMessageBox.Information)
            # 添加确定按钮
            ok_button = msg_box.addButton(QMessageBox.Ok)
            msg_box.setDefaultButton(ok_button)
            msg_box.exec()
        else:

            input_file = self.file_path.text()
            filename = os.path.basename(input_file)
            last_dot_index = filename.rfind('.')
            filename_without_extension = filename[:last_dot_index]
            output_file = os.path.join(self.output_path.text(),
                                       filename_without_extension + "_compressed" + os.path.splitext(input_file)[-1])
            crf = self.crf_tf.text()
            target_file_size = self.target_size.text()


            self.thread = ui_thread()
            self.thread.progress_signal.connect(self.dialog.update_progress)
            self.thread.success_signal.connect(self.handle_success)
            self.thread.error_signal.connect(self.handle_error)

            self.thread.setValue(input_file, output_file, crf, target_file_size)
            self.thread.start()

            self.dialog.setStatus(output_file)
            self.dialog.setModal(True)  # 将对话框设置为模态对话框
            self.dialog.exec_()

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

    def handle_dialog_close(self, closed):
        if closed:
            self.thread.process.process.terminate()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())