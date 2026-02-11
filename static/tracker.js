(function () {
  if (!window.ENABLE_TRACKING) return;

  const page = document.body.getAttribute('data-page') || 'unknown';

  function send(action, value = '') {
    fetch('/interaction', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ page, action, value })
    }).catch(() => {});
  }

  send('page_visited', window.location.pathname + window.location.search);

  document.addEventListener('click', (event) => {
    const target = event.target.closest('button, a');
    if (!target) return;
    const label = (target.textContent || target.getAttribute('href') || '').trim().slice(0, 80);
    send('click', label);
  });

  document.querySelectorAll('input[type="text"], input[type="email"], input[type="password"], textarea').forEach((input) => {
    let timer;
    input.addEventListener('input', () => {
      clearTimeout(timer);
      timer = setTimeout(() => send('typed', input.value.slice(0, 100)), 500);
    });
  });

  document.querySelectorAll('form').forEach((form) => {
    form.addEventListener('submit', () => {
      const values = [];
      form.querySelectorAll('input,textarea').forEach((el) => {
        if (el.name) values.push(`${el.name}:${(el.value || '').slice(0, 40)}`);
      });
      send('form_submit', values.join(';'));
    });
  });

  window.addEventListener('popstate', () => send('navigation', 'browser_navigation'));
})();
