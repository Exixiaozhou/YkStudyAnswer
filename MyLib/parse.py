import os
import re


class AnswerResponseParse(object):
    def __init__(self, params_items, common_function):
        self.username = params_items['account_items']['username']
        self.answer_succeed_json = params_items['answer_succeed_json']
        self.answer_directory_path = params_items['answer_directory_path']
        self.CourseAnswerList = os.listdir(self.answer_directory_path)
        self.common_function = common_function

    def course_search_response_parse(self, response, log_print=None):
        course_params_list = list()
        for CourseItem in response.json()['data']['processList']:
            for item in CourseItem['userFosterSchemeTermCourseVOList']:
                course_name = item['courseName'].replace("★", '')
                course_resource_id = item['courseResourceId']
                if course_name not in self.CourseAnswerList:
                    # 如果该科目名称不存在本地答案已有的答案，则不做存储,
                    continue
                content = f"存储成功：{self.username} {course_name} {course_resource_id}\n"
                log_content = self.common_function.get_log_item(
                    content=content, one=self.username, two=course_name, four=response.json()['msg'], five='存储成功'
                )
                self.common_function.logger_print(log_content, log_print)
                course_params_list.append({"courseTitle": course_name, "courseResourceId": course_resource_id})
                if course_name in self.answer_succeed_json[self.username]['success']:
                    # 初始化该账户的科目列表，用以存放已成功的子科目
                    continue
                self.answer_succeed_json[self.username]['success'][course_name] = {}
                self.answer_succeed_json[self.username]['failing'][course_name] = {}
        return course_params_list

    def homework_search_response_parse(self, response, course_item, answer_file_list, log_print=None):
        homework_param_list = list()
        course_title = course_item['courseTitle']
        course_resource_id = course_item['courseResourceId']
        for item in response.json()['data']['recordList']:
            score = item['score']
            task_id = item['taskId']
            subject_id = item['subjectId']
            exam_id = item['examId']
            task_name = item['taskName']
            if task_name in list(self.answer_succeed_json[self.username]['success'][course_title].keys()):
                log_content = self.common_function.get_log_item(
                    content=f"已经完成：{self.username} {course_title} {task_name}\n", one=self.username, two=course_title,
                    three=task_name, four='已经完成', five='科目子作业存储阶段'
                )
                self.common_function.logger_print(log_content, log_print)
                continue  # 判断json数据对象中是否存在该作业，如果存在则不做存储任务
            content = f"存储成功：{self.username} {course_title} ID：{course_resource_id} 子问题-taskId：{task_id}," \
                      f"subjectId：{subject_id},examId：{exam_id}-{task_name}\n"
            log_content = self.common_function.get_log_item(
                content=content, one=self.username, two=course_title, three=task_name, four='存储成功', five='科目子作业存储阶段'
            )
            self.common_function.logger_print(log_content, log_print)
            homework_param_list.append(
                {
                    "courseResourceId": course_resource_id, "taskId": task_id, "subjectId": subject_id,
                    "examId": exam_id, 'taskName': task_name, 'courseTitle': course_title, 'score': score,
                    'answerFileList': answer_file_list
                }
            )
        return homework_param_list

    def online_question_answer_search_response_parse(self, homework_request_param, start_response):
        """ 解析startUrl返回的响应 """
        task_id = f"{homework_request_param['taskId']}"
        test_user_id = start_response.json()['data']['testUserId']
        answer_list = {'child_params': [], 'test_user_id': test_user_id}
        for groups in start_response.json()['data']['groups']:
            topic = groups['topic']
            for startItem in groups['questions']:
                answer = f"{startItem['answer']}"
                answer = [str_ for str_ in answer] if topic == '多选题' and len(answer) >= 2 else [answer]
                answer_list['child_params'].append(
                    {
                        'answer': answer, 'questionId': startItem['id'], 'questionType': startItem['questionType'],
                        'sequence': startItem['sequence'], 'taskId': task_id, 'userAnswerId': startItem['userAnswerId']
                    }
                )
        return {'taskStatus': True, 'answer_list': answer_list}

    def img_text_info_find_response_parse(self, info_response):
        img_min_num = info_response.json()['data']['imgMinNum']
        tex_min_num = info_response.json()['data']['texMinNum']
        img_status = True if img_min_num >= 1 else False
        text_status = True if tex_min_num >= 1 else False
        return {'imgStatus': img_status, 'textStatus': text_status, 'taskStatus': True, 'msg': '图片、文字填充-查询成功'}


