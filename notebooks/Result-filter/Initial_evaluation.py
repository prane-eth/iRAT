from sentence_transformers import CrossEncoder
import os

os.chdir('irat')
os.chdir('notebooks')
os.chdir('Result-filter')
from AR_evaluate import evaluate_model_2  # from local file

model_name = 'cross-encoder/ms-marco-MiniLM-L6-v2'
# model_name = 'cross-encoder/ms-marco-MiniLM-L4-v2'
# model_name = 'cross-encoder/ms-marco-MiniLM-L12-v2'
# model_name = 'mixedbread-ai/mxbai-rerank-xsmall-v1'


model = CrossEncoder(model_name)

# Get top k+1 scores and apply a threshold of 60%
evaluate_model_2(model, model_name_short=None, add_r=1, threshold=6.0)
