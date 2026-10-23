/* Post-Labor Economics: research library filter (progressive enhancement).
   Without JavaScript the filter box stays hidden and the full library shows.
   Matches report titles, theme names and hidden keywords (data-k), so "ubi"
   finds Universal Basic Income and "sigma" finds the σ title. Escape clears. */
(function () {
  var box = document.querySelector('[data-filter]');
  var lib = document.querySelector('[data-library]');
  if (!box || !lib || !('hidden' in box)) return;

  var input = box.querySelector('input');
  var status = box.querySelector('[role="status"]');
  var empty = lib.querySelector('[data-empty]');
  var overview = document.getElementById('themes');
  var themes = [].slice.call(lib.querySelectorAll('.theme'));
  var total = lib.querySelectorAll('[data-row]').length;

  function norm(s) {
    return (s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '')
      .replace(/[.‘’“”'"()]/g, '')
      .replace(/[\-‐-―\/:;,&]+/g, ' ')
      .replace(/\s+/g, ' ').trim();
  }

  themes.forEach(function (t) {
    var name = t.getAttribute('data-theme') || '';
    t._rows = [].slice.call(t.querySelectorAll('[data-row]')).map(function (li) {
      return { li: li, text: ' ' + norm(name + ' ' + li.textContent + ' ' + (li.getAttribute('data-k') || '')) + ' ' };
    });
    t._groups = [].slice.call(t.querySelectorAll('[data-group]'));
    t._count = t.querySelector('[data-count]');
  });

  function run() {
    var words = norm(input.value).split(' ').filter(Boolean);
    var shown = 0;
    themes.forEach(function (t) {
      var n = 0;
      t._rows.forEach(function (r) {
        var ok = words.every(function (w) { return r.text.indexOf(w) !== -1; });
        r.li.hidden = !ok;
        if (ok) n++;
      });
      t._groups.forEach(function (g) {
        g.hidden = !g.querySelector('[data-row]:not([hidden])');
      });
      t.hidden = n === 0;
      if (t._count) {
        var all = t._count.getAttribute('data-total');
        t._count.textContent = words.length ? n + ' of ' + all + ' reports' : all + ' reports';
      }
      shown += n;
    });
    if (overview) overview.hidden = words.length > 0;
    if (empty) empty.hidden = shown !== 0;
    status.textContent = !words.length ? '' :
      shown === 0 ? 'No reports match' :
      'Showing ' + shown + ' of ' + total + ' report' + (total === 1 ? '' : 's');
  }

  var timer;
  input.addEventListener('input', function () {
    clearTimeout(timer);
    timer = setTimeout(run, 120);
  });
  input.addEventListener('keydown', function (e) {
    if ((e.key === 'Escape' || e.key === 'Esc') && input.value) {
      e.preventDefault();
      input.value = '';
      clearTimeout(timer);
      run();
    }
  });
  box.hidden = false;
  if (input.value) run();
})();
