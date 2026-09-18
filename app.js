'use strict';

const $ = selector => document.querySelector(selector);
const state = {
  screen: 'home', lesson: null, deckId: null, page: 1, tutorOpen: false, zoom: 100,
  selectedText: '', selectionSource: null, selectedMessage: null,
  selectionDeckId: null, selectionPage: null,
  pending: null, chatPending: null, textLayerRequest: 0, textItems: [], slideDimensions: null,
  chatHistory: [], conversationGeneration: 0,
};
const HISTORY_MAX_MESSAGES = 8;
const HISTORY_MAX_CHARS = 8000;
let courseData = null;
let selectionTimer = null;

const esc = value => String(value ?? '').replace(/[&<>"']/g, character => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
}[character]));
const lessonByDeck = deckId => (courseData?.lessons || []).find(item => item.deck_id === deckId);
const on = (selector, event, handler) => {
  const element = $(selector);
  if (element) element.addEventListener(event, handler);
};

window.__vlearnEarly = true;

function showHome() {
  resetChat({render: false});
  state.screen = 'home';
  state.tutorOpen = false;
  $('#home-nav').hidden = false;
  $('#home-screen').hidden = false;
  $('#lesson-screen').hidden = true;
  $('#tutor').hidden = true;
  clearSelection();
}

function renderSessions() {
  const items = [
    ['Buổi 1: Day01', 'day01'], ['Buổi 2: DAY02', 'day02'],
    ['Buổi 3: DAY03', null], ['Buổi 4: DAY04', null],
    ['Buổi 5: DAY05', null], ['Buổi 6: DAY06', null],
  ];
  $('#session-list').innerHTML = items.map(([name, id], index) => id
    ? `<a class="session available" href="?lesson=${id}" data-session="${id}"><span class="radio">▶</span><strong>${name}</strong><small>${index === 0 ? 'ĐANG HỌC' : 'SẴN SÀNG'}</small></a>`
    : `<button class="session unavailable" disabled><span class="radio">○</span><strong>${name}</strong><small>Chưa có data demo</small></button>`).join('');
}

async function loadCourse() {
  try {
    const response = await fetch('/api/course-data');
    courseData = await response.json();
  } catch {
    courseData = {lessons: [
      {id: 'day01', title: 'Day01 · AI & LLM Foundation', deck_id: 'd1', pages: 29},
      {id: 'day02', title: 'Day02 · Xác định bài toán cho AI', deck_id: 'd2', pages: 29},
    ]};
  }
  renderSessions();
}

function openLesson(id, page = 1) {
  const lesson = (courseData?.lessons || []).find(item => item.id === id);
  if (!lesson) return;
  const continuingConversation = state.screen === 'lesson';
  const tutorWasOpen = state.tutorOpen;
  if (!continuingConversation) resetChat({render: false});
  state.screen = 'lesson';
  state.lesson = lesson;
  state.deckId = lesson.deck_id;
  state.page = page;
  state.tutorOpen = continuingConversation && tutorWasOpen;
  state.zoom = 100;
  $('#slide-page').style.transform = 'scale(1)';
  $('#zoom-label').textContent = '100%';
  $('#home-nav').hidden = true;
  $('#home-screen').hidden = true;
  $('#lesson-screen').hidden = false;
  $('#tutor').hidden = !state.tutorOpen;
  if (!continuingConversation) $('#conversation').replaceChildren();
  $('#lesson-heading').textContent = `Bài ${id === 'day01' ? '1' : '2'} · ${id.toUpperCase()}`;
  renderSlideItems();
  loadSlide();
}

function renderSlideItems() {
  $('#slide-items').innerHTML = (courseData?.lessons || []).map(lesson =>
    `<button class="lesson-item ${lesson.id === state.lesson.id ? 'active' : ''}" data-lesson="${lesson.id}"><span class="slide-icon">▱</span><span>${esc(lesson.title)}</span>${lesson.id === state.lesson.id ? '<b>Đang học</b>' : ''}</button>`).join('');
  document.querySelectorAll('[data-lesson]').forEach(button => {
    button.onclick = () => openLesson(button.dataset.lesson);
  });
}

