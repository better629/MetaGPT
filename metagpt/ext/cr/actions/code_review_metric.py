#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   :
import datetime
import io
import json
import os

import pandas as pd
from metagpt.actions.action import Action
from metagpt.const import DEFAULT_WORKSPACE_ROOT
from metagpt.utils.common import parse_json_code_block

CODE_REVIEW_EVALUATION_PROMPT_TEMPLATE = """
## GT要点信息表
- 此表的内容是Code Review的正确结果记录，可以把它定位成"标准答案"
```
{gt_df}
```

## CR结果表
- 此表是对**GT要点信息表**所关联的Patch代码而进行的一次Code Review的结果，这个结果不确定正确与否，所以需要对此表数据进行评估打分
```
{results_diff}
```

## Output Format
```json
[
    {{
        "PR": "PR",
        "commented_file": "commented_file",
        "code": "code",
        "code_start_line": "code_start_line",
        "code_end_line": "code_end_line",
        "comment": "comment",
        "point_id": "point_id",
        "point": "point",
        "point_detail": "point_detail",
        "score": "分数",
    }}
]
```

## 你的任务
1.根据给你的**GT要点信息表**，对**CR结果表**中的每1条记录进行评估打分
2.评估规则
- 遍历**CR结果表**
    - 首先根据**CR结果表**当前行的'point_id' 从 **GT要点信息表**中过滤出'point_id'一样的行
    - 然后遍历 从**GT要点信息表**中过滤出'point_id'一样的行，然后逐行找出'commented_file'、'code'2个字段和遍历**CR结果表**当前行的'commented_file'、'code'有比较高的匹配度
    - 如果'commented_file'、'code'匹配度高，则判定为**CR结果表**当前行是正确的，正确打分结果为：1，否则为：0
    - 如果判定**CR结果表**当前行是正确的，那么将与之对应的**GT要点信息表**的数据从表中删除

## 需严格遵守
1.根据提供给你的**GT要点信息表**作为"标准答案"对**CR结果表**的每1条记录逐条的进行评估打分，如果**CR结果表**对应的行是正确的，则打分结果为：1，否则为：0
2.在**CR结果表**的基础上加上一列"score"来记录打分结果，以**Output Format**的形式输出
3.不要漏掉**CR结果表**的任何一条记录

"""


