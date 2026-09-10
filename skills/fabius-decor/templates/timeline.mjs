// Original deterministic timeline: no timers, network calls, random values or autoplay.
export function stateAt(scenes, seconds, motion, reduced = false) {
  if (typeof seconds !== 'number' || !Number.isFinite(seconds)) throw new Error('Seek time must be a finite number');
  const total = scenes.reduce((sum, scene) => sum + scene.durationSeconds, 0);
  const time = Math.max(0, Math.min(total, seconds));
  let start = 0, index = 0;
  while (index < scenes.length - 1 && time >= start + scenes[index].durationSeconds) start += scenes[index++].durationSeconds;
  const elapsed = time - start;
  const progress = reduced || motion.durationMs === 0 ? 1 : Math.min(1, elapsed * 1000 / motion.durationMs);
  const ease = 1 - (1 - progress) ** 3;
  return { time, total, index, start, elapsed, opacity: 1, offset: (1 - ease) * motion.distancePx };
}
export function mount(board) {
  const scenes = [...document.querySelectorAll('[data-scene]')];
  const slider = document.querySelector('#time'), clock = document.querySelector('#time-label');
  const previous = document.querySelector('#previous'), next = document.querySelector('#next');
  const staticView = document.querySelector('#static'), status = document.querySelector('#status');
  const preference = matchMedia('(prefers-reduced-motion: reduce)');
  let current = 0, previousIndex = -1;
  const seek = seconds => {
    // Read the current preference when seeking; a retained MediaQueryList can
    // update later than a fresh query during browser preference emulation.
    const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches || staticView.checked;
    const state = stateAt(board.scenes, seconds, board.tokens.motion, reduced);
    current = state.time;
    scenes.forEach((element, index) => {
      element.hidden = index !== state.index;
      // All text remains opaque to preserve the measured token contrast.
      element.style.transform = `translateY(${state.offset}px)`;
    });
    slider.value = String(state.time); clock.textContent = `${state.time.toFixed(2)} / ${state.total.toFixed(2)} s`;
    slider.setAttribute('aria-valuetext', `${state.time.toFixed(2)} seconds, ${board.scenes[state.index].label}`);
    previous.disabled = state.index === 0; next.disabled = state.index === scenes.length - 1;
    if (state.index !== previousIndex) status.textContent = board.scenes[state.index].label;
    previousIndex = state.index;
    return { ...state, reducedMotion: reduced };
  };
  const boundary = index => board.scenes.slice(0, index).reduce((sum, scene) => sum + scene.durationSeconds, 0);
  slider.addEventListener('input', () => seek(Number(slider.value)));
  previous.addEventListener('click', () => seek(boundary(Math.max(0, previousIndex - 1))));
  next.addEventListener('click', () => seek(boundary(Math.min(scenes.length - 1, previousIndex + 1))));
  staticView.addEventListener('change', () => seek(current));
  preference.addEventListener('change', () => seek(current));
  document.querySelector('.transport').addEventListener('submit', event => event.preventDefault());
  window.__seek = seek;
  window.__storyboard = Object.freeze({ duration: board.scenes.reduce((sum, scene) => sum + scene.durationSeconds, 0), sceneCount: board.scenes.length });
  seek(0);
}
