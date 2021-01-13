from gremlin_python.structure.graph import Graph
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
import pandas as pd
from util.utils import containsAlpha
from gremlin_python.process.traversal import P
from gremlin_python.process.traversal import T

graph = Graph()
# covid数据库
connection_c = DriverRemoteConnection('ws://47.115.21.171:8182/gremlin', 'covid_traversal')
g_c = graph.traversal().withRemote(connection_c)
check_labels = pd.read_csv('./data/covid/check_categories.csv')['category'].tolist()

# operation数据库
connection_o = DriverRemoteConnection('ws://47.115.21.171:8182/gremlin', 'operation_traversal')
g_o = graph.traversal().withRemote(connection_o)

p_hierarchy = ['运维操作', '实现方式', '常用命令', ['参数说明', '作用']]  # 边的层级关系，里边的列表表示同级边
path = []  # 记录做深度搜索时的轨迹，同级别的记录到一个列表里存入该列表，每次使用先清空
target_found = False

def _clinicalManifestations(spo, forward):  # 临床表现

    entity, _, answer = spo

    if forward:
        s = '、'.join(entity) + '的临床表现为' + '、'.join(answer) + '。'
    else:
        s = '、'.join(answer) + '的临床表现为' + '、'.join(entity) + '。'

    return s


def _highRiskPart(spo, forward):  # 发病部位

    entity, _, answer = spo

    if forward:
        s = '、'.join(entity) + '的发病部位为' + '、'.join(answer) + '。'
    else:
        s = '、'.join(answer) + '的发病部位为' + '、'.join(entity) + '。'

    return s


def _office(spo, forward):  # 医学专科，科室，就诊科室
    # print(f"传入的spo是：{spo}")
    entity, edges, answer = spo
    s = ''
    for edge in edges:
        if edge == '医学专科':
            if forward:
                s = '、'.join(entity) + '所属的医学专科为' + '、'.join(answer) + '。'
            else:
                s = '、'.join(answer) + '所属的医学专科为' + '、'.join(entity) + '。'
            s = s + '\n'
        if edge == '科室' or edge == '就诊科室':
            if forward:
                s = '、'.join(entity) + '需要到' + '、'.join(answer) + '就诊' + '。'
            else:
                s = '、'.join(answer) + '需要到' + '、'.join(entity) + '就诊' + '。'
            s = s + '\n'

    return s


def _relatedSymptomAndDisease(spo, forward):  # 涉及症状;涉及疾病
    # print(f"传入的spo是：{spo}")
    entity, edges, answer = spo
    s = ''
    for edge in edges:
        if edge == '涉及症状':
            if forward:
                ss = '、'.join(entity) + '会出现的症状是' + '、'.join(answer) + '。'
            else:
                ss = '、'.join(answer) + '会出现的症状是' + '、'.join(entity) + '。'
            s += ss + '\n'
        if edge == '涉及疾病':
            if forward:
                ss = '出现' + '、'.join(entity) + '症状可能涉及到的疾病是' + '、'.join(answer) + '。'
            else:
                ss = '出现' + '、'.join(answer) + '症状可能涉及到的疾病是' + '、'.join(entity) + '。'
            s += ss + '\n'

    return s


def _relatedDiseaseAndCheck(spo, forward):  # 涉及症状;涉及疾病;涉及检查;相关检查
    # print(f"传入的spo是：{spo}")
    entity, edges, answer = spo
    s = ''
    answer_check = []
    answer_not_check = []

    for a in answer:
        a_label = g_c.V().has('name', a).label().toList()[0]
        if a_label in check_labels:
            answer_check.append(a)
        else:
            answer_not_check.append(a)

    for edge in edges:
        if answer_check:
            if edge == '涉及疾病' or edge == '涉及症状':
                s += '、'.join(answer_check) + '能对' + '、'.join(entity) + '做出检查。'
            if edge == '涉及检查' or edge == '相关检查':
                s += '、'.join(entity) + '需要做的检查是' + '、'.join(answer_check) + '。'
        if answer_not_check:
            if edge == '涉及疾病':
                s += '、'.join(entity) + '涉及到的疾病是' + '、'.join(answer_not_check) + '。'
            elif edge == '涉及症状':
                s += '、'.join(entity) + '会出现的症状是' + '、'.join(answer_not_check) + '。'

    return s


