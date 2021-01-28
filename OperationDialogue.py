from TagPredict import TagPredict
from question2gremlin import create_gremlin
import json, os
import pandas as pd
from util.answerTemplate import ServerTemplate2Gremlin
# from util.dictProcessing import create_dict_matrix
# from util.cleanPrediction import clean

config_dir = './configs/configs.json'
model_dir = './output/server/pytorch_model_server.bin'
tag_dir = './data/server/tag_vocab.json'
label_dir = './data/server/label_vocab.json'
keywords_dict_dir = './data/server/keywords_dict.json'
# keywords_matrix_dict = './data/server/keywords_matrix_dict.json'
keywords_dict = json.loads(open(keywords_dict_dir, encoding='utf-8').read())
template = ServerTemplate2Gremlin()
predictor = TagPredict(config_dir, model_dir, tag_dir, label_dir)

"""##############新功能调试代码区域###################"""
# if not os.path.exists(keywords_matrix_dict):
#     create_dict_matrix(predictor.model, keywords_dict_dir, 'server')
#
# with open(keywords_matrix_dict, encoding='utf-8', mode='r') as f:
#     matrix_list = json.load(f)
"""##############新功能调试代码区域###################"""


def process_question(question):
    if ' ' in question:
        question = question.replace(' ', '-')
    result, label_id = predictor.predict(question)
    # print(f"predicted results: {result, label_id}")

    if not result[0]:
        return {'none': ["非常抱歉，没找到您想要的答案!"]}

    domains = ['redis', 'redis数据库', 'mongodb', 'mongodb数据库', 'mysql', 'mysql数据库']
    domain = ''
    if len(result[0]) > 1:  # 涉及domain，用来判断实体属于哪个数据库的
        domain_contain = set(domains) & set(result[0])
        if len(domain_contain) == 1:
            for d in domain_contain:
                result[0].remove(d)
                domain = d

    for i, item in enumerate(result[0]):  # 有空格的实体在识别后会被去掉空格，加‘-’防止空格被去掉
        result[0][i] = item.replace('-', ' ')

    # print(f"predicted results: {result, label_id}")
    """##############新功能调试代码区域###################"""
    # 试用语义相似度过滤匹配实体的功能
    # result = clean(predictor.model, result[0], matrix_list)
    # return
    # all_possible_gremlins, vertices = create_gremlin(predictor.model, result, keywords_dict, matrix_list)
    """##############新功能调试代码区域###################"""

    all_possible_gremlins, vertices = create_gremlin(result, keywords_dict, 'o', domain=domain)

    all_answers = template.getAnswer(label_id, (all_possible_gremlins, vertices, domain), True)
    return all_answers


if __name__ == "__main__":


    # question = 'MySQL数据库都包括哪些运维操作？'
    # question = '在mysql中，怎么连接数据库？'
    # question = '在mysql中，创建数据库的常用命令？'
    # question = '在mongodb中，创建数据库的常用命令？'
    # question = '创建数据库的常用命令？'
    # question = 'mysql如何实现安装管理？'
    # question = '删除数据库的命令是什么？'
    # question = 'WHERE子句的命令是什么？'
    # question = 'ZREMRANGEBYLEX的参数都有哪些？'
    # question = '在Redis中，消费者组经常用到什么命令？'
    # question = '消费者组经常用到什么命令？'
    # question = 'MOVE命令的作用是什么？'
    # question = '在Redis中，消息通信的常用命令是什么？'  # 与常用命令无直接联系，做深度搜索
    # question = '在Redis中，安全管理经常用到什么命令？'
    # question = '在Redis中，XREVRANGE的参数都有哪些？'
    # question = '在Redis中，数据管理经常用到什么命令？'
    # question = '在Redis中，管道技术的优点是什么？'
    # question = '在MongoDB数据库中，都有哪些运维操作？'
    # question = '在MongoDB中，都有哪些运维操作？'
    # question = '数据处理的实现方式有哪些？'
    # question = '在MongoDB中，如何做到文档管理？'
    # question = '在MongoDB中，文档管理都会用到什么命令？'
    # question = '在Redis中，如何进行安全管理？'
    # question = '如何安装redis数据库？'
    # question = '如何配置redis数据库？'
    # question = '如何配置mongodb数据库？'
    # question = 'redis的常用命令是什么？'
    # question = '在mongodb中，数据库管理都使用什么命令？'
    # question = '在redis中，客户端命令有哪些？'
    # question = '客户端的命令都有哪些？'
    # question = 'mongodb中，createIndex有哪些参数？'
    # question = '存储优化都用到什么命令？'
    # question = '怎么配置Redis？'
    ################################################################################################
    # TODO：想办法在keywords_dict里对两个同名实体做区分。临时解决办法，给mysql的‘数据类型’加上‘包括’边。
    # 问题：与其他domain里的‘数据类型’的边冲突，在keywords_dict里，两个实体的边合并到了一起。
    # question = 'mysql中，数据类型都有哪些？'
    ################################################################################################
    # question = 'mysql里，数据管理是如何做到的？'
    # question = '修改字段的命令是什么？'
    # question = '异常数据是如何处理的？'
    # question = 'mysql如何处理异常数据？'
    # question = 'Expire命令有哪些参数？'
    # question = '分区是什么？'
    # question = 'mysql使用什么命令处理特殊表？'
    question = '复制是什么？'
    print(f"question: {question}")

    answer = process_question(question)
    print(answer)
    for key, value in answer.items():
        print(f"{key}: {value[0]}")

    # questions = pd.read_csv('./data/server/real_questions.csv')
    # questions = questions['questions']
    # for question in questions:
    #     print(f"question: {question}")
    #     answer = process_question(question)
    #     print(answer)
    #     print('-' * 20)

    # create_dict_matrix(predictor.model, keywords_dict_dir)
    # print(result.size())




