const printButton = document.querySelector('[data-print]');
const copyButton = document.querySelector('[data-copy]');
const guideLink = document.getElementById('guide-url');
const status = document.querySelector('.status');

printButton.hidden = false;
printButton.addEventListener('click', () => window.print());

copyButton.hidden = false;
copyButton.addEventListener('click', async () => {
  try {
    await navigator.clipboard.writeText(guideLink.href);
    status.textContent = 'ガイドのリンクをコピーしました。';
  } catch {
    const selection = window.getSelection();
    const range = document.createRange();
    range.selectNodeContents(guideLink);
    selection.removeAllRanges();
    selection.addRange(range);
    status.textContent = '表示中のURLを選択しました。端末のコピー機能でコピーしてください。';
  }
});