def _infectiousness(spo, forward):  # 传染性
    # print(f"传入的spo是：{spo}")
    entity, _, answer = spo
    if '无' in '、'.join(answer) or '否' in '、'.join(answer) or '不' in '、'.join(answer):
        s = '、'.join(entity) + '无传染性。\n'
    elif '强' in '、'.join(answer):
        s = '、'.join(entity) + '传染性强。\n'
    elif '弱' in '、'.join(answer):
        s = '、'.join(entity) + '传染性弱。\n'
    elif '有' in '、'.join(answer) or '是' in '、'.join(answer):
        s = '、'.join(entity) + '具有传染性。\n'
    else:
        s = '传染性未知！'
    return s


def _commonCause(spo, forward):  # 常见病因
    entity, edges, answer = spo
    s = ''
    for edge in edges:
        if edge == '发病机制':
            if forward:
                s = '、'.join(entity) + '的发病机制是' + '、'.join(answer) + '。'
            else:
                s = '、'.join(answer) + '的发病机制是' + '、'.join(entity) + '。'
        else:
            if forward:
                s = '、'.join(entity) + '的常见病因是' + '、'.join(answer) + '。'
            else:
                s = '、'.join(answer) + '的常见病因是' + '、'.join(entity) + '。'

    return s


def _dosage(spo, forward):  # 剂量
    entity, _, answer = spo

    s = '、'.join(entity) + '的剂量是：' + '、'.join(answer) + '。\n'

    return s


def _typeAndPrescriptionDrug(spo, forward):  # 类型;是否处方药
    entity, edges, answer = spo
    s = ''
    for edge in edges:
        if edge == '类型':
            if forward:
                s = '、'.join(entity) + '的类型是' + '、'.join(answer) + '。'
            else:
                s = '、'.join(answer) + '的类型是' + '、'.join(entity) + '。'
        else:
            if '非' in '、'.join(answer) or '否' in '、'.join(answer):
                s = '、'.join(entity) + '是非处方药。'
            else:
                s = '、'.join(entity) + '是处方药。'

    return s


def _precaution(spo, forward):  # 注意事项
    entity, _, answer = spo

    s = '、'.join(entity) + '的注意事项有：' + '、'.join(answer) + '。'

    return s


def _prevention(spo, forward):  # 预防
    entity, _, answer = spo

    s = '、'.join(entity) + '的预防措施有：' + '、'.join(answer) + '。'

    return s


def _adverseReaction(spo, forward):  # 不良反应
    entity, _, answer = spo

    s = '、'.join(entity) + '的不良反应是' + '、'.join(answer) + '。'

    return s


def _taboos(spo, forward):  # 禁忌;饮食禁忌;忌同食
    entity, edges, answer = spo
    s = ''
    for edge in edges:
        if edge == '忌同食':
            s = '、'.join(entity) + '切忌与' + '、'.join(answer) + '同食。'
        else:
            s = '、'.join(entity) + '禁忌有：' + '、'.join(answer)
    return s


def _highRiskGroups(spo, forward):  # 多发人群;高发人群
    entity, edges, answer = spo
    s = ''
    for edge in edges:
        if edge == '多发人群':
            s = '、'.join(entity) + '多发人群为' + '、'.join(answer)
        else:
            s = '、'.join(entity) + '高发人群为' + '、'.join(answer)
    return s


class CovidTemplate2Gremlin:
    def __init__(self):
        pass

    def getAnswer(self, cls, spo, is_forward):
        classification = {
            0: _clinicalManifestations,
            1: _highRiskPart,
            2: _office,
            3: _relatedSymptomAndDisease,
            4: _relatedDiseaseAndCheck,
            5: _infectiousness,
            6: _commonCause,
            7: _dosage,
            8: _typeAndPrescriptionDrug,
            9: _precaution,
            10: _prevention,
            11: _adverseReaction,
            12: _taboos,
            13: _highRiskGroups,
        }
        return classification[cls](spo, is_forward)


"""
以下是运维得回答模板方法
"""

