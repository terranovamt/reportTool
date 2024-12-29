document.getElementById('about-title').addEventListener('click', function () {
  this.classList.toggle('about-font');

  fetch('/click', { method: 'POST' })
    .then((response) => response.text())
    .then((data) => console.log(data))
    .catch((error) => console.error('Error:', error));
});
