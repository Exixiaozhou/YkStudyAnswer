import os
import sys
import time
import json
import threading
import subprocess  # 杀死进程
from queue import Queue
from PySide2.QtWidgets import QApplication, QMessageBox, QWidget, QFileDialog, QTableWidgetItem, QMainWindow
from PySide2.QtUiTools import loadUiType, QUiLoader
from PySide2.QtCore import QFile, Qt
from PySide2.QtGui import QIcon, QTextCursor, QTextDocument, QImage, QPixmap
from PySide2.QtWidgets import QTextBrowser
from MyLib.utils import CommonFunction
from MyLib.pipeline import DataRead, DataSave
from MyLib.controller import OnlineInfoFindController
from MyLib.settings import ResourcePath
from MyLib.run_thread import MyThread, BrushClassThread


class YkGui(QWidget):
    def __init__(self):
        super().__init__()
        self.common_function = CommonFunction(qt_gui=self)
        self.pipeline_read = DataRead(self, self.common_function)
        self.pipeline_save = DataSave(self, self.common_function)
        self.online_find = OnlineInfoFindController(self, self.common_function)
        self.yk_ico_dir = ResourcePath.YkIcoPath.value
        self.yk_ui_dir = ResourcePath.YkUiPath.value
        self.wx_img_dir = ResourcePath.WxImgPath.value
        self.csdn_img_dir = ResourcePath.CsdnImgPath.value

        # 变量、对象定义
        self.log_answer = 'answer'
        self.log_info_find = 'info_find'
        self.log_brush_class = 'brush_class'
        self.answer_directory_path = None  # 答题目录路径
        self.answer_account_file_path = None  # 答题账户文件路径
        self.find_account_file_path = None  # 本地需要查询的账户文件路径
        self.find_account_number_input_text = None  # 指定查询文本
        self.brush_class_account_file_path = None  # 刷课账户文件路径
        self.brush_class_course_number_input_text = None  # 刷课课程编号查询

        self.answer_thread = None  # 答题启动线程对象
        self.brush_class_thread = None  # 刷课启动线程对象

        self.queue_items = {'data_save_queue': Queue(), 'signal_save_queue': Queue()}  # 刷课数据、刷课信号 存储队列

        # 加载ui文件，创建qt文件对象，加载文件对象并创建ui对象
        qt_file_obj = QFile(self.yk_ui_dir)
        qt_file_obj.open(QFile.ReadOnly)
        qt_file_obj.close()

        # 设置ico、另外定义外观
        self.ui = QUiLoader().load(qt_file_obj)
        icon = QIcon(self.yk_ico_dir)
        self.ui.setWindowIcon(icon)  # 设置ico
        self.ui.tableWidgetAnswer.horizontalHeader().setVisible(True)  # 另外定义外观，显示tableWidget标题
        self.ui.tableWidgetFind.horizontalHeader().setVisible(True)
        self.ui.tableWidgetAnswer.verticalHeader().setVisible(True)  # 设置行号可见
        self.ui.tableWidgetFind.verticalHeader().setVisible(True)

        pixmap = QPixmap(self.wx_img_dir)  # 添加微信图片
        self.ui.wx_img_label.setPixmap(pixmap)
        pixmap = QPixmap(self.csdn_img_dir)  # 添加CSDN图片
        self.ui.csdn_img_label.setPixmap(pixmap)

        # 自动答题输入参数、按钮绑定
        self.ui.answerDirecotryInputButton.clicked.connect(self.answer_directory_import)
        self.ui.answerAccountFileInputButton.clicked.connect(self.answer_account_file_import)
        self.ui.answerStartButton.clicked.connect(self.answer_start_running)
        self.ui.answerStopButton.clicked.connect(lambda: self.thread_it(self.answer_stop_running()))
        self.ui.answerClearLoggerButton.clicked.connect(lambda: self.thread_it(self.clear_logger, self.log_answer))
        self.ui.answerExitButton.clicked.connect(lambda: self.thread_it(self.exit_program, self.log_answer))  # 杀死线程

        # 答题本地，线上数据查询输入参数、按钮绑定
        self.ui.findAccountFileinputBuuton.clicked.connect(self.answer_find_file_import)
        self.ui.onlineFindButton.clicked.connect(self.online_info_find)
        self.ui.successFindButton.clicked.connect(lambda: self.local_info_find('success'))
        self.ui.failingFindButton.clicked.connect(lambda: self.local_info_find('failing'))
        self.ui.findClearLoggerButton.clicked.connect(lambda: self.thread_it(self.clear_logger, self.log_info_find))
        self.ui.exitProgramTwo.clicked.connect(lambda: self.thread_it(self.exit_program, self.log_info_find))

        # 自动刷课学习、输入参数、按钮 绑定
        self.ui.brushClassFileInputButton.clicked.connect(self.brush_class_account_file_import)
        self.ui.brushClassStartButton.clicked.connect(lambda: self.thread_it(self.brush_class_start_running))
        self.ui.brushClassStopButton.clicked.connect(lambda: self.thread_it(self.brush_class_stop_running))
        self.ui.brushClassClearLoggerButton.clicked.connect(lambda: self.thread_it(self.clear_logger, self.log_brush_class))
        self.ui.brushClassExitButton.clicked.connect(lambda: self.thread_it(self.exit_program, self.log_brush_class))

        # 定义日志打印对象
        self.logger_object = {
            self.log_answer: {
                'index': 0, 'tableWidget': self.ui.tableWidgetAnswer
            },
            self.log_info_find: {
                'index': 0, 'tableWidget': self.ui.tableWidgetFind
            },
            self.log_brush_class: {
                'index': 0, 'tableWidget': self.ui.tableWidgetBrushClass
            }
        }

    def answer_directory_import(self):
        # 打开目录对话框
        self.answer_directory_path = QFileDialog.getExistingDirectory(self.ui, "选择答案目录", "")
        self.ui.answerDirecotryInput.setText(self.answer_directory_path)

    def answer_account_file_import(self):
        # 打开文件对话框
        self.answer_account_file_path, _ = QFileDialog.getOpenFileName(self.ui, "选择账户文件", "", "All Files (*);;Text Files (*.txt)")
        # 输出选择的文件路径和目录路径
        self.ui.answerAccountFileInput.setText(self.answer_account_file_path)

    def answer_find_file_import(self):
        self.find_account_file_path, _ = QFileDialog.getOpenFileName(self.ui, "选择JSON文件", "", "All Files (*);;Text Files (*.txt)")
        self.ui.findAccountFileinput.setText(self.find_account_file_path)

    def brush_class_account_file_import(self):
        self.brush_class_account_file_path, _ = QFileDialog.getOpenFileName(self.ui, "选择账户文件", "", "All Files (*);;Text Files (*.txt)")
        self.ui.brushClassFileInput.setText(self.brush_class_account_file_path)

    def thread_it(self, func, *args):
        '''
            将函数打包进线程
        '''
        self.myThread = threading.Thread(target=func, args=args)
        self.myThread.setDaemon(True)
        self.myThread.start()

    def answer_start_running(self):
        if self.answer_directory_path is None or self.answer_account_file_path is None:
            QMessageBox.warning(self.ui, "警告", "请选择答案目录和账户文件！", QMessageBox.Ok)
            return False
        logger_item = {
            'one': '-' * 20, 'two': '-' * 20, 'three': '-' * 20, 'four': '-' * 20,
            'five': '答题程序已经开始运行，请勿多次点击开始运行按钮'
        }
        [self.logger_output(logger_item, self.log_answer) for kk in range(5)]
        # 创建线程对象
        self.answer_thread = MyThread(self.answer_directory_path, self.answer_account_file_path, self)
        # 启动线程
        self.answer_thread.start()

    def answer_stop_running(self):
        # 停止线程
        self.answer_thread.stop()
        logger_item = {
            'one': '-' * 20, 'two': '-' * 20, 'three': '-' * 20, 'four': '-' * 20,
            'five': '答题程序已设置停止线程，请等待最后一个账号运行完再进行下一步操作'
        }
        [self.logger_output(logger_item, self.log_answer) for kk in range(5)]
        # self.thread = MyThread(self.directoryPath, self.accountFilePath, self)

    def brush_class_start_running(self):
        if self.brush_class_account_file_path is None:
            QMessageBox.warning(self.ui, "警告", "请选择需要刷课的账户文件！", QMessageBox.Ok)
            return False
        logger_item = {
            'one': '-' * 20, 'two': '-' * 20,
            'three': '-' * 20, 'four': '-' * 20,
            'five': '刷课程序已经开始运行，请勿多次点击开始运行按钮'
        }
        [self.logger_output(logger_item, self.log_brush_class) for kk in range(5)]
        self.brush_class_thread = BrushClassThread(self.brush_class_account_file_path, self)
        self.brush_class_thread.start()

    def brush_class_data_save(self):
        """ 通过定时器、定期存储队列中的数据"""
        pass

    def brush_class_stop_running(self):
        self.brush_class_thread.stop()
        logger_item = {
            'one': '-' * 20, 'two': '-' * 20, 'three': '-' * 20, 'four': '-' * 20,
            'five': '刷课程序已设置停止线程，请等待最后一个账号运行完再进行下一步操作'
        }
        [self.logger_output(logger_item, self.log_brush_class) for kk in range(5)]

    def answer_info_find_params_verify(self, route_key):
        account_list = []
        if self.find_account_file_path is None or len(self.find_account_file_path.strip()) < 2:
            self.find_account_file_path = None
        self.find_account_number_input_text = self.ui.findAccountNumberInput.text()
        if '请输入账号' in self.find_account_number_input_text or len(self.find_account_number_input_text.strip()) < 2:
            self.find_account_number_input_text = None

        else:
            if route_key == 'local':
                account_list = [str_.split(',')[0] for str_ in self.find_account_number_input_text.split(";")]
            else:
                for str_ in self.find_account_number_input_text.strip().split(";"):
                    if len(str_) <= 1:
                        continue
                    username, password = str_.split(',')
                    account_list.append({'username': username, 'password': password})
            self.find_account_number_input_text = True  # 是否为指定账号查询
        if self.find_account_file_path is None and self.find_account_number_input_text is None:
            QMessageBox.warning(self.ui, "警告", "请选择JSON文件或输入账户密码！", QMessageBox.Ok)
            return {'taskStatus': False}
        return {'taskStatus': True, 'account_list': account_list}

    def online_info_find(self, route_key):
        # 线上账号答题状态数据查询
        verify_result = self.answer_info_find_params_verify('online')
        print(verify_result)
        if verify_result['taskStatus'] is False:
            return False
        if self.answer_directory_path is None or len(self.answer_directory_path) <= 1:
            QMessageBox.warning(self.ui, "警告", "线上查询需要在自动答题模块中选择答案目录！", QMessageBox.Ok)
            return False
        account_list = verify_result['account_list']
        self.thread_it(self.online_find.answer_info_controller(self.find_account_file_path, account_list))

    def local_info_find(self, route_key):
        # 本地账号答题状态数据查询
        verify_result = self.answer_info_find_params_verify('local')
        if verify_result['taskStatus'] is False:
            return False
        account_list = verify_result['account_list']
        self.thread_it(self.pipeline_read.local_answered_find(self.find_account_file_path, route_key, account_list))

    def logger_output(self, logger_item, route_name=None):
        print(route_name, logger_item)
        table_widget = self.logger_object[route_name]['tableWidget']
        self.logger_object[route_name]['index'] += 1
        table_widget.insertRow(int(table_widget.rowCount()))
        new_item_one = QTableWidgetItem(logger_item['one'])
        new_item_one.setTextAlignment(Qt.AlignCenter)
        new_item_two = QTableWidgetItem(logger_item['two'])
        new_item_two.setTextAlignment(Qt.AlignCenter)
        new_item_three = QTableWidgetItem(logger_item['three'])
        new_item_three.setTextAlignment(Qt.AlignCenter)
        new_item_four = QTableWidgetItem(logger_item['four'])
        new_item_four.setTextAlignment(Qt.AlignCenter)
        new_item_five = QTableWidgetItem(logger_item['five'])
        new_item_five.setTextAlignment(Qt.AlignCenter)
        table_widget.setItem(self.logger_object[route_name]['index'] - 1, 0, new_item_one)
        table_widget.setItem(self.logger_object[route_name]['index'] - 1, 1, new_item_two)
        table_widget.setItem(self.logger_object[route_name]['index'] - 1, 2, new_item_three)
        table_widget.setItem(self.logger_object[route_name]['index'] - 1, 3, new_item_four)
        table_widget.setItem(self.logger_object[route_name]['index'] - 1, 4, new_item_five)
        table_widget.verticalScrollBar().setSliderPosition(self.logger_object[route_name]['index'])
        QApplication.processEvents()

    def clear_logger(self, route_name=None):
        print("清除日志", route_name, self.logger_object[route_name]['index'])
        table_widget = self.logger_object[route_name]['tableWidget']
        for i in range(self.logger_object[route_name]['index']):
            table_widget.removeRow(0)  # 删除第i行数据
        # self.ui.tableWidget.clearContents()  # 清除/删除所有内容
        time.sleep(1)
        self.logger_object[route_name]['index'] = 0

    def exit_program(self, route_name):
        tmp = os.popen("tasklist").readlines()
        for tm in tmp:
            if 'python' not in tm and 'demo_gui' not in tm and 'yk_auto_answer' not in tm:
                continue
            logger_item = {
                'one': '-' * 20, 'two': '-' * 20,
                'three': '-' * 20, 'four': '-' * 20,
                'five': '进程杀死成功：{tm}'
            }
            self.logger_output(logger_item, route_name)
            time.sleep(0.5)
            pid = tm.strip().replace(' ', '').split('.exe')[-1].split('Console')[0]
            subprocess.Popen("taskkill /F /T /PID " + str(pid), shell=True)
        return True
