document.querySelectorAll('.nl-btn-primary, .nl-btn-secondary').forEach(btn => {
  btn.addEventListener('click', () => {
    console.log(`Clicked: ${btn.textContent.trim()}`);
  });
});
