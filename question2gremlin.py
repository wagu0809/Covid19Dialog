from gremlin_python.structure.graph import Graph
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
import json
from util.utils import clean_entity, containsAlpha
from util.utils import g_o, g_c
from gremlin_python.process.traversal import P, T
# from util.cleanPrediction import clean


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


# def create_gremlin(conditions, vocabs, use_id=False):
def create_gremlin(conditions, vocabs, database='c', domain=''):
    if database == 'o':
        g = g_o
    elif database == 'c':
        g = g_c
    else:
        g = g_c
    vertices, edges = conditions
    edges = edges.split(';')
    edges, vertices, unreachable_verticies = _filter(vertices, edges, vocabs)

    new_vertices = {}  #TODO: 在这里对vertices处理，filter之后对vertices进行，多实体重名处理
    for i, vertice in enumerate(vertices):
        # 先查询实体信息，判断是否有多个重名实体
        if containsAlpha(vertice):
            vertice_info = g.V().has('name', P('textContains', vertice)).elementMap().toList()
        else:
            vertice_info = g.V().has('name', vertice).elementMap().toList()
        if domain and len(vertice_info) > 1:  # 判断是否有多个重名实体，在domain存在且重名实体数量大于1的时候进行筛选
            for v_info in vertice_info:
                if 'domain' in v_info.keys():  # 根据domain筛选出唯一实体
                    if domain == v_info['domain'] and v_info['name'].lower() == vertice:
                        new_vertices[v_info[T.id]] = vertice
        elif len(vertice_info) > 1:
            for v_info in vertice_info:
                if v_info['name'].lower() == vertice:
                    new_vertices[v_info[T.id]] = vertice
        else:
            new_vertices[vertice_info[0][T.id]] = vertice

    # if unreachable_verticies:  # 试用语义相似度做过滤，暂时不用
    #     cleaned_entities = clean(model, unreachable_verticies, matrix)
    #     verticies = list(verticies) + cleaned_entities
    all_possible_gremlin = {'forward': [], 'backward': []}
    for edge in edges['forward']:
        for key in new_vertices.keys():
            vertice = new_vertices[key]
            # if vertice in unreachable_verticies:
            #     continue
            forward_gremlin = f"g.V({key}).outE().hasLabel('{edge}').inV().elementMap().toList()"
            all_possible_gremlin['forward'].append({'gsql': forward_gremlin, 'entity': vertice, 'edge': edge, 'id':key})

        # for i, vertice in enumerate(vertices):
        #     if vertice in unreachable_verticies:
        #         continue
        #     # if use_id:  # 如果使用id为真，返回通过id查找的gremlin语句
        #     #     forward_gremlin = f"g.V({vertices_ids[i]}).outE().hasLabel('{edge}').inV().elementMap().toList()"
        #     else:
        #         if containsAlpha(vertice):
        #             forward_gremlin = f"g.V().has('name', P('textContains', '{vertice}')).outE().hasLabel('{edge}').inV().elementMap().toList()"
        #         else:
        #             forward_gremlin = f"g.V().has('name', '{vertice}').outE().hasLabel('{edge}').inV().elementMap().toList()"
        #     all_possible_gremlin['forward'].append({'gsql': forward_gremlin, 'entity': vertice, 'edge': edge})

    for edge in edges['backward']:
        for key in new_vertices.keys():
            vertice = new_vertices[key]
            # if vertice in unreachable_verticies:
            #     continue
            backward_gremlin = f"g.V({key}).inE().hasLabel('{edge}').outV().elementMap().toList()"
            all_possible_gremlin['backward'].append({'gsql': backward_gremlin, 'entity': vertice, 'edge': edge, 'id':key})

        # for vertice in vertices:
        #     if vertice in unreachable_verticies:
        #         continue
        #     if containsAlpha(vertice):
        #         backward_gremlin = f"g.V().has('name', P('textContains', '{vertice}')).inE().hasLabel('{edge}').outV().elementMap().toList()"
        #     else:
        #         backward_gremlin = f"g.V().has('name', '{vertice}').inE().hasLabel('{edge}').outV().elementMap().toList()"
        #     all_possible_gremlin['backward'].append({'gsql': backward_gremlin, 'entity': vertice, 'edge': edge})

    return all_possible_gremlin, new_vertices


if __name__ == "__main__":
    graph = Graph()
    connection = DriverRemoteConnection('ws://47.115.21.171:8182/gremlin', 'covid_traversal')
    g = graph.traversal().withRemote(connection)

    # rr = (['鼻腔分泌物外溢'], '临床表现')
    # keywords = json.loads(open('./data/keywords.json', encoding='utf-8').read())
    # result1 = create_gremlin(rr, keywords)
    # print(result1)
