import json
from Model import TagBert
import torch
from dataloader import Dataloader
from util.utils import recover_result


class TagPredict:
    def __init__(self, config_dir, model_dir, tag_dir, label_dir):
        with open(config_dir, encoding='utf-8', mode='r') as f:
            content = f.read()
        self.configs = json.loads(content)
        self.DEVICE = self.configs['DEVICE']
        # DEVICE = 'cpu' if not torch.cuda.is_available() else 'cuda:0'
        # tag_dir = './data/tag_vocab.json'
        # data_dir = './data'
        with open(label_dir, encoding='utf-8') as f:
            label_vocab = json.load(f)
        self.label2id = dict([(tag, i) for i, tag in enumerate(label_vocab)])
        self.id2label = dict([(i, tag) for i, tag in enumerate(label_vocab)])

        # self.tokenizer = BertTokenizer.from_pretrained('./temp/bert-base-chinese')
        self.dataloader = Dataloader(tag_dir, label_dir)
        self.tokenizer = self.dataloader.tokenizer
        # self.dataloader.load_data(os.path.join(data_dir, "val_data.json"), 'val', self.configs['max_len'])

        print('Load from', model_dir)
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
        # print(f"pad_batch: {pad_batch}")
        word_seq_tensor, _, word_mask_tensor, tag_mask_tensor = pad_batch

        tag_logits = self.model(word_seq_tensor, word_mask_tensor)

        result = recover_result(self.dataloader, tag_logits[0][0], tag_mask_tensor[0], word_squence, new2ori)

        # print(f"result: {result}")
        return result, self.label2id[result[-1]] if result[-1] != '' else 0


if __name__ == '__main__':
    config_dir = './configs/configs.json'
    model_dir = './output/pytorch_model_covid.bin'
    tag_dir = './data/covid/tag_vocab.json'
    label_dir = './data/covid/label_vocab.json'
    predictor = TagPredict(config_dir, model_dir, tag_dir, label_dir)
    keywords = json.loads(open('./data/covid/keywords_dict.json', encoding='utf-8').read())
    # question = '出现皮肤发红和发炎的症状可能与什么疾病有关？'  # (['发炎'], '涉及症状')
    # question = '哪种病会与咽部溃疡以及鼻衄症状有关？'  # (['咽部溃疡', '鼻衄'], '涉及症状')
    # question = '从医学专科上来讲，结核病属于什么科？'  # (['结核病'], '医学专科;就诊;就诊科室')
    # question = '哪项检查能有效检测汉坦病毒肺综合征、沙雷菌肺炎和肺组织细胞增生症？'  # (['沙雷菌肺炎', '肺组织细胞增生症'], '涉及疾病;涉及检查')
    # question = '蜂窝织炎在什么科室就诊？'  # (['蜂窝织炎'], '医学专科;就诊;就诊科室')
    # question = '胸腔积液患者有哪些临床表现？'  # (['胸腔积液患'], '临床表现')
    # question = '颈椎病患者有哪些临床表现？'  # (['颈椎病'], '临床表现')
    # question = '感染了新型冠状病毒需要去哪个科室就诊？'  # (['感染了', '新型冠状病毒'], '医学专科;就诊;就诊科室')
    # question = '出现哮鸣音和浑身忽冷忽热症状时，应该是得了什么病？'  # (['哮鸣音', '浑身忽冷忽热'], '涉及疾病;涉及检查')
    # question = '出现肌肉萎缩和水肿伴呼吸困难、紫绀可能与什么疾病相关？'  # (['出现肌肉萎缩', '水肿伴呼吸困难、紫绀'], '涉及症状')

    # question = '查看用户权限的常见命令是什么?'  # (['查看用户权限'], '常见命令')
    # question = '删除用户的常见命令是什么?'  # (['删除用户'], '常见命令')
    # question = '数据库的定义是什么?'  # (['数据库'], '定义')
    # question = '用户授权的概念是什么?'  # (['用户授权'], '概念')
    # question = '举个关系型数据库的例子.'  # (['关系型数据库'], '例子')
    # question = '我经常耳闷，应该去哪个科室进行检查？'  # (['关系型数据库'], '例子')
    question = '在医学专科领域中，细菌性肺炎属于什么疾病？'  # (['关系型数据库'], '例子')
    result, label_id = predictor.predict(question)

    print(result, label_id)

    # gremlin = create_gremlin(result, keywords)




