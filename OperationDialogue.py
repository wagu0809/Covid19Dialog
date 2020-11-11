from TagPredict import TagPredict
from question2gremlin import create_gremlin
import json
from gremlin_python.structure.graph import Graph
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from collections import Counter

graph = Graph()
connection = DriverRemoteConnection('ws://47.115.21.171:8182/gremlin', 'Operation_traversal')
g = graph.traversal().withRemote(connection)


def qa(question, predictor):
    result = predictor.predict(question)
    print(f"predicted results: {result}")
    all_possible_gremlins, _ = create_gremlin(result, keywords_dict)
    final_forward_answer, final_backward_answer = '', ''

    # forward
    forward_answers = []
    for gsql in all_possible_gremlins['forward']:
        result = eval(gsql['gsql'])
        for item in result:
            forward_answers.append({'answer': item['name'], 'entity': gsql['entity'], 'edge': gsql['edge']})
        # print(f"forward_result: {forward_answers}")

    # backward
    backward_anwsers = []
    for gsql in all_possible_gremlins['backward']:
        result = eval(gsql['gsql'])
        for item in result:
            backward_anwsers.append({'answer': item['name'], 'entity': gsql['entity'], 'edge': gsql['edge']})
        # print(f"backward_result: {backward_anwsers}")

    if forward_answers:
        final_forward_answer = process_answer(forward_answers, True)

        print(f"final_forward_answer: {final_forward_answer}")

    if backward_anwsers:
        final_backward_answer = process_answer(backward_anwsers, False)

        print(f"final_backward_answer: {final_backward_answer}")

    if not final_backward_answer and not final_forward_answer:
        print('')


def process_answer(returned_answers, forward):
    count = Counter([a['answer'] for a in returned_answers])
    count = sorted(count.items(), key=lambda i: i[1], reverse=True)
    # print(count)
    answer_count = count[0][1]
    num_answer = 0
    for item in count:
        if item[1] == answer_count:
            num_answer += 1
    selected_answers = [i[0] for i in count[:num_answer]]
    final_selected_returned_answers = []
    for answer in selected_answers:
        for returned_answer in returned_answers:
            if returned_answer['answer'] == answer:
                final_selected_returned_answers.append(returned_answer)
    final_entities, final_answers, edge = [], [], []
    for final_selected_returned_answer in final_selected_returned_answers:
        if final_selected_returned_answer['answer'] not in final_answers:
            final_answers.append(final_selected_returned_answer['answer'])
        if final_selected_returned_answer['entity'] not in final_entities:
            final_entities.append(final_selected_returned_answer['entity'])
        if final_selected_returned_answer['edge'] not in edge:
            edge.append(final_selected_returned_answer['edge'])
    if forward:
        final_processed_answer = ','.join(final_entities) + ' ' + ','.join(edge) + ' ' + ','.join(final_answers)
    else:
        final_processed_answer = ','.join(final_answers) + ' ' + ','.join(edge) + ' ' + ','.join(final_entities)

    return final_processed_answer


if __name__ == "__main__":
    config_dir = './configs/configs.json'
    model_dir = './output/pytorch_model_server.bin'
    tag_dir = './data/server/tag_vocab.json'
    data_dir = './data/server'
    keywords_dict_dir = './data/server/keywords_dict.json'
    keywords_dict = json.loads(open(keywords_dict_dir, encoding='utf-8').read())

    predictor = TagPredict(config_dir, model_dir, tag_dir, data_dir)
    # question = '查看用户权限的常见命令是什么?'  # (['查看用户权限'], '常见命令')
    question = '删除用户的常见命令是什么?'  # (['删除用户'], '常见命令')
    # question = '数据库的定义是什么?'  # (['数据库'], '定义')
    # question = '用户授权的概念是什么?'  # (['用户授权'], '概念')
    # question = '举个关系型数据库的例子.'  # (['关系型数据库'], '例子')
    print(f"question: {question}")

    qa(question, predictor)