function fitSlidePage() {
  if (!state.slideDimensions) return;
  const frame = $('.slide-frame');
  const page = $('#slide-page');
  const frameRatio = frame.clientWidth / frame.clientHeight;
  const pageRatio = state.slideDimensions.width / state.slideDimensions.height;
  if (frameRatio > pageRatio) {
    page.style.height = '100%';
    page.style.width = `${pageRatio / frameRatio * 100}%`;
  } else {
    page.style.width = '100%';
    page.style.height = `${frameRatio / pageRatio * 100}%`;
  }
  layoutTextLayer();
}

function layoutTextLayer() {
  const layer = $('#slide-text-layer');
  const width = layer.clientWidth;
  const height = layer.clientHeight;
  layer.querySelectorAll('span').forEach(span => {
    const item = span.dataset;
    const boxHeight = Number(item.height) * height;
    const targetWidth = Number(item.width) * width;
    span.style.left = `${Number(item.x) * width}px`;
    span.style.top = `${Number(item.y) * height}px`;
    span.style.height = `${boxHeight}px`;
    span.style.fontSize = `${Math.max(4, boxHeight * 0.82)}px`;
    span.style.lineHeight = `${boxHeight}px`;
    span.style.transform = 'none';
    const naturalWidth = span.scrollWidth;
    span.style.transform = `scaleX(${naturalWidth > 0 ? targetWidth / naturalWidth : 1})`;
  });
}

function renderTextLayer(data) {
  const layer = $('#slide-text-layer');
  layer.replaceChildren();
  state.slideDimensions = {width: data.width, height: data.height};
  const lines = new Map();
  (data.items || []).forEach((word, index) => {
    const key = Number.isInteger(word.block) && Number.isInteger(word.line)
      ? `${word.block}:${word.line}` : `word:${index}`;
    const existing = lines.get(key) || {words: [], x0: 1, y0: 1, x1: 0, y1: 0};
    existing.words.push(word);
    existing.x0 = Math.min(existing.x0, word.x);
    existing.y0 = Math.min(existing.y0, word.y);
    existing.x1 = Math.max(existing.x1, word.x + word.w);
    existing.y1 = Math.max(existing.y1, word.y + word.h);
    lines.set(key, existing);
  });
  state.textItems = [...lines.values()].map(line => ({
    text: line.words.sort((a, b) => (a.word ?? 0) - (b.word ?? 0)).map(word => word.text).join(' '),
    x: line.x0, y: line.y0, w: line.x1 - line.x0, h: line.y1 - line.y0,
  }));
  const fragment = document.createDocumentFragment();
  state.textItems.forEach(item => {
    const span = document.createElement('span');
    span.textContent = item.text;
    span.dataset.x = item.x;
    span.dataset.y = item.y;
    span.dataset.width = item.w;
    span.dataset.height = item.h;
    fragment.append(span);
  });
  layer.append(fragment);
  fitSlidePage();
}

async function loadTextLayer(requestId) {
  try {
    const response = await fetch(`/api/slide-text-layer?deck_id=${encodeURIComponent(state.deckId)}&page=${state.page}`);
    const data = await response.json();
    if (!response.ok) throw Error(data.message || 'Không tải được lớp văn bản.');
    if (requestId === state.textLayerRequest) renderTextLayer(data);
  } catch {
    if (requestId === state.textLayerRequest) $('#slide-text-layer').replaceChildren();
  }
}

function loadSlide() {
  clearSelection();
  const total = state.lesson.pages;
  state.page = Math.max(1, Math.min(total, state.page));
  const image = $('#slide-image');
  const requestId = ++state.textLayerRequest;
  state.textItems = [];
  state.slideDimensions = null;
  $('#slide-text-layer').replaceChildren();
  $('#slide-loading').textContent = 'Đang tải slide…';
  $('#slide-loading').hidden = false;
  image.hidden = true;
  image.src = `/api/slide-image?deck_id=${encodeURIComponent(state.deckId)}&page=${state.page}`;
  image.onload = () => {
    if (requestId !== state.textLayerRequest) return;
    $('#slide-loading').hidden = true;
    image.hidden = false;
  };
  image.onerror = () => {
    if (requestId === state.textLayerRequest) $('#slide-loading').textContent = 'Không tải được slide.';
  };
  loadTextLayer(requestId);
  $('#slide-number').textContent = state.page;
  $('#slide-total').textContent = total;
  $('#prev-slide').disabled = state.page <= 1;
  $('#next-slide').disabled = state.page >= total;
  $('#lecturer-note').textContent = `Trang ${state.page} · ${state.lesson.title}`;
  document.title = `${state.lesson.title} · Trang ${state.page}`;
  const context = $('.context-label');
  if (context) context.textContent = `Đang mở: ${state.lesson.title} · trang ${state.page}`;
}

