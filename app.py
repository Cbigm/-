import re
from dataclasses import dataclass
from typing import List, Dict

import pandas as pd
import streamlit as st


STOPWORDS = {
    "the", "and", "for", "with", "from", "this", "that", "your", "you", "are", "our",
    "amazon", "product", "new", "best", "use", "using", "tool", "tools", "kit", "set"
}


@dataclass
class KeywordCandidate:
    keyword: str
    source: str
    frequency: int
    relevance: float
    intent: str


def normalize_text(text: str) -> str:
    text = str(text).lower().strip()
    text = re.sub(r"[^a-z0-9\u4e00-\u9fff\s-]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def tokenize(text: str) -> List[str]:
    text = normalize_text(text)
    tokens = text.split(" ")
    return [t for t in tokens if len(t) > 1 and t not in STOPWORDS]


def extract_ngrams(tokens: List[str], n_max: int = 3) -> List[str]:
    out = []
    for n in range(1, n_max + 1):
        for i in range(0, len(tokens) - n + 1):
            gram = " ".join(tokens[i:i + n]).strip()
            if gram:
                out.append(gram)
    return out


def infer_intent(keyword: str) -> str:
    k = keyword.lower()
    if any(x in k for x in ["buy", "price", "deal", "coupon", "cheap", "sale"]):
        return "购买意图"
    if any(x in k for x in ["how", "what", "guide", "vs", "review", "教程", "测评"]):
        return "信息意图"
    if any(x in k for x in ["brand", "official", "旗舰", "官网"]):
        return "品牌意图"
    return "泛搜索意图"


def build_keyword_library(
    traffic_df: pd.DataFrame,
    feature_text: str,
    image_tags: str,
    keyword_col: str,
    volume_col: str | None,
) -> pd.DataFrame:
    candidates: Dict[str, KeywordCandidate] = {}

    # 1) 来自流量词表
    for _, row in traffic_df.iterrows():
        raw = row.get(keyword_col, "")
        vol = float(row.get(volume_col, 0) or 0) if volume_col else 0
        tokens = tokenize(raw)
        for gram in extract_ngrams(tokens):
            if gram not in candidates:
                candidates[gram] = KeywordCandidate(
                    keyword=gram,
                    source="流量表",
                    frequency=0,
                    relevance=0.0,
                    intent=infer_intent(gram),
                )
            candidates[gram].frequency += 1
            candidates[gram].relevance += 1.0 + (vol / 10000.0)

    # 2) 来自产品描述
    for gram in extract_ngrams(tokenize(feature_text), n_max=3):
        if gram not in candidates:
            candidates[gram] = KeywordCandidate(gram, "产品参数/卖点", 0, 0.0, infer_intent(gram))
        candidates[gram].frequency += 1
        candidates[gram].relevance += 1.3

    # 3) 来自图片标签
    for gram in extract_ngrams(tokenize(image_tags), n_max=2):
        if gram not in candidates:
            candidates[gram] = KeywordCandidate(gram, "产品图片", 0, 0.0, infer_intent(gram))
        candidates[gram].frequency += 1
        candidates[gram].relevance += 1.1

    data = []
    for _, c in candidates.items():
        score = round(c.relevance * (1 + min(c.frequency, 8) * 0.08), 4)
        data.append(
            {
                "keyword": c.keyword,
                "source": c.source,
                "frequency": c.frequency,
                "intent": c.intent,
                "score": score,
                "recommended_slot": recommend_slot(c.keyword, c.intent),
            }
        )

    out = pd.DataFrame(data)
    out = out[out["keyword"].str.len() >= 2]
    out = out.sort_values(["score", "frequency"], ascending=False).reset_index(drop=True)
    return out


def recommend_slot(keyword: str, intent: str) -> str:
    if len(keyword.split()) <= 2 and intent in {"泛搜索意图", "购买意图"}:
        return "Title"
    if intent == "购买意图":
        return "Bullet"
    if intent == "信息意图":
        return "A+ / QA"
    return "Search Term"


def main() -> None:
    st.set_page_config(page_title="Amazon词库自动搭建", layout="wide")
    st.title("Amazon词库自动搭建应用")
    st.caption("上传流量词表 + 产品卖点 + 图片标签，自动生成可投放词库。")

    uploaded = st.file_uploader("上传流量词表（CSV/XLSX）", type=["csv", "xlsx"])

    col1, col2 = st.columns(2)
    with col1:
        feature_text = st.text_area(
            "产品参数与特性描述",
            placeholder="例如：stainless steel, rustproof, heavy-duty, adjustable wrench...",
            height=180,
        )
    with col2:
        image_tags = st.text_area(
            "图片标签（可从主图/场景图提炼）",
            placeholder="例如：garage repair, mechanic gift, anti-slip handle...",
            height=180,
        )

    if uploaded is None:
        st.info("先上传词表再开始。")
        return

    if uploaded.name.endswith(".csv"):
        df = pd.read_csv(uploaded)
    else:
        df = pd.read_excel(uploaded)

    st.subheader("词表预览")
    st.dataframe(df.head(20), use_container_width=True)

    cols = list(df.columns)
    keyword_col = st.selectbox("选择关键词列", options=cols)
    volume_col = st.selectbox("选择搜索量列（可选）", options=["<无>"] + cols)
    volume_col = None if volume_col == "<无>" else volume_col

    if st.button("生成词库", type="primary"):
        out = build_keyword_library(df, feature_text, image_tags, keyword_col, volume_col)
        st.success(f"已生成 {len(out)} 个候选词")
        st.dataframe(out, use_container_width=True)

        csv_bytes = out.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "下载词库CSV",
            data=csv_bytes,
            file_name="amazon_keyword_library.csv",
            mime="text/csv",
        )


if __name__ == "__main__":
    main()