def find_next(vertice, target_edge, i=0):
    """
    :param vertice: 第一次输入为问题中识别的实体，之后再输入时其下级实体
    :param target_edge: 目标edge（即通过问题识别的意图）
    :return: 返回遍历的路径，包括节点名称及信息

    遍历信息以{'answer': , 'entity': , 'edge': }形式存储，方便生成答案
    """
    all_spos = []
    assert isinstance(vertice, str), "Input vertice should be string."
    if i > 2:  # 控制递归深度
        return all_spos

    # 找到传入节点射出的边（outE），next_edges
    if containsAlpha(vertice):
        next_edges = g_o.V().has('name', P('textContains', vertice)).outE().elementMap().toList()
    else:
        next_edges = g_o.V().has('name', vertice).outE().elementMap().toList()

    # 对next_edges去重
    edges = set()
    for next_edge in next_edges:
        name = next_edge[T.label]
        edges.add(name)

    # 遍历每个边，找到下个节点及下个节点射出的边
    for next_edge_name in edges:
        if next_edge_name not in p_hierarchy:  # 限定深度搜索的适用范围
            continue
        # 查询其连接的下一个级点的信息，
        if containsAlpha(vertice):
            next_vertices = g_o.V().has('name', P('textContains', vertice)).outE().hasLabel(next_edge_name).inV().elementMap().toList()
        else:
            next_vertices = g_o.V().has('name', vertice).outE().hasLabel(next_edge_name).inV().elementMap().toList()

        if next_edge_name == target_edge:
            global target_found
            target_found = True  # 找到目标意图的标识
            next_vertice_names = []  # 存储所有next_vertices的名称
            # 遍历所有节点，记录next_vertices的信息
            for next_vertice in next_vertices:
                # 记录next_edge的信息
                next_vertice_name = next_vertice['name']
                next_vertice_names.append(next_vertice_name)
            all_spos.append({'answer': next_vertice_names, 'entity': vertice, 'edge': next_edge_name})

        else:
            vertice_names = []
            for next_vertice in next_vertices:
                vertice_names.append(next_vertice['name'])
            all_spos.append({'answer': vertice_names, 'entity': vertice, 'edge': next_edge_name})
            # 递归
            for next_vertice in vertice_names:
                next_spos = find_next(next_vertice, target_edge, i+1)
                all_spos += next_spos
    return all_spos


def find_answer(spo, target_edge=None, recursion=True):
    """
    :param spo: 包括可能的gremlin语句和问题中识别的实体
    :param target_edge: 目标意图
    :param additional_key: 该节点的额外信息的键
    :param recursion: 是否需要递归去查找更深的信息
    :return:
    """
    gremlins, vertices, domain = spo
    # forward
    f_gremlins = gremlins['forward']
    forward_answers = {}  # 直接查找找到的答案
    recursion_answers = {}  # 通过深度递归查找找到的答案
    if f_gremlins:  # TODO: 改造成试用实体id的方式进行递归查找
        for gsql in f_gremlins:
            gremlin_sql = gsql['gsql'].replace('g.V(', 'g_o.V(')
            result = eval(gremlin_sql)
            forward_answers[gsql['entity']] = []
            answers = []
            for item in result:
                answers.append(item['name'])
            forward_answers[gsql['entity']].append({'answer': answers, 'entity': gsql['entity'], 'edge': gsql['edge']})

    else:
        if recursion:
            for vertice in vertices:
                global target_found
                target_found = False
                recursion_answers[vertice] = []
                recursion_answers[vertice] += find_next(vertice, target_edge)
            # 需要对recursion_answer做处理
            if target_found:
                forward_answers = recursion_answers

    return forward_answers


def _methods(spo, forward):  # 实现方式
    target_edge = '实现方式'
    gremlins, vertices, domain = spo
    final_answer = {}
    forward_answers = find_answer(spo, target_edge)

    if forward_answers:
        s = ''
        for vertice in vertices:
            final_answer[vertice] = []
            for answer in forward_answers[vertice]:
                if target_edge == answer['edge']:
                    s += answer['entity'] + '的实现方式为：' + '，'.join(answer['answer']) + '。\n'
                else:
                    s += answer['entity'] + '的' + answer['edge'] + '为' + '，'.join(answer['answer']) + '。\n'
            final_answer[vertice].append(s)
        return final_answer
    else:
        return {'none': ["非常抱歉，没找到您想要的答案!"]}


