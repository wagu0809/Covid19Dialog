import json
import os
from Model import TagBert
import torch
from dataloader import Dataloader
from transformers import BertTokenizer
from util.utils import recover_result
from question2gremlin import create_gremlin


class TagPredict:
    def __init__(self, config_dir, model_dir):
        with open(config_dir, encoding='utf-8', mode='r') as f:
            content = f.read()
        self.configs = json.loads(content)
        self.DEVICE = self.configs['DEVICE']
        # DEVICE = 'cpu' if not torch.cuda.is_available() else 'cuda:0'
        tag_dir = './data/covid/tag_vocab.json'
        label_dir = './data/covid/label_vocab.json'
        data_dir = './data/covid'

        self.tokenizer = BertTokenizer.from_pretrained('./temp/bert-base-chinese')
        self.dataloader = Dataloader(tag_dir, label_dir)
        self.dataloader.load_data(os.path.join(data_dir, "val_data.json"), 'val', self.configs['max_len'])

        self.model = TagBert(self.configs['model'], self.dataloader.tag_dim)
        self.model.load_state_dict(torch.load(model_dir, self.DEVICE))
        self.model.to(self.DEVICE)
        self.model.eval()

    def predict(self, question):
        question = question.strip()
        word_squence = self.tokenizer.tokenize(question)
        tag_squence = ['0'] * len(word_squence)
        new2ori = {}
        for i in range(len(word_squence)):
            new2ori[i] = i
        pad_data = [[word_squence, tag_squence, [], question, new2ori, self.dataloader.seq_tag2id(tag_squence)]]
        pad_batch = self.dataloader.pad_batch(pad_data)
        pad_batch = tuple(t.to(self.DEVICE) for t in pad_batch)
        word_seq_tensor, _, word_mask_tensor, tag_mask_tensor = pad_batch
        tag_logits = self.model(word_seq_tensor, word_mask_tensor)

        result = recover_result(self.dataloader, tag_logits[0][0], tag_mask_tensor[0], word_squence, new2ori)

        return result


if __name__ == '__main__':
    config_dir = './configs/configs.json'
    model_dir = './output/pytorch_model_covid.bin'
    data_dir = './data/covid/real_test_data.json'
    keywords_dict_dir = './data/covid/keywords_dict.json'

    keywords_dict = json.loads(open(keywords_dict_dir, encoding='utf-8').read())
    with open(data_dir, encoding='utf-8', mode='r') as f:
        content = f.read()
    data = json.loads(content)
    predictor = TagPredict(config_dir, model_dir)

    # result = (['对', '肺组织细胞增生症', '急性呼吸窘迫综合症', '新生儿呼吸窘迫综合征患者'], '涉及疾病;涉及检查')
    # all_possible_gremlins, unreachable_entities = create_gremlin(result, keywords_dict)
    # print(f"gremlins: {all_possible_gremlins}")
    # print(f"unreachable_entities: {unreachable_entities}")
    for item in data:
        question, label, tags = item
        result = predictor.predict(question)
        all_possible_gremlins, unreachable_entities = create_gremlin(result, keywords_dict)
        print('---------------------------------------------------------------------')
        print(f"gremlins: {all_possible_gremlins}")
        print(f"unreachable_entities: {unreachable_entities}")
        print(f"the question is:{question}")
        print(f"the real result is: {item[1:]}")
        print(f"the prediction is: {result}")







