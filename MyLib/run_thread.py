import time
import threading
import concurrent.futures
from queue import Queue
from MyLib.controller import AnswerController, BrushClassController


class MyThread(threading.Thread):
    def __init__(self, directory_path, account_file_path, qt):
        super().__init__()
        self.log_answer = 'answer'
        self.directory_path = directory_path
        self.account_file_path = account_file_path
        self.qtGui = qt
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def run(self):
        account_list = self.qtGui.pipeline_read.read_account(self.account_file_path)
        token_list = self.qtGui.common_function.get_token_list(account_list)
        log_content = {'one': '-' * 20, 'two': '-' * 20, 'three': '-' * 20, 'four': '-' * 20}
        for tokenItem in token_list:
            if self._stop_event.is_set() is True:
                break
            AnswerController(tokenItem, self.qtGui, self.directory_path).runs()
            time.sleep(0.05)
        log_content['five'] = '答题子线程已停止运行，请进行下一步操作'
        [self.qtGui.logger_output(log_content, self.log_answer) for kk in range(5)]
        return True


class BrushClassThread(threading.Thread):
    def __init__(self, account_file_path, qt):
        super().__init__()
        self.log_brush_class = 'brush_class'
        self.account_file_path = account_file_path
        self.qtGui = qt
        self.executor = None  # 创建线程池

        self._stop_event = threading.Event()

    def stop(self):
        if self.executor:
            self.executor.shutdown(wait=False)  # 立即停止线程，不等待任务执行完成
            self.executor = None
        self._stop_event.set()

    def run(self):
        account_list = self.qtGui.pipeline_read.read_account(self.account_file_path)
        token_list = self.qtGui.common_function.get_token_list(account_list, self.log_brush_class)
        token_queue = Queue()
        [token_queue.put(token_item) for token_item in token_list]
        log_content = {'one': '-' * 20, 'two': '-' * 20, 'three': '-' * 20, 'four': '-' * 20}
        thread_number = 2
        while token_queue.qsize():
            if self.executor is None or self.executor._shutdown:
                # 创建线程池
                self.executor = concurrent.futures.ThreadPoolExecutor()
            brush_class_object = BrushClassController(self.log_brush_class)
            for kkk in range(thread_number):  # 线程数
                self.executor.submit(brush_class_object.runs, token_queue.get(), self.qtGui.queue_items, self.qtGui)
                time.sleep(2)
            # brush_class_object.runs(token_queue.get(), self.qtGui.queue_items, self.qtGui)
            self.executor.shutdown(wait=True)  # 等待任务执行完成
            if self._stop_event.is_set() is True or self.executor is None:
                break
        log_content['five'] = '刷课程序运行完毕，请进行下一步操作'
        [self.qtGui.logger_output(log_content, self.log_brush_class) for kk in range(5)]
        return True