class CodeReviewEvaluation(Action):
    name: str = "CodeReviewEvaluation"
    pr: str = ""
    mode: int = 0
    calculate_type: str = ""

    async def run(self, cr_result: list = []):
        cr_output_name = DEFAULT_WORKSPACE_ROOT / "cr" / str(datetime.date.today()) / f'CR-{self.pr}'
        cr_output_name.mkdir(parents=True, exist_ok=True)
        with open(cr_output_name / f'CR-{self.pr}-result.json', 'w', encoding='utf-8') as file:
            file.writelines(json.dumps(cr_result, ensure_ascii=False))
        await self.metric(cr_result=cr_result, metric_name=cr_output_name)
        return f'自动化评估结果已经写入{cr_output_name}/CR-{self.pr}-metric.csv'

    def init_metric_null_df(self):
        columns = ["PR", "commented_file", "code", "code_start_line", "code_end_line", "comment", "point_id", "point", "score"]
        df = pd.DataFrame(columns=columns)
        return df

    def get_metric_df_row(self, gt_num: int = 0, recall_num: int = 0,  recall: float = 0, precision_num: int = 0, precision: float = 0):
        metric_count_row_name = {
            "PR": "GT要点数",
            "commented_file": "召回数",
            "code": "召回率",
            "code_start_line": "准确数",
            "code_end_line": "准确率",
            "comment": "",
            "point_id": "",
            "point": "",
            "point_detail": "",
            "score": ""
        }
        metric_count_row_value = {
            "PR": gt_num,
            "commented_file": recall_num,
            "code": recall,
            "code_start_line": precision_num,
            "code_end_line": precision,
            "comment": "",
            "point_id": "",
            "point": "",
            "point_detail": "",
            "score": ""
        }
        return metric_count_row_name, metric_count_row_value

    async def calculate(self, gt_df: pd.DataFrame, results_diff: list, metric_name: str):
        # 当前PR的GT要点总数
        gt_num = gt_df.shape[0]
        # GT要点召回数，默认等于CR结果中全部为diff的总条数
        recall_num = len(results_diff)
        # CR准确的个数
        precision_num = 0

        evaluation_result = []
        if self.calculate_type != 'llm':
            # 指标打分结果详细表
            '''
            统计逻辑
            1.判断CR结果是否同时满足"目标文件"和"要点id"和GT数据对应
            2.将当前条数据打上标(对应上则score设置为1)
            3.将结果写入对应的"METRIC.csv"
            4.计算召回和准确率并终端打印结果
            5.公式: 
                召回数：即GT要点召回数，默认等于CR结果中全部为diff的总条数
                召回率：召回数除以当前PR的GT总数
                准确数：经过上述第1、2条判断后，precision_num的值
                准确率：准确数除以召回数
            '''
            for result in results_diff:
                result['PR'] = int(self.pr)
                result['score'] = 0
                for index, row in gt_df.iterrows():
                    if row['commented_file'] == result['commented_file'] and row['point_id'] == result['point_id']:
                        precision_num += 1
                        result['score'] = 1
                        gt_df = gt_df.loc[(gt_df.index != index)]
                        break
                evaluation_result.append(result)
        else:
            prompt = CODE_REVIEW_EVALUATION_PROMPT_TEMPLATE.format(gt_df=gt_df.to_string(), results_diff=str(results_diff))
            resp = await self.llm.aask(prompt)
            json_str = parse_json_code_block(resp)[0]
            evaluation_result = json.loads(json_str)
            if len(evaluation_result) != 0:
                evaluation_result_df = pd.read_json(io.StringIO(json.dumps(evaluation_result)))
                for index, row in evaluation_result_df.iterrows():
                    if row['score'] == 1:
                        precision_num += 1

        # 计算召回率
        if gt_num == 0:
            recall = 1
        else:
            recall = round(recall_num / gt_num, 2)
            if recall > 1:
                recall = 1

        # 计算准确率
        if recall_num == 0:
            precision = 0
        else:
            precision = round(precision_num / recall_num, 2)

        # 将上述判断结果写入对应的metric的csv文件
        if len(evaluation_result) != 0:
            evaluation_result_df = pd.read_json(io.StringIO(json.dumps(evaluation_result)))
        else:
            evaluation_result_df = self.init_metric_null_df()

        metric_count_row_name, metric_count_row_value = self.get_metric_df_row(gt_num=gt_num, recall_num=recall_num, recall=recall, precision_num=precision_num, precision=precision)

        evaluation_result_df.insert(0, 'PR', evaluation_result_df.pop('PR'))
        evaluation_result_df.loc[len(evaluation_result_df)] = metric_count_row_name
        evaluation_result_df.loc[len(evaluation_result_df)] = metric_count_row_value
        evaluation_result_df.to_csv(metric_name / f'CR-{self.pr}-metric.csv', index=False, encoding='utf-8')

        print(f"召回数是{recall_num}，召回率是{recall}\n准确数是{precision_num}，准确率是{precision}\n")
        print(f"详细信息如下表\n{evaluation_result_df}")

    async def metric(self, cr_result: list, metric_name: str):
        if len(cr_result) == 0:
            print("CR结果为空，指标全为0")
            return
        gt_csv_path = '蚂蚁-CR-GT_4_llm.csv'
        gt_df = pd.read_csv(gt_csv_path)

        # 获取GT要点中当前PR的GT要点数据
        gt_df = gt_df[gt_df['PR'] == int(self.pr)]
        # 如果mode是1（忽略要点中24 25 26这3个不可精确描述的问题）
        ignore_points = [24, 25, 26]
        if self.mode == 1:
            gt_df = gt_df.loc[~gt_df['point_id'].isin(ignore_points)]

        # result中diff的部分，是我们关注的，另外如果mode为1（忽略要点中24 25 26这3个不可精确描述的问题）
        results_diff = []
        for result in cr_result:
            if result['code'].startswith('+'):
                if self.mode == 0 or (self.mode == 1 and result['point_id'] not in ignore_points):
                    results_diff.append(result)

        await self.calculate(gt_df=gt_df, results_diff=results_diff, metric_name=metric_name)
