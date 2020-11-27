from TagPredict import TagPredict
from question2gremlin import create_gremlin
import json, os
from gremlin_python.structure.graph import Graph
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.traversal import P
from collections import Counter
from util.answerTemplate import ServerTemplate2Gremlin
# from util.dictProcessing import create_dict_matrix

graph = Graph()
connection = DriverRemoteConnection('ws://47.115.21.171:8182/gremlin', 'operation3_traversal')
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

# if not os.path.exists(keywords_dict_dir):
#     create_dict_matrix(predictor.model, keywords_dict_dir)


def process_question(question):
    result, label_id = predictor.predict(question)
    # print(f"predicted results: {result, label_id}")
    if not result[0]:
        return {'none': ["非常抱歉，没找到您想要的答案!"]}
    all_possible_gremlins, _ = create_gremlin(result, keywords_dict)
    # print(f"all_possible gremlin: {all_possible_gremlins}")

    # forward
    forward_answers = []
    for gsql in all_possible_gremlins['forward']:
        result = eval(gsql['gsql'])
        for item in result:
            forward_answers.append({'answer': item['name'], 'entity': gsql['entity'], 'edge': gsql['edge']})

    # backward
    backward_anwsers = []
    for gsql in all_possible_gremlins['backward']:
        result = eval(gsql['gsql'])
        for item in result:
            backward_anwsers.append({'answer': item['name'], 'entity': gsql['entity'], 'edge': gsql['edge']})

    all_answers = {}
    if forward_answers:
        forward_processed_answer = process_answer(forward_answers, True)
        forwardkeys = forward_processed_answer.keys()
    if backward_anwsers:
        backward_processed_answer = process_answer(backward_anwsers, False)
        backwardkeys = backward_processed_answer.keys()

    if (forward_answers and not backward_anwsers) or (forward_answers and backward_anwsers):
        for edge in set(forwardkeys):
            all_answers[edge] = []
            final_forward_answer = forward_processed_answer[edge]
            final_processed_forward_answer = template.getAnswer(label_id, final_forward_answer, True)
            all_answers[edge].append(final_processed_forward_answer)
        # print(f'final answers: {all_answers}')
    elif backward_anwsers and not forward_answers:
        for edge in set(backwardkeys):
            all_answers[edge] = []
            final_backward_answer = backward_processed_answer[edge]
            final_processed_backward_answer = template.getAnswer(label_id, final_backward_answer, False)
            all_answers[edge].append(final_processed_backward_answer)
    else:
        all_answers['none'] = ["非常抱歉，没找到您想要的答案!"]

    return all_answers


def process_answer(returned_answers, forward):
    """
    如果问题中有多个实体，每个实体的答案会不一样，将这些答案中相同的找出来作为问题答案。
    :param returned_answers:
    :param forward:
    :return:
    """
    edges = set([returned_answer['edge'] for returned_answer in returned_answers])
    # edges = predictor.id2label[label_id].split(';')
    process_answers = {}
    for edge in edges:
        # process_answers[edge] = []
        answers = [returned_answer for returned_answer in returned_answers if returned_answer['edge'] == edge]
        # if len(answers) > 0:
        count = Counter([a['answer'] for a in answers])
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
            for returned_answer in answers:
                if returned_answer['answer'] == answer:
                    final_selected_returned_answers.append(returned_answer)
        final_entities, final_answers = [], []
        for final_selected_returned_answer in final_selected_returned_answers:
            if final_selected_returned_answer['answer'] not in final_answers:
                final_answers.append(final_selected_returned_answer['answer'])
            if final_selected_returned_answer['entity'] not in final_entities:
                final_entities.append(final_selected_returned_answer['entity'])
            # if final_selected_returned_answer['edge'] not in final_edge:
            #     edge.append(final_selected_returned_answer['edge'])
        process_answers[edge] = [final_entities, [edge], final_answers]

    # final_processed_answer = template.getAnswer(label_id, [final_entities, edge, final_answers], forward)

    return process_answers


if __name__ == "__main__":


    # question = 'MySQL数据库都包括哪些运维操作？'
    # question = '怎么连接数据库？'
    # question = '创建数据库的常用命令？'
    # question = 'mysql如何实现安装管理？'
    # question = '删除数据库的命令是什么？'
    question = 'WHERE子句的命令是什么？'
    print(f"question: {question}")

    answer = process_question(question)
    print(answer)


