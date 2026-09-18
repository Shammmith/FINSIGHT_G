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


import os
import numpy as np
import requests
import onnxruntime as ort
from tokenizers import Tokenizer
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.feature_extraction.text import TfidfVectorizer
from kneed import KneeLocator

# Paths where we cache the model files inside the container
MODEL_DIR = "/tmp/minilm"
TOKENIZER_URL = "https://huggingface.co/Xenova/all-MiniLM-L6-v2/resolve/main/tokenizer.json"
MODEL_URL = "https://huggingface.co/Xenova/all-MiniLM-L6-v2/resolve/main/onnx/model.onnx"


def _download_if_missing(url: str, dest_path: str):
    if not os.path.exists(dest_path):
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)


class HybridClusteringPipeline:
    """
    Pure ONNX Runtime inference — zero PyTorch, zero transformers library.
    Downloads model.onnx and tokenizer.json directly from HuggingFace.
    Memory footprint: ~180MB total (well within 512MB free tier).
    """
    _session = None
    _tokenizer = None

    def __init__(self, min_k: int = 2, max_k: int = 10, top_n_keywords: int = 5):
        self.min_k = min_k
        self.max_k = max_k
        self.top_n_keywords = top_n_keywords

        if HybridClusteringPipeline._session is None:
            tokenizer_path = f"{MODEL_DIR}/tokenizer.json"
            model_path = f"{MODEL_DIR}/model.onnx"

            _download_if_missing(TOKENIZER_URL, tokenizer_path)
            _download_if_missing(MODEL_URL, model_path)

            HybridClusteringPipeline._tokenizer = Tokenizer.from_file(tokenizer_path)
            HybridClusteringPipeline._tokenizer.enable_padding(pad_token="[PAD]")
            HybridClusteringPipeline._tokenizer.enable_truncation(max_length=128)

            sess_options = ort.SessionOptions()
            sess_options.intra_op_num_threads = 1
            sess_options.inter_op_num_threads = 1
            HybridClusteringPipeline._session = ort.InferenceSession(
                model_path,
                sess_options=sess_options,
                providers=["CPUExecutionProvider"],
            )

        self.session = HybridClusteringPipeline._session
        self.tokenizer = HybridClusteringPipeline._tokenizer

    def _embed(self, descriptions: list[str]) -> np.ndarray:
        encoded = self.tokenizer.encode_batch(descriptions)

        input_ids = np.array([e.ids for e in encoded], dtype=np.int64)
        attention_mask = np.array([e.attention_mask for e in encoded], dtype=np.int64)
        token_type_ids = np.zeros_like(input_ids, dtype=np.int64)

        outputs = self.session.run(
            None,
            {
                "input_ids": input_ids,
                "attention_mask": attention_mask,
                "token_type_ids": token_type_ids,
            },
        )

        # outputs[0] = last_hidden_state: (batch, seq_len, 384)
        token_embeddings = outputs[0]

        # Mean pooling
        mask_expanded = np.expand_dims(attention_mask, axis=-1).astype(float)
        sum_embeddings = np.sum(token_embeddings * mask_expanded, axis=1)
        sum_mask = np.clip(mask_expanded.sum(axis=1), a_min=1e-9, a_max=None)
        embeddings = sum_embeddings / sum_mask

        # L2 normalize
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        embeddings = embeddings / np.clip(norms, a_min=1e-9, a_max=None)

        return embeddings.astype(np.float32)

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