function changePage(delta) {
  state.page = Math.max(1, Math.min(state.lesson.pages, state.page + delta));
  loadSlide();
}

function initialChat() {
  if (!state.tutorOpen || state.chatPending || state.pending) return;
  $('#conversation').innerHTML = `<p class="context-label">Đang mở: ${esc(state.lesson?.title || '')} · trang ${state.page}</p><div class="message assistant"><div class="message-label">✦ Trợ giảng AI</div><p>Xin chào DŨNG! Mình có thể giải thích nội dung các slide đang mở.</p><p class="selection-hint">Hãy đặt câu hỏi về bài học để bắt đầu.</p></div>`;
  scrollChat();
}

function openTutor({focus = true} = {}) {
  state.tutorOpen = true;
  $('#tutor').hidden = false;
  if (!$('#conversation').children.length) initialChat();
  if (focus) $('#chat-input').focus();
}

function closeTutor() {
  state.tutorOpen = false;
  $('#tutor').hidden = true;
  hideAction();
}

function scrollChat() {
  requestAnimationFrame(() => {
    const conversation = $('#conversation');
    conversation.scrollTop = conversation.scrollHeight;
  });
}

function rememberChatMessage(role, content) {
  if (!['user', 'assistant'].includes(role) || typeof content !== 'string' || !content.trim()) return;
  state.chatHistory.push({role, content: content.trim()});
}

function getRecentChatHistory() {
  // Model context is capped at the newest 8 messages and 8,000 characters.
  const recent = [];
  let characters = 0;
  for (let index = state.chatHistory.length - 1; index >= 0 && recent.length < HISTORY_MAX_MESSAGES; index -= 1) {
    const item = state.chatHistory[index];
    if (!['user', 'assistant'].includes(item?.role) || typeof item.content !== 'string') continue;
    const content = item.content.trim();
    if (!content || characters + content.length > HISTORY_MAX_CHARS) break;
    recent.push({role: item.role, content});
    characters += content.length;
  }
  return recent.reverse();
}

function resetChat({render = true} = {}) {
  state.conversationGeneration += 1;
  state.chatPending?.abort();
  state.pending?.abort();
  state.chatPending = null;
  state.pending = null;
  state.chatHistory = [];
  const input = $('#chat-input');
  if (input) input.value = '';
  const conversation = $('#conversation');
  if (conversation) conversation.replaceChildren();
  const send = $('#send-message');
  if (send) send.disabled = true;
  hideAction();
  if (render && state.tutorOpen) initialChat();
}

function appendMessage(text, type = 'assistant', options = {}) {
  const node = document.createElement('div');
  node.className = `message ${type}`;
  if (type === 'assistant') {
    const label = document.createElement('div');
    label.className = 'message-label';
    label.textContent = '✦ Trợ giảng AI';
    node.append(label);
    if (options.originalQuestion) node.dataset.originalQuestion = options.originalQuestion;
  }
  const paragraph = document.createElement('p');
  paragraph.className = 'answer-text';
  paragraph.textContent = text;
  node.append(paragraph);
  $('#conversation').append(node);
  scrollChat();
  return node;
}

function appendSelectionRequest(selectedText) {
  const node = document.createElement('div');
  node.className = 'message user selection-request';
  const label = document.createElement('p');
  label.className = 'selection-request-label';
  label.textContent = 'Giải thích đoạn này:';
  const quote = document.createElement('blockquote');
  quote.className = 'selected-quote';
  const excerpt = selectedText.length > 320 ? `${selectedText.slice(0, 317)}…` : selectedText;
  quote.textContent = `“${excerpt}”`;
  node.append(label, quote);
  $('#conversation').append(node);
  scrollChat();
  return node;
}

function visibleAssistantText(data, selection = false) {
  const fields = selection
    ? {explain: 'explanation', clarify: 'question', no_grounding: 'message', refuse: 'message'}
    : {answer: 'answer', clarify: 'question', no_grounding: 'message', refuse: 'message'};
  const field = fields[data?.action];
  return field && typeof data[field] === 'string' ? data[field].trim() : '';
}

