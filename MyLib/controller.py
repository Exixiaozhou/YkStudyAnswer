from MyLib.constants import AnswerPathAndUploadUrl
from MyLib.settings import ResourcePath
from MyLib.pipeline import DataSave, DataRead
from MyLib.utils import AnswerTaskRequest, CommonFunction, OnlineInfoFindTaskRequest, BrushClassTaskRequest


class AnswerController(object):
    def __init__(self, account_items, qt_gui, answer_directory_path, log_print=None):
        self.account_items = account_items
        self.username = self.account_items['username']  # 该取值无误
        self.qt_gui = qt_gui
        self.answer_directory_path = answer_directory_path
        self.log_print = None if log_print is None else log_print
        self.common_function = CommonFunction(self.qt_gui)  # 创建公共函数对象
        self.pipeline_save = DataSave(self.qt_gui, self.common_function)
        self.pipeline_read = DataRead(self.qt_gui, self.common_function)
        self.answer_succeed_json = self.pipeline_read.read_success_json(self.username)  # 调用读入success json 文件
        self.params_items = {
            'account_items': account_items, 'qt_gui': qt_gui, 'answer_directory_path': answer_directory_path,
            'answer_succeed_json': self.answer_succeed_json
        }
        self.answer_request = AnswerTaskRequest(self.params_items)
        self.save_number_count = 0  # 该数字大于10则进行一次写入操作

    def course_list_search_controller(self, log_print=None):
        """
        账号所有的科目id，名称，搜索存储
        :return: 科目id，名称，返回list
        """
        course_params_list = self.answer_request.course_list_search_request(log_print)
        return course_params_list

    def homework_list_search_controller(self, course_params_list, log_print=None):
        """
        根据科目的id信息，搜索该账号的所有子作业，并存储
        :return: 作业的taskid，examid，作业名称, 返回 list
        """
        homework_list = list()
        for course_item in course_params_list:
            homework_list += self.answer_request.homework_list_search_request(course_item, log_print)
        return homework_list

    def homework_answer_controlled(self, homework_list):
        """
        根据不同的作业id和信息，对url发起请求，添加数据
        :param homework_list:
        :return: 作业完成状态
        """
        homework_name_list = list(AnswerPathAndUploadUrl.items.value.keys())  # 已有的作业对接
        for homeworkRequestParam in homework_list:
            course_title = homeworkRequestParam['courseTitle']
            task_name = homeworkRequestParam['taskName']
            if (task_name == '小组学习' or task_name == '课程实践') and "小组讨论" in homeworkRequestParam['answerFileList']:
                pass  # 小组学习、课程实践 的答案都是小组讨论.png、小组讨论.pdf 所以要以这种方式做判断
            elif '线上作业' in task_name or '在线作业' in task_name:  # 判断是否为线上作业
                route_key = '线上作业' if task_name == '线上作业' else '在线作业'
                task_result = self.online_question_answer_controller(homeworkRequestParam, route_key)
                if task_result['taskStatus']:
                    self.answer_succeed_json[self.username]['success'][course_title][route_key] = task_result['msg']
                else:
                    self.answer_succeed_json[self.username]['failing'][course_title][route_key] = task_result['msg']
                continue
            elif task_name not in homeworkRequestParam['answerFileList']:  # 如果作业名称不存在本地对应目录答案文件列表
                continue
            elif task_name not in homework_name_list:  # 如果作业名称不存在已支持的作业对接列表
                continue
            task_result = self.file_upload_controlled(homeworkRequestParam, task_name)
            if task_result['taskStatus'] is True:
                self.answer_succeed_json[self.username]['success'][course_title][task_name] = task_result['msg']
            else:
                self.answer_succeed_json[self.username]['failing'][course_title][task_name] = task_result['msg']
            self.data_save()
        return True

    def online_question_answer_controller(self, homework_request_param, task_name):
        """
        提供参数调用 单选题、多选题、判断题、填充题 实现函数
        :return: 线上作业的完成情况
        """
        answer_result = self.answer_request.online_homework_answer_search(homework_request_param, task_name)
        if answer_result['taskStatus'] is True and 'answer_list' not in answer_result:  # 该线上作业已经完成
            return answer_result
        answer_list = answer_result['answer_list']
        task_id = homework_request_param['taskId']
        submit_form_data = {
            "questionAnswers": [], 'taskId': task_id, 'testUserId': answer_list['test_user_id'], 'version': None
        }
        for answer in answer_list['child_params']:  # 1-10个子问题提交
            task_result = self.answer_request.online_homework_submit_answer(homework_request_param, answer, task_name)
            if task_result['taskStatus'] is False:
                return task_result
            submit_form_data['questionAnswers'].append({
                'answer': answer, 'questionId': answer['questionId'], 'questionType': answer['questionType'],
                'sequence': answer['sequence'], 'userAnswerId': answer['userAnswerId']
                }
            )
        return self.answer_request.online_homework_all_submit_answer(homework_request_param, submit_form_data, task_name)

    def file_upload_controlled(self, homework_request_param, task_name):
        """
        提供参数调用 文件上传、文本填充
        :return: 作业完成情况
        """
        info_find_result = self.answer_request.img_text_info_find_search(homework_request_param, task_name)
        if info_find_result['taskStatus'] is False:  # 判断img图片查询状态
            return info_find_result
        course_title = homework_request_param['courseTitle']
        file_prefix = f"{self.answer_directory_path}/{course_title}"
        if info_find_result['imgStatus']:  # 判断是否存在图片上传
            file_path = f"{file_prefix}/{AnswerPathAndUploadUrl.items.value[task_name]['imgFilename']}"
            upload_result = self.answer_request.file_upload_homework_submit(homework_request_param, file_path, task_name)
            if upload_result['taskStatus']:  # 判断图片上传结果
                file_ids = [upload_result['fileIds']]
            else:
                return upload_result
        else:
            file_ids = []
        common_filename = AnswerPathAndUploadUrl.items.value[task_name]['commonFilename']
        if homework_request_param['taskName'] == '课程实践' or homework_request_param['taskName'] == "小组学习":
            common_file_path = f"{file_prefix}/{common_filename}"  # pdf是固定名称
        else:
            common_file_path = f"{file_prefix}/{course_title}-{common_filename}"  # 拼接字符串课程名称-答案名称
        upload_result = self.answer_request.file_upload_homework_submit(homework_request_param, common_file_path, task_name)
        if upload_result['taskStatus'] is False:  # 判断word、pdf上传结果
            return upload_result
        student_file_ids = upload_result['fileIds']
        if info_find_result['textStatus'] is True:   # pdf,img,word,文字 提交
            return self.answer_request.last_text_homework_submit(homework_request_param, student_file_ids, task_name)
        else:  # pdf,img,word 提交
            return self.answer_request.last_file_homework_submit(homework_request_param, file_ids, student_file_ids, task_name)

    def data_save(self):
        """ 将每个账户的成功、失败作业情况进行存储 """
        self.save_number_count += 1
        if self.save_number_count >= 10:
            file_path = ResourcePath.SuccessJsonFilePath.value
            self.answer_succeed_json = self.pipeline_save.answer_json_save(self.username, file_path, self.answer_succeed_json)
            self.save_number_count = 0
        return True

    def runs(self):
        """ 启动自动答题和上传功能 方法 """
        course_params_list = self.course_list_search_controller(self.log_print)
        homework_list = self.homework_list_search_controller(course_params_list, self.log_print)
        self.homework_answer_controlled(homework_list)
        self.data_save()