class BrushClassResponseParse(object):
    def __init__(self, log_print):
        self.log_print = log_print

    def course_info_search_parse(self, object_items, response):
        """  """
        username = object_items['account_item']['username']
        course_info_list = []
        for items in response.json()['data']['processList']:
            for item in items['userFosterSchemeTermCourseVOList']:
                major_title = item['courseName'].replace(',', '，')
                course_resource_id = re.search(pattern="courseResourceId':(.*?),", string=str(item)).group(1)
                if 'None' in course_resource_id:
                    continue
                log_content = object_items['common_function'].get_log_item(one=username, two=major_title,
                    three=f'课程id：{course_resource_id}', four='存储成功', five='主修科目搜索 阶段')
                object_items['common_function'].logger_print(log_content, self.log_print)
                course_info_list.append({'major_title': major_title, 'course_resource_id': course_resource_id})
        return course_info_list

    def course_video_info_parse(self, object_items, video_list_response):
        """ 课程接口响应解析函数
        :return:
        """
        course_video_info_list = list()
        param_items = {"username": object_items['account_item']['username'], 'major_title': object_items['major_title']}
        for items in video_list_response.json()['data']['charterSectionList']:
            param_items['charter_section_id'] = items['id']
            param_items['course_title'] = items['name'].replace(',', '，')
            course_video_info_list += self.course_video_son_element_parse(param_items, items, object_items)
            for son_item in items['sectionList']:
                # charterSectionId = items['id'], course_title = items['name'].replace(',', '，') 坑，判断是否为item
                course_video_info_list += self.course_video_son_element_parse(param_items, son_item, object_items)
        return course_video_info_list

    def course_video_son_element_parse(self, param_items, items, object_items):
        """ 课程接口响应子属性解析函数
        :return:
        """
        video_list = []
        for item in items['videoList']:
            video_id = item['id']
            video_name = item['title'].replace(',', '，')
            course_total_time = item['duration']
            course_now_time = 0 if item['videoStudyTime'] is None else item['videoStudyTime']
            if course_now_time >= course_total_time:  # 如果当前进度大于或等于总时长则不做存储
                continue
            log_content = object_items['common_function'].get_log_item(one=param_items['username'],
                two=param_items['major_title'], three=video_name, four='course 存储成功', five='视频信息搜索 阶段')
            object_items['common_function'].logger_print(log_content, self.log_print)
            video_list.append({
                'charterSectionId': param_items['charter_section_id'], 'videoId': video_id, 'video_name': video_name,
                'course_title': param_items['course_title'], 'course_total_time': course_total_time,
                'major_title': param_items['major_title'], 'course_now_time': course_now_time
            })
        return video_list

    def live_video_info_parse(self, object_items, video_list_response):
        """ 直播接口响应解析函数
            :return 直播标题、总时长、当前时长、科目名称 list
        """
        live_video_info_list = list()
        for item in video_list_response.json()['data']:
            video_id = item['id']
            if item['duration'] is None:  # 如果该视频的时长没有开放则不做存储
                continue
            live_total_time = item['duration']
            live_now_time = 0 if item['playbackStudyTime'] is None else item['playbackStudyTime']
            live_title = item['name'].replace(',', '，')
            video_title = item['title'].replace(',', '，')
            if live_now_time >= live_total_time:  # 如果上次的学习时长大于视频时长则不做存储
                continue
            live_video_info_list.append({
                'videoId': video_id, 'live_total_time': live_total_time, 'live_now_time': live_now_time,
                'live_title': live_title, 'video_title': video_title, 'major_title': object_items['major_title']
            })
            log_content = object_items['common_function'].get_log_item(one=object_items['account_item']['username'],
                two=object_items['major_title'], three=live_title, four='live 存储成功', five='视频信息搜索 阶段')
            object_items['common_function'].logger_print(log_content, self.log_print)
        return live_video_info_list
