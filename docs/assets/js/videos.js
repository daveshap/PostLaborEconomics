/* Post-Labor Economics: the Videos page player (progressive enhancement).
   Without JavaScript the player and every card link to YouTube. With it, a
   video plays on the page in YouTube's privacy-enhanced mode, and nothing
   loads from YouTube until a video is chosen. A click with a modifier key
   (or a middle click) still opens YouTube. */
(function () {
  var theater = document.querySelector('[data-theater]');
  if (!theater || !theater.replaceChildren || !theater.closest) return;
  var frame = theater.querySelector('[data-frame]');
  var label = theater.querySelector('[data-label]');
  var title = theater.querySelector('[data-title]');
  var meta = theater.querySelector('[data-meta]');
  var link = theater.querySelector('[data-link]');
  var list = theater.getAttribute('data-list') || '';
  var still = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)');

  function play(a) {
    var id = a.getAttribute('data-play') || '';
    if (!/^[A-Za-z0-9_-]{11}$/.test(id)) return false;
    var card = a.closest('.video-card');
    if (card) {
      var day = card.querySelector('.video-meta');
      var len = card.querySelector('[data-len]');
      title.textContent = card.querySelector('.video-link').textContent;
      meta.innerHTML = (day ? day.innerHTML : '') + (day && len ? ' <span aria-hidden="true">&middot;</span> ' : '') +
        (len ? '<span class="vh">Length </span>' + len.outerHTML : '');
      link.href = 'https://www.youtube.com/watch?v=' + id;
    }
    label.textContent = 'Now playing';
    document.querySelectorAll('.video-link[aria-current]').forEach(function (x) { x.removeAttribute('aria-current'); });
    var current = document.querySelector('.video-link[data-play="' + id + '"]');
    if (current) current.setAttribute('aria-current', 'true');
    var f = document.createElement('iframe');
    f.src = 'https://www.youtube-nocookie.com/embed/' + id + '?autoplay=1&rel=0&playsinline=1' +
      (list ? '&list=' + encodeURIComponent(list) : '');
    f.title = 'YouTube video player: ' + title.textContent;
    f.allow = 'autoplay; encrypted-media; picture-in-picture; fullscreen; web-share';
    f.allowFullscreen = true;
    f.referrerPolicy = 'strict-origin-when-cross-origin';
    frame.replaceChildren(f);
    if (card) theater.scrollIntoView({ behavior: still && still.matches ? 'auto' : 'smooth', block: 'start' });
    f.focus({ preventScroll: true });
    return true;
  }

  document.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('a[data-play]');
    if (!a || e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    if (play(a)) e.preventDefault();
  });
})();
