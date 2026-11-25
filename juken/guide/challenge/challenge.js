document.querySelectorAll('form[data-choice]').forEach(form => {
  const result = form.querySelector('[role="status"]');
  const answer = form.nextElementSibling;
  form.querySelector('button').hidden = false;
  form.addEventListener('submit', event => {
    event.preventDefault();
    const selected = new FormData(form).get('choice');
    if (selected === null) {
      result.textContent = '最初に使う方針を選んでください。';
      return;
    }
    result.textContent = selected === form.dataset.choice
      ? 'この問題に合う方針です。理由を確かめましょう。'
      : '別の方針が合います。問題文の手がかりを確認しましょう。';
    answer.open = true;
  });
});
