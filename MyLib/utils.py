import os
import sys
import time
import execjs
import requests
from requests import exceptions as request_exceptions
from requests_toolbelt.multipart.encoder import MultipartEncoder
from MyLib.constants import TaskReturnMessage, Headers, AnswerPathAndUploadUrl, BrushClassUrl
from MyLib.parse import AnswerResponseParse, BrushClassResponseParse
from MyLib.settings import ResourcePath


class YkLogin(object):
    def __init__(self, username, password, common_function):
        self.common_headers = Headers.CommonHeaders.value
        self.login_url = AnswerPathAndUploadUrl.items.value['url']['loginUrl']
        self.username = username
        self.password = password
        self.common_function = common_function
        self.request_service = RequestService(self.username, self.common_function)

    def login(self, log_print=None):
        token = 'null'
        form_data = {
            'imageValidCode': "", 'loginType': 1, 'orgId': 260,
            'passwd': self.common_function.jsEncrypt.call('AES_Encrypt', self.password),
            'rentId': 179, 'userName': self.username
        }
        params = {'data': form_data, 'parameter_mode': 'json', 'headers': self.common_headers}
        request_result = self.request_service.request(url=self.login_url, method='POST', time_sleep=1.5, items=params)
        if request_result['status'] is True and request_result['response'].json():
            login_response = request_result['response']
            if login_response.json()['code'] == 'REQ001':
                token = login_response.json()['data']['token']
                content = f"userName:{self.username} Token：{token} - {login_response.json()['msg']}\n"
                log_content = self.common_function.get_log_item(
                    content=content, one=self.username, four='登录成功', five=f"token：{token}"
                )
            else:
                content = f"userName:{self.username} Token：{token} - {login_response.json()['msg']}\n"
                log_content = self.common_function.get_log_item(
                    content=content, one=self.username, four='登录失败', five=login_response.json()['msg']
                )
        else:
            content = f"userName:{self.username} Token：{token} - 连续请求不成功\n"
            log_content = self.common_function.get_log_item(
                content=content, one=self.username, four='登录失败', five=f"连续请求不成功"
            )
        self.common_function.logger_print(log_content, log_print)
        return token


class RequestService(object):
    def __init__(self,  username, common_function):
        self.username = username
        self.common_function = common_function

    def request(self, url, method='GET', time_sleep=1.25, max_retry=3, items=None):
        request_result = {'status': False}
        try:
            time.sleep(time_sleep)
            headers = items['headers']
            if method == 'GET':
                response = requests.get(url=url, headers=headers, timeout=5)
            elif method == 'POST' and items['parameter_mode'] == 'json':
                response = requests.post(url=url, headers=headers, json=items['data'], timeout=5)
            elif method == 'POST' and items['parameter_mode'] == 'data':
                response = requests.post(url=url, headers=headers, data=items['data'], timeout=5)
            response.raise_for_status()  # 如果响应码不为 200，抛出异常
            request_result['status'] = True
            request_result['response'] = response
            return request_result
        except request_exceptions.ConnectTimeout:
            log_content = self.common_function.get_log_item(
                content=f'{url}-请求失败 ConnectTimeout!\n', one=self.username, four='请求失败 ConnectTimeout', five=url
            )
            self.common_function.logger_print(log_content)
        except request_exceptions.RequestException:
            log_content = self.common_function.get_log_item(
                content=f'{url}-请求失败 RequestException!\n', one=self.username, four='请求失败 RequestException', five=url
            )
            self.common_function.logger_print(log_content)
        if max_retry > 0:
            return self.request(url=url, method=method, time_sleep=time_sleep, max_retry=max_retry - 1, items=items)
        return request_result


