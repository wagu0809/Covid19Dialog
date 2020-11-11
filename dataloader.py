import json
import random
import torch
import math
from transformers import BertTokenizer


class Dataloader:
    def __init__(self, tag_dir, intent_dir):

        with open(tag_dir) as f:
            tag_vocab = json.load(f)
        self.tag2id = dict([(tag, i) for i, tag in enumerate(tag_vocab)])
        self.id2tag = dict([(i, tag) for i, tag in enumerate(tag_vocab)])
        with open(intent_dir) as f:
            intent_vocab = json.load(f)
        self.intent2id = dict([(intent, i) for i, intent in enumerate(intent_vocab)])
        self.id2intent = dict([(i, intent) for i, intent in enumerate(intent_vocab)])
        self.tag_dim = len(tag_vocab)
        self.intent_dim = len(intent_vocab)
        self.data = {}
        self.tokenizer = BertTokenizer.from_pretrained('./temp/bert-base-chinese')

    def load_data(self, data_dir, key, max_len):
        if data_dir:
            self.data[key] = json.load(open(data_dir))

            for d in self.data[key]:

                d[0] = d[0][:max_len]
                d[1] = d[1][:max_len]
                d[3][0] = d[3][0][:max_len]
                d[3] = [self.tokenizer.encode("[CLS]" + d[3][0]), d[3][1]]
                new2ori = {}
                for i in range(len(d[0])):
                    new2ori[i] = i
                d.append(new2ori)
                tag_seq = d[1]
                d.append(self.seq_tag2id(tag_seq))

    def seq_tag2id(self, tags):
        return [self.tag2id[x] if x in self.tag2id else self.tag2id['0'] for x in tags]

    def seq_id2tag(self, ids):
        return [self.id2tag[x] for x in ids]

    def get_train_batch(self, batch_size):
        batch_data = random.choices(self.data['train'], k=batch_size)
        return self.pad_batch(batch_data)

    def pad_batch(self, batch_data):
        # print(f"batch_data: {batch_data}")
        batch_size = len(batch_data)
        max_seq_len = max([len(x[0]) for x in batch_data]) + 2
        word_mask_tensor = torch.zeros((batch_size, max_seq_len), dtype=torch.long)
        word_seq_tensor = torch.zeros((batch_size, max_seq_len), dtype=torch.long)
        tag_mask_tensor = torch.zeros((batch_size, max_seq_len), dtype=torch.long)
        tag_seq_tensor = torch.zeros((batch_size, max_seq_len), dtype=torch.long)
        for i in range(batch_size):
            words = batch_data[i][0]
            tags = batch_data[i][-1]
            words = ['[CLS]'] + words + ['[SEP]']
            indexed_tokens = self.tokenizer.convert_tokens_to_ids(words)
            sen_len = len(words)
            word_seq_tensor[i, :sen_len] = torch.LongTensor([indexed_tokens])
            tag_seq_tensor[i, 1:sen_len-1] = torch.LongTensor(tags)
            word_mask_tensor[i, :sen_len] = torch.LongTensor([1] * sen_len)
            tag_mask_tensor[i, 1:sen_len-1] = torch.LongTensor([1] * (sen_len-2))

        return word_seq_tensor, tag_seq_tensor, word_mask_tensor, tag_mask_tensor

    def yield_batches(self, batch_size, data_key):
        batch_num = math.ceil(len(self.data[data_key]) / batch_size)
        for i in range(batch_num):
            batch_data = self.data[data_key][i * batch_size:(i + 1) * batch_size]
            yield self.pad_batch(batch_data), batch_data, len(batch_data)