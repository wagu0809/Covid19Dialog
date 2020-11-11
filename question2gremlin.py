from gremlin_python.structure.graph import Graph
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
import json
import time


def _filter(entities, predicted_edges, vocabs):
    """
    一些规则：
    依据：作为同时出现在一个问题里的实体，应该同时在某个方向上具有相同的关系
    如果entity大于一个，判断所有entity正反两个方向是否都有相同的预测出来的edge，
    如果在一个方向上有一个没有该edge，就放弃该方向。
    例子：(['口炎', '发热'], '涉及症状')
    在正向上，发热没有涉及症状的关系存在，所以舍弃正向的可能。
    规则1：如果在一个方向上有不同关系，另一个方向上有相同关系，保留有相同关系的方向
    规则2：如果两个方向都存在相同关系，保留两个方向且只保留该关系
    规则3：如果两个方向上都不存在相同的关系，那就正反都作为答案返回
    :param entities:
    :param predicted_edges:
    :param vocabs:
    :return:
    """
    keywords = vocabs.keys()
    forward_edges = []
    backward_edges = []
    unreachable_verticies = set()
    cleared_verticies = set()

    for entity in entities:
        if entity in keywords:
            cleared_verticies.add(entity)
        else:
            c_entity = clean_entity(entity)
            if c_entity in keywords:
                cleared_verticies.add(c_entity)
            else:
                unreachable_verticies.add(entity)

    for edge in predicted_edges:
        for entity in cleared_verticies:
            if edge in vocabs[entity]['forward']:
                continue
            else:
                break
        else:
            forward_edges.append(edge)

        for entity in cleared_verticies:
            if edge in vocabs[entity]['backward']:
                continue
            else:
                break
        else:
            backward_edges.append(edge)

    return {'forward': forward_edges, 'backward': backward_edges}, cleared_verticies, unreachable_verticies


def clean_entity(entity):
    words = ['患有', '患者', '症状', '的人', '的', '测定', '检查', '出现', '检测', '在', '感染', '后', '我', '经常', '时']

    for word in words:
        # if word in entity:
        if entity.endswith(word) or entity.startswith(word):
            # if word in entity:
            #     entity.replace(word, '')
            # else:
            #     continue
            entity = entity.replace(word, '')

    return entity


def create_gremlin(conditions, vocabs):
    verticies = conditions[0]
    edges = conditions[1].split(';')
    edges, verticies, unreachable_verticies = _filter(verticies, edges, vocabs)
    all_possible_gremlin = {'forward': [], 'backward': []}

    for edge in edges['forward']:
        for vertice in verticies:

            if vertice in unreachable_verticies:
                continue
            forward_gremlin = f"g.V().has('name', '{vertice}').outE().hasLabel('{edge}').inV().elementMap()"
            all_possible_gremlin['forward'].append({'gsql': forward_gremlin, 'entity': vertice, 'edge': edge})

    for edge in edges['backward']:
        for vertice in verticies:
            if vertice in unreachable_verticies:
                continue
            backward_gremlin = f"g.V().has('name', '{vertice}').inE().hasLabel('{edge}').outV().elementMap()"
            all_possible_gremlin['backward'].append({'gsql': backward_gremlin, 'entity': vertice, 'edge': edge})

    return all_possible_gremlin, unreachable_verticies


if __name__ == "__main__":
    graph = Graph()
    connection = DriverRemoteConnection('ws://47.115.21.171:8182/gremlin', 'covid191029_traversal')
    g = graph.traversal().withRemote(connection)

    rr = (['鼻腔分泌物外溢'], '临床表现')
    keywords = json.loads(open('./data/keywords.json', encoding='utf-8').read())
    result1 = create_gremlin(rr, keywords)
    print(result1)