class CommonFunction(object):
    def __init__(self, qt_gui=None):
        self.qt_gui = None if qt_gui is None else qt_gui
        self.js_file_dir = ResourcePath.JsAesEncryptFilePath.value
        with open(file=self.js_file_dir, mode='r', encoding='utf-8') as fis:
            js_code = fis.read()
        self.jsEncrypt = execjs.compile(js_code)
        self.everyday_token_path = ResourcePath.TokenPath.value

    def get_log_item(self, content='null', one='null', two='null', three='null', four='null', five='null'):
        Log_item = {
            'content': f"{content}",
            'loggerItem': {
                'one': one, 'two': two, 'three': three, 'four': four, 'five': five
            }
        }
        return Log_item

    def logger_print(self, item, route_key=None):
        if self.qt_gui is None:
            print(item['content'], end='')
        elif route_key is None:
            self.qt_gui.logger_output(item['loggerItem'], 'answer')
        elif route_key == 'info_find':
            self.qt_gui.logger_output(item['loggerItem'], route_key)
        elif route_key == 'brush_class':
            self.qt_gui.logger_output(item['loggerItem'], route_key)

    def get_token_list(self, account_ls, log_print=None):
        """ 获取token """
        exists_token_list = self.qt_gui.pipeline_read.read_everyday_token(self.everyday_token_path)
        exists_token_item = dict()
        for item in exists_token_list:
            exists_token_item[item['username']] = item['token']
        save_status = False
        token_ls = list()
        for item in account_ls[:6]:
            username = item['username']
            password = item['password']
            if username in exists_token_item:
                token_ls.append(
                    {'username': username, 'password': password, 'token': exists_token_item[username]}
                )
                continue
            token = YkLogin(username, password, self).login(log_print)
            if token is False:
                continue
            token_ls.append({'username': username, 'password': password, 'token': token})  # 返回指定账户的token
            exists_token_list.append({'username': username, 'password': password, 'token': token})  # 写入所有的token
            save_status = True
        if save_status:
            self.qt_gui.pipeline_save.json_save(file_path=self.everyday_token_path, token_list=exists_token_list)
        return token_ls

    def file_exists(self, username, course_title, task_name, file_path):
        if os.path.exists(file_path) is False:
            content = f"{username} {course_title} {task_name} {file_path} - 文件不存在\n"
            log_content = self.get_log_item(content=content, one=username, two=course_title, three=task_name,
                four='文件不存在', five=file_path
            )
            self.logger_print(log_content)
            return {'taskStatus': False, 'msg': f"文件不存在：{file_path}"}
        return TaskReturnMessage.FileExists.value


