from TagPredict import TagPredict
from question2gremlin import create_gremlin
import json
from gremlin_python.structure.graph import Graph
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from collections import Counter
from util.answerTemplate import CovidTemplate2Gremlin

graph = Graph()
connection = DriverRemoteConnection('ws://47.115.21.171:8182/gremlin', 'covid19_traversal')
g = graph.traversal().withRemote(connection)

config_dir = './configs/configs.json'
model_dir = './output/pytorch_model_covid.bin'
tag_dir = './data/covid/tag_vocab.json'
label_dir = './data/covid/label_vocab.json'
keywords_dict_dir = './data/covid/keywords_dict.json'
keywords_dict = json.loads(open(keywords_dict_dir, encoding='utf-8').read())
template = CovidTemplate2Gremlin()
predictor = TagPredict(config_dir, model_dir, tag_dir, label_dir)


def process_question(question):
    result, label_id = predictor.predict(question)
    # print(f"predicted results: {result, label_id}")
    all_possible_gremlins, _ = create_gremlin(result, keywords_dict)

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
        forward_processed_answer = process_answer(forward_answers, True, label_id)
        forwardkeys = forward_processed_answer.keys()
    if backward_anwsers:
        backward_processed_answer = process_answer(backward_anwsers, False, label_id)
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
        # print(f'final answers: {all_answers}')
    else:
        all_answers['none'] = ["非常抱歉，没找到您想要的答案!"]
        # print(f"非常抱歉，没找到您想要的答案!")

    return all_answers

def process_answer(returned_answers, forward, label_id):
    """
    如果问题中有多个实体，每个实体的答案会不一样，将这些答案中相同的找出来作为问题答案。
    :param returned_answers:
    :param forward:
    :param label_id:
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

    # question = '怎样的检查项目能对小儿多源性房性心动过速、急性肾功能不全以及动静脉血管瘤做出检测？'  # 单向、多实体、单答案
    # question = '哪项检查能有效检测汉坦病毒肺综合征、沙雷菌肺炎和肺组织细胞增生症？'  # 双向、多实体、单答案
    # question = '患有小儿先天性肺囊肿、小儿多源性房性心动过速以及急性肾功能不全等疾病时，应该做哪一种检查？'
    # question = '对于肺组织细胞增生症、急性呼吸窘迫综合症和新生儿呼吸窘迫综合征患者，需要做哪项检查对病情有用？'
    # question = '哪种医学检查能检测出新生儿晚期代谢性酸中毒、新生儿低体温和百草枯中毒？'
    # question = '阵发性鼻塞和耳闷症状与什么疾病相关？'
    # question = '伴随皮肤发红症状的疾病是什么？'
    # question = '新型冠状病毒肺炎的临床表现有哪些？'
    # question = '哪个病有可能涉及到口炎和发热的症状？'
    # question = '急性盆腔炎涉及哪些症状？'
    # question = '从医学专科上讲，增龄性黄斑变性属于什么科？'
    # question = '在医学专科中口腔溃疡属于什么科？'
    # question = '新生儿肺炎在医学专科中属于什么科？'
    # question = '患有小儿先天性肺囊肿、小儿多源性房性心动过速以及急性肾功能不全等疾病时，应该做哪一种检查？'
    # question = '哪项检查能有效检测汉坦病毒肺综合征、沙雷菌肺炎和肺组织细胞增生症？'
    # question = '哪项检查能有效检测汉坦病毒肺综合征？'
    question = '长期使用糖皮质激素导致的损害有哪些症状？'   # 双向，单实体，多答案
    # question = '泌尿道感染在医学专科中属于什么科？'   # predicted results: ((['泌尿道感染在医学专科中'], '医学专科;就诊;就诊科室'), 1)
    # question = '什么疾病的临床表现为鼻腔分泌物外溢？'
    # question = '有雀斑的人有何临床表现？'
    # question = '猪李氏杆菌病是否具有传染性？'
    # question = '氟灭酸属于什么类型的药？'
    # question = '杏苏感冒冲剂是处方药吗？'
    # question = '妊娠合并慢性肾小球肾炎的高发人群是哪些人？'
    # question = '哪一种检查对于检测小儿多源性房性心动过速有帮助？'  # ((['于检测小儿多源性房性心动过速有帮'], '涉及症状;涉及疾病;涉及检查;相关检查'), 4)
    print(f"question: {question}")
    process_question(question)
    # while True:
    #     q = input('please input a question: ')
    #     print(f"time from inputting a question: {time.time()}")
    #     qa(q)


