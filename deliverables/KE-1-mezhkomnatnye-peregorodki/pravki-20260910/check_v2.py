#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Проверка редакции 2 по листу приёмки от 10.09.2026."""

import json
import os
import re
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
FILE = os.path.join(HERE, "genglass_peregorodki_SEO_block_v2.html")


class Extract(HTMLParser):
    """Достаёт видимый текст, заголовки, ссылки и JSON-LD."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.text_parts = []
        self.h3 = []
        self.paras = []
        self.links = []
        self.imgs = []
        self.jsonld = []
        self._buf = []
        self._in_script = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "script" and a.get("type") == "application/ld+json":
            self._in_script = True
            self._buf = []
            return
        if tag == "a" and "href" in a:
            self.links.append(a["href"])
        if tag == "img":
            self.imgs.append(a.get("alt", ""))
        if tag in ("h2", "h3", "p", "td", "th"):
            self.stack.append(tag)
            self._buf = []

    def handle_endtag(self, tag):
        if tag == "script" and self._in_script:
            self.jsonld.append("".join(self._buf))
            self._in_script = False
            return
        if self.stack and self.stack[-1] == tag:
            text = "".join(self._buf).strip()
            text = re.sub(r"\s+", " ", text)
            self.stack.pop()
            self.text_parts.append(text)
            if tag == "h3":
                self.h3.append(text)
            if tag == "p":
                self.paras.append(text)
            self._buf = []

    def handle_data(self, data):
        self._buf.append(data)


def main():
    raw = open(FILE, encoding="utf-8").read()
    body = raw.split("<!-- =================================================================")
    visible_src = raw[: raw.index("SCHEMA.ORG")]

    p = Extract()
    p.feed(raw)

    text = " ".join(p.text_parts)
    problems, notes = [], []

    # --- объём -------------------------------------------------------------
    volume = sum(len(t) for t in p.text_parts)
    notes.append(f"объём видимого текста: {volume} знаков с пробелами")
    if volume > 5250:
        problems.append(f"объём {volume}, норма 4000-5000 (+5% допустимо)")

    # --- раздел 2: убранная выдуманная фактура ------------------------------
    banned = {
        "22-28 кг": "вес створки занижен вдвое",
        "3-4 часов": "цикл закалки не подтверждён",
        "около 15 дней": "срок сборки готовой модели не подтверждён",
        "40х40": "сечение профиля не подтверждено",
        "2900": "высота 2900 мм не подтверждена",
        "10-15 мм": "допуск не из PK",
        "15-18": "срок стационарной выдуман",
        "18-22": "срок раздвижной противоречит сайту",
        "16-20": "срок распашной выдуман",
        "12-15": "срок реечной выдуман",
        "22-25": "срок каскадной выдуман",
    }
    for frag, why in banned.items():
        if frag in text:
            problems.append(f"осталось «{frag}»: {why}")

    # --- раздел 2: обязательные замены --------------------------------------
    required = [
        ("около 50 кг", "вес полотна по расчёту 20 кг/м2"),
        ("600-700 °C", "проверяемое описание закалки"),
        ("4-19 мм", "рабочий диапазон толщин вместо правила 8/10"),
        ("20x20", "подтверждённое сечение профиля"),
        ("+/- 2,0 мм", "допуск до 2000 мм"),
        ("+/- 3,0 мм", "допуск 2000-3000 мм"),
        ("30-35", "срок раздвижных и лофт"),
        ("2000, 2200 и 2400 мм", "серийный ряд высот"),
    ]
    for frag, why in required:
        if frag not in text:
            problems.append(f"нет «{frag}»: {why}")

    # --- раздел 3: семантика -------------------------------------------------
    density = len(re.findall(r"стеклянн", text, re.I))
    notes.append(f"корень «стеклянн»: {density} раз (цель 8-10)")
    if not 8 <= density <= 11:
        problems.append(f"плотность «стеклянн» {density}, цель 8-10")
    if "купить" not in text.lower():
        problems.append("нет слова «купить» на транзакционной странице")
    for phrase in ("стеклянные перегородки", "светопрозрачные перегородки",
                   "стеклянная перегородка в комнату"):
        if phrase.lower() not in text.lower():
            problems.append(f"нет фразы кластера: {phrase}")

    # --- раздел 4: CTA, FAQ, изображения ------------------------------------
    cta = re.findall(r'class="cta"', raw)
    if len(cta) != 2:
        problems.append(f"CTA {len(cta)}, нужно 2")
    if len(p.imgs) != 3:
        problems.append(f"изображений {len(p.imgs)}, нужно 3")
    for alt in p.imgs:
        if not alt.strip():
            problems.append("у изображения пустой alt")

    faq_start = p.h3.index("Сколько стоит межкомнатная перегородка")
    faq_q = p.h3[faq_start:]
    if len(faq_q) != 6:
        problems.append(f"в FAQ {len(faq_q)} вопросов, нужно 6")

    # --- раздел 5: Schema совпадает с видимым посимвольно --------------------
    schemas = [json.loads(s) for s in p.jsonld]
    types = [s["@type"] for s in schemas]
    if types != ["BreadcrumbList", "FAQPage"]:
        problems.append(f"Schema: {types}")
    faq = [s for s in schemas if s["@type"] == "FAQPage"][0]["mainEntity"]
    if len(faq) != 6:
        problems.append(f"в JSON-LD {len(faq)} вопросов")
    for item in faq:
        q = item["name"]
        a = item["acceptedAnswer"]["text"]
        if q not in p.h3:
            problems.append(f"вопрос JSON-LD не найден в видимом тексте: {q}")
            continue
        idx = p.h3.index(q)
        visible_answer = p.paras[[i for i, _ in enumerate(p.paras)]
                                 .index(p.paras.index(a))] if a in p.paras else None
        if visible_answer is None:
            problems.append(f"ответ JSON-LD не совпадает с видимым: {q}")

    # --- ссылки --------------------------------------------------------------
    allowed = {
        "/mezhkomnatnye-peregorodki-na-zakaz/",
        "/mezhkomnatnye-peregorodki-na-zakaz/razdvizhnye-steklyannye-peregorodki/",
        "/mezhkomnatnye-peregorodki-na-zakaz/loft-peregorodki/",
        "/mezhkomnatnye-peregorodki-na-zakaz/stalnye-peregorodki/",
    }
    stop = ["/czena-peregorodki/", "/montazh-peregorodok/", "/mobilnye-peregorodki/",
            "/peregorodka-mezhdu-kuhnej-i-gostinoj/", "/peregorodki-dlya-garderobnoj/"]
    content_links = [l for l in p.links if not l.startswith("#")]
    if set(content_links) != allowed:
        problems.append(f"ссылки разошлись со списком: {sorted(set(content_links))}")
    for s in stop:
        if s in raw:
            problems.append(f"ссылка из стоп-листа: {s}")
    anchors = [l for l in p.links if l.startswith("#")]
    if anchors:
        notes.append(f"якоря CTA под подстановку разработчиком: {anchors}")

    # --- раздел 6: EEAT ------------------------------------------------------
    for frag, why in [("ГОСТ 30698-2014", "ГОСТ на закалённое стекло"),
                      ("ГОСТ 32539-2013", "ГОСТ на безопасное светопрозрачное"),
                      ("+7 (495) 120-75-35", "телефон производства"),
                      ("«Интегра»", "адрес производства"),
                      ("300+ лк", "проверяемое описание ОТК")]:
        if frag not in text:
            problems.append(f"нет «{frag}»: {why}")

    # --- рамки карточки ------------------------------------------------------
    for dash in ("—", "–"):
        if dash in text:
            problems.append(f"найдено тире {dash!r}")
    for word in ("единственн", "лучший", "лучшая", "лучшие", "преимуществ"):
        if word in text.lower():
            problems.append(f"стоп-слово: {word}")
    if re.search(r"за м2|за кв\. ?м|/м²|за м²|за квадратный метр(?!\.)", text.lower()):
        for m in re.findall(r"[^.]*за квадратный метр[^.]*", text.lower()):
            if "а не за квадратный метр" not in m:
                problems.append("цена за квадратный метр")
    brand = len(re.findall(r"GENGLASS", text))
    notes.append(f"GENGLASS заглавными: {brand} раз, 1 на {volume // max(brand,1)} знаков")
    if re.search(r"Genglass|GenGlass|genglass(?!\.ru)", text):
        problems.append("бренд не заглавными")
    if "2200" in text and "3600" in text:
        problems.append("упомянут формат 2200 x 3600")

    print("\n".join("  " + n for n in notes))
    print()
    if problems:
        print("ПРОБЛЕМЫ:")
        for x in problems:
            print("  -", x)
    else:
        print("Проверка редакции 2: без замечаний")


if __name__ == "__main__":
    main()
