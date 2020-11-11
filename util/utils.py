import torch
import json
from gremlin_python.structure.graph import Graph
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection


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


# def create_keyword_dict(keywords_dict_dir, keywords, g):
#     keyword_dict = {}
#     for keyword in keywords:
#         keyword_dict[keyword] = {'forward': [], 'backward': []}
#         in_edges = g.V().has('name', keyword).inE().elementMap()
#         out_edges = g.V().has('name', keyword).outE().elementMap()
#         backward_edges = []
#         for edge in in_edges:
#             e = list(edge.values())[1]
#             keyword_dict[keyword]['backward'].append(e)
#         forward_edges = []
#         for edge in out_edges:
#             e = list(edge.values())[1]
#             keyword_dict[keyword]['forward'].append(e)
#
#     with open(keywords_dict_dir, 'w', encoding='utf-8') as ff:
#         json.dump(keyword_dict, ff, ensure_ascii=False, indent=4)
#
#     return keyword_dict