class AnswerTaskRequest(object):
    def __init__(self, params_items):
        self.account_items = params_items['account_items']
        self.qt_gui = params_items['qt_gui']
        self.answer_directory_path = params_items['answer_directory_path']  # 答案目录
        self.answer_succeed_json = params_items['answer_succeed_json']
        self.username = self.account_items['username']  # 该取值无误
        self.common_headers = Headers.CommonHeaders.value
        self.common_headers['authorization'] = self.account_items['token']
        self.file_upload_headers = Headers.FileUploadHeaders.value
        self.file_upload_headers['authorization'] = self.account_items['token']
        self.common_function = CommonFunction(self.qt_gui)  # 创建公共函数对象
        self.request_service = RequestService(self.username, self.common_function)  # 创建请求类对象
        self.answer_parse = AnswerResponseParse(params_items, self.common_function)  # 创建响应解析类

    def course_list_search_request(self, log_print=None):
        # 请求 科目接口，查询子作业的信息和参数
        course_params_list = list()
        log_content = self.common_function.get_log_item(one=self.username)  # 获取日志信息
        url = AnswerPathAndUploadUrl.items.value['url']['courseListSearchUrl']
        params = {'data': {}, 'parameter_mode': 'json', 'headers': self.common_headers}
        request_result = self.request_service.request(url=url, method='POST', time_sleep=1.5, items=params)
        if request_result['status'] is True and request_result['response'].json():
            response = request_result['response']
            if response.json()['code'] != 'REQ001' and 'processList' not in response.json()['data']:
                log_content['content'] = f"{self.username} courseListSearch 数据响应不一致 缺失REQ001 or data!\n"
                log_content['loggerItem']['four'] = f"courseListSearch 数据响应不一致 缺失REQ001 or data!"
                self.common_function.logger_print(log_content, log_print)
                return course_params_list
        else:
            log_content['content'] = f"{self.username} courseListSearch 连续请求不成功\n"
            log_content['loggerItem']['four'] = f"courseListSearch 连续请求不成功!"
            self.common_function.logger_print(log_content, log_print)
            return course_params_list
        return self.answer_parse.course_search_response_parse(response, log_print)  # 调用解析响应函数

    def homework_list_search_request(self, course_item, log_print=None):
        # 根据科目id等信息，请求子作业的接口，存储子作业的参数信息
        homework_param_list = list()
        url = AnswerPathAndUploadUrl.items.value['url']['homeworkListSearchUrl']
        course_title = course_item['courseTitle']
        course_resource_id = course_item['courseResourceId']
        file_prefix = f"{self.answer_directory_path}/{course_title}"
        log_content = self.common_function.get_log_item(one=self.username, two=course_title)  # 获取日志信息
        # 本地对应目录的答案文件列表
        answer_file_list = [os.path.splitext(path)[0].split('-')[-1] for path in os.listdir(file_prefix)]
        form_data = {'courseResourceId': course_resource_id}
        params = {'data': form_data, 'parameter_mode': 'json', 'headers': self.common_headers}
        request_result = self.request_service.request(url=url, method='POST', time_sleep=1.5, items=params)
        if request_result['status'] is True and request_result['response'].json():
            response = request_result['response']
            if response.json()['code'] != 'REQ001' and 'recordList' not in response.json()['data']:
                log_content['content'] = f"{self.username} homeworkListSearch 数据响应不一致 缺失REQ001 or data!\n"
                log_content['loggerItem']['four'] = f"homeworkListSearch 数据响应不一致 缺失REQ001 or data!"
                self.common_function.logger_print(log_content, log_print)
                return homework_param_list
        else:
            log_content['content'] = f"{self.username} homeworkListSearch 连续请求不成功!\n"
            log_content['loggerItem']['four'] = f"homeworkListSearch 连续请求不成功!"
            self.common_function.logger_print(log_content, log_print)
            return homework_param_list
        return self.answer_parse.homework_search_response_parse(response, course_item, answer_file_list, log_print)

    def online_homework_answer_search(self, homework_request_param, task_name):
        # 搜索单选题、多选题、判断题、填充题 的答案
        course_title = homework_request_param['courseTitle']
        if homework_request_param['score'] is not None and homework_request_param['score'] > 80:
            content = f"{self.username} {course_title} {task_name} 线上作业已完成 {homework_request_param['score']}"
            log_content = self.common_function.get_log_item(content=content, one=self.username, two=course_title,
                three=task_name, four='线上作业已完成', five=f"成绩：{homework_request_param['score']}"
            )
            self.common_function.logger_print(log_content)
            return TaskReturnMessage.OnlineHomeWorkFinished.value  # score不为None 并且大于80分
        start_url = AnswerPathAndUploadUrl.items.value[task_name]['startUrl']
        start_params = {
            'id': homework_request_param['examId'], 'subjectId': homework_request_param['subjectId'],
            'taskId': homework_request_param['taskId']
        }
        params = {'data': start_params, 'parameter_mode': 'json', 'headers': self.common_headers}
        request_result = self.request_service.request(url=start_url, method='POST', time_sleep=1.5, items=params)
        if request_result['status'] is True and request_result['response'].json():
            start_response = request_result['response']
        else:
            return TaskReturnMessage.QuestionAnswerSearchRequestFailing.value
        if 'answer' not in start_response.json()['data']['groups'][0]['questions'][0]:
            time.sleep(1.5)
            request_result = self.request_service.request(url=start_url, method='POST', time_sleep=1.5, items=params)
        if request_result['status'] is True and request_result['response'].json():
            start_response = request_result['response']
            if start_response.json()['code'] != 'REQ001' or start_response.json()['msg'] != "请求成功":
                return TaskReturnMessage.QuestionAnswerSearchDataLost.value
            elif 'data' not in start_response.json() or 'groups' not in start_response.json()['data']:
                return TaskReturnMessage.QuestionAnswerSearchDataLost.value
            elif 'questions' not in start_response.json()['data']['groups'][0]:
                return TaskReturnMessage.QuestionAnswerSearchDataLost.value
        else:
            return TaskReturnMessage.QuestionAnswerSearchRequestFailing.value
        return self.answer_parse.online_question_answer_search_response_parse(homework_request_param, start_response)

    def online_homework_submit_answer(self, homework_request_param, answer, task_name):
        """ 线上作业 子问题 提交答案 """
        course_title = homework_request_param['courseTitle']
        sequence = answer['sequence']
        update_url = AnswerPathAndUploadUrl.items.value[task_name]['updateUrl']
        params = {'data': answer, 'parameter_mode': 'json', 'headers': self.common_headers}
        request_result = self.request_service.request(url=update_url, method='POST', time_sleep=1.5, items=params)
        if request_result['status'] is True and request_result['response'].json():
            update_response = request_result['response']
            content = f"{self.username} {course_title} {task_name} 第{sequence}题 - {update_response.json()['msg']}\n"
            log_content = self.common_function.get_log_item(content=content, one=self.username,
                two=course_title, three=task_name, four=update_response.json()['msg'], five=f"第{sequence}题"
            )
            self.common_function.logger_print(log_content)
            if update_response.json()['code'] != 'REQ001':
                return {'taskStatus': False, 'msg': update_response.json()['msg']}
        else:
            content = f"{self.username} {course_title} {task_name} 第{sequence}题 - 连续请求不成功\n"
            log_content = self.common_function.get_log_item(content=content, one=self.username,
                two=course_title, three=task_name, four='连续请求不成功', five=f"第{sequence}题"
            )
            self.common_function.logger_print(log_content)
            return TaskReturnMessage.ChildHomeWorkFailing.value
        return TaskReturnMessage.ChildHomeWorkSuccess.value

    def online_homework_all_submit_answer(self, homework_request_param, submit_form_data, task_name):
        """线上作业 总提交 答案 """
        course_title = homework_request_param['courseTitle']
        submit_url = AnswerPathAndUploadUrl.items.value[task_name]['submitUrl']
        params = {'data': submit_form_data, 'parameter_mode': 'json', 'headers': self.common_headers}
        request_result = self.request_service.request(url=submit_url, method='POST', time_sleep=1.5, items=params)
        if request_result['status'] is True and request_result['response'].json():
            submit_response = request_result['response']
            content = f"{self.username} {course_title} {task_name} - {submit_response.json()['msg']}\n"
            log_content = self.common_function.get_log_item(content=content, one=self.username,
                two=course_title, three=task_name, four=submit_response.json()['msg'], five='选择题总提交'
            )
            self.common_function.logger_print(log_content)
            if submit_response.json()['code'] == 'REQ001':
                return TaskReturnMessage.LastOnlineHomeWorkSuccess.value
            return {'taskStatus': False, 'msg': submit_response.json()['msg']}
        else:
            content = f"{self.username} {course_title} {task_name} - 连续请求不成功\n"
            log_content = self.common_function.get_log_item(content=content, one=self.username,
                two=course_title, three=task_name, four='连续请求不成功', five='选择题总提交'
            )
            self.common_function.logger_print(log_content)
            return TaskReturnMessage.LastOnlineHomeWorkFailing.value

    def img_text_info_find_search(self, homework_request_param, task_name):
        # 查询该作业是否需要上传图片、填充文字;
        info_url = AnswerPathAndUploadUrl.items.value['url']['infoUrl']
        task_id = homework_request_param['taskId']
        course_title = homework_request_param['courseTitle']
        params = {'data': {'taskId': task_id}, 'parameter_mode': 'json', 'headers': self.common_headers}
        request_result = self.request_service.request(url=info_url, method='POST', time_sleep=1.5, items=params)
        if request_result['status'] is True and request_result['response'].json():
            info_response = request_result['response']
            content = f"{self.username} - {course_title} {task_name} infoFind {info_response.json()['msg']}\n"
            log_content = self.common_function.get_log_item(content=content, one=self.username,
                two=course_title, three=task_name, four=info_response.json()['msg'], five='图片、文字填充-查询阶段'
            )
            self.common_function.logger_print(log_content)
            if info_response.json()['code'] != 'REQ001':
                return TaskReturnMessage.ImgTextFindFailingDetail.value
        else:
            content = f"{self.username} - {course_title} {task_name} infoFind 图片、文字填充-连续请求不成功!\n"
            log_content = self.common_function.get_log_item(content=content, one=self.username,
               two=course_title, three=task_name, four='查询失败-连续请求不成功', five='图片、文字填充-查询阶段'
            )
            self.common_function.logger_print(log_content)
            return TaskReturnMessage.ImgTextFindFailing.value
        return self.answer_parse.img_text_info_find_response_parse(info_response)

    def file_upload_homework_submit(self, homework_request_param, file_path, task_name):
        # 上传 pdf、图片、word
        course_title = homework_request_param['courseTitle']
        file_exists_result = self.common_function.file_exists(self.username, course_title, task_name, file_path)
        if file_exists_result['taskStatus'] is False:
            return file_exists_result
        upload_url = AnswerPathAndUploadUrl.items.value['url']['uploadUrl']
        multipart_encoder = MultipartEncoder(fields={
            'file': (file_path, open(file_path, 'rb'), 'application/octet-stream')
        })
        self.file_upload_headers['Content-Type'] = multipart_encoder.content_type
        params = {'data': multipart_encoder, 'parameter_mode': 'data', 'headers': self.file_upload_headers}
        request_result = self.request_service.request(url=upload_url, method='POST', time_sleep=1.5, items=params)
        if request_result['status'] is True and request_result['response'].json():
            upload_response = request_result['response']
            content = f"{self.username} {course_title} {task_name} {file_path} {upload_response.json()['msg']} 文件上传\n"
            log_content = self.common_function.get_log_item(content=content, one=self.username, two=course_title,
                three=task_name, four=upload_response.json()['msg'], five=f"文件上传阶段：{file_path}"
            )
            self.common_function.logger_print(log_content)
            if upload_response.json()['code'] == 'REQ001' or upload_response.json()['msg'] == '请求成功':
                task_result = TaskReturnMessage.FileUploadSuccess.value
                task_result['msg'] += f' {file_path}'
                task_result["fileIds"] = upload_response.json()['data']['id']
                return task_result
            return {'taskStatus': False, 'msg': f"{upload_response.json()['msg']} {file_path}"}
        else:
            content = f"{self.username} - {task_name} {file_path} 文件上传失败 - 连续请求不成功\n"
            log_content = self.common_function.get_log_item(content=content, one=self.username, two=course_title,
                three=task_name, four='文件上传失败', five=f"文件上传失败-连续请求不成功：{file_path}"
            )
            self.common_function.logger_print(log_content)
            task_result = TaskReturnMessage.FileUploadFailing.value
            task_result['msg'] += f' {file_path}'
            return task_result

    def last_text_homework_submit(self, homework_request_param, student_file_ids, task_name):
        # pdf,img,word,文字 提交
        answer_url = AnswerPathAndUploadUrl.items.value['url']['answerUrl']
        course_title = homework_request_param['courseTitle']
        task_id = homework_request_param['taskId']
        text_params = {
            'answer': "1", 'answerText': "<p>1</p>", 'fileIds': [], 'studentFileIds': [student_file_ids],
            'taskId': task_id, 'version': 'null'
        }
        params = {'data': text_params, 'parameter_mode': 'json', 'headers': self.common_headers}
        request_result = self.request_service.request(url=answer_url, method='POST', time_sleep=1.5, items=params)
        if request_result['status'] is True and request_result['response'].json():
            text_response = request_result['response']
            content = f"{self.username} {course_title} {task_name} {text_response.json()['msg']} 文本填充"
            log_content = self.common_function.get_log_item(content=content, one=self.username, two=course_title,
                three=task_name, four=text_response.json()['msg'], five='总提交-文本填充'
            )
            self.common_function.logger_print(log_content)
            if text_response.json()['code'] == 'REQ001':
                return TaskReturnMessage.LastTextUploadSuccess.value
            return {'taskStatus': False, 'msg': f'总提交失败-文本填充阶段 {text_response.json()["msg"]}'}
        else:
            content = f"{self.username} {course_title} {task_name} 总提交-文本填充失败 连续请求不成功\n"
            log_content = self.common_function.get_log_item(content=content, one=self.username, two=course_title,
                three=task_name, four='总提交-文本填充失败', five='连续请求不成功'
            )
            self.common_function.logger_print(log_content)
            return TaskReturnMessage.LastTextUploadFailing.value

    def last_file_homework_submit(self, homework_request_param, file_ids, student_file_ids, task_name):
        # pdf,img,word 提交
        answer_url = AnswerPathAndUploadUrl.items.value['url']['answerUrl']
        task_id = homework_request_param['taskId']
        course_title = homework_request_param['courseTitle']
        submit_params = {
            'answer': "", 'answerText': "", 'fileIds': file_ids, 'studentFileIds': [student_file_ids],
            'taskId': task_id, 'version': 'null'
        }
        params = {'data': submit_params, 'parameter_mode': 'json', 'headers': self.common_headers}
        request_result = self.request_service.request(url=answer_url, method='POST', time_sleep=1.5, items=params)
        if request_result['status'] is True and request_result['response'].json():
            submit_response = request_result['response']
            content = f"{self.username} {course_title} {task_name} {submit_response.json()['msg']} 总提交-文件上传"
            log_content = self.common_function.get_log_item(content=content, one=self.username, two=course_title,
                three=task_name, four=submit_response.json()['msg'], five='总提交-文件上传'
            )
            self.common_function.logger_print(log_content)
            if submit_response.json()['code'] == 'REQ001':
                return TaskReturnMessage.LastFileUploadSuccess.value
            return {'taskStatus': False, 'msg': f'总提交-文件上传失败 {submit_response.json()["msg"]}'}
        else:
            content = f"{self.username} {course_title} {task_name} 总提交-文本填充失败 连续请求不成功\n"
            log_content = self.common_function.get_log_item(content=content, one=self.username, two=course_title,
                three=task_name, four='总提交-文件上传失败', five='连续请求不成功'
            )
            self.common_function.logger_print(log_content)
            return TaskReturnMessage.LastFileUploadFailing.value