def _commonCommand(spo, forward):  # 常用命令
    target_edge = '常用命令'
    gremlins, vertices, _ = spo
    final_answer = {}
    forward_answers = find_answer(spo, target_edge)

    if forward_answers:
        s = ''
        for vertice in vertices:
            final_answer[vertice] = []
            for answer in forward_answers[vertice]:
                command_format = ''
                if target_edge == answer['edge']:
                    for i, a in enumerate(answer['answer']):
                        punctuation = '。\n' if i + 1 == len(answer['answer']) else '；\n'
                        additional_info = g_o.V().has('name', a).elementMap().toList()[0]
                        if '命令' in additional_info.keys():
                            command_format += a + '，其命令格式为：' + additional_info['命令'] + punctuation
                        else:
                            command_format += a + punctuation
                    s += answer['entity'] + '的常用命令为：' + command_format
                else:
                    s += answer['entity'] + '的' + answer['edge'] + '为：' + '，'.join(answer['answer']) + '。\n'
            final_answer[vertice].append(s)
        return final_answer
    else:
        return {'none': ["非常抱歉，没找到您想要的答案!"]}


def _mentenanceOperation(spo, forward):  # 运维操作
    target_edge = '运维操作'
    gremlins, vertices, _ = spo
    final_answer = {}
    forward_answers = find_answer(spo, target_edge, False)

    if forward_answers:
        s = ''
        for vertice in vertices:
            final_answer[vertice] = []
            for answer in forward_answers[vertice]:
                if target_edge == answer['edge']:
                    s += answer['entity'] + '的运维操作包括：'  + '，'.join(answer['answer']) + '。\n'
                else:
                    s += answer['entity'] + '的' + answer['edge'] + '为：' + '，'.join(answer['answer']) + '。\n'
            final_answer[vertice].append(s)
        return final_answer
    else:
        return {'none': ["非常抱歉，没找到您想要的答案!"]}


def _parameters(spo, forward):  # 参数说明
    target_edge = '参数说明'
    gremlins, vertices = spo
    final_answer = {}
    forward_answers = find_answer(spo, target_edge)

    if forward_answers:
        s = ''
        for vertice in vertices:
            final_answer[vertice] = []
            for answer in forward_answers[vertice]:
                command_format = ''
                if target_edge == answer['edge']:
                    for i, a in enumerate(answer['answer']):
                        punctuation = '。\n' if i + 1 == len(answer['answer']) else '；\n'
                        additional_info = g_o.V().has('name', a).elementMap().toList()[0]
                        if '说明' in additional_info.keys():
                            command_format += a + '：' + additional_info['说明'] + punctuation
                        else:
                            command_format += a + punctuation
                    s += answer['entity'] + '的参数包括：' + command_format
                else:
                    s += answer['entity'] + '的' + answer['edge'] + '为：' + '，'.join(answer['answer']) + '。\n'
            final_answer[vertice].append(s)
        return final_answer
    else:
        return {'none': ["非常抱歉，没找到您想要的答案!"]}


def _commondFunction(spo, forward):  # 作用：命令的作用
    target_edge = '作用'
    gremlins, vertices = spo
    final_answer = {}
    forward_answers = find_answer(spo, target_edge, False)

    if forward_answers:
        s = ''
        for vertice in vertices:
            final_answer[vertice] = []
            for answer in forward_answers[vertice]:
                if target_edge == answer['edge']:
                    s += answer['entity'] + '的作用是：' + '，'.join(answer['answer'])
                else:
                    s += answer['entity'] + '的' + answer['edge'] + '为：' + '，'.join(answer['answer'])
                s += '\n' if s.endswith('。') else '。\n'
            final_answer[vertice].append(s)
        return final_answer
    else:
        return {'none': ["非常抱歉，没找到您想要的答案!"]}


def _returnValue(spo, forward):  # 返回值：命令或者方法的返回值
    target_edge = '返回值'
    gremlins, vertices = spo
    final_answer = {}
    forward_answers = find_answer(spo, target_edge, False)

    if forward_answers:
        s = ''
        for vertice in vertices:
            final_answer[vertice] = []
            for answer in forward_answers[vertice]:
                if target_edge == answer['edge']:
                    s += answer['entity'] + '的返回值有：' + '，'.join(answer['answer']) + '。\n'
                else:
                    s += answer['entity'] + '的' + answer['edge'] + '为：' + '，'.join(answer['answer']) + '。\n'
            final_answer[vertice].append(s)
        return final_answer
    else:
        return {'none': ["非常抱歉，没找到您想要的答案!"]}


