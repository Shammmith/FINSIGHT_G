# # ml_engine/app/pipeline.py
# import numpy as np
# from sklearn.cluster import KMeans
# from sklearn.metrics import silhouette_score
# from sklearn.feature_extraction.text import TfidfVectorizer
# from kneed import KneeLocator
# from optimum.onnxruntime import ORTModelForFeatureExtraction
# from transformers import AutoTokenizer
# import torch


# class HybridClusteringPipeline:
#     _model = None
#     _tokenizer = None

#     def __init__(self, min_k: int = 2, max_k: int = 10, top_n_keywords: int = 5):
#         self.min_k = min_k
#         self.max_k = max_k
#         self.top_n_keywords = top_n_keywords
        
#         if HybridClusteringPipeline._model is None:
#             model_id = "sentence-transformers/all-MiniLM-L6-v2"
#             # Load the ONNX version of the model (much lighter!)
#             HybridClusteringPipeline._tokenizer = AutoTokenizer.from_pretrained(model_id)
#             HybridClusteringPipeline._model = ORTModelForFeatureExtraction.from_pretrained(model_id, export=True)
            
#         self.model = HybridClusteringPipeline._model
#         self.tokenizer = HybridClusteringPipeline._tokenizer

#     def _embed(self, descriptions: list[str]) -> np.ndarray:
#         # Tokenize
#         inputs = self.tokenizer(descriptions, padding=True, truncation=True, return_tensors="pt")
        
#         # Run inference through ONNX
#         outputs = self.model(**inputs)
        
#         # Mean pooling (standard for sentence transformers)
#         token_embeddings = outputs.last_hidden_state
#         attention_mask = inputs['attention_mask']
#         input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
#         sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
#         sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
#         embeddings = sum_embeddings / sum_mask
        
#         # Normalize (L2)
#         embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
        
#         return embeddings.detach().numpy()
    
#     def _determine_optimal_k(self, embeddings: np.ndarray, min_k: int, max_k: int):
#         inertias, silhouettes = [], []
#         k_range = list(range(min_k, max_k + 1))
#         for k in k_range:
#             km = KMeans(n_clusters=k, n_init=10, random_state=42)
#             labels = km.fit_predict(embeddings)
#             inertias.append(km.inertia_)
#             silhouettes.append(silhouette_score(embeddings, labels))

#         kneedle = KneeLocator(k_range, inertias, curve="convex", direction="decreasing")
#         optimal_k = kneedle.elbow or k_range[int(np.argmax(silhouettes))]
#         return optimal_k, inertias, silhouettes

#     def _extract_keywords_per_cluster(self, descriptions, labels, n_clusters) -> dict:
#         """TF-IDF used purely for interpretability — NOT for clustering itself."""
#         tfidf = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", max_features=3000)
#         matrix = tfidf.fit_transform(descriptions)
#         terms = np.array(tfidf.get_feature_names_out())

#         keywords = {}
#         for c in range(n_clusters):
#             idx = np.where(labels == c)[0]
#             if len(idx) == 0:
#                 keywords[c] = []
#                 continue
#             mean_scores = np.asarray(matrix[idx].mean(axis=0)).ravel()
#             top_idx = mean_scores.argsort()[::-1][: self.top_n_keywords]
#             keywords[c] = terms[top_idx].tolist()
#         return keywords

#     def run(self, descriptions: list[str]) -> dict:
#         # Guard: filter out blank/whitespace-only descriptions but preserve count mapping
#         cleaned = [d if d and d.strip() else "unknown transaction" for d in descriptions]

#         embeddings = self._embed(cleaned)
#         n = len(cleaned)

#         # Guard: can't run KMeans with k >= n_samples
#         effective_max_k = min(self.max_k, max(n - 1, 1))
#         effective_min_k = min(self.min_k, effective_max_k)

#         if n <= 2 or effective_max_k < effective_min_k:
#             # Degenerate case: too few transactions to meaningfully cluster —
#             # assign everything to a single cluster rather than crashing.
#             labels = np.array([0] * n)
#             centroid = embeddings.mean(axis=0, keepdims=True)
#             keywords = self._extract_keywords_per_cluster(cleaned, labels, 1)
#             return {
#                 "optimal_k": 1,
#                 "labels": labels.tolist(),
#                 "embeddings": embeddings.tolist(),
#                 "centroids": centroid.tolist(),
#                 "silhouette": 0.0,
#                 "keywords": keywords,
#             }

#         optimal_k, inertias, silhouettes = self._determine_optimal_k(
#             embeddings, min_k=effective_min_k, max_k=effective_max_k
#         )
#         final_model = KMeans(n_clusters=optimal_k, n_init=10, random_state=42)
#         labels = final_model.fit_predict(embeddings)
#         keywords = self._extract_keywords_per_cluster(cleaned, labels, optimal_k)

#         return {
#             "optimal_k": optimal_k,
#             "labels": labels.tolist(),
#             "embeddings": embeddings.tolist(),
#             "centroids": final_model.cluster_centers_.tolist(),
#             "silhouette": float(silhouette_score(embeddings, labels)) if optimal_k > 1 else 0.0,
#             "keywords": keywords,
#         }


import numpy as np
import torch
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.feature_extraction.text import TfidfVectorizer
from kneed import KneeLocator
from optimum.onnxruntime import ORTModelForFeatureExtraction
from transformers import AutoTokenizer

class HybridClusteringPipeline:
    """
    Clustering happens in SEMANTIC embedding space.
    OPTIMIZED FOR PRODUCTION: Uses ONNX Runtime instead of native PyTorch
    to drastically reduce memory footprint (<512MB) for free-tier deployments.
    """
    _model = None
    _tokenizer = None

    def __init__(self, min_k: int = 2, max_k: int = 10, top_n_keywords: int = 5):
        self.min_k = min_k
        self.max_k = max_k
        self.top_n_keywords = top_n_keywords
        
        if HybridClusteringPipeline._model is None:
            # Use a pre-converted ONNX model from the HuggingFace Hub
            # This skips the memory-heavy conversion step entirely
            model_id = "Xenova/all-MiniLM-L6-v2" 
            HybridClusteringPipeline._tokenizer = AutoTokenizer.from_pretrained(model_id)
            HybridClusteringPipeline._model = ORTModelForFeatureExtraction.from_pretrained(model_id, file_name="onnx/model.onnx")

        self.model = HybridClusteringPipeline._model
        self.tokenizer = HybridClusteringPipeline._tokenizer

    def _embed(self, descriptions: list[str]) -> np.ndarray:
        # 1. Tokenize
        inputs = self.tokenizer(descriptions, padding=True, truncation=True, return_tensors="pt")
        
        # 2. ONNX Inference
        outputs = self.model(**inputs)
        
        # 3. Mean Pooling (standard for sentence-transformers)
        token_embeddings = outputs.last_hidden_state
        attention_mask = inputs['attention_mask']
        
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
        sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
        embeddings = sum_embeddings / sum_mask
        
        # 4. L2 Normalize
        embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
        
        return embeddings.detach().numpy()

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
        cleaned = [d if d and d.strip() else "unknown transaction" for d in descriptions]
        embeddings = self._embed(cleaned)
        n = len(cleaned)

        effective_max_k = min(self.max_k, max(n - 1, 1))
        effective_min_k = min(self.min_k, effective_max_k)

        if n <= 2 or effective_max_k < effective_min_k:
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