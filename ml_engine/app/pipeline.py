# ml_engine/app/pipeline.py
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.feature_extraction.text import TfidfVectorizer
from kneed import KneeLocator


class HybridClusteringPipeline:
    """
    Clustering happens in SEMANTIC embedding space (SBERT) so that
    'SBUX COFFEE' and 'STARBUCKS' land in the same cluster even
    with zero lexical overlap. TF-IDF is used ONLY afterwards, to
    generate human-readable keyword labels for each discovered cluster.
    """
    _embedder = None  # process-wide singleton — loaded once, not per-instance

    def __init__(self, min_k: int = 2, max_k: int = 10, top_n_keywords: int = 5):
        self.min_k = min_k
        self.max_k = max_k
        self.top_n_keywords = top_n_keywords
        if HybridClusteringPipeline._embedder is None:
            HybridClusteringPipeline._embedder = SentenceTransformer(
                "all-MiniLM-L6-v2", device="cpu"
            )
        self.embedder = HybridClusteringPipeline._embedder

    def _embed(self, descriptions: list[str]) -> np.ndarray:
        embeddings = self.embedder.encode(
            descriptions,
            normalize_embeddings=True,
            show_progress_bar=False,
            convert_to_tensor=True,   # get torch.Tensor, bypasses numpy ABI entirely
        )
        return embeddings.cpu().numpy()  # explicit, controlled conversion after the fact

    def _determine_optimal_k(self, embeddings: np.ndarray, min_k: int, max_k: int):
        inertias, silhouettes = [], []
        k_range = list(range(min_k, max_k + 1))
        for k in k_range:
            km = KMeans(n_clusters=k, n_init=10, random_state=42)
            labels = km.fit_predict(embeddings)
            inertias.append(km.inertia_)
            silhouettes.append(silhouette_score(embeddings, labels))

        kneedle = KneeLocator(k_range, inertias, curve="convex", direction="decreasing")
        optimal_k = kneedle.elbow or k_range[int(np.argmax(silhouettes))]
        return optimal_k, inertias, silhouettes

    def _extract_keywords_per_cluster(self, descriptions, labels, n_clusters) -> dict:
        """TF-IDF used purely for interpretability — NOT for clustering itself."""
        tfidf = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", max_features=3000)
        matrix = tfidf.fit_transform(descriptions)
        terms = np.array(tfidf.get_feature_names_out())

        keywords = {}
        for c in range(n_clusters):
            idx = np.where(labels == c)[0]
            if len(idx) == 0:
                keywords[c] = []
                continue
            mean_scores = np.asarray(matrix[idx].mean(axis=0)).ravel()
            top_idx = mean_scores.argsort()[::-1][: self.top_n_keywords]
            keywords[c] = terms[top_idx].tolist()
        return keywords

    def run(self, descriptions: list[str]) -> dict:
        # Guard: filter out blank/whitespace-only descriptions but preserve count mapping
        cleaned = [d if d and d.strip() else "unknown transaction" for d in descriptions]

        embeddings = self._embed(cleaned)
        n = len(cleaned)

        # Guard: can't run KMeans with k >= n_samples
        effective_max_k = min(self.max_k, max(n - 1, 1))
        effective_min_k = min(self.min_k, effective_max_k)

        if n <= 2 or effective_max_k < effective_min_k:
            # Degenerate case: too few transactions to meaningfully cluster —
            # assign everything to a single cluster rather than crashing.
            labels = np.array([0] * n)
            centroid = embeddings.mean(axis=0, keepdims=True)
            keywords = self._extract_keywords_per_cluster(cleaned, labels, 1)
            return {
                "optimal_k": 1,
                "labels": labels.tolist(),
                "embeddings": embeddings.tolist(),
                "centroids": centroid.tolist(),
                "silhouette": 0.0,
                "keywords": keywords,
            }

        optimal_k, inertias, silhouettes = self._determine_optimal_k(
            embeddings, min_k=effective_min_k, max_k=effective_max_k
        )
        final_model = KMeans(n_clusters=optimal_k, n_init=10, random_state=42)
        labels = final_model.fit_predict(embeddings)
        keywords = self._extract_keywords_per_cluster(cleaned, labels, optimal_k)

        return {
            "optimal_k": optimal_k,
            "labels": labels.tolist(),
            "embeddings": embeddings.tolist(),
            "centroids": final_model.cluster_centers_.tolist(),
            "silhouette": float(silhouette_score(embeddings, labels)) if optimal_k > 1 else 0.0,
            "keywords": keywords,
        }