function renderClarifyOptions(messageNode, options) {
  if (!Array.isArray(options) || options.length < 2 || options.length > 4) return;
  const values = options.filter(option => typeof option === 'string' && option.trim()).map(option => option.trim());
  if (values.length < 2) return;
  const group = document.createElement('div');
  group.className = 'clarify-options';
  group.setAttribute('aria-label', 'Các lựa chọn làm rõ');
  values.forEach(value => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'clarify-option';
    button.textContent = value;
    button.addEventListener('click', () => {
      if (group.dataset.resolved === 'true' || state.chatPending || state.pending) return;
      group.dataset.resolved = 'true';
      group.classList.add('resolved');
      group.querySelectorAll('button').forEach(option => { option.disabled = true; });
      sendChatQuestion(value);
    });
    group.append(button);
  });
  messageNode.append(group);
  scrollChat();
}

function closeSearch() {
  $('#search-results').hidden = true;
  $('#lesson-list').hidden = false;
}

async function searchSlides(query) {
  $('#lesson-list').hidden = true;
  $('#search-results').hidden = false;
  $('#search-results').innerHTML = '<p class="empty-state">Đang tìm trong slide thật…</p>';
  try {
    const response = await fetch('/api/search', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({query})});
    const data = await response.json();
    if (!response.ok) throw Error(data.message || 'Không tìm được slide.');
    const results = data.results || [];
    $('#search-results').innerHTML = `<div class="results-heading"><span>${results.length} kết quả · ${esc(data.mode)}</span><button id="close-search">Đóng ×</button></div>` + (results.length
      ? results.map((item, index) => `<article class="result-card"><h3>${esc(item.lesson)}</h3><span class="slide-ref">Trang ${item.page} · điểm ${item.score}</span><p>${esc(item.snippet)}</p><button data-result="${index}">Mở slide ↗</button></article>`).join('')
      : '<p class="empty-state">Chưa tìm thấy slide phù hợp. Thử từ khóa khác.</p>');
    $('#close-search').onclick = closeSearch;
    document.querySelectorAll('[data-result]').forEach(button => {
      button.onclick = () => openSearchResult(results[Number(button.dataset.result)]);
    });
  } catch (error) {
    $('#search-results').innerHTML = `<p class="empty-state">${esc(error.message)}</p>`;
  }
}

function openSearchResult(result) {
  const lesson = lessonByDeck(result.deck_id);
  if (!lesson) return;
  closeSearch();
  openLesson(lesson.id, result.page);
}

function hideAction() {
  $('#explain-selection').hidden = true;
  state.selectedText = '';
  state.selectionSource = null;
  state.selectedMessage = null;
  state.selectionDeckId = null;
  state.selectionPage = null;
}

function clearSelection() {
  hideAction();
  const selection = window.getSelection();
  if (selection) selection.removeAllRanges();
}

function selectionElement(node) {
  return node?.nodeType === Node.ELEMENT_NODE ? node : node?.parentElement;
}

function selectedSlideText(range, layer) {
  // Selection.toString() concatenates adjacent absolutely-positioned spans.
  // Reconstruct the visible phrase from intersected line spans with spaces.
  const pieces = [...layer.querySelectorAll('span')].filter(span => range.intersectsNode(span)).map(span => {
    const text = span.textContent || '';
    let start = 0;
    let end = text.length;
    if (span.contains(range.startContainer)) start = range.startOffset;
    if (span.contains(range.endContainer)) end = range.endOffset;
    return text.slice(Math.max(0, start), Math.max(start, end));
  }).filter(Boolean);
  return pieces.join(' ').replace(/\s+/g, ' ').trim();
}

function inspectSelection() {
  const selection = window.getSelection();
  if (!selection || selection.isCollapsed || !selection.rangeCount || state.pending) return hideAction();
  const range = selection.getRangeAt(0);
  const start = selectionElement(range.startContainer);
  const end = selectionElement(range.endContainer);
  const startMessage = start?.closest('.message.assistant');
  const endMessage = end?.closest('.message.assistant');
  const layer = $('#slide-text-layer');
  let source = null;
  let message = null;
  if (startMessage && startMessage === endMessage) {
    source = 'tutor';
    message = startMessage;
  } else if (layer.contains(start) && layer.contains(end)) {
    source = 'slide';
  } else {
    return hideAction();
  }
  const selectedText = (source === 'slide' ? selectedSlideText(range, layer) : selection.toString())
    .replace(/\s+/g, ' ').trim();
  if (selectedText.length < 2 || selectedText.length > 2000) return hideAction();
  state.selectedText = selectedText;
  state.selectionSource = source;
  state.selectedMessage = message;
  state.selectionDeckId = state.deckId;
  state.selectionPage = state.page;
  const action = $('#explain-selection');
  const rect = range.getBoundingClientRect();
  action.hidden = false;
  const width = action.offsetWidth || 170;
  const height = action.offsetHeight || 42;
  action.style.left = `${Math.max(8, Math.min(window.innerWidth - width - 8, rect.left))}px`;
  action.style.top = `${Math.max(8, rect.top - height - 8)}px`;
}

