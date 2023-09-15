import pathlib

from PySide2.QtWidgets import QApplication, QMainWindow, QPushButton
from PySide2.QtCore import Slot, Signal, QObject, QThread, QTimer
import queue
import threading




# 定义主窗口类
# class MainWindow(QMainWindow):
#     def __init__(self):
#         super().__init__()
#         self.setWindowTitle("GUI Example")
#
#         # 创建按钮
#         self.button = QPushButton("Store Data", self)
#         self.button.clicked.connect(self.on_button_clicked)
#
#         # 创建队列对象
#         self.data_queue = queue.Queue()
#
#         # 创建定时器
#         self.timer = QTimer()
#         self.timer.timeout.connect(self.process_data_queue)
#         self.timer.start(2000)  # 每秒检查一次队列
#
#     def on_button_clicked(self):
#         # 启动子线程
#         thread = DataStorageThread(self.data_queue)
#         thread.start()
#
#     def process_data_queue(self):
#         print("process_data_queue")
#         while not self.data_queue.empty():
#             data = self.data_queue.get()
#             self.update_data(data)
#
#     def update_data(self, data):
#         # 在界面上更新数据
#         print(f"Data Updated: {data}")
#
#
# if __name__ == "__main__":
#     app = QApplication([])
#     window = MainWindow()
#     window.show()
#     app.exec_()


# from PySide2.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
# from PySide2.QtCore import Slot
# import concurrent.futures
# import time
#
#
# # 定义子线程类
# class DataStorageThread(threading.Thread):
#     def __init__(self):
#         super().__init__()
#         self._stop_event = threading.Event()
#         # 创建线程池
#         self.executor = None
#
#     def stop(self):
#         if self.executor:
#             # 停止线程池
#             self.executor.shutdown(wait=False)  # 立即停止线程，不等待任务执行完成
#             self.executor = None
#         print("停止线程 Tasks started\n\n", end='')
#         self._stop_event.set()
#
#     def run(self):
#         # 模拟数据存储操作
#         while True:
#             # 提交任务
#             print("创建线程池")
#             if self.executor is None or self.executor._shutdown:
#                 # 创建线程池
#                 self.executor = concurrent.futures.ThreadPoolExecutor()
#                 print("创建成功 executor")
#             self.executor.submit(self.task, "Task 1")
#             self.executor.submit(self.task, "Task 2")
#             self.executor.submit(self.task, "Task 3")
#             self.executor.shutdown(wait=True)
#             print("任务运行完成 Tasks started\n\n", end='')
#             time.sleep(5)
#             if self.executor is None:
#                 break
#
#     def task(self, name):
#         print(f"Task {name} started")
#         time.sleep(15)
#         print(f"Task {name} completed")
#
#
# class ThreadPoolExample(QMainWindow):
#     def __init__(self):
#         super().__init__()
#         self.setWindowTitle("ThreadPool Example")
#
#         # 创建开始按钮
#         self.start_button = QPushButton("Start Tasks")
#         self.start_button.clicked.connect(self.start_tasks)
#
#         # 创建停止按钮
#         self.stop_button = QPushButton("Stop Tasks")
#         self.stop_button.clicked.connect(self.stop_tasks)
#
#         # 创建垂直布局
#         layout = QVBoxLayout()
#         layout.addWidget(self.start_button)
#         layout.addWidget(self.stop_button)
#
#         # 创建主窗口部件并设置布局
#         central_widget = QWidget()
#         central_widget.setLayout(layout)
#
#         # 设置主窗口的中央部件
#         self.setCentralWidget(central_widget)
#
#         self.thread = None
#
#     def start_tasks(self):
#         # 创建线程池
#         print("gui 调用 start_tasks")
#         self.thread = DataStorageThread()
#         self.thread.start()
#
#     def stop_tasks(self):
#         self.thread.stop()
#
#
# if __name__ == "__main__":
#     app = QApplication([])
#     window = ThreadPoolExample()
#     window.show()
#     app.exec_()
# import time
# from queue import Queue
#
# a_queue = Queue()
# a_queue.put(1)
# a_queue.put(2)
# a_queue.put(3)
#
# while a_queue.qsize():
#     # if a_queue.qsize() < 1:
#     #     break
#     print(a_queue.get())
#     time.sleep(2)

import ctypes
import threading


class ThreadWithException(threading.Thread):
    def __init__(self, _tk, route_number=0):
        threading.Thread.__init__(self)
        self._tk = _tk
        self.route_number = route_number

    def run(self):
        pass

    def get_id(self):
        if hasattr(self, '_thread_id'):
            return self._thread_id
        for id, thread in threading._active.items():
            if thread is self:
                return id

    def raise_exception(self):
        thread_id = self.get_id()
        # 精髓就是这句话，给线程发过去一个exceptions，线程就那边响应完就停了
        response = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, ctypes.py_object(SystemExit))
        if response > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)


