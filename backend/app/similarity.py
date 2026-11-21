"""Поиск похожих докладов: нормализация, понятийные группы, TF-IDF и покрытие названия."""
import math
import re
from dataclasses import dataclass

STOP = set(
    "расскажу покажу разберем разберём сравним покажем типичные способ результата нельзя отдавать вместе "
    "работать работе работы использования использование идея ошибки ошибка контекста и в во не на с со по к о об "
    "от до для из за как что это или а но то же бы мы я вы он она они их его ее у при без над под про все всё так "
    "уже еще ещё только там тут чтобы если когда где кто чем нас вас наш ваш the of a an and to in for on with is are".split()
)
BOOST = {"ai", "agent", "req", "doc", "prompt", "scen"}
CONCEPTS = [
    (re.compile(r"^(ии|ai|llm|gpt|нейро|ml)"), "ai"),
    (re.compile(r"^(агент|agent)"), "agent"),
    (re.compile(r"^(тз|техзад|техническ|задани|требовани|требова|requir|spec|спец)"), "req"),
    (re.compile(r"^(документ|docs|doc|wiki|вики)"), "doc"),
    (re.compile(r"^(аналитик|аналит|analy)"), "analyst"),
    (re.compile(r"^(промпт|prompt)"), "prompt"),
    (re.compile(r"^(сценар|usecase|use)"), "scen"),
]
_SPLIT = re.compile(r"[^a-zа-я0-9]+")


def concept_of(w: str):
    for rx, name in CONCEPTS:
        if rx.match(w):
            return name
    return None


def stem(w: str) -> str:
    if re.search(r"[а-я]", w):
        return w[:5] if len(w) > 5 else w
    return w[:6] if len(w) > 6 else w


def tokens(text: str):
    out = []
    for w in _SPLIT.split(text.lower().replace("ё", "е")):
        if not w or len(w) < 2 or w in STOP:
            continue
        out.append((w, concept_of(w) or stem(w)))
    return out


def text_hash(text: str) -> str:
    s = re.sub(r"\s+", " ", text.lower()).strip()
    h = 2166136261
    for ch in s:
        h ^= ord(ch) & 0xFFFF
        h = (h * 16777619) & 0xFFFFFFFF
    return f"{h:08x}"


@dataclass
class Match:
    talk_id: str
    score: float
    aspects: list


@dataclass
class Result:
    level: str
    top_score: float
    matches: list


class SimilarityIndex:
    def __init__(self, talks):
        """talks: iterable of (id, title, annotation)."""
        self.docs = []
        df = {}
        for tid, title, ann in talks:
            tk = tokens(f"{title} {ann or ''}")
            tf, disp = {}, {}
            for raw, t in tk:
                tf[t] = tf.get(t, 0) + 1
                disp.setdefault(t, raw)
            for k in tf:
                df[k] = df.get(k, 0) + 1
            self.docs.append({"id": tid, "tf": tf, "disp": disp})
        self.n = len(self.docs)
        self.df = df
        for d in self.docs:
            vec = {k: (1 + math.log(c)) * self.idf(k) for k, c in d["tf"].items()}
            d["vec"] = vec
            d["norm"] = math.sqrt(sum(v * v for v in vec.values())) or 1.0

    def idf(self, k: str) -> float:
        base = math.log((self.n + 1) / (self.df.get(k, 0) + 0.5))
        return base * (2.5 if k in BOOST else 1.0)

    def search(self, query: str, high: float, medium: float, limit: int = 5) -> Result:
        tf = {}
        for _, t in tokens(query):
            tf[t] = tf.get(t, 0) + 1
        qv = {k: (1 + math.log(c)) * self.idf(k) for k, c in tf.items()}
        qn = math.sqrt(sum(v * v for v in qv.values())) or 1.0
        scored = []
        for d in self.docs:
            dot, shared = 0.0, []
            for k, qw in qv.items():
                dw = d["vec"].get(k)
                if dw:
                    dot += qw * dw
                    shared.append((qw * dw, k))
            if not shared:
                continue
            tot = sum(d["vec"].values())
            cov = sum(w for k, w in d["vec"].items() if k in qv)
            score = 0.5 * dot / (qn * d["norm"]) + 0.5 * (cov / tot if tot else 0) * min(1.0, len(d["vec"]) / 5)
            shared.sort(reverse=True)
            scored.append(Match(d["id"], score, [d["disp"].get(k, k) for _, k in shared[:4]]))
        scored.sort(key=lambda m: m.score, reverse=True)
        top = scored[:limit]
        s = top[0].score if top else 0.0
        level = "HIGH" if s >= high else "MEDIUM" if s >= medium else "LOW"
        return Result(level, s, top)
