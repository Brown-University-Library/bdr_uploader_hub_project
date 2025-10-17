/*
  Minimal helpers for keyword segmentation and replacement.
  Exposed as window.BDRKeywords.{ lastSegment, replaceLastSegment }.
*/
(function () {
  function normalizeSpaces(s) {
    return (s || '').replace(/\s+/g, ' ').trim();
  }

  function lastSegment(value) {
    if (typeof value !== 'string') return '';
    const raw = value;
    // Split on pipe and return the trimmed final segment
    const parts = raw.split('|');
    const last = parts[parts.length - 1];
    return (last || '').trim();
  }

  function replaceLastSegment(inputEl, text) {
    if (!inputEl) return;
    const value = inputEl.value || '';
    const parts = value.split('|');
    const trimmedText = (text || '').trim();

    if (parts.length <= 1) {
      inputEl.value = trimmedText;
    } else {
      const prefixParts = parts.slice(0, -1).map(function (p) { return normalizeSpaces(p); }).filter(Boolean);
      const prefix = prefixParts.join(' | ');
      inputEl.value = prefix ? (prefix + ' | ' + trimmedText) : trimmedText;
    }

    // Focus and move caret to end
    try {
      inputEl.focus();
      const len = inputEl.value.length;
      if (inputEl.setSelectionRange) {
        inputEl.setSelectionRange(len, len);
      }
    } catch (e) { /* ignore */ }

    // Trigger input event so htmx can react
    try {
      const ev = new Event('input', { bubbles: true });
      inputEl.dispatchEvent(ev);
    } catch (e) { /* ignore */ }
  }

  window.BDRKeywords = {
    lastSegment: lastSegment,
    replaceLastSegment: replaceLastSegment
  };
})();