class OnlineInfoFindController(object):
    """ 线上账户信息查询 """
    def __init__(self, qt_gui, common_function):
        self.qt_gui = qt_gui
        self.common_function = common_function
        self.pipeline_save = DataSave(self.qt_gui, self.common_function)
        self.pipeline_read = DataRead(self.qt_gui, self.common_function)
        self.answer_succeed_json = None
        self.log_print = 'info_find'

    def answer_info_controller(self, account_file_path, specify_account_list=None):
        """
        根据传入的账户文件批量查询以及指定的账户列表指定查询
        """
        if len(specify_account_list) < 1:
            account_list = self.qt_gui.pipeline_read.read_account(account_file_path)
        else:
            account_list = specify_account_list
        token_list = self.common_function.get_token_list(account_list, self.log_print)
        for token_item in token_list:
            if self.answer_succeed_json is None:
                self.answer_succeed_json = self.pipeline_read.read_success_json(token_item['username'])
            answer_object = AnswerController(token_item, self.qt_gui, self.qt_gui.answer_directory_path, self.log_print)
            course_params_list = answer_object.course_list_search_controller(self.log_print)
            homework_list = answer_object.homework_list_search_controller(course_params_list, self.log_print)
            self.answer_info_request_controller(token_item, homework_list)
            break

    def answer_info_request_controller(self, token_item, homework_list):
        """ 线上答题信息查询，并调用json更新函数 """
        username = token_item['username']
        if username not in self.answer_succeed_json:  # 初始化一个新的科目，作业存储json对象
            self.answer_succeed_json[username] = {'success': {}, 'failing': {}}
        online_info_request = OnlineInfoFindTaskRequest(token_item, self.qt_gui, self.common_function)
        homework_name_list = list(AnswerPathAndUploadUrl.items.value.keys())  # 已有的作业对接
        for homework_param in homework_list:
            course_title = homework_param['courseTitle']
            if course_title not in self.answer_succeed_json[username]['success']:  # 记录每个科目
                self.answer_succeed_json[username]['success'][course_title] = {}
                self.answer_succeed_json[username]['failing'][course_title] = {}
            task_name = homework_param['taskName']
            if (task_name == '小组学习' or task_name == '课程实践') and "小组讨论" in homework_param['answerFileList']:
                pass
            elif '线上作业' in task_name or '在线作业' in task_name:  # or '在线作业' in task_name:  # 判断是否为线上作业
                route_key = '线上作业' if '线上作业' in task_name else '在线作业'
                task_result = online_info_request.online_answer_info_request(homework_param, route_key, self.log_print)
                if task_result['taskStatus'] is True:
                    self.answer_succeed_json[username]['success'][course_title][route_key] = task_result['homework_status']
                else:
                    self.answer_succeed_json[username]['failing'][course_title][route_key] = task_result['homework_status']
            elif task_name not in homework_param['answerFileList']:  # 如果作业名称不存在本地对应目录答案文件列表
                continue
            elif task_name not in homework_name_list:  # 如果作业名称不存在已支持的作业对接列表
                continue
            # 调用文件上传查询答题信息方法
            task_result = online_info_request.upload_answer_info_request(homework_param, self.log_print)
            if task_result['taskStatus'] is True:
                self.answer_succeed_json[username]['success'][course_title][task_name] = task_result['homework_status']
            else:
                self.answer_succeed_json[username]['failing'][course_title][task_name] = task_result['homework_status']
        self.data_save(token_item)  # 调用本地json文件更新方法
        return True

    def data_save(self, token_item):
        """ 将每个账户的成功、失败作业情况进行存储 """
        username = token_item['username']
        file_path = ResourcePath.SuccessJsonFilePath.value
        self.answer_succeed_json = self.pipeline_save.answer_json_save(username, file_path, self.answer_succeed_json, self.log_print)
        return True

    def token_verify(self):
        pass


