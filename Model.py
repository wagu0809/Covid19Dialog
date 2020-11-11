import torch
import torch.nn as nn
from transformers import BertModel


class TagBert(nn.Module):
    def __init__(self, model_config, tag_num):
        super(TagBert, self).__init__()
        self.model_config = model_config
        self.hidden_units = model_config['hidden_units']
        self.tag_dim = tag_num
        self.bert = BertModel.from_pretrained('./temp/bert-base-chinese')
        self.dropout = nn.Dropout(model_config['dropout'])
        self.finetune = model_config['finetune']
        self.hidden_units = model_config['hidden_units']

        # self.ln = nn.LayerNorm(self.hidden_units)  # TODO: add a normalization layer
        if self.hidden_units > 0:
            self.slot_classifier = nn.Linear(self.hidden_units, self.tag_dim)
            self.slot_hidden = nn.Linear(self.bert.config.hidden_size, self.hidden_units)
            nn.init.xavier_uniform_(self.slot_hidden.weight)
        else:
            self.slot_classifier = nn.Linear(self.bert.config.hidden_size, self.tag_dim)

        nn.init.xavier_uniform_(self.slot_classifier.weight)
        self.slot_loss_fct = nn.CrossEntropyLoss()

    def forward(self, word_seq_tensor, word_mask_tensor, tag_seq_tensor=None, tag_mask_tensor=None):
        if not self.finetune:
            self.bert.eval()
            with torch.no_grad():
                outputs = self.bert(input_ids=word_seq_tensor,
                                    attention_mask=word_mask_tensor)
        else:
            outputs = self.bert(input_ids=word_seq_tensor,
                                attention_mask=word_mask_tensor)

        sequence_output = outputs[0]

        if self.hidden_units > 0:
            sequence_output = nn.functional.relu(self.slot_hidden(self.dropout(sequence_output)))

        sequence_output = self.dropout(sequence_output)
        slot_logits = self.slot_classifier(sequence_output)
        outputs = (slot_logits,)

        if tag_seq_tensor is not None:
            active_tag_loss = tag_mask_tensor.view(-1) == 1
            active_tag_logits = slot_logits.view(-1, self.tag_dim)[active_tag_loss]
            active_tag_labels = tag_seq_tensor.view(-1)[active_tag_loss]
            slot_loss = self.slot_loss_fct(active_tag_logits, active_tag_labels)
            outputs = outputs + (slot_loss,)

        return outputs  # slot_logits, (slot_loss),


class IntentBert(nn.Module):
    def __init__(self, model_config, intent_dim):
        super(IntentBert, self).__init__()
        self.model_config = model_config
        self.hidden_units = model_config['hidden_units']
        self.intent_dim = intent_dim
        self.bert = BertModel.from_pretrained('./temp/bert-base-chinese')
        self.dropout = nn.Dropout(model_config['dropout'])
        self.finetune = model_config['finetune']
        self.hidden_units = model_config['hidden_units']
        self.intent_weight = torch.tensor([1.] * intent_dim)

        # self.ln = nn.LayerNorm(self.hidden_units)  # TODO: add a normalization layer
        if self.hidden_units > 0:
            self.intent_classifier = nn.Linear(self.hidden_units, self.intent_dim)
            self.intent_hidden = nn.Linear(self.bert.config.hidden_size, self.hidden_units)
            nn.init.xavier_uniform_(self.intent_hidden.weight)
        else:
            self.intent_classifier = nn.Linear(self.bert.config.hidden_size, self.intent_dim)

        nn.init.xavier_uniform_(self.intent_classifier.weight)

        self.intent_loss_fct = torch.nn.BCEWithLogitsLoss(pos_weight=self.intent_weight)

    def forward(self, word_seq_tensor, word_mask_tensor, intent_tensor=None):
        if not self.finetune:
            self.bert.eval()
            with torch.no_grad():
                outputs = self.bert(input_ids=word_seq_tensor,
                                    attention_mask=word_mask_tensor)
        else:
            outputs = self.bert(input_ids=word_seq_tensor,
                                attention_mask=word_mask_tensor)

        pooled_output = outputs[1]

        if self.hidden_units > 0:
            pooled_output = nn.functional.relu(self.intent_hidden(self.dropout(pooled_output)))

        pooled_output = self.dropout(pooled_output)
        intent_logits = self.intent_classifier(pooled_output)
        outputs = (intent_logits,)

        if intent_tensor is not None:
            intent_loss = self.intent_loss_fct(intent_logits, intent_tensor)
            outputs = outputs + (intent_loss,)

        return outputs  # intent_logits, (intent_loss),