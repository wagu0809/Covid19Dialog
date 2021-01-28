import torch
import re
from collections import Counter
import json
from gremlin_python.structure.graph import Graph
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection

graph = Graph()
# covid数据库
connection_c = DriverRemoteConnection('ws://47.115.21.171:8182/gremlin', 'covid_traversal')
g_c = graph.traversal().withRemote(connection_c)

# operation数据库
connection_o = DriverRemoteConnection('ws://47.115.21.171:8182/gremlin', 'operation_traversal')
g_o = graph.traversal().withRemote(connection_o)

def calculateF1(predict_golden):
    # print(f"predict_golden")
    TP, FP, FN = 0, 0, 0
    for item in predict_golden:
        try:
            predicts = item['predict']
            # predicts = [[x[0], x[1], x[2].lower()] for x in predicts]
            labels = item['golden']
            # labels = [[x[0], x[1], x[2].lower()] for x in labels]
            # if predicts == labels:
            #     TP += 1
            # else:
            #     FP += 1
            for ele in predicts:
                if ele in labels:
                    TP += 1
                else:
                    FP += 1
            for ele in labels:
                if ele not in predicts:
                    FN += 1
        except:
            print(item)
    # print(TP, FP, FN)
    precision = 1.0 * TP / (TP + FP) if TP + FP else 0.
    recall = 1.0 * TP / (TP + FN) if TP + FN else 0.
    F1 = 2.0 * precision * recall / (precision + recall) if precision + recall else 0.
    return precision, recall, F1


def tag2triples(word_seq, tag_seq):
    # print(f"word_seq: {word_seq}")
    # print(f"tag_seq: {tag_seq}")
    assert len(word_seq) == len(tag_seq)
    values = []
    slot = ''
    i = 0
    # print(f"tag_seq: {tag_seq}")
    while i < len(tag_seq):
        tag = tag_seq[i]
        if tag.startswith('B'):
            slot = tag[2:]
            value = word_seq[i]
            j = i + 1
            while j < len(tag_seq):
                if tag_seq[j].startswith('I') and tag_seq[j][2:] == tag[2:]:
                    value += word_seq[j]
                    i += 1
                    j += 1
                else:
                    break
            value = value.replace('##', '')
            values.append(value)
        i += 1
    # return triples
    return values, slot


def recover_result(dataloader, tag_logits, tag_mask_tensor, ori_word_seq, new2ori):
    # print(f"tag_logits: {tag_logits}")
    # print(f"tag_mask_tensor: {tag_mask_tensor}")
    # print(f"ori_word_seq: {ori_word_seq}")
    # print(f"new2ori: {new2ori}")
    # print(f"tag_logits.size(): {tag_logits.size()}")
    max_seq_len = tag_logits.size(0)
    tags = []
    for j in range(1, max_seq_len-1):
        if tag_mask_tensor[j] == 1:
            value, tag_id = torch.max(tag_logits[j], dim=-1)
            tags.append(dataloader.id2tag[tag_id.item()])
    recover_tags = []
    for i, tag in enumerate(tags):
        if new2ori[i] >= len(recover_tags):
            recover_tags.append(tag)
    tag_intent = tag2triples(ori_word_seq, recover_tags)

    return tag_intent


def clean_entity(entity):
    words = ['，', '。', '有', '和', '时', '患有', '查', '患者', '症状', '的人', '测定', '的', '等',
             '检查', '出现', '出', '现', '检测', '在', '感染', '后', '我', '经常', ]

    for word in words:
        # if word in entity:
        if entity.endswith(word) or entity.startswith(word):
            # if word in entity:
            #     entity.replace(word, '')
            # else:
            #     continue
            entity = entity.replace(word, '')

    return entity


def containsAlpha(s):

    return bool(re.search('[a-z]', s))

def process_answer(returned_answers, forward):
    """
    如果问题中有多个实体，每个实体的答案会不一样，将这些答案中相同的找出来作为问题答案。
    :param returned_answers:
    :param forward:  boolean，判断正反向
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