def _introduction(spo, forward):  # 简介
    target_edge = '简介'
    gremlins, vertices = spo
    final_answer = {}
    forward_answers = find_answer(spo, target_edge, False)

    if forward_answers:
        s = ''
        for vertice in vertices:
            final_answer[vertice] = []
            for answer in forward_answers[vertice]:
                if target_edge == answer['edge']:
                    s += answer['entity'] + '的简介：' + '，'.join(answer['answer'])
                else:
                    s += answer['entity'] + '的' + answer['edge'] + '为：' + '，'.join(answer['answer'])
                s += '\n' if s.endswith('。') else '。\n'
            final_answer[vertice].append(s)
        return final_answer
    else:
        return {'none': ["非常抱歉，没找到您想要的答案!"]}


def _virtue(spo, forward):  # 优点
    target_edge = '优点'
    gremlins, vertices = spo
    final_answer = {}
    forward_answers = find_answer(spo, target_edge, False)

    if forward_answers:
        s = ''
        for vertice in vertices:
            final_answer[vertice] = []
            for answer in forward_answers[vertice]:
                if target_edge == answer['edge']:
                    s += answer['entity'] + '的优点是：' + '，'.join(answer['answer'])
                else:
                    s += answer['entity'] + '的' + answer['edge'] + '为：' + '，'.join(answer['answer'])
                s += '\n' if s.endswith('。') else '。\n'
            final_answer[vertice].append(s)
        return final_answer
    else:
        return {'none': ["非常抱歉，没找到您想要的答案!"]}


def _shortcoming(spo, forward):  # 缺点
    target_edge = '缺点'
    gremlins, vertices = spo
    final_answer = {}
    forward_answers = find_answer(spo, target_edge, False)

    if forward_answers:
        s = ''
        for vertice in vertices:
            final_answer[vertice] = []
            for answer in forward_answers[vertice]:
                if target_edge == answer['edge']:
                    s += answer['entity'] + '的缺点是：' + '，'.join(answer['answer'])
                else:
                    s += answer['entity'] + '的' + answer['edge'] + '为：' + '，'.join(answer['answer'])
                s += '\n' if s.endswith('。') else '。\n'
            final_answer[vertice].append(s)
        return final_answer
    else:
        return {'none': ["非常抱歉，没找到您想要的答案!"]}


def _charateristics(spo, forward):  # 特点
    target_edge = '特点'
    gremlins, vertices = spo
    final_answer = {}
    forward_answers = find_answer(spo, target_edge, False)

    if forward_answers:
        s = ''
        for vertice in vertices:
            final_answer[vertice] = []
            for answer in forward_answers[vertice]:
                if target_edge == answer['edge']:
                    s += answer['entity'] + '的特点是：' + '，'.join(answer['answer'])
                else:
                    s += answer['entity'] + '的' + answer['edge'] + '为：' + '，'.join(answer['answer'])
                s += '\n' if s.endswith('。') else '。\n'
            final_answer[vertice].append(s)
        return final_answer
    else:
        return {'none': ["非常抱歉，没找到您想要的答案!"]}


def _theory(spo, forward):  # 原理
    target_edge = '原理'
    gremlins, vertices = spo
    final_answer = {}
    forward_answers = find_answer(spo, target_edge, False)

    if forward_answers:
        s = ''
        for vertice in vertices:
            final_answer[vertice] = []
            for answer in forward_answers[vertice]:
                if target_edge == answer['edge']:
                    s += answer['entity'] + '的原理是：' + '，'.join(answer['answer'])
                else:
                    s += answer['entity'] + '的' + answer['edge'] + '为：' + '，'.join(answer['answer'])
                s += '\n' if s.endswith('。') else '。\n'
            final_answer[vertice].append(s)
        return final_answer
    else:
        return {'none': ["非常抱歉，没找到您想要的答案!"]}


class ServerTemplate2Gremlin():
    def __init__(self):
        pass

    def getAnswer(self, cls, spo, is_forward):
        classification = {
            0: _methods,
            1: _commonCommand,
            2: _mentenanceOperation,
            3: _parameters,
            4: _commondFunction,
            5: _returnValue,
            6: _introduction,
            7: _virtue,
            8: _shortcoming,
            9: _charateristics,
            10: _theory,
        }
        return classification[cls](spo, is_forward)


if __name__ == "__main__":
    result = g_c.V().has('name', '氧分压').label().toList()  # ['疾病']
    # print(list(result[0].values())[1])
    print(result)

    # for item in result:
    #     print(item)