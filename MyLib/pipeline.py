import os
import json
import time
from .settings import ResourcePath


class DataRead(object):
    def __init__(self, qt_gui=None, common_function=None):
        self.qt_gui = qt_gui
        self.common_function = common_function
        self.resource = ResourcePath.ResourceDirectory.value
        self.json_path = ResourcePath.SuccessJsonFilePath.value
        self.init_resource_file()
        self.log_info_find = 'info_find'

    def init_resource_file(self):
        """ 初始化资源文件 """
        if os.path.exists(self.resource) is False:
            os.mkdir(self.resource)

    def read_account(self, file_path):
        """ 读取账户密码 """
        with open(file=file_path, mode='r', encoding='utf-8') as fis:
            content_list = fis.readlines()
        account_ls = list()
        un_rept_list = list()
        for content in content_list:
            item = content.strip().split(',')
            if item[0] in un_rept_list:
                continue
            else:
                un_rept_list.append(item[0])
            account_ls.append({'username': item[0], 'password': item[1]})
        return account_ls

    def read_success_json(self, username):
        """ 读取答题成功的json """
        if os.path.exists(self.json_path) is True:
            with open(file=self.json_path, mode='r', encoding='utf-8') as fis:
                json_data = fis.read()
            json_data = json.loads(json_data)
        else:
            json_data = dict()
        if username not in json_data:
            json_data[username] = {"success": {}, "failing": {}}
        return json_data

    def local_answered_find(self, file_path, route_key, find_account_number_list):
        """ 本地成功, 失败数据查询 """
        homework_status = '作业完成' if route_key == 'success' else '作业失败'
        with open(file=self.json_path, mode='r', encoding='utf-8') as fis:
            json_string = fis.read()
        if len(find_account_number_list) < 1:
            with open(file=file_path, mode='r', encoding='utf-8') as fis:
                account_list = [account_string.strip().split(',')[0] for account_string in fis.readlines()]
        else:
            account_list = find_account_number_list
        json_data = json.loads(json_string)
        for username in json_data:
            # 判断是否指定了查询账号
            if username not in account_list:  # 判断遍历的账号是否存在指定的账号列表
                continue
            for courseTitle in json_data[username][route_key]:
                for homeworkName in json_data[username][route_key][courseTitle]:
                    logger_content = {
                        'one': username, 'two': courseTitle, 'three': homeworkName, 'four': homework_status,
                        'five': json_data[username][route_key][courseTitle][homeworkName]
                    }
                    self.qt_gui.logger_output(logger_content, self.log_info_find)
                    time.sleep(0.02)
        logger_content = {
            'one': '-' * 20, 'two': '-' * 20, 'three': '-' * 20, 'four': '-' * 20,
            'five': f'{homework_status}-查询完毕'
        }
        [self.qt_gui.logger_output(logger_content, self.log_info_find) for kk in range(10)]

    def read_everyday_token(self, file_path):
        if os.path.exists(file_path) is False:
            return {}
        with open(file=file_path, mode='r', encoding='utf-8') as fis:
            json_data = fis.read()
        json_data = json.loads(json_data)
        return json_data


class DataSave(object):
    def __init__(self, qt_gui, common_function):
        self.qt_gui = qt_gui
        self.common_function = common_function

    def init_resource_file(self, directory_path):
        if os.path.exists(directory_path) is False:
            os.makedirs(directory_path)

    def answer_json_save(self, username, file_path, answer_succeed_json, log_print=None):
        """ 写入json文件 """
        answer_succeed_json = self.json_data_verify(username, answer_succeed_json)  # 调用json数据校验删除，以免已经完成的数据，还在failing中
        with open(file=file_path, mode='w', encoding='utf-8') as fis:
            fis.write(json.dumps(answer_succeed_json, ensure_ascii=False, indent=4))
        content = f"{username} accountJson 写入成功：{answer_succeed_json}\n"
        log_content = self.common_function.get_log_item(content=content, one=username, two='-'*20,
            three='-'*20, four='json 写入成功', five=str(answer_succeed_json[username])
        )
        [self.common_function.logger_print(log_content, log_print) for i in range(5)]
        return answer_succeed_json

    def json_data_verify(self, username, answer_succeed_json):
        """
        将success和failing的数据进行比较，如果success和failing科目中存在相同的子作业，则删除failing科目的子作业
        """
        success_item = answer_succeed_json[username]['success']
        failing_item = answer_succeed_json[username]['failing']
        keys_list = list(success_item.keys())
        for courseTitle in keys_list:
            del_key_list = list()
            for failingHomeWork in failing_item[courseTitle]:
                if failingHomeWork not in success_item[courseTitle]:
                    continue
                del_key_list.append(failingHomeWork)
            [failing_item[courseTitle].pop(key) for key in del_key_list]
        answer_succeed_json[username]['failing'] = failing_item
        return answer_succeed_json

    def json_save(self, file_path, token_list):
        # 保存每天的token
        self.init_resource_file(os.path.dirname(file_path))
        with open(file=file_path, mode='w', encoding='utf-8') as fis:
            fis.write(json.dumps(token_list, ensure_ascii=False, indent=4))
