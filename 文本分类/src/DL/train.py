'''
@Author: xiaoyao jiang
@Date: 2020-04-09 17:45:10
@LastEditTime: 2020-07-17 16:34:45
@LastEditors: xiaoyao jiang
@Description: main
@FilePath: /bookClassification/src/DL/train.py
'''
import time
import torch
import numpy as np
import pandas as pd
from importlib import import_module
import argparse
from torch.utils.data import DataLoader
import joblib
from src.data.dataset import MyDataset, collate_fn
from src.DL.train_helper import train, init_network
from src.data.dictionary import Dictionary
from src.utils.tools import create_logger
from src.utils import config
from transformers import BertTokenizer, RobertaTokenizer, XLNetTokenizer


parser = argparse.ArgumentParser(description='Chinese Text Classification')
parser.add_argument(
    '--model',
    type=str,
    # required=True,
    default="bert",
    help='choose a model: CNN, RNN, RCNN, RNN_Att, DPCNN, Transformer')
parser.add_argument('--word',
                    default=True,
                    type=bool,
                    help='True for word, False for char')
parser.add_argument('--max_length',
                    default=400,
                    type=int,
                    help='True for word, False for char')
parser.add_argument('--dictionary',
                    default=None,
                    type=str,
                    help='dictionary path')
args = parser.parse_args()

logger = create_logger(config.root_path + '/logs/main.log')

if __name__ == '__main__':
    # model_name = args.model
    model_name="bert"

    x = import_module('models.' + model_name)
    if model_name in ['bert', 'xlnet', 'roberta']:
        config.bert_path = config.root_path + '/model/' + model_name + '/'
        if 'bert' in model_name:
            # config.tokenizer = BertTokenizer.from_pretrained(config.bert_path)
            config.tokenizer = BertTokenizer.from_pretrained("bert-base-chinese")

        elif 'xlnet' in model_name:
            config.tokenizer = XLNetTokenizer.from_pretrained(config.bert_path)
        elif 'roberta' in model_name:
            config.tokenizer = RobertaTokenizer.from_pretrained(config.bert_path)
        else:
            raise NotImplementedError

        config.save_path = config.root_path + 'model/saved_dict/' + model_name + '.ckpt'  # 模型训练结果
        config.log_path = config.root_path + '/logs/' + model_name
        config.hidden_size = 768
        config.eps = 1e-8
        config.gradient_accumulation_steps = 1
        config.word = True
        config.max_length = 400
    np.random.seed(1)
    torch.manual_seed(1)
    torch.cuda.manual_seed_all(1)
    torch.backends.cudnn.deterministic = True  # 保证每次结果一样

    start_time = time.time()
    logger.info("Loading data...")

    logger.info('Building dictionary ...')

    data = pd.read_csv(config.train_file, sep='\t')
    if args.word:
        data = data['text'].values.tolist()
    else:
        data = data['text'].apply(lambda x: " ".join("".join(x.split())))
    if args.dictionary is None:
        dictionary = Dictionary()
        dictionary.build_dictionary(data)
        del data
        joblib.dump(dictionary, config.root_path + '/model/vocab.bin')
    else:
        dictionary = joblib.load(args.dictionary)
    if not args.model.isupper():
        tokenizer = config.tokenizer
    else:
        tokenizer = None

    logger.info('Making dataset & dataloader...')
    train_dataset = MyDataset(config.train_file,
                              dictionary,
                              args.max_length,
                              tokenizer=tokenizer,
                              word=args.word)
    train_dataloader = DataLoader(train_dataset,
                                  batch_size=config.batch_size,
                                  shuffle=True,
                                  drop_last=True,
                                  collate_fn=collate_fn)
    dev_dataset = MyDataset(config.dev_file,
                            dictionary,
                            args.max_length,
                            tokenizer=tokenizer,
                            word=args.word)
    dev_dataloader = DataLoader(dev_dataset,
                                batch_size=config.batch_size,
                                shuffle=True,
                                drop_last=True,
                                collate_fn=collate_fn)
    test_dataset = MyDataset(config.test_file,
                             dictionary,
                             args.max_length,
                             tokenizer=tokenizer,
                             word=args.word)
    test_dataloader = DataLoader(test_dataset,
                                 batch_size=config.batch_size,
                                 shuffle=True,
                                 drop_last=True,
                                 collate_fn=collate_fn)

    # train

    #     conf.n_vocab = dictionary.max_vocab_size
    model = x.Model(config).to(config.device)
    if model_name != 'Transformer':
        init_network(model)
    print(model.parameters)

    train(config, model, train_dataloader, dev_dataloader, test_dataloader)