class BrushClassController(object):
    def __init__(self, log_print):
        self.log_print = log_print

    def course_info_search_controller(self, items):
        """
        搜索主修科目的标题、资源id
        :return: 课程的标题、资源id list
        """
        course_info_list = items['brush_class_request'].course_info_search_request(items)
        return course_info_list

    def video_info_search_controller(self, items, course_info_list):
        """
        搜索课程、直播两个模块的视频id、标题、视频总时长、视频当前时长
        :return: 课程、直播两个模块的视频信息list
        """
        course_video_list = []
        live_video_list = []
        for param_items in course_info_list:
            course_video_list += items['brush_class_request'].course_video_info_search_request(items, param_items)
            live_video_list += items['brush_class_request'].live_video_info_search_request(items, param_items)
        return {'course_video_list': course_video_list, 'live_video_list': live_video_list}

    def course_video_add_progress_controller(self, items, course_video_list):
        """
        请求课程模块的视频接口，添加进度时长
        :return:
        """
        for param_items in course_video_list:
            logger_item = items['brush_class_request'].course_video_param_add_progress_request(param_items, items)
            items['data_save_queue'].put(logger_item)  # 存储请求成功后的信息
        return items

    def live_video_add_progress_controller(self, items, live_video_list):
        """
        请求直播模块的视频接口，添加进度时长
        :return:
        """
        for param_items in live_video_list:
            logger_item = items['brush_class_request'].live_video_add_progress_request(param_items, items)
            items['data_save_queue'].put(logger_item)  # 存储请求成功后的信息
        return items

    def runs(self, account_item, queue_items, qt_gui=None, choose_course_info_item=None):
        common_function = CommonFunction(qt_gui)  # 创建公共函数对象
        pipeline_save = DataSave(qt_gui, common_function)
        pipeline_read = DataRead(qt_gui, common_function)
        brush_class_request = BrushClassTaskRequest(self.log_print)
        items = {
            'account_item': account_item, 'common_function': common_function, 'pipeline_save': pipeline_save,
            'pipeline_read': pipeline_read, 'brush_class_request': brush_class_request, 'qt_gui': qt_gui,
            'data_save_queue': queue_items['data_save_queue'], 'signal_save_queue': queue_items['signal_save_queue']
        }
        course_info_list = self.course_info_search_controller(items)  # 调用主修科目搜索函数
        video_info_list = self.video_info_search_controller(items=items, course_info_list=course_info_list)
        items = self.course_video_add_progress_controller(items, video_info_list['course_video_list'])
        items = self.live_video_add_progress_controller(items, video_info_list['live_video_list'])

    def code_annotation(self):
        """
        函数调用流程：
            1、主修科目info搜索
            2、课程模块、直播模块的视频标题、资源id搜索
            3、课程视频进度条添加函数
            4、直播视频进度条添加函数
            5、添加该账户任务完成信号
        待提高的功能代码：
            1、任务完成信号
            2、线程之间的通信
        :return:
        """

