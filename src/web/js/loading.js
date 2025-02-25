function checkStatus() {
  fetch('/post.json')
    .then((response) => response.json())
    .then((data) => {
      // Check if all items have 'Run' set to '0'
      if (data.data.every((item) => item.Run === '0')) {
        window.location.href = '/';
      } else {
        fetchLogData();
        setTimeout(checkStatus, 1000); // Check again after 1 second
      }
    })
    .catch((error) => console.error('Error:', error));
}

function fetchLogData() {
  fetch('/log')
    .then((response) => response.text())
    .then((data) => {
      const logContainer = document.getElementById('log-container');
      logContainer.innerHTML = '';
      const lines = data.split('\n');
      if (lines.length > 0 && lines[0].trim() !== '') {
        const logEntry = document.createElement('div');
        logEntry.className = 'log-entry';
        const line = lines[0];
        const Match = line.match(/\[(.*?)\]/)[1];
        const [dateMatch, timeMatch] = Match.split(' ');
        const durationMatch = line.match(/\((.*?)\)/)[1];
        const messageMatch = line.split(' |--> ')[1];

        const date = dateMatch ? dateMatch : '';
        const [aa, mm, dd] = date.split('-');
        const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        const month = monthNames[parseInt(mm) - 1];
        const time = timeMatch ? timeMatch : '';
        const [hh, min, sec] = time.split(':');
        const message = messageMatch ? messageMatch : '';

        // Start the timer to update elapsed time
        const logTime = new Date(`${aa}-${mm}-${dd}T${hh}:${min}:${sec}`);
        const duration = updateElapsedTime(logTime);

        logEntry.innerHTML = `<!--digital clock start-->
    <div class="datetime">
      <div class="date-time">
        <div class="date">
          <span id="daynum">${dd}</span>
          <span id="month">${month}</span>
          <span id="year">${aa}</span>
          </div>
          <div class="time">
          <span id="hour">${hh}</span>:
          <span id="minutes">${min}</span>:
          <span id="seconds">${sec}</span>
          <span id="duration">${duration}</span>
        </div>
      </div>
      <div style="width: 40px;">
      </div>
      <div class="message">
        <span id="message">${message}</span>
      </div>
      <div class="elapsed-time">
        <span id="elapsed-time"></span>
      </div>
    </div>
    <!--digital clock end-->`;
        logContainer.appendChild(logEntry);
      }
    })
    .catch((error) => console.error('Error:', error));
}

function updateElapsedTime(logTime) {
  const now = new Date();
  const elapsed = now - logTime;

  const seconds = Math.floor((elapsed / 1000) % 60);
  const minutes = Math.floor((elapsed / (1000 * 60)) % 60);
  const hours = Math.floor((elapsed / (1000 * 60 * 60)) % 24);
  const days = Math.floor(elapsed / (1000 * 60 * 60 * 24));

  // const elapsedTimeString = `(+${days}d ${hours}h ${minutes}m ${seconds}s)`;
  const elapsedTimeString = `(+${hours}h ${minutes}m ${seconds}s)`;
  return elapsedTimeString;

  // update();
  // setInterval(update, 1000);
}

window.onload = function () {
  checkStatus();
  fetchLogData();
};
