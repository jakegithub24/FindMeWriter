/**
 * FindMeWriter Accessibility and Theme Management
 */
(function () {
  // Constants
  const THEME_KEY = 'fmw-theme'; // 'default' or 'high-contrast'
  const SIZE_KEY = 'fmw-size'; // 'default' or 'large-text'

  // Apply saved preferences immediately to prevent flash
  const savedTheme = localStorage.getItem(THEME_KEY) || 'default';
  const savedSize = localStorage.getItem(SIZE_KEY) || 'default';

  if (savedTheme === 'high-contrast') {
    document.documentElement.setAttribute('data-theme', 'high-contrast');
  }
  if (savedSize === 'large-text') {
    document.documentElement.setAttribute('data-size', 'large-text');
  }

  // Once DOM is fully loaded, set up toggle buttons and event listeners
  document.addEventListener('DOMContentLoaded', () => {
    const contrastBtn = document.getElementById('toggle-contrast');
    const sizeBtn = document.getElementById('toggle-size');

    // Initialize button states
    if (contrastBtn) {
      const isHighContrast = document.documentElement.getAttribute('data-theme') === 'high-contrast';
      contrastBtn.setAttribute('aria-pressed', isHighContrast ? 'true' : 'false');
      if (isHighContrast) {
        contrastBtn.classList.add('active');
      }

      contrastBtn.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        if (currentTheme === 'high-contrast') {
          document.documentElement.removeAttribute('data-theme');
          localStorage.setItem(THEME_KEY, 'default');
          contrastBtn.setAttribute('aria-pressed', 'false');
          contrastBtn.classList.remove('active');
        } else {
          document.documentElement.setAttribute('data-theme', 'high-contrast');
          localStorage.setItem(THEME_KEY, 'high-contrast');
          contrastBtn.setAttribute('aria-pressed', 'true');
          contrastBtn.classList.add('active');
        }
      });
    }

    if (sizeBtn) {
      const isLargeText = document.documentElement.getAttribute('data-size') === 'large-text';
      sizeBtn.setAttribute('aria-pressed', isLargeText ? 'true' : 'false');
      if (isLargeText) {
        sizeBtn.classList.add('active');
      }

      sizeBtn.addEventListener('click', () => {
        const currentSize = document.documentElement.getAttribute('data-size');
        if (currentSize === 'large-text') {
          document.documentElement.removeAttribute('data-size');
          localStorage.setItem(SIZE_KEY, 'default');
          sizeBtn.setAttribute('aria-pressed', 'false');
          sizeBtn.classList.remove('active');
        } else {
          document.documentElement.setAttribute('data-size', 'large-text');
          localStorage.setItem(SIZE_KEY, 'large-text');
          sizeBtn.setAttribute('aria-pressed', 'true');
          sizeBtn.classList.add('active');
        }
      });
    }
  });
})();
