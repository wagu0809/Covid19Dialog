from Model import TagBert
from dataloader import Dataloader
from transformers import AdamW, get_linear_schedule_with_warmup
import json
import os
import torch
from util.utils import recover_result, calculateF1
from util.logger import get_logger
logger = get_logger('./output/log/training_log.log')

from warnings import simplefilter
simplefilter(action='ignore', category=FutureWarning)


def set_seed(seed):
    # random.seed(seed)
    # np.random.seed(seed)
    torch.manual_seed(seed)


if __name__ == "__main__":
    # domain = 'covid'
    domain = 'server'
    config_path = './configs/configs.json'
    log_dir = './temp/log'

    tag_dir = f'./data/{domain}/tag_vocab.json'
    intent_dir = f'./data/{domain}/label_vocab.json'
    data_dir = f'./data/{domain}'
    output_dir = f'./output/{domain}'
    checkpoint = ''
    # checkpoint = './output/covid/pytorch_model.bin'
    zipped_model_path = os.path.join(output_dir, 'bert_convid19.zip')

    with open(config_path, encoding='utf-8', mode='r') as f:
        content = f.read()
    configs = json.loads(content)
    set_seed(configs['seed'])
    DEVICE = configs['DEVICE']
    # writer = SummaryWriter(log_dir)

    dataloader = Dataloader(tag_dir, intent_dir)
    for data_key in ['train', 'val']:
        dataloader.load_data(os.path.join(data_dir, data_key+"_data.json"), data_key, configs['max_len'])

    model = TagBert(configs['model'], dataloader.tag_dim)
    if checkpoint:
        model.load_state_dict(torch.load(checkpoint, DEVICE))
    model.to(DEVICE)

    if configs['model']['finetune']:
        no_decay = ['bias', 'LayerNorm.weight']
        optimizer_grouped_parameters = [
            {'params': [p for n, p in model.named_parameters() if
                        not any(nd in n for nd in no_decay) and p.requires_grad],
             'weight_decay': configs['model']['weight_decay']},
            {'params': [p for n, p in model.named_parameters() if any(nd in n for nd in no_decay) and p.requires_grad],
             'weight_decay': 0.0}
        ]
        optimizer = AdamW(optimizer_grouped_parameters, lr=configs['model']['learning_rate'],
                          eps=configs['model']['adam_epsilon'])
        scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=configs['model']['warmup_steps'],
                                                    num_training_steps=configs['model']['max_step'])
    else:
        for n, p in model.named_parameters():
            if 'bert' in n:
                p.requires_grad = False
        optimizer = torch.optim.Adam(filter(lambda p: p.requires_grad, model.parameters()),
                                     lr=configs['model']['learning_rate'])

    for name, param in model.named_parameters():
        print(name, param.shape, param.device, param.requires_grad)

    max_step = configs['model']['max_step']
    check_step = configs['model']['check_step']
    batch_size = configs['model']['batch_size']
    model.zero_grad()

    train_slot_loss = 0
    best_val_f1 = 0.

    for step in range(1, max_step + 1):
        model.train()
        batched_data = dataloader.get_train_batch(batch_size)
        batched_data = tuple(t.to(DEVICE) for t in batched_data)

        word_seq_tensor, tag_seq_tensor, word_mask_tensor, tag_mask_tensor = batched_data

        _, slot_loss = model.forward(word_seq_tensor, word_mask_tensor, tag_seq_tensor, tag_mask_tensor)
        train_slot_loss += slot_loss.item()
        slot_loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()

        if configs['model']['finetune']:
            scheduler.step()  # Update learning rate schedule

        model.zero_grad()

        if step % check_step == 0:
            train_slot_loss = train_slot_loss / check_step
            logger.info('[%d|%d] step' % (step, max_step))
            logger.info(f'\t slot loss: {train_slot_loss}')

            predict_golden = []

            val_slot_loss = 0
            model.eval()
            for pad_batch, ori_batch, real_batch_size in dataloader.yield_batches(batch_size, data_key='val'):
                pad_batch = tuple(t.to(DEVICE) for t in pad_batch)
                word_seq_tensor, tag_seq_tensor, word_mask_tensor, tag_mask_tensor = pad_batch

                with torch.no_grad():
                    slot_logits, slot_loss = model.forward(word_seq_tensor,
                                                           word_mask_tensor,
                                                           tag_seq_tensor,
                                                           tag_mask_tensor)

                val_slot_loss += slot_loss.item() * real_batch_size
                for j in range(real_batch_size):
                    predicts, _ = recover_result(dataloader, slot_logits[j], tag_mask_tensor[j],
                                                 ori_batch[j][0], ori_batch[j][-2])
                    labels = ori_batch[j][2]

                    predict_golden.append({
                        'predict': predicts,
                        'golden': labels
                    })

            total = len(dataloader.data['val'])
            val_slot_loss /= total
            logger.info('%d samples val' % total)
            logger.info(f'\t slot loss: {val_slot_loss}')

            # calculate F1 score
            precision, recall, F1 = calculateF1(predict_golden)
            logger.info('-' * 20 + 'tags' + '-' * 20)
            logger.info('\t Precision: %.2f' % (100 * precision))
            logger.info('\t Recall: %.2f' % (100 * recall))
            logger.info('\t F1: %.2f' % (100 * F1))

            if F1 > best_val_f1:
                best_val_f1 = F1
                torch.save(model.state_dict(), os.path.join(output_dir, 'pytorch_model' + str(step) + '.bin'))
                logger.info('best val precision %.4f' % best_val_f1)
                logger.info(f'save on {output_dir}')

            train_slot_loss = 0


