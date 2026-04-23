"""
RAG 检索模块 — 星座知识库
优先使用 ChromaDB 向量检索；如果 ChromaDB embedding 模型下载失败，
自动回退到 jieba + TF-IDF 方案（纯本地，不需要下载任何模型）
"""
import os
import json
import numpy as np

# 知识库路径
KNOWLEDGE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "knowledge", "astrology_knowledge.json"
)

# ChromaDB 持久化路径（使用可写目录）
_default_chroma = os.path.join(os.path.dirname(__file__), "..", "data", "chroma_db")
CHROMA_PATH = os.environ.get("CHROMA_PATH", _default_chroma)

# 全局状态
_backend = None          # "chromadb" | "tfidf"
_collection = None       # ChromaDB collection（chromadb模式）
_tfidf_data = None       # TF-IDF 数据（tfidf模式）


# ──────────────────────────────────────────────
#  公共接口
# ──────────────────────────────────────────────

def retrieve_knowledge(query: str, n_results: int = 3) -> str:
    """
    根据用户提问检索相关知识

    参数:
        query: 用户的问题，比如 "今天适合投简历吗"
        n_results: 返回的知识条数

    返回:
        格式化后的知识文本，可直接注入 Prompt
    """
    _ensure_initialized()

    if _backend == "chromadb":
        return _retrieve_chromadb(query, n_results)
    else:
        return _retrieve_tfidf(query, n_results)


def rebuild_index():
    """重建索引（知识库更新后调用）"""
    global _backend, _collection, _tfidf_data
    _backend = None
    _collection = None
    _tfidf_data = None
    _ensure_initialized()
    if _backend == "chromadb":
        return _collection.count()
    else:
        return len(_tfidf_data["documents"])


# ──────────────────────────────────────────────
#  初始化：先试 ChromaDB，失败则回退 TF-IDF
# ──────────────────────────────────────────────

def _ensure_initialized():
    global _backend
    if _backend is not None:
        return

    # 先尝试 ChromaDB
    try:
        _init_chromadb()
        _backend = "chromadb"
        print("[RAG] 使用 ChromaDB 向量检索")
        return
    except Exception as e:
        print(f"[RAG] ChromaDB 初始化失败({e})，回退到 TF-IDF")

    # 回退到 TF-IDF
    _init_tfidf()
    _backend = "tfidf"
    print("[RAG] 使用 jieba + TF-IDF 检索")


# ──────────────────────────────────────────────
#  方案A：ChromaDB
# ──────────────────────────────────────────────

def _init_chromadb():
    global _collection
    import chromadb

    client = chromadb.PersistentClient(path=CHROMA_PATH)

    try:
        _collection = client.get_collection("astrology_knowledge")
        print(f"[RAG] 已加载 ChromaDB 知识库，共 {_collection.count()} 条")
    except Exception:
        print("[RAG] 首次启动，正在构建 ChromaDB 索引...")
        _collection = client.create_collection(
            name="astrology_knowledge",
            metadata={"description": "星座占星知识库"},
        )
        _build_chromadb_index()


def _build_chromadb_index():
    knowledge = _load_knowledge()
    ids, documents, metadatas = [], [], []

    for item in knowledge:
        ids.append(item["id"])
        doc = f"{item['category']} - {item['topic']}: {item['content']}"
        documents.append(doc)
        metadatas.append({"category": item["category"], "topic": item["topic"]})

    _collection.add(ids=ids, documents=documents, metadatas=metadatas)
    print(f"[RAG] ChromaDB 索引构建完成，共 {len(ids)} 条")


def _retrieve_chromadb(query: str, n_results: int) -> str:
    results = _collection.query(query_texts=[query], n_results=n_results)

    if not results["documents"] or not results["documents"][0]:
        return ""

    pieces = []
    for i, doc in enumerate(results["documents"][0]):
        parts = doc.split(": ", 1)
        content = parts[1] if len(parts) > 1 else doc
        topic = results["metadatas"][0][i].get("topic", "")
        pieces.append(f"【{topic}】{content}")

    return "\n".join(pieces)


# ──────────────────────────────────────────────
#  方案B：jieba + TF-IDF（纯本地，零依赖下载）
# ──────────────────────────────────────────────

def _init_tfidf():
    global _tfidf_data
    import jieba
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    knowledge = _load_knowledge()

    # 构建文档列表
    documents = []
    topics = []
    contents = []
    for item in knowledge:
        doc = f"{item['category']} {item['topic']} {item['content']}"
        documents.append(doc)
        topics.append(item["topic"])
        contents.append(item["content"])

    # jieba 分词后用 TF-IDF 向量化
    def tokenize(text):
        return " ".join(jieba.cut(text))

    tokenized_docs = [tokenize(d) for d in documents]

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(tokenized_docs)

    _tfidf_data = {
        "vectorizer": vectorizer,
        "tfidf_matrix": tfidf_matrix,
        "topics": topics,
        "contents": contents,
        "documents": documents,
        "tokenize": tokenize,
    }
    print(f"[RAG] TF-IDF 索引构建完成，共 {len(documents)} 条")


def _retrieve_tfidf(query: str, n_results: int) -> str:
    from sklearn.metrics.pairwise import cosine_similarity

    data = _tfidf_data
    query_tok = data["tokenize"](query)
    query_vec = data["vectorizer"].transform([query_tok])

    similarities = cosine_similarity(query_vec, data["tfidf_matrix"]).flatten()
    top_indices = similarities.argsort()[::-1][:n_results]

    pieces = []
    for idx in top_indices:
        if similarities[idx] > 0.01:  # 相似度太低就不返回
            pieces.append(f"【{data['topics'][idx]}】{data['contents'][idx]}")

    return "\n".join(pieces)


# ──────────────────────────────────────────────
#  工具函数
# ──────────────────────────────────────────────

def _load_knowledge():
    with open(KNOWLEDGE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)