class OnlineInfoFindTaskRequest(object):
    def __init__(self, token_items, qt_gui, common_function):
        self.qt_gui = qt_gui
        self.username = token_items['username']
        self.common_function = common_function
        self.common_headers = Headers.CommonHeaders.value
        self.common_headers['authorization'] = token_items['token']
        self.request_service = RequestService(self.username, self.common_function)  # 创建请求类对象

    def online_answer_info_request(self, homework_param, route_key, log_print=None):
        """ 根据传入的作业详情进行数据比较，判断该作业的完成情况
            :return 作业完成情况
        """
        course_title = homework_param['courseTitle']
        task_name = route_key
        score = homework_param['score']
        homework_status = '未完成' if score is None or score <= 0 else '已完成'
        log_content = self.common_function.get_log_item(one=self.username, two=course_title, three=task_name,
            four=homework_status, five=f"成绩详情：{score}"
        )
        self.common_function.logger_print(log_content, log_print)
        return {"taskStatus": True if homework_status == '已完成' else False, 'homework_status': homework_status}

    def upload_answer_info_request(self, homework_param, log_print=None):
        """ 账户文件上传答题的详细信息情况
        :return 作业完成情况
        """
        url = AnswerPathAndUploadUrl.info_find_items.value['answerSuccessUrl']
        course_title = homework_param['courseTitle']
        task_name = homework_param['taskName']
        log_content = self.common_function.get_log_item(one=self.username, two=course_title, three=task_name)  # 获取日志信息
        task_id = homework_param['taskId']
        params = {'data': {'taskId': task_id}, 'parameter_mode': 'json', 'headers': self.common_headers}
        request_result = self.request_service.request(url=url, method='POST', time_sleep=1.5, items=params)
        if request_result['status'] is True and request_result['response'].json():
            upload_answer_response = request_result['response']
            if upload_answer_response.json()['code'] == 'REQ001' and "请求成功" in upload_answer_response.json()['msg']:
                # 此处"answerFileList" is None 表示该账户对应的作业上传情况为空
                homework_status = '未完成' if upload_answer_response.json()['data']['answerFileList'] is None else '已完成'
            else:
                homework_status = '请求失败'
                return {"taskStatus": False, 'homework_status': homework_status}
            msg = f"线上答题信息查询 {upload_answer_response.json()['msg']}"
            log_content['content'] = f'{self.username} {course_title} {task_name} {homework_status} {msg}'
            log_content['loggerItem']['four'] = homework_status
            log_content['loggerItem']['five'] = msg
            self.common_function.logger_print(log_content, log_print)
            return {"taskStatus": True if homework_status == '已完成' else False, 'homework_status': homework_status}
        else:
            log_content['content'] = f"{self.username} {course_title} {task_name} 线上答题信息查询 连续请求不成功\n"
            log_content['loggerItem']['four'] = f"连续请求不成功"
            log_content['loggerItem']['five'] = f"线上答题信息查询!"
            self.common_function.logger_print(log_content, log_print)
        return {"taskStatus": False, 'homework_status': '线上答题信息查询 连续请求不成功'}


