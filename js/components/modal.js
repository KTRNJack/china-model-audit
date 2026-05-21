import { esc } from '../utils.js';

export function openRespModal(btn) {
  const full = btn.dataset.full;
  document.getElementById('resp-modal-title').textContent = btn.dataset.title;
  document.getElementById('resp-modal-chars').textContent = full.length.toLocaleString() + ' 字';
  document.getElementById('resp-modal-body').textContent  = full;
  document.getElementById('resp-modal').classList.add('open');
  document.body.classList.add('modal-open');
}

export function closeRespModal() {
  document.getElementById('resp-modal').classList.remove('open');
  document.body.classList.remove('modal-open');
}

export function initModal() {
  document.getElementById('resp-modal-close').addEventListener('click', closeRespModal);
  document.getElementById('resp-modal').addEventListener('click', e => {
    if (e.target === document.getElementById('resp-modal')) closeRespModal();
  });
  document.addEventListener('keydown', e => { if (e.key === 'Escape') closeRespModal(); });
  window.openRespModal = openRespModal;
}
