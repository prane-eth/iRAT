# uncertainty.py

from irat.stage_base import StageBase
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime
from ..main_pipeline import get_draft  # adjust if your get_draft is elsewhere

class Uncertainty(StageBase):
    STAGE = "uncertainty"

    # Load SentenceTransformer model once
    model = SentenceTransformer('all-MiniLM-L6-v2')

    @staticmethod
    def token_entropy(token_probs: list[float]) -> float:
        """
        Placeholder for token-level entropy. Not implemented because OpenAI does not provide token-level probabilities.
        """
        return 0.0

    @staticmethod
    def estimate_uncertainty(llm_response: str, token_probs: list[float] = None, consistency_scores: list[float] = None) -> float:
        """
        Computes an uncertainty score based on consistency score (self-consistency) of multiple outputs.
        Lower consistency => higher uncertainty.
        """
        if consistency_scores is None or len(consistency_scores) == 0:
            print("Warning: No consistency scores provided. Returning maximum uncertainty.")
            return 1.0  # Maximum uncertainty

        avg_consistency = np.mean(consistency_scores)

        uncertainty_score = 1.0 - avg_consistency
        uncertainty_score = max(0.0, min(1.0, uncertainty_score))

        return uncertainty_score

    @staticmethod
    def compute_uncertainty_for_question(question, num_samples=3):
        """
        Computes uncertainty score for the given question using multiple drafts.
        Uses self-consistency (via cosine similarity) as the consistency score.
        """
        print(f"{datetime.now()} [INFO] Generating multiple drafts for uncertainty calculation...")
        responses = []
        for _ in range(num_samples):
            draft = get_draft(question)  # reuse your existing function
            responses.append(draft)

        # Compute pairwise cosine similarity
        embeddings = Uncertainty.model.encode(responses)
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

        print(f"{datetime.now()} [INFO] Uncertainty Score: {uncertainty_score:.3f}")
        return uncertainty_score
