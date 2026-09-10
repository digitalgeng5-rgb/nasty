/* Примерочная фото для дзеновских статей.
   Каждый <figure class="ph" data-slot="..." data-ratio="16:9" data-min-w="1280">
   умеет: перетащить файл, вставить из буфера, подвигать кадр, приблизить.
   Выбранное фото запоминается в браузере (localStorage), файлы никуда не уходят. */

(function () {
  'use strict';

  var KEY = 'dzen-fit:' + location.pathname;
  var store = load();
  var active = null;

  function load() {
    try { return JSON.parse(localStorage.getItem(KEY) || '{}'); }
    catch (e) { return {}; }
  }

  function save() {
    try { localStorage.setItem(KEY, JSON.stringify(store)); }
    catch (e) { /* картинки крупные, места может не хватить: это не критично */ }
  }

  function ratio(str) {
    var p = String(str || '3:2').split(':');
    var w = parseFloat(p[0]) || 3;
    var h = parseFloat(p[1]) || 2;
    return w / h;
  }

  function fmtRatio(w, h) {
    var r = w / h;
    var known = [[16 / 9, '16:9'], [3 / 2, '3:2'], [4 / 3, '4:3'], [1, '1:1'], [2 / 3, '2:3'], [3 / 4, '3:4'], [9 / 16, '9:16']];
    for (var i = 0; i < known.length; i++) {
      if (Math.abs(r - known[i][0]) < 0.02) return known[i][1];
    }
    return r.toFixed(2) + ':1';
  }

  function build(fig) {
    var slot = fig.dataset.slot || 'slot-' + Math.random().toString(36).slice(2, 7);
    fig.dataset.slot = slot;

    var need = ratio(fig.dataset.ratio);
    var minW = parseInt(fig.dataset.minW || '0', 10);

    var frame = document.createElement('div');
    frame.className = 'frame';
    frame.style.aspectRatio = String(need);

    var img = document.createElement('img');
    img.alt = '';
    img.draggable = false;
    frame.appendChild(img);

    var drop = document.createElement('div');
    drop.className = 'drop';
    drop.innerHTML =
      '<div class="big">Перетащите фото сюда</div>' +
      '<div>или кликните, или вставьте из буфера (Ctrl+V)</div>' +
      '<div class="req">' + (fig.dataset.ratio || '3:2') +
      (minW ? ', от ' + minW + ' px по ширине' : '') + '</div>';
    frame.appendChild(drop);

    var file = document.createElement('input');
    file.type = 'file';
    file.accept = 'image/*';
    file.style.display = 'none';

    var tools = document.createElement('div');
    tools.className = 'tools';
    tools.innerHTML =
      '<button type="button" data-act="replace">Заменить</button>' +
      '<button type="button" data-act="center">Центр</button>' +
      '<button type="button" data-act="clear">Убрать</button>' +
      '<label>Крупнее <input type="range" min="100" max="250" value="100" step="1"></label>' +
      '<span class="info"></span>';

    fig.insertBefore(frame, fig.firstChild);
    fig.appendChild(file);
    var cap = fig.querySelector('figcaption');
    if (cap) fig.insertBefore(tools, cap); else fig.appendChild(tools);

    var range = tools.querySelector('input[type=range]');
    var info = tools.querySelector('.info');
    var state = { x: 50, y: 50, zoom: 100, src: null, w: 0, h: 0, name: '' };

    function paint() {
      img.style.objectPosition = state.x + '% ' + state.y + '%';
      img.style.transform = 'scale(' + (state.zoom / 100) + ')';
      range.value = state.zoom;
      if (state.w) {
        var small = minW && state.w < minW;
        info.innerHTML = '<b>' + state.w + '×' + state.h + '</b> px, ' +
          fmtRatio(state.w, state.h) +
          (small ? ' <span class="bad">— мелковато для Дзена</span>' : '');
      } else {
        info.textContent = '';
      }
    }

    function apply(src, meta) {
      state.src = src;
      img.src = src;
      img.onload = function () {
        state.w = img.naturalWidth;
        state.h = img.naturalHeight;
        fig.classList.add('filled');
        paint();
        persist();
      };
      if (meta) { state.name = meta.name || ''; }
    }

    function persist() {
      store[slot] = { x: state.x, y: state.y, zoom: state.zoom, src: state.src, name: state.name };
      save();
    }

    function clear() {
      state.src = null; state.w = 0; state.h = 0; state.x = 50; state.y = 50; state.zoom = 100;
      img.removeAttribute('src');
      fig.classList.remove('filled');
      delete store[slot];
      save();
      paint();
    }

    function read(f) {
      if (!f || !/^image\//.test(f.type)) return;
      var fr = new FileReader();
      fr.onload = function () { apply(fr.result, f); };
      fr.readAsDataURL(f);
    }

    // клик и выбор файла
    frame.addEventListener('click', function (e) {
      if (fig.classList.contains('filled')) return;
      file.click();
    });
    file.addEventListener('change', function () { read(file.files[0]); file.value = ''; });

    // перетаскивание файла
    ['dragenter', 'dragover'].forEach(function (t) {
      frame.addEventListener(t, function (e) { e.preventDefault(); frame.classList.add('over'); });
    });
    ['dragleave', 'drop'].forEach(function (t) {
      frame.addEventListener(t, function (e) { e.preventDefault(); frame.classList.remove('over'); });
    });
    frame.addEventListener('drop', function (e) {
      var dt = e.dataTransfer;
      if (dt && dt.files && dt.files.length) read(dt.files[0]);
    });

    // вставка из буфера — в последний тронутый слот
    frame.addEventListener('mouseenter', function () { active = read; });

    // кнопки
    tools.addEventListener('click', function (e) {
      var act = e.target.dataset && e.target.dataset.act;
      if (act === 'replace') file.click();
      if (act === 'center') { state.x = 50; state.y = 50; state.zoom = 100; paint(); persist(); }
      if (act === 'clear') clear();
    });
    range.addEventListener('input', function () { state.zoom = parseInt(range.value, 10); paint(); });
    range.addEventListener('change', persist);

    // двигаем кадр мышью
    var drag = null;
    frame.addEventListener('pointerdown', function (e) {
      if (!fig.classList.contains('filled')) return;
      e.preventDefault(); // иначе браузер начнёт своё перетаскивание картинки
      drag = { px: e.clientX, py: e.clientY, x: state.x, y: state.y };
      frame.classList.add('dragging');
      frame.setPointerCapture(e.pointerId);
    });
    frame.addEventListener('pointermove', function (e) {
      if (!drag) return;
      var r = frame.getBoundingClientRect();
      state.x = Math.max(0, Math.min(100, drag.x - (e.clientX - drag.px) / r.width * 100));
      state.y = Math.max(0, Math.min(100, drag.y - (e.clientY - drag.py) / r.height * 100));
      paint();
    });
    ['pointerup', 'pointercancel'].forEach(function (t) {
      frame.addEventListener(t, function () {
        if (!drag) return;
        drag = null;
        frame.classList.remove('dragging');
        persist();
      });
    });

    // фото, прописанное в разметке (лежит в photos/) — приоритетнее сохранённого
    var preset = fig.dataset.src;
    var saved = store[slot];
    if (preset) {
      state.x = saved && saved.x != null ? saved.x : 50;
      state.y = saved && saved.y != null ? saved.y : 50;
      state.zoom = saved && saved.zoom ? saved.zoom : 100;
      apply(preset, null);
    } else if (saved && saved.src) {
      state.x = saved.x; state.y = saved.y; state.zoom = saved.zoom || 100; state.name = saved.name || '';
      apply(saved.src, null);
    }
    paint();
  }

  document.addEventListener('paste', function (e) {
    if (!active || !e.clipboardData) return;
    var items = e.clipboardData.items || [];
    for (var i = 0; i < items.length; i++) {
      if (items[i].type && items[i].type.indexOf('image/') === 0) {
        active(items[i].getAsFile());
        e.preventDefault();
        return;
      }
    }
  });

  function counter() {
    var box = document.querySelector('.article');
    var out = document.querySelector('[data-count]');
    if (!box || !out) return;
    var clone = box.cloneNode(true);
    Array.prototype.forEach.call(clone.querySelectorAll('figure, .service'), function (n) { n.remove(); });
    var text = (clone.textContent || '').replace(/\s+/g, ' ').trim();
    out.innerHTML = 'Знаков: <b>' + text.length + '</b>';
  }

  document.addEventListener('DOMContentLoaded', function () {
    Array.prototype.forEach.call(document.querySelectorAll('figure.ph'), build);
    counter();
  });
})();