async function explainSelection() {
  if (!state.selectedText || !state.selectionSource || state.pending || state.chatPending || !state.lesson) return;
  if (state.selectionDeckId !== state.deckId || state.selectionPage !== state.page) return hideAction();
  const selectedText = state.selectedText;
  const source = state.selectionSource;
  const selectedMessage = state.selectedMessage;
  const selectedDeckId = state.selectionDeckId;
  const selectedPage = state.selectionPage;
  const originalAnswer = source === 'tutor' ? (selectedMessage?.querySelector('.answer-text')?.textContent || '') : '';
  const originalQuestion = source === 'tutor' ? (selectedMessage?.dataset.originalQuestion || '') : '';
  if (source === 'tutor' && !originalAnswer.includes(selectedText)) return hideAction();

  clearSelection();
  if (!state.tutorOpen) openTutor({focus: false});
  const previousHistory = getRecentChatHistory();
  const semanticRequest = `Giải thích đoạn này: “${selectedText}”`;
  appendSelectionRequest(selectedText);
  rememberChatMessage('user', semanticRequest);
  const pending = appendMessage('Đang giải thích đoạn bạn chọn…', 'assistant', {originalQuestion: semanticRequest});
  pending.setAttribute('aria-busy', 'true');
  const controller = new AbortController();
  state.pending = controller;
  const generation = state.conversationGeneration;
  try {
    const request = {
      source, deck_id: selectedDeckId, page: selectedPage, selected_text: selectedText,
      history: previousHistory, current_request: semanticRequest,
    };
    if (source === 'tutor') {
      request.original_question = originalQuestion;
      request.original_answer = originalAnswer;
    }
    const response = await fetch('/api/explain-selection', {
      method: 'POST', headers: {'Content-Type': 'application/json'}, signal: controller.signal,
      body: JSON.stringify(request),
    });
    const data = await response.json();
    if (generation !== state.conversationGeneration) return;
    if (!response.ok) {
      throw Error(response.status >= 500
        ? 'Trợ giảng AI đang tạm thời không phản hồi. Hãy thử lại.'
        : (data.message || 'Không thể giải thích đoạn đã chọn.'));
    }
    const answer = visibleAssistantText(data, true);
    if (!answer) throw Error('Phản hồi AI không hợp lệ.');
    pending.querySelector('.answer-text').textContent = answer;
    rememberChatMessage('assistant', answer);
    if (data.action === 'clarify') renderClarifyOptions(pending, data.clarify_options);
  } catch (error) {
    if (generation !== state.conversationGeneration) return;
    pending.querySelector('.answer-text').textContent = error.name === 'AbortError'
      ? 'Yêu cầu đã bị hủy.'
      : (error.message || 'Trợ giảng AI đang tạm thời không phản hồi. Hãy thử lại.');
  } finally {
    if (generation !== state.conversationGeneration) return;
    pending.removeAttribute('aria-busy');
    if (state.pending === controller) state.pending = null;
    scrollChat();
  }
}

