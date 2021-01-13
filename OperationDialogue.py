from TagPredict import TagPredict
from question2gremlin import create_gremlin
import json, os
from gremlin_python.structure.graph import Graph
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.traversal import P, T
from collections import Counter
from util.answerTemplate import ServerTemplate2Gremlin
from util.dictProcessing import create_dict_matrix
from util.utils import containsAlpha
# from util.cleanPrediction import clean

graph = Graph()
connection = DriverRemoteConnection('ws://47.115.21.171:8182/gremlin', 'operation_traversal')
g = graph.traversal().withRemote(connection)

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
    print(f"predicted results: {result, label_id}")

    if not result[0]:
        return {'none': ["非常抱歉，没找到您想要的答案!"]}

    domains = ['redis', 'redis数据库', 'mongodb', 'mongodb数据库', 'mysql', 'mysql数据库']
    domain = ''
    if len(result[0]) > 1:  # TODO: 涉及domain，用来判断实体属于哪个数据库的
        domain_contain = set(domains) & set(result[0])
        if len(domain_contain) == 1:
            for d in domain_contain:
                result[0].remove(d)
                # domain = d

    for i, item in enumerate(result[0]):  # 有空格的实体在识别后会被去掉空格，加‘-’防止空格被去掉
        result[0][i] = item.replace('-', ' ')

    print(f"predicted results: {result, label_id}")
    """##############新功能调试代码区域###################"""
    # result = clean(predictor.model, result[0], matrix_list)
    # return
    # all_possible_gremlins, vertices = create_gremlin(predictor.model, result, keywords_dict, matrix_list)
    """##############新功能调试代码区域###################"""
    if domain:  # 问题中明确了domain
        # 试用实体的id作为搜索条件，在有多个重名实体的情况下，可根据domain获取唯一实体
        vertice_ids = {}
        vertices = result[0]
        for i, vertice in enumerate(vertices):
            # 先查询实体信息，判断是否有多个重名实体
            if containsAlpha(vertice):
                vertice_info = g.V().has('name', P('textContains', vertice)).elementMap().toList()
            else:
                vertice_info = g.V().has('name', vertice).elementMap().toList()
            if domain and len(vertice_info) > 1:  # 判断是否有多个重名实体，在domain存在且重名实体数量大于1的时候进行筛选
                for v_info in vertice_info:
                    if 'domain' in v_info.keys():  # 根据domain筛选出唯一实体
                        if domain == v_info['domain']:
                            vertice_ids[i] = v_info[T.id]
            # elif len(vertice_info) > 1:
            #     for v_info in vertice_info:
            #         vertice_ids[i] = v_info[T.id]
            else:
                vertice_ids[i] = vertice_info[0][T.id]
        if vertice_ids:
            all_possible_gremlins, vertices = create_gremlin((result, vertice_ids), keywords_dict, use_id=True)
        else:
            all_possible_gremlins, vertices = create_gremlin(result, keywords_dict)
    else:
        all_possible_gremlins, vertices = create_gremlin(result, keywords_dict)

    all_answers = template.getAnswer(label_id, (all_possible_gremlins, vertices, domain), True)
    return all_answers


if __name__ == "__main__":


    # question = 'MySQL数据库都包括哪些运维操作？'
    # question = '怎么连接数据库？'
    # question = '创建数据库的常用命令？'
    # question = 'mysql如何实现安装管理？'
    # question = '删除数据库的命令是什么？'
    # question = 'WHERE子句的命令是什么？'
    # question = 'ZREMRANGEBYLEX的参数都有哪些？'
    # question = '在Redis中，消费者组经常用到什么命令？'
    # question = '在Redis中，消费者组经常用到什么命令，及其作用是什么？'
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
    question = '在Redis中，是如何进行安装管理的？'
    print(f"question: {question}")

    answer = process_question(question)
    # for key in answer.keys():
    #     a = answer[key]
    #     for item in a:
    #         print(a[0])
    print(f"answer: {answer}")

    # create_dict_matrix(predictor.model, keywords_dict_dir)
    # print(result.size())



