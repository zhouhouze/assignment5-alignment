"""Biased diagnostic supplement to the uniform 20-row audit; CPU only."""
import argparse
import json
from pathlib import Path
import random
import re

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--train', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
pattern = re.compile(r"^(?:I(?:’|')m sorry|I am sorry|I cannot|I can(?:’|')t|Sorry)", re.I)
candidates = []
with args.train.open() as source:
    for index, line in enumerate(source):
        row = json.loads(line)
        if pattern.search(row['response'].lstrip()):
            candidates.append((index, row))
with args.output.open('x') as target:
    for index, row in random.Random(0).sample(candidates, 3):
        item = dict(example_id=index, line_number=index+1, selection_seed=0,
                    selection='3 from response refusal-prefix regex candidates; biased diagnostic sample',
                    candidate_count=len(candidates), **row, human_label=None,
                    human_notes=None, human_review_status='pending')
        target.write(json.dumps(item, ensure_ascii=False)+'\n')
