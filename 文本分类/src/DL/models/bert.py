'''
@Author: your name
@Date: 2020-06-18 21:15:35
@LastEditTime: 2020-07-06 14:08:35
@LastEditors: xiaoyao jiang
@Description: In User Settings Edit
@FilePath: /bookClassification/src/DL/models/bert.py
'''
# coding: UTF-8
import torch.nn as nn
from transformers import BertModel, BertConfig

class Model(nn.Module):
    def __init__(self, config):
        super(Model, self).__init__()
        model_config = BertConfig.from_pretrained(
            "bert-base-chinese", num_labels=config.num_classes)
        self.bert = BertModel.from_pretrained("bert-base-chinese",
                                              config=model_config)
        for param in self.bert.parameters():
            param.requires_grad = True
        self.fc = nn.Linear(config.hidden_size, config.num_classes)

    def forward(self, x):
        context = x[0]  # 输入的句子
        mask = x[
            1]  # 对padding部分进行mask，和句子一个size，padding部分用0表示，如：[1, 1, 1, 1, 0, 0]
        token_type_ids = x[2]
        result = self.bert(context,
                              attention_mask=mask,
                              token_type_ids=token_type_ids)
        pooled=result[1]
        out = self.fc(pooled)
        return out