class BrushClassTaskRequest(object):
    def __init__(self, log_print, qt_gui=None, common_function=None):
        self.log_print = log_print
        self.brush_class_parse = BrushClassResponseParse(self.log_print)  # 创建解析类对象
        self.add_progress_url = BrushClassUrl.items.value['add_progress']
        self.add_time_url = BrushClassUrl.items.value['add_time']

    def course_info_search_request(self, items):
        """ 请求主修科目接口，对响应进行判断，将正确的响应传入course_info_search_parse解析函数
            :return 课程title，课程资源id list
        """
        course_info_list = []
        account_item = items['account_item']
        username = account_item['username']
        headers = Headers.CommonHeaders.value
        headers['authorization'] = account_item['token']  # 组建请求头信息
        params = {'data': {}, 'parameter_mode': 'json', 'headers': headers}
        request_service = RequestService(username, items['common_function'])  # 创建请求类对象
        url = BrushClassUrl.items.value['course_list']
        request_result = request_service.request(url=url, method='POST', time_sleep=1.5, items=params)
        log_content = items['common_function'].get_log_item(one=username, five='主修科目搜索 阶段')
        content = '请求成功'
        if request_result['status'] is True and request_result['response'].json():
            course_list_response = request_result['response']
            status = course_list_response.json()['code']
            if status == 'REQ001' and 'processList' in course_list_response.json()['data']:
                course_info_list = self.brush_class_parse.course_info_search_parse(items, course_list_response)
                return course_info_list
            else:
                content = 'course_info_search_request 数据响应不一致 缺失REQ001 or data'
        else:
            content = 'course_info_search_request 连续请求不成功'
        log_content['content'] = f'{username} {content}'
        log_content['loggerItem']['four'] = content
        items['common_function'].logger_print(log_content, self.log_print)
        return course_info_list

    def course_video_info_search_request(self, object_items, param_items):
        """ 课程视频接口请求，并将正确的响应，传入解析函数中
            :return 课程视频id、标题、视频总时长、视频当前时长 list
        """
        course_video_list = list()
        username = object_items['account_item']['username']
        course_resource_id = param_items['course_resource_id']
        major_title = param_items['major_title']
        object_items['major_title'] = major_title  # 存储主修科目名称至 类方法对象中
        headers = Headers.CommonHeaders.value
        headers['authorization'] = object_items['account_item']['token']  # 组建请求头信息
        params = {'parameter_mode': 'json', 'headers': headers, 'data': {'courseResourceId': course_resource_id}}
        url = BrushClassUrl.items.value['course_video_info']
        request_service = RequestService(username, object_items['common_function'])  # 创建请求类对象
        request_result = request_service.request(url=url, method='POST', time_sleep=1.5, items=params)
        log_content = object_items['common_function'].get_log_item(one=username, two=major_title, five='视频信息搜索 阶段')
        content = '课程 请求成功'
        if request_result['status'] is True and request_result['response'].json():
            video_list_response = request_result['response']
            if video_list_response.json()['code'] == 'REQ001' and '请求成功' in video_list_response.json()['msg']:
                course_video_list = self.brush_class_parse.course_video_info_parse(object_items, video_list_response)
            else:
                content = 'course_video_info_search_request 课程 数据响应不一致 缺失REQ001 or data'
        else:
            content = 'video_info_search_request 课程 连续请求不成功'
        log_content['content'] = f'{username} {content}'
        log_content['loggerItem']['three'] = "课程 全部检索完成"
        log_content['loggerItem']['four'] = content
        object_items['common_function'].logger_print(log_content, self.log_print)
        return course_video_list

    def live_video_info_search_request(self, object_items, param_items):
        """ 直播视频、接口请求，将正确的响应传入解析函数
            :return 直播标题、总时长、当前时长、科目名称 list
        """
        live_video_list = []
        username = object_items['account_item']['username']
        course_resource_id = param_items['course_resource_id']
        major_title = param_items['major_title']
        object_items['major_title'] = major_title  # 存储主修科目名称至 类方法对象中
        headers = Headers.CommonHeaders.value
        headers['authorization'] = object_items['account_item']['token']  # 组建请求头信息
        params = {'parameter_mode': 'json', 'headers': headers, 'data': {'id': course_resource_id}}
        url = BrushClassUrl.items.value['live_video_info']
        request_service = RequestService(username, object_items['common_function'])  # 创建请求类对象
        request_result = request_service.request(url=url, method='POST', time_sleep=1.5, items=params)
        log_content = object_items['common_function'].get_log_item(one=username, two=major_title, five='视频信息搜索 阶段')
        content = '直播 请求成功'
        if request_result['status'] is True and request_result['response'].json():
            video_list_response = request_result['response']
            if video_list_response.json()['code'] == 'REQ001' and '请求成功' in video_list_response.json()['msg']:
                live_video_list = self.brush_class_parse.live_video_info_parse(object_items, video_list_response)
            else:
                content = 'live_video_info_search_request 直播 数据响应不一致 缺失REQ001 or data'
        else:
            content = 'video_info_search_request 直播 连续请求不成功'
        log_content['content'] = f'{username} {content}'
        log_content['loggerItem']['three'] = "直播 全部检索完成"
        log_content['loggerItem']['four'] = content
        return live_video_list

    def course_video_param_add_progress_request(self, param_items, object_items):
        seconds = 10
        username = object_items['account_item']['username']
        course_now_time = param_items['course_now_time']
        request_total = int(param_items['course_total_time'] / 10) + 1 - int(course_now_time / 10)
        last_study_time = course_now_time
        video_id = param_items['videoId']
        headers = Headers.CommonHeaders.value
        headers['authorization'] = object_items['account_item']['token']  # 组建请求头信息
        request_service = RequestService(username, object_items['common_function'])  # 创建请求类对象
        log_content = object_items['common_function'].get_log_item(one=username, two=param_items['major_title'],
            three=param_items['course_title'], five='课程视频 进度条添加阶段')
        for i in range(request_total):
            last_study_time += seconds
            form_data = {'lastStudyTime': last_study_time, 'videoId': video_id}
            params = {'data': form_data, 'parameter_mode': 'json', 'headers': headers}
            request_service.request(url=self.add_progress_url, method='POST', time_sleep=1.5, items=params)
            local_create_time = int((time.time() + seconds) * 1000)
            form_data = {
                'appType': '3', 'charterSectionId': param_items['charterSectionId'], 'lastStudyTime': last_study_time,
                'localCreateTime': local_create_time, 'studyTime': '10', 'uploadType': '1', 'videoId': video_id,
                'videoType': '1'
            }
            params = {'data': form_data, 'parameter_mode': 'json', 'headers': headers}
            request_result = request_service.request(url=self.add_time_url, method='POST', time_sleep=1.5, items=params)
            if request_result['status'] is True and request_result['response'].json():
                add_response = request_result['response']
                if add_response.json()['code'] == 'REQ001' and '请求成功' in add_response.json()['msg']:
                     content = f"{param_items['video_name']} 添加成功 {i + 1}/{request_total}"
                else:
                    content = f"{param_items['video_name']} 添加失败 {i + 1}/{request_total} 数据响应不一致 缺失REQ001"
            else:
                content = f'{param_items["video_name"]} 添加失败 {i + 1}/{request_total} 连续请求不成功'
            log_content['content'] = f'{username} {content}'
            log_content['loggerItem']['four'] = content
            object_items['common_function'].logger_print(log_content, self.log_print)
        content = f'观看完成 --------------------------- {request_total}/{request_total}'
        log_content['content'] = f'{username} {content}'
        log_content['loggerItem']['four'] = content
        object_items['common_function'].logger_print(log_content, self.log_print)
        return log_content['loggerItem']

    def live_video_add_progress_request(self, param_items, object_items):
        seconds = 10
        username = object_items['account_item']['username']
        live_now_time = param_items['live_now_time']
        request_total = int(param_items['live_total_time'] / 10) + 1 - int(live_now_time / 10)
        last_study_time = live_now_time
        headers = Headers.CommonHeaders.value
        headers['authorization'] = object_items['account_item']['token']  # 组建请求头信息
        request_service = RequestService(username, object_items['common_function'])  # 创建请求类对象
        log_content = object_items['common_function'].get_log_item(one=username, two=param_items['major_title'],
             three=param_items['live_title'], five='直播视频 进度条添加阶段')
        for i in range(request_total):
            last_study_time += seconds
            form_data = {'lastStudyTime': last_study_time, 'videoId': param_items['videoId']}
            params = {'data': form_data, 'parameter_mode': 'json', 'headers': headers}
            request_service.request(url=self.add_progress_url, method='POST', time_sleep=1.5, items=params)
            local_create_time = int((time.time() + seconds) * 1000)
            form_data = {
                'appType': '3', 'lastStudyTime': last_study_time, 'localCreateTime': local_create_time,
                'studyTime': '10', 'uploadType': '1', 'videoId': param_items['videoId']
            }
            params = {'parameter_mode': 'json', 'headers': headers, 'data': form_data}
            request_result = request_service.request(url=self.add_time_url, method='POST', time_sleep=1.5, items=params)
            if request_result['status'] is True and request_result['response'].json():
                add_response = request_result['response']
                if add_response.json()['code'] == 'REQ001' and '请求成功' in add_response.json()['msg']:
                     content = f"{param_items['video_title']} 添加成功 {i + 1}/{request_total}"
                else:
                    content = f"{param_items['video_title']} 添加失败 {i + 1}/{request_total} 数据响应不一致 缺失REQ001"
            else:
                content = f'{param_items["video_title"]} 添加失败 {i + 1}/{request_total} 连续请求不成功'
            log_content['content'] = f'{username} {content}'
            log_content['loggerItem']['four'] = content
            object_items['common_function'].logger_print(log_content, self.log_print)
        content = f'观看完成 --------------------------- {request_total}/{request_total}'
        log_content['content'] = f'{username} {content}'
        log_content['loggerItem']['four'] = content
        object_items['common_function'].logger_print(log_content, self.log_print)
        return log_content['loggerItem']