async function sendChatQuestion(question) {
  question = String(question || '').trim();
  if (!question || state.chatPending || state.pending || !state.lesson) return;
  const previousHistory = getRecentChatHistory();
  appendMessage(question, 'user');
  rememberChatMessage('user', question);
  const input = $('#chat-input');
  input.value = '';
  $('#send-message').disabled = true;
  const pending = appendMessage('Đang suy nghĩ…', 'assistant', {originalQuestion: question});
  pending.setAttribute('aria-busy', 'true');
  const controller = new AbortController();
  state.chatPending = controller;
  const generation = state.conversationGeneration;
  const timeout = setTimeout(() => controller.abort(), 60000);
  try {
    const response = await fetch('/api/chat', {
      method: 'POST', headers: {'Content-Type': 'application/json'}, signal: controller.signal,
      body: JSON.stringify({deck_id: state.deckId, page: state.page, question, history: previousHistory}),
    });
    const data = await response.json();
    if (generation !== state.conversationGeneration) return;
    if (!response.ok) throw Error(data.message || 'Không gọi được AI. Hãy thử lại.');
    const answer = visibleAssistantText(data);
    if (!answer) throw Error('Phản hồi AI không hợp lệ.');
    pending.querySelector('.answer-text').textContent = answer;
    rememberChatMessage('assistant', answer);
    if (data.action === 'clarify') renderClarifyOptions(pending, data.clarify_options);
  } catch (error) {
    if (generation !== state.conversationGeneration) return;
    pending.querySelector('.answer-text').textContent = error.name === 'AbortError' ? 'Yêu cầu đã hết thời gian. Hãy thử lại.' : (error.message || 'Không gọi được AI. Hãy thử lại.');
  } finally {
    clearTimeout(timeout);
    if (generation !== state.conversationGeneration) return;
    pending.removeAttribute('aria-busy');
    if (state.chatPending === controller) state.chatPending = null;
    $('#send-message').disabled = !input.value.trim();
    scrollChat();
  }
}

function submitChat(event) {
  event.preventDefault();
  sendChatQuestion($('#chat-input').value);
}

on('#home-brand', 'click', event => { event.preventDefault(); showHome(); });
on('#back-home', 'click', showHome);
on('#ask-ai', 'click', () => openTutor());
on('#close-tutor', 'click', closeTutor);
on('#prev-slide', 'click', () => changePage(-1));
on('#next-slide', 'click', () => changePage(1));
on('#zoom-out', 'click', () => {
  state.zoom = Math.max(75, state.zoom - 10);
  $('#zoom-label').textContent = `${state.zoom}%`;
  $('#slide-page').style.transform = `scale(${state.zoom / 100})`;
});
on('#zoom-in', 'click', () => {
  state.zoom = Math.min(150, state.zoom + 10);
  $('#zoom-label').textContent = `${state.zoom}%`;
  $('#slide-page').style.transform = `scale(${state.zoom / 100})`;
});
const toggleNotes = () => { $('#personal-note').hidden = !$('#personal-note').hidden; };
on('#note-button', 'click', toggleNotes);
on('#notebook', 'click', toggleNotes);
on('#slides-toggle', 'click', () => { $('#slide-items').hidden = !$('#slide-items').hidden; });
on('#search-form', 'submit', event => {
  event.preventDefault();
  const query = $('#search-input').value.trim();
  if (query) searchSlides(query);
});
on('#search-input', 'input', () => { if (!$('#search-input').value.trim()) closeSearch(); });
on('#explain-selection', 'mousedown', event => event.preventDefault());
on('#explain-selection', 'click', explainSelection);
on('#conversation', 'mouseup', () => setTimeout(inspectSelection, 0));
on('#conversation', 'keyup', inspectSelection);
on('#slide-text-layer', 'mouseup', () => setTimeout(inspectSelection, 0));
on('#slide-text-layer', 'keyup', inspectSelection);
on('#chat-input', 'input', event => {
  $('#send-message').disabled = !event.target.value.trim() || Boolean(state.chatPending || state.pending);
});
on('#chat-input', 'keydown', event => {
  if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
    event.preventDefault();
    if (!state.chatPending && !state.pending && event.currentTarget.value.trim()) $('#chat-form').requestSubmit();
  }
});
on('#chat-form', 'submit', submitChat);
on('#new-chat', 'click', () => resetChat());

document.addEventListener('mousedown', event => {
  if (!event.target.closest?.('#explain-selection')) hideAction();
});
document.addEventListener('selectionchange', () => {
  clearTimeout(selectionTimer);
  selectionTimer = setTimeout(inspectSelection, 120);
});
document.addEventListener('click', event => {
  const session = event.target.closest?.('[data-session]');
  if (session && !session.disabled) {
    event.preventDefault();
    openLesson(session.dataset.session);
    return;
  }
  if (event.target.closest?.('#enter-course')) openLesson('day01');
}, true);

new ResizeObserver(fitSlidePage).observe($('.slide-frame'));
window.__vlearnWired = true;
loadCourse().then(() => {
  const lesson = new URLSearchParams(location.search).get('lesson');
  if (lesson) openLesson(lesson);
  else showHome();
});
