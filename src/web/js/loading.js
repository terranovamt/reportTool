function checkStatus() {
  fetch('/post.json')
    .then((response) => response.json())
    .then((data) => {
      // Check if all items have 'Run' set to '0'
      if (data.data.every((item) => item.Run === '0')) {
        window.location.href = '/';
      } else {
        setTimeout(checkStatus, 1000); // Check again after 1 second
      }
    })
    .catch((error) => console.error('Error:', error));
}

window.onload = function () {
  checkStatus();
};
