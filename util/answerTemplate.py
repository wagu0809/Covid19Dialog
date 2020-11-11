from gremlin_python.structure.graph import Graph
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection

graph = Graph()
connection = DriverRemoteConnection('ws://47.115.21.171:8182/gremlin', 'covid191029_traversal')
g = graph.traversal().withRemote(connection)


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
    print(f"传入的spo是：{spo}")
    entity, edges, answer = spo
    s = ''
    for edge in edges:
        if edge == '医学专科':
            if forward:
                s = '、'.join(entity) + '所属的医学专科为' + '、'.join(answer) + '。'
            else:
                s = '、'.join(answer) + '所属的医学专科为' + '、'.join(entity) + '。'
            s = s + '\n'
        if edge == '就诊' or edge == '就诊科室':
            if forward:
                s = '、'.join(entity) + '需要到' + '、'.join(answer) + '就诊' + '。'
            else:
                s = '、'.join(answer) + '需要到' + '、'.join(entity) + '就诊' + '。'
            s = s + '\n'

    return s


def _relatedSymptomAndDisease(spo, forward):  # 涉及症状;涉及疾病
    print(f"传入的spo是：{spo}")
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
    print(f"传入的spo是：{spo}")
    entity, edges, answer = spo
    s = ''
    for edge in edges:
        if edge == '涉及疾病' or edge == '涉及症状':
            s = '、'.join(answer) + '能对' + '、'.join(entity) + '做出检查。\n'

        if edge == '涉及检查' or edge == '相关检查':
            s = '、'.join(entity) + '需要做的检查是' + '、'.join(answer) + '。\n'

    return s


def _infectiousness(spo, forward):  # 传染性
    print(f"传入的spo是：{spo}")
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


def _commonCommand():
    pass




class ServerTemplate2Gremlin():
    def __init__(self):
        pass

    def getGremlin(self, cls, entity):
        classification = {
            0: _commonCommand,
            1: _commonCommand,
            2: _commonCommand,
            3: _commonCommand,
            4: _commonCommand,
        }
        return classification[cls](entity)


if __name__ == "__main__":

    ans = [['阵发性鼻塞'], ['涉及症状'], ['发热', '鼻痒', '头昏', '打鼾', '鼻孔闭锁', '打喷嚏', '鼻塞', '张口呼吸']]
    template = CovidTemplate2Gremlin().getAnswer(0, ans)