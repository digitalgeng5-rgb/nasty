#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
КЕ-1. SEO-блок под товарную сетку категории
genglass.ru/product-category/mezhkomnatnye-peregorodki/

Единый источник текста. Из него собираются:
  seo-block.html  - готовый блок для вставки под сетку (с JSON-LD)
  seo-block.md    - текст для согласования
  schema.jsonld   - BreadcrumbList + FAQPage отдельным файлом
  GENGLASS_KE-1_peregorodki.docx - версия для заказчика

Запуск: python3 build.py
"""

import json
import os
import re

BASE = "https://genglass.ru"
PAGE = f"{BASE}/product-category/mezhkomnatnye-peregorodki/"

H1 = "Стеклянные межкомнатные перегородки"

TITLE = "Стеклянные перегородки купить в Москве | GENGLASS"
DESCRIPTION = (
    "Стеклянные перегородки межкомнатные: прозрачное закалённое стекло, "
    "готовые модели и изготовление на заказ. Доставка и монтаж по Москве."
)

# ---------------------------------------------------------------------------
# Разрешённые ссылки. Больше в тексте нет ни одной.
# ---------------------------------------------------------------------------
LINKS = {
    "перегородки на заказ по вашим размерам":
        "/mezhkomnatnye-peregorodki-na-zakaz/",
    "раздвижные перегородки":
        "/mezhkomnatnye-peregorodki-na-zakaz/razdvizhnye-steklyannye-peregorodki/",
    "лофт-перегородки":
        "/mezhkomnatnye-peregorodki-na-zakaz/loft-peregorodki/",
    "перегородки в стальной раме":
        "/mezhkomnatnye-peregorodki-na-zakaz/stalnye-peregorodki/",
}

# Адреса, которые отдают 404. Сборка падает, если такой адрес попал в текст.
STOP_URLS = [
    "/czena-peregorodki/",
    "/montazh-peregorodok/",
    "/mobilnye-peregorodki/",
    "/peregorodka-mezhdu-kuhnej-i-gostinoj/",
    "/peregorodki-dlya-garderobnoj/",
]

# ---------------------------------------------------------------------------
# Контент. Разметка ссылок внутри абзацев: [анкор](url)
# ---------------------------------------------------------------------------
BLOCKS = [
    ("p",
     "GENGLASS изготавливает межкомнатные перегородки из закалённого стекла "
     "и стальных профилей на собственном производстве в Домодедово с 2018 года. "
     "В каталоге выше - готовые модели в ходовых размерах, нестандартный проём "
     "собираем по замерам."),

    ("h2", "Какие бывают межкомнатные перегородки"),
    ("p",
     "Тип выбирают по проёму: сколько места есть вокруг него и нужно ли "
     "открывать проход целиком."),
    ("table",
     ["Тип", "Где уместен", "Срок, дней", "Толщина стекла, мм"],
     [
         ["Стационарная", "Зона гостиной и спальни, кабинет в нише",
          "20-25", "8, 10, 12"],
         ["Раздвижная", "Проём от 900 мм без места под распашную створку",
          "22-25", "8, 10"],
         ["Распашная", "Кабинет или гардеробная шириной до 900 мм",
          "20-25", "8, 10"],
         ["Гармошка", "Проём 1800-3000 мм, открывается полностью",
          "25", "6, 8"],
         ["Каскадная", "Проём от 2400 мм, створки уходят вдоль стены",
          "25", "8, 10"],
         ["Реечная", "Мягкое зонирование студии без глухой стены",
          "20-22", "6, 8"],
     ]),
    ("p",
     "В стационарной конструкции нет подвижных узлов. Если проход должен "
     "открываться, берут "
     "[раздвижные перегородки](/mezhkomnatnye-peregorodki-na-zakaz/razdvizhnye-steklyannye-peregorodki/). "
     "Под чёрную раму с расстекловкой - "
     "[лофт-перегородки](/mezhkomnatnye-peregorodki-na-zakaz/loft-peregorodki/)."),

    ("h2", "Из чего делают: стекло, сталь, алюминий"),
    ("p",
     "Стекло. Работает закалённое 8, 10 и 12 мм. Закалка поднимает стойкость "
     "к удару примерно в 5 раз, а при разрушении лист рассыпается на мелкие "
     "осколки с тупыми краями. Квадратный метр стекла 10 мм весит около 25 кг, "
     "у 12 мм это 30 кг. Максимальный формат листа на производстве GENGLASS - "
     "3210 × 2250 мм."),
    ("p",
     "Сталь. Профиль 20 × 40 или 25 × 25 мм с порошковой покраской, чаще "
     "матовый чёрный RAL 9005. Держит геометрию на высоте до 3000 мм и "
     "позволяет оставить рамку тонкой: так собраны "
     "[перегородки в стальной раме](/mezhkomnatnye-peregorodki-na-zakaz/stalnye-peregorodki/)."),
    ("p",
     "Алюминий. Легче стали, красится по каталогу RAL, идёт в раздвижных "
     "системах со скрытой направляющей."),

    ("h2", "Сколько стоит межкомнатная перегородка"),
    ("p",
     "Готовые модели из каталога выше начинаются от 64 900 ₽ за изделие. "
     "Это цена конструкции целиком, а не расчёт по метрам: фурнитура и "
     "обработка кромки стоят почти одинаково на узкой и на широкой створке. "
     "Из чего складывается сумма:"),
    ("ul", [
        "площадь и толщина стекла: лист 12 мм заметно дороже 8 мм;",
        "тип открывания: механизм с доводчиком дороже глухой рамы;",
        "обработка: полировка кромки, отверстия под петли, вырезы под ручки;",
        "декор и профиль: тонировка, рифление, керамопечать, покраска по RAL;",
        "доставка и монтаж по Москве и области.",
    ]),
    ("h3", "Что входит в срок изготовления"),
    ("p",
     "Индивидуальная перегородка от GENGLASS делается 20-25 дней, и это "
     "технология, а не очередь:"),
    ("ul", [
        "замер, рабочий чертёж и согласование проекта: 3-5 дней;",
        "раскрой, кромка, отверстия: 3-4 дня;",
        "закалка: партия проходит печь за 3-4 дня;",
        "покраска профиля: 3-5 дней, эмаль полимеризуется в камере;",
        "сборка, ОТК, упаковка: 2-3 дня;",
        "монтаж на объекте: 1 день.",
    ]),
    ("p",
     "Закалённое стекло нельзя резать и сверлить после печи: все отверстия "
     "делают до закалки, и ошибка в размере на 5 мм означает новый лист."),

    ("h2", "Как выбрать перегородку под свою квартиру"),
    ("p",
     "Замерьте проём в трёх точках: сверху, посередине и снизу. Расхождение "
     "15-20 мм в новостройке - обычное дело, его закрывают регулировкой профиля."),
    ("p",
     "Если уложен тёплый пол, нижнюю направляющую не ставят: створку вешают "
     "на верхнюю балку с креплением в потолок или в стену."),
    ("p",
     "Считайте вес: створка 900 × 2400 мм из стекла 10 мм весит около 54 кг, "
     "и нести её должно перекрытие, а не гипсокартонный короб без закладной. "
     "Стекло 10 мм с уплотнителем приглушает разговор, но полной тишины за "
     "перегородкой не будет."),

    ("h2", "Изготовление под нестандартный размер"),
    ("p",
     "Когда каталожные габариты не подходят, GENGLASS делает "
     "[перегородки на заказ по вашим размерам](/mezhkomnatnye-peregorodki-na-zakaz/): "
     "высота до 3200 мм одним листом, ширина створки до 1200 мм, число секций "
     "и цвет профиля - по проекту. Скошенный потолок и колонна в проёме "
     "решаются на чертеже."),
    ("p",
     "На конструкцию и фурнитуру действует гарантия 12 месяцев. За ней стоят "
     "производство, работающее с 2018 года, и собственный ОТК: перед отгрузкой "
     "изделие сверяют с чертежом по геометрии, кромке и ходу фурнитуры."),

    ("h2", "Частые вопросы о межкомнатных перегородках"),
    ("faq", [
        ("Сколько стоит межкомнатная перегородка",
         "Готовые модели начинаются от 64 900 ₽ за изделие. Итог зависит от "
         "толщины стекла, типа открывания, фурнитуры и декора. Смету менеджер "
         "GENGLASS считает после замера."),
        ("Можно ли поставить перегородку без сверления пола",
         "Да. Раздвижную створку вешают на верхнюю направляющую с креплением "
         "в потолок или в стену, стационарное полотно заводят в П-образный "
         "профиль по стенам."),
        ("Какое стекло выбрать для перегородки в квартире",
         "Закалённое 8 мм - для стационарных полотен и лёгких створок, 10 мм - "
         "универсальный вариант для раздвижных систем, 12 мм берут при высоте "
         "от 2700 мм."),
        ("Сколько дней занимает изготовление и монтаж",
         "По индивидуальным размерам - 20-25 дней: замер, чертёж, раскрой, "
         "закалка, покраска профиля, сборка и ОТК. Монтаж занимает 1 день, "
         "каскадные конструкции - до 2 дней."),
        ("Безопасна ли стеклянная перегородка, если в доме дети",
         "Закалённое стекло при ударе рассыпается на мелкие осколки с тупыми "
         "краями. Для детской наклеивают защитную плёнку или ставят триплекс: "
         "склеенные стёкла остаются в раме."),
        ("Нужно ли согласовывать перегородку в квартире",
         "Перегородка не опирается на несущие конструкции, поэтому обычно её "
         "ставят без перепланировки. Согласование нужно, если меняются границы "
         "мокрых зон или закрывается проём в несущей стене."),
    ]),
]

IMAGES = [
    {
        "file": "steklyannaya-mezhkomnatnaya-peregorodka-stalnaya-rama.webp",
        "alt": "Стеклянная межкомнатная перегородка в стальной раме между гостиной и спальней",
        "after": "Какие бывают межкомнатные перегородки",
    },
    {
        "file": "uzel-krepleniya-zakalennogo-stekla-profil.webp",
        "alt": "Узел крепления закалённого стекла в стальном профиле перегородки GENGLASS",
        "after": "Из чего делают: стекло, сталь, алюминий",
    },
    {
        "file": "tri-tipa-mezhkomnatnyh-peregorodok.webp",
        "alt": "Три типа межкомнатных перегородок: стационарная, раздвижная и гармошка",
        "after": "Как выбрать перегородку под свою квартиру",
    },
]

LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


# ---------------------------------------------------------------------------
# Хелперы
# ---------------------------------------------------------------------------
def plain(text):
    """Текст без разметки ссылок - для подсчёта знаков и для docx."""
    return LINK_RE.sub(r"\1", text)


def esc(text):
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def to_html(text):
    out = esc(text)
    out = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', out)
    return out


def faq_pairs():
    for kind, *rest in BLOCKS:
        if kind == "faq":
            return rest[0]
    return []


def count_chars():
    """Знаки с пробелами по видимому тексту блока (без H1 страницы)."""
    parts = []
    for block in BLOCKS:
        kind = block[0]
        if kind in ("h2", "h3", "p"):
            parts.append(plain(block[1]))
        elif kind == "ul":
            parts.extend(plain(i) for i in block[1])
        elif kind == "table":
            parts.extend(block[1])
            for row in block[2]:
                parts.extend(c for c in row if c)
        elif kind == "faq":
            for q, a in block[1]:
                parts.append(q)
                parts.append(a)
    return sum(len(p) for p in parts), parts


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------
def breadcrumb_schema():
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Главная", "item": f"{BASE}/"},
            {"@type": "ListItem", "position": 2, "name": H1, "item": PAGE},
        ],
    }


def faq_schema():
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": q + "?",
                "acceptedAnswer": {"@type": "Answer", "text": a},
            }
            for q, a in faq_pairs()
        ],
    }


# ---------------------------------------------------------------------------
# Рендеры
# ---------------------------------------------------------------------------
def render_html():
    img_by_heading = {i["after"]: i for i in IMAGES}
    out = ['<section class="category-seo">']
    for block in BLOCKS:
        kind = block[0]
        if kind == "h2":
            out.append(f"  <h2>{esc(block[1])}</h2>")
            img = img_by_heading.get(block[1])
            if img:
                out.append(
                    f'  <figure><img src="/wp-content/uploads/{img["file"]}" '
                    f'alt="{esc(img["alt"])}" width="1200" height="800" '
                    f'loading="lazy"></figure>'
                )
        elif kind == "h3":
            out.append(f"  <h3>{esc(block[1])}</h3>")
        elif kind == "p":
            out.append(f"  <p>{to_html(block[1])}</p>")
        elif kind == "ul":
            out.append("  <ul>")
            out.extend(f"    <li>{to_html(i)}</li>" for i in block[1])
            out.append("  </ul>")
        elif kind == "table":
            head, rows = block[1], block[2]
            out.append('  <table class="peregorodki-types">')
            out.append("    <thead><tr>"
                       + "".join(f"<th>{esc(h)}</th>" for h in head)
                       + "</tr></thead>")
            out.append("    <tbody>")
            for row in rows:
                cells = "".join(f"<td>{esc(c)}</td>" for c in row)
                out.append(f"      <tr>{cells}</tr>")
            out.append("    </tbody>")
            out.append("  </table>")
        elif kind == "faq":
            for q, a in block[1]:
                out.append(f"  <h3>{esc(q)}?</h3>")
                out.append(f"  <p>{esc(a)}</p>")
    out.append("</section>")
    out.append("")
    for schema in (breadcrumb_schema(), faq_schema()):
        out.append('<script type="application/ld+json">')
        out.append(json.dumps(schema, ensure_ascii=False, indent=2))
        out.append("</script>")
    return "\n".join(out) + "\n"


def render_md():
    out = [f"# {H1}", ""]
    for block in BLOCKS:
        kind = block[0]
        if kind == "h2":
            out += [f"## {block[1]}", ""]
        elif kind == "h3":
            out += [f"### {block[1]}", ""]
        elif kind == "p":
            out += [block[1], ""]
        elif kind == "ul":
            out += [f"- {i}" for i in block[1]] + [""]
        elif kind == "table":
            head, rows = block[1], block[2]
            out.append("| " + " | ".join(head) + " |")
            out.append("|" + "|".join(["---"] * len(head)) + "|")
            for row in rows:
                out.append("| " + " | ".join(c if c else "-" for c in row) + " |")
            out.append("")
        elif kind == "faq":
            for q, a in block[1]:
                out += [f"**{q}?**", "", a, ""]
    return "\n".join(out)


def render_docx(path):
    from docx import Document
    from docx.shared import Pt

    doc = Document()
    doc.core_properties.title = TITLE
    doc.add_heading(H1, level=1)

    meta = doc.add_paragraph()
    meta.add_run("Title: ").bold = True
    meta.add_run(TITLE + "\n")
    meta.add_run("Description: ").bold = True
    meta.add_run(DESCRIPTION)
    for run in meta.runs:
        run.font.size = Pt(9)

    for block in BLOCKS:
        kind = block[0]
        if kind == "h2":
            doc.add_heading(block[1], level=2)
        elif kind == "h3":
            doc.add_heading(block[1], level=3)
        elif kind == "p":
            doc.add_paragraph(plain(block[1]))
        elif kind == "ul":
            for i in block[1]:
                doc.add_paragraph(plain(i), style="List Bullet")
        elif kind == "table":
            head, rows = block[1], block[2]
            table = doc.add_table(rows=1, cols=len(head))
            table.style = "Table Grid"
            for cell, text in zip(table.rows[0].cells, head):
                cell.text = text
                for p in cell.paragraphs:
                    for r in p.runs:
                        r.bold = True
            for row in rows:
                cells = table.add_row().cells
                for cell, text in zip(cells, row):
                    cell.text = text if text else "-"
            doc.add_paragraph()
        elif kind == "faq":
            for q, a in block[1]:
                p = doc.add_paragraph()
                p.add_run(q + "?").bold = True
                doc.add_paragraph(a)

    doc.add_page_break()
    doc.add_heading("Ссылки в тексте", level=2)
    for anchor, url in LINKS.items():
        doc.add_paragraph(f"{anchor} - {url}", style="List Bullet")

    doc.add_heading("Изображения", level=2)
    for i, img in enumerate(IMAGES, 1):
        doc.add_paragraph(
            f"{i}. {img['file']} (WebP, до 300 КБ, 3:2). "
            f"alt: {img['alt']}. Ставится после H2 «{img['after']}».",
            style="List Bullet",
        )
    doc.save(path)


# ---------------------------------------------------------------------------
# Проверки перед сборкой
# ---------------------------------------------------------------------------
def selfcheck():
    text_all = render_md()
    problems = []

    total, _ = count_chars()
    if not 4000 <= total <= 5000:
        problems.append(f"объём {total} знаков, нужно 4000-5000")

    for dash in ("—", "–"):
        if dash in text_all:
            problems.append(f"найдено тире {dash!r}")

    for word in ("единственн", "лучш", "преимуществ", "за м2", "за кв. м", "/м²", "за м²"):
        if word.lower() in text_all.lower():
            problems.append(f"стоп-слово: {word}")

    for url in STOP_URLS:
        if url in text_all:
            problems.append(f"ссылка из стоп-листа: {url}")

    urls_in_text = set(LINK_RE.findall(text_all))
    for anchor, url in urls_in_text:
        if LINKS.get(anchor) != url:
            problems.append(f"недопустимая ссылка: [{anchor}]({url})")
    if len(urls_in_text) != 4:
        problems.append(f"ссылок {len(urls_in_text)}, нужно 4")

    if "2200" in text_all or "3600" in text_all:
        problems.append("упомянут формат 2200 x 3600")

    if text_all.count("GENGLASS") < 4:
        problems.append("GENGLASS упомянут реже, чем нужно")

    if len(faq_pairs()) != 6:
        problems.append(f"в FAQ {len(faq_pairs())} пар, нужно 6")

    digits = re.findall(r"\d[\d\s]*", text_all)
    if len(digits) < 12:
        problems.append(f"цифр {len(digits)}, нужно минимум 12")

    return total, len(digits), problems


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    total, digits, problems = selfcheck()

    with open(os.path.join(here, "seo-block.html"), "w", encoding="utf-8") as f:
        f.write(render_html())
    with open(os.path.join(here, "seo-block.md"), "w", encoding="utf-8") as f:
        f.write(render_md())
    with open(os.path.join(here, "schema.jsonld"), "w", encoding="utf-8") as f:
        json.dump([breadcrumb_schema(), faq_schema()], f,
                  ensure_ascii=False, indent=2)
        f.write("\n")
    render_docx(os.path.join(here, "GENGLASS_KE-1_peregorodki.docx"))

    print(f"Объём: {total} знаков с пробелами")
    print(f"Числовых значений в тексте: {digits}")
    print(f"FAQ: {len(faq_pairs())} пар")
    if problems:
        print("ПРОБЛЕМЫ:")
        for p in problems:
            print("  -", p)
    else:
        print("Самопроверка: без замечаний")


if __name__ == "__main__":
    main()
