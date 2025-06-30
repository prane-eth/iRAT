# Uncertainty estimation module

from irat.utils.lm_functions import get_response
from irat.utils.settings import env
from irat.utils.stage_base import StageBase
from irat.utils.logger import log_debug, log_error, log_info

import numpy as np
from openai import OpenAI
from sklearn.metrics.pairwise import cosine_similarity

client = OpenAI(base_url=env('EMBED_API_URL'))

def model_encode(texts: list[str]) -> np.ndarray:
	resp = client.embeddings.create(input=texts, model='Any')
	embeddings = [item.embedding for item in resp.data]
	return np.array(embeddings)

try:
    model_encode(['test'])  # Test the model encoding function
except Exception as e:
	log_error(f'Error in model encoding: {e}')
	raise RuntimeError('Failed to initialize the embedding model. Run the server.')
	# run_vllm_command(embed_model_name, task='embed', port=8002)


class Uncertainty(StageBase):
	STAGE = "uncertainty"

	@staticmethod
	def token_entropy(token_probs: list[float]) -> float:
		"""
		Placeholder for token-level entropy. Not implemented because OpenAI does not provide token-level probabilities.
		"""
		return 0.0

	@staticmethod
	def estimate_uncertainty(llm_response: str, token_probs: list[float] = None, 
							 consistency_scores: list[float] = None) -> float:
		"""
		Computes an uncertainty score based on consistency score (self-consistency) of multiple outputs.
		Lower consistency => higher uncertainty.
		"""
		if consistency_scores is None or len(consistency_scores) == 0:
			log_error("Warning: No consistency scores provided. Returning maximum uncertainty.")
			return 1.0  # Maximum uncertainty

		avg_consistency = np.mean(consistency_scores)

		uncertainty_score = 1.0 - avg_consistency
		uncertainty_score = max(0.0, min(1.0, uncertainty_score))

		return uncertainty_score

	@staticmethod
	def compute_uncertainty_for_question(question, num_samples=3, draft=None):
		"""
		Computes uncertainty score for the given question using multiple drafts.
		Uses self-consistency (via cosine similarity) as the consistency score.
		"""
		log_info(f"Generating multiple drafts for uncertainty calculation...")
		responses = []
		if draft:  # first sample is available
			responses.append(draft)
			num_samples -= 1
		for _ in range(num_samples):
			draft = get_response(question)
			responses.append(draft)

		# Compute pairwise cosine similarity
		embeddings = model_encode(responses)
		similarities = cosine_similarity(embeddings)
		n = len(responses)
		pairwise_scores = []
		for i in range(n):
			for j in range(i+1, n):
				pairwise_scores.append(similarities[i][j])
		avg_consistency = np.mean(pairwise_scores)

		# Call the uncertainty estimation module
		uncertainty_score = Uncertainty.estimate_uncertainty(
			llm_response=responses[0],  # main draft
			token_probs=None,
			consistency_scores=[avg_consistency]
		)

		log_debug(f"Uncertainty Score: {uncertainty_score:.3f}")
		return uncertainty_score

if __name__ == "__main__":
	# Example usage
	question = "Who is the new President of France?"
	uncertainty_score = Uncertainty.compute_uncertainty_for_question(question, num_samples=3)
	log_debug(f"Uncertainty Score for the question '{question}': {uncertainty_score:.3f}")
