from enum import Enum


class Headers(Enum):
    FileUploadHeaders = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/95.0.4638.69 Safari/537.36',
    }

    CommonHeaders = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/95.0.4638.69 Safari/537.36',
        'Content-Type': 'application/json;charset=UTF-8',
    }


class AnswerPathAndUploadUrl(Enum):
    items = {
            'url': {
                'loginUrl': 'https://yk.myunedu.com/yunkai/sys/identification/login',
                'courseListSearchUrl': 'https://yk.myunedu.com/yunkai/web/study/userPracticeScheme/overview',
                'homeworkListSearchUrl': 'https://yk.myunedu.com/yunkai/web/student/task/list',
                'uploadUrl': 'https://yk.myunedu.com/yunkai/file/upload',
                'answerUrl': 'https://yk.myunedu.com/yunkai/web/student/task/submit/answer',
                'infoUrl': 'https://yk.myunedu.com/yunkai/web/student/task/info',
            },
            "课程实践": {
                'commonFilename': "小组讨论.pdf",
                'imgFilename': '小组讨论.png',
            },
            "小组学习": {
                'commonFilename': "小组讨论.pdf",
                'imgFilename': '小组讨论.png',
            },
            "线下作业1": {
                'commonFilename': "线下作业1.docx",
                'imgFilename': '小组讨论.png',
            },
            "线下作业2": {
                'commonFilename': "线下作业2.docx",
                'imgFilename': '小组讨论.png',
            },
            "线下作业3": {
                'commonFilename': "线下作业3.docx",
                'imgFilename': '小组讨论.png',
            },
            "线下作业4": {
                'commonFilename': "线下作业4.docx",
                'imgFilename': '小组讨论.png',
            },
            '离线作业1': {
                'commonFilename': "离线作业1.docx",
                'imgFilename': '小组讨论.png',
            },
            '离线作业2': {
                'commonFilename': "离线作业2.docx",
                'imgFilename': '小组讨论.png',
            },
            '离线作业3': {
                'commonFilename': "离线作业3.docx",
                'imgFilename': '小组讨论.png',
            },
            '离线作业4': {
                'commonFilename': "离线作业4.docx",
                'imgFilename': '小组讨论.png',
            },
            "线上作业": {
                'startUrl': 'https://yk.myunedu.com/yunkai/web/examPaper/start',
                'updateUrl': 'https://yk.myunedu.com/yunkai/web/examPaper/update',
                'submitUrl': 'https://yk.myunedu.com/yunkai/web/examPaper/submit',
            },
            '在线作业': {
                'startUrl': 'https://yk.myunedu.com/yunkai/web/examPaper/start',
                'updateUrl': 'https://yk.myunedu.com/yunkai/web/examPaper/update',
                'submitUrl': 'https://yk.myunedu.com/yunkai/web/examPaper/submit',
            }
        }

    info_find_items = {
        'answerSuccessUrl': 'https://yk.myunedu.com/yunkai/web/student/task/info'
    }


class BrushClassUrl(Enum):
    items = {
        'add_progress': 'https://yk.myunedu.com/yunkai/admin/userstudyrecord/addVideoProgress',
        'add_time': 'https://yk.myunedu.com/yunkai/admin/userstudyrecord/addVideoTime',
        'course_list':  'https://yk.myunedu.com/yunkai/web/study/userPracticeScheme/overview',
        'course_video_info': 'https://yk.myunedu.com/yunkai/web/charterSection/charterSectionList',
        'live_video_info': 'https://yk.myunedu.com/yunkai/web/study/liveLessons'
    }


class TaskReturnMessage(Enum):
    ImgTextFindSuccess = {'imgStatus': None, 'textStatus': None, 'taskStatus': True, 'msg': '图片、文字填充-查询成功'}
    ImgTextFindFailing = {'taskStatus': False, 'msg': '图片、文字填充查询-连续请求不成功'}
    ImgTextFindFailingDetail = {'taskStatus': False, 'msg': '图片、文字填充查询-数据缺失'}

    FileNotFound = {'taskStatus': False, 'msg': f"文件不存在："}
    FileExists = {'taskStatus': True, 'msg': f"文件存在"}

    FileUploadSuccess = {'taskStatus': True, 'msg': '文件上传成功'}
    FileUploadFailing = {'taskStatus': False, 'msg': '文件上传失败 连续请求不成功'}

    LastFileUploadSuccess = {'taskStatus': True, 'msg': '总提交成功-pdf、word、img答案提交阶段'}
    LastFileUploadFailing = {'taskStatus': False, 'msg': '总提交失败-pdf、word、img答案提交阶段 连续请求不成功'}

    LastTextUploadSuccess = {'taskStatus': True, 'msg': f'总提交成功-文本填充阶段'}
    LastTextUploadFailing = {'taskStatus': False, 'msg': f'总提交失败-文本填充阶段 连续请求不成功'}

    LastOnlineHomeWorkSuccess = {'taskStatus': True, 'msg': '总提交成功-线上作业'}
    LastOnlineHomeWorkFailing = {'taskStatus': False, 'msg': '总提交失败-线上作业 连续请求不成功'}
    LastOnlineHomeWorkFailingDetail = {'taskStatus': False, 'msg': '总提交失败-线上作业'}

    ResponseDataLost = {'taskStatus': False, 'msg': '题目答案搜索-缺失答案数据'}

    ChildHomeWorkFailing = {'taskStatus': False, 'msg': '子问题 连续请求不成功'}
    ChildHomeWorkSuccess = {'taskStatus': True, 'msg': '子问题 提交成功'}

    OnlineHomeWorkFinished = {'taskStatus': True, 'msg': '选择题已完成'}

    QuestionAnswerSearchDataLost = {'taskStatus': False, 'msg': '线上作业 答案搜索-缺失答案数据'}
    QuestionAnswerSearchRequestFailing = {'taskStatus': False, 'msg': '线上作业 答案搜索-请求不成功'}


class LogMessage(Enum):
    CourseListSearchLogItem = {
        'content': "{} courseListSearch 连续请求不成功!\n",
        'loggerItem': {
            'one': None, 'two': 'null', 'three': 'null', 'four': '连续请求不成功', 'five': '课程列表搜索阶段'
        }
    }

    HomeworkListSearchLogItem = {  # 日志对象
        'content': "{} homeworkListSearch 连续请求不成功!\n",
        'loggerItem': {
            'one': None, 'two': None, 'three': 'null', 'four': '连续请求不成功', 'five': '子作业列表搜索阶段'
        }
    }

    ChildHomeWorkFinished = {
        'content': "已经完成：{} {} {}\n",
        'loggerItem': {
            'one': None, 'two': None, 'three': None, 'four': '已经完成', 'five': '科目子作业存储阶段'
        }
    }

    ChildHomeWorkSaved = {
        'content': "已经完成：{} {} {}\n",
        'loggerItem': {
            'one': None, 'two': None, 'three': None, 'four': '存储成功', 'five': '科目子作业存储阶段'
        }
    }


# print(Headers.FileUploadHeaders.value)
# # AnswerPathAndUploadUrl.items.value['url']['uploadUrl'] += '13rqwrqr'
# # print(AnswerPathAndUploadUrl.items.value['url']['uploadUrl'])
# # print(TaskReturnMessage.LastOnlineHomeWorkFailingDetail.value['msg'].format("xiaoz"))
# items = TaskReturnMessage.LastOnlineHomeWorkFailingDetail.value
# items['msg'] = items['msg'].format('xiaozhou')
# print(items)

