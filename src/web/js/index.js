document.addEventListener('DOMContentLoaded', function () {
  // Get references to the DOM elements
  const authorTable = document.getElementById('authorTable').getElementsByTagName('tbody')[0];
  const dataTable = document.getElementById('dataTable').getElementsByTagName('tbody')[0];
  const submitForm = document.getElementById('submitForm');
  const authorFields = ['Author', 'Mail', 'Site', 'Group'];
  let dataFields = [];

  // Load existing data from JSON file
  fetch('post.json')
    .then((response) => {
      if (!response.ok) {
        throw new Error('Network response was not ok ' + response.statusText);
      }
      return response.json();
    })
    .then((jsonData) => {
      const authorInfo = jsonData.authorInfo;
      const data = jsonData.data;

      // Determine data fields from the JSON data
      if (data.length > 0) {
        dataFields = Object.keys(data[0]).filter((field) => !authorFields.includes(field));
      }
      // console.log('Fields detected from JSON:', dataFields); // Debug log
      // console.log('Data loaded from JSON:', data); // Debug log

      // Create table headers dynamically
      createTableHeaders(authorFields, 'authorTable');
      createTableHeaders(dataFields, 'dataTable');

      // Add author info to the table
      addRow(authorInfo, authorFields, authorTable, true);

      // Add data rows to the table
      data.forEach((rowData) => {
        addRow(rowData, dataFields, dataTable, true);
      });
      addEmptyRow(dataFields, dataTable);
    })
    .catch((error) => {
      console.error('Error loading data:', error);
    });

  // Handle form submission
  submitForm.addEventListener('submit', function (event) {
    event.preventDefault();
    const authorRow = authorTable.getElementsByTagName('tr')[0];
    const dataRows = dataTable.getElementsByTagName('tr');
    const authorData = {};
    const data = [];

    // Collect and validate author data
    let allAuthorFieldsFilled = true;
    authorFields.forEach((field, j) => {
      const cell = authorRow.getElementsByTagName('td')[j];
      const value = cell ? cell.innerText.trim() : '';
      if (!value) {
        allAuthorFieldsFilled = false;
      }
      authorData[field] = value;
    });

    if (!allAuthorFieldsFilled) {
      alert('Please fill all author fields.');
      return;
    }

    // Collect and validate data rows
    for (let i = 0; i < dataRows.length; i++) {
      const cells = dataRows[i].getElementsByTagName('td');
      const rowData = {};
      let allFieldsFilled = true;

      dataFields.forEach((field, j) => {
        const cell = cells[j];
        if (field === 'Run') {
          const checkbox = cell.querySelector('.yep');
          rowData[field] = checkbox && checkbox.checked ? '1' : '0';
        } else if (field === 'File') {
          const filePath = cell ? cell.dataset.filePath : '{}';
          rowData[field] = filePath ? JSON.parse(filePath) : {};
        } else {
          const value = cell ? cell.innerText.trim() : '';
          if (!value) {
            allFieldsFilled = false;
          }
          rowData[field] = value;
        }
      });

      if (allFieldsFilled) {
        data.push(rowData);
      }
    }

    if (data.length === 0) {
      alert('Please fill all data fields.');
      return;
    }

    // Check if at least one item has 'Run' set to '1'
    const hasRun = data.some((item) => item.Run === '1');
    if (!hasRun) {
      alert('Set at least one item with Run set to 1');
      return;
    }

    // Validate File paths only for rows with 'Run' set to '1'
    for (let i = 0; i < data.length; i++) {
      const rowData = data[i];
      if (rowData.Run === '1') {
        const wafers = rowData.Wafer === 'All' ? ['All'] : rowData.Wafer === '-' ? ['-'] : rowData.Wafer.split(', ').map(Number);
        const filePaths = rowData.File;
        console.log(filePaths);
        for (const wafer of wafers) {
          const filePath = filePaths[wafer];
          if (!filePath || !filePath.path || filePath.path.trim() === '' || !filePath.corner || filePath.corner.trim() === '') {
            alert(`Please specify a valid File path and corner for wafer ${wafer} in row ${i + 1}.`);
            return;
          }
        }
      }
    }

    // Redirect to loading page immediately after form submission
    window.location.href = '/loading';

    console.log('Data to be submitted:', { authorInfo: authorData, data: data }); // Debug log

    // Submit the form data to the server
    fetch('/submit', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({ data: JSON.stringify({ authorInfo: authorData, data: data }) }),
    })
      .then((response) => {
        if (response.redirected) {
          window.location.href = response.url;
        } else {
          return response.text().then((data) => {
            console.log(data);
          });
        }
      })
      .catch((error) => console.error('Error:', error));
  });

  // Function to create table headers dynamically
  function createTableHeaders(fields, tableId) {
    const thead = document.getElementById(tableId).getElementsByTagName('thead')[0];
    const headerRow = thead.insertRow();
    fields.forEach((field) => {
      const th = document.createElement('th');
      th.innerText = field;
      headerRow.appendChild(th);
    });
  }

  // Function to add a new row to the table
  function addRow(rowData, fields, table, editable) {
    const row = table.insertRow();
    fields.forEach((field) => {
      const cell = row.insertCell();
      cell.dataset.field = field;
      if (field === 'Run') {
        const checkboxApple = document.createElement('div');
        checkboxApple.classList.add('checkbox-apple');

        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.classList.add('yep');
        checkbox.id = `check-${row.rowIndex}`;
        if (rowData[field] === '1') {
          checkbox.checked = true;
        }

        const label = document.createElement('label');
        label.setAttribute('for', checkbox.id);

        checkboxApple.appendChild(checkbox);
        checkboxApple.appendChild(label);
        cell.appendChild(checkboxApple);
      } else if (field === 'File') {
        updateFileIcon(cell, JSON.stringify(rowData[field]));
        cell.addEventListener('click', () => openOverlay(field, cell));
      } else {
        if (field !== 'Flow' && field !== 'Type' && field !== 'Wafer') {
          cell.contentEditable = editable;
          cell.addEventListener('input', () => {
            const runCell = row.querySelector('td[data-field="Run"] input[type="checkbox"]');
            if (runCell) {
              runCell.checked = true;
            }
          });
        }
        cell.innerText = rowData[field] || '';

        if (field === 'COM' && (rowData['Type'] === 'TTIME' || rowData['Type'] === 'YIELD')) {
          cell.innerText = rowData['Type'];
          cell.contentEditable = false;
        }

        if (field === 'Type') {
          if (rowData[field] === 'CONDITION') {
            const lotCell = row.querySelector('td[data-field="LOT"]');
            const waferCell = row.querySelector('td[data-field="Wafer"]');
            const fileCell = row.querySelector('td[data-field="File"]');
            if (waferCell) {
              waferCell.innerText = '-';
              waferCell.classList.add('disabled');
            }
            if (lotCell) {
              lotCell.innerText = '-';
              lotCell.classList.add('disabled');
            }
            if (fileCell) {
              fileCell.classList.remove('disabled');
              fileCell.addEventListener('click', () => openOverlay('File', fileCell));
            }
          } else if (rowData[field] === 'CONCLUSION') {
            const lotCell = row.querySelector('td[data-field="LOT"]');
            const waferCell = row.querySelector('td[data-field="Wafer"]');
            const fileCell = row.querySelector('td[data-field="File"]');
            if (waferCell) {
              waferCell.innerText = '-';
              waferCell.classList.add('disabled');
            }
            if (lotCell) {
              lotCell.innerText = '-';
              lotCell.classList.add('disabled');
            }
            if (fileCell) {
              fileCell.innerText = '';
              updateFileIcon(fileCell, '');
              fileCell.removeEventListener('click', openOverlay);
              fileCell.classList.add('disabled');
            }
          }
        }
      }
    });
  }

  // Function to add an empty row to the table
  function addEmptyRow(fields, table) {
    const row = table.insertRow();
    fields.forEach((field) => {
      const cell = row.insertCell();
      cell.dataset.field = field;
      if (field === 'Run') {
        const checkboxApple = document.createElement('div');
        checkboxApple.classList.add('checkbox-apple');

        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.classList.add('yep');
        checkbox.id = `check-${row.rowIndex}`;

        const label = document.createElement('label');
        label.setAttribute('for', checkbox.id);

        checkboxApple.appendChild(checkbox);
        checkboxApple.appendChild(label);
        cell.appendChild(checkboxApple);
      } else if (field === 'File') {
        updateFileIcon(cell, '');
        cell.addEventListener('click', () => openOverlay(field, cell));
      } else {
        // Make cells editable except for specific fields
        if (field !== 'Flow' && field !== 'Type' && field !== 'Wafer') {
          cell.contentEditable = true;
          cell.addEventListener('input', () => {
            const runCell = row.querySelector('td[data-field="Run"] input[type="checkbox"]');
            if (runCell) {
              runCell.checked = true;
            }
          });
        }
        cell.innerText = '';
      }
    });
    // console.log('Empty row added'); // Debug log
  }

  // Function to update File icon
  function updateFileIcon(cell, filePath) {
    const icon = document.createElement('img');
    icon.classList.add('file-icon');
    icon.src = filePath ? 'https://www.svgrepo.com/show/532747/file-alt.svg' : 'https://www.svgrepo.com/show/532811/file-xmark-alt-1.svg';
    cell.innerHTML = '';
    cell.appendChild(icon);
    cell.dataset.filePath = filePath || '{}'; // Ensure it's a valid JSON
  }

  // Function to open overlay based on the field
  function openOverlay(field, cell) {
    const overlay = document.getElementById('overlay');
    const overlayContent = document.getElementById('overlayContent');
    overlayContent.innerHTML = ''; // Clear previous content

    // Add close button
    const closeButton = document.createElement('div');
    closeButton.classList.add('close-container');
    closeButton.innerHTML = `
      <div class="leftright"></div>
      <div class="rightleft"></div>
    `;
    closeButton.addEventListener('click', closeOverlay);
    overlayContent.appendChild(closeButton);

    if (field === 'Flow') {
      createOptions(['EWS1', 'EWS2', 'EWS3', 'EWSDIE', 'FT1'], cell);
    } else if (field === 'Type') {
      createOptions(['VOLUME', 'x30', 'TTIME', 'YIELD', 'CONDITION', 'CONCLUSION'], cell);
    } else if (field === 'Wafer') {
      createMultiSelectOptions(cell);
    } else if (field === 'File') {
      createFileOverlay(cell);
    }
    overlay.style.display = 'block';
  }

  // Function to create options for the overlay
  function createOptions(options, cell) {
    const overlayContent = document.getElementById('overlayContent');
    options.forEach((option) => {
      const button = document.createElement('button');
      button.innerText = option;
      button.addEventListener('click', function () {
        cell.innerText = option;

        const comCell = cell.parentElement.querySelector('td[data-field="COM"]');
        if (comCell) {
          if (option === 'TTIME' || option === 'YIELD') {
            comCell.innerText = option;
            comCell.contentEditable = false;
          } else {
            comCell.contentEditable = true;
          }
        }

        const waferCell = cell.parentElement.querySelector('td[data-field="Wafer"]');
        const lotCell = cell.parentElement.querySelector('td[data-field="LOT"]');
        const fileCell = cell.parentElement.querySelector('td[data-field="File"]');
        if (option === 'CONDITION') {
          if (waferCell) {
            waferCell.innerText = '-';
            waferCell.classList.add('disabled');
          }
          if (lotCell) {
            lotCell.innerText = '-';
            lotCell.classList.add('disabled');
          }
          if (fileCell) {
            fileCell.classList.remove('disabled');
            fileCell.addEventListener('click', () => openOverlay('File', fileCell));
          }
        } else if (option === 'CONCLUSION') {
          if (waferCell) {
            waferCell.innerText = '-';
            waferCell.classList.add('disabled');
          }
          if (lotCell) {
            lotCell.innerText = '-';
            lotCell.classList.add('disabled');
          }
          if (fileCell) {
            fileCell.innerText = '';
            updateFileIcon(fileCell, '');
            fileCell.removeEventListener('click', openOverlay);
            fileCell.classList.add('disabled');
          }
        } else {
          if (waferCell) {
            waferCell.classList.remove('disabled');
            if (waferCell.innerText === '-') {
              waferCell.innerText = '';
            }
          }
          if (lotCell) {
            lotCell.classList.remove('disabled');
            if (lotCell.innerText === '-') {
              lotCell.innerText = '';
            }
          }
          if (fileCell) {
            fileCell.classList.remove('disabled');
            fileCell.addEventListener('click', () => openOverlay('File', fileCell));
          }
        }

        closeOverlay();
      });
      overlayContent.appendChild(button);
    });
  }

  document.addEventListener('input', function (event) {
    const target = event.target;
    if (target.tagName === 'TD' && target.dataset.field === 'Type') {
      const typeValue = target.innerText.trim();
      const comCell = target.parentElement.querySelector('td[data-field="COM"]');
      if (comCell && (typeValue === 'TTIME' || typeValue === 'YIELD')) {
        comCell.innerText = typeValue;
        comCell.contentEditable = false;
      } else if (comCell) {
        comCell.contentEditable = true;
      }
    }
  });

  // Function to create multi-select options for the overlay
  function createMultiSelectOptions(cell) {
    const overlayContent = document.getElementById('overlayContent');
    const allButton = document.createElement('button');
    allButton.innerText = 'All';
    allButton.addEventListener('click', function () {
      cell.innerText = 'All';
      closeOverlay();
    });
    overlayContent.appendChild(allButton);

    const selectedNumbers = cell.innerText.split(', ').map(Number);

    for (let i = 1; i <= 25; i++) {
      const button = document.createElement('button');
      button.innerText = i;
      if (selectedNumbers.includes(i)) {
        button.classList.add('selected');
      }
      button.addEventListener('click', function () {
        if (cell.innerText === 'All') {
          cell.innerText = '';
        }
        if (!cell.innerText.includes(i)) {
          cell.innerText += cell.innerText ? `, ${i}` : i;
          button.classList.add('selected');
        } else {
          cell.innerText = cell.innerText
            .split(', ')
            .filter((num) => num != i)
            .join(', ');
          button.classList.remove('selected');
        }
      });
      overlayContent.appendChild(button);
    }
  }

  function createFileOverlay(cell) {
    const overlayContent = document.getElementById('overlayContent');
    overlayContent.innerHTML = ''; // Clear previous content

    const waferCell = cell.parentElement.querySelector('td[data-field="Wafer"]');
    const wafers =
      waferCell.innerText === 'All'
        ? Array.from({ length: 25 }, (_, i) => i + 1)
        : waferCell.innerText === '-'
        ? ['-']
        : waferCell.innerText
            .split(', ')
            .map(Number)
            .sort((a, b) => a - b);

    let existingPaths = {};
    try {
      existingPaths = cell.dataset.filePath ? JSON.parse(cell.dataset.filePath) : {};
    } catch (e) {
      console.error('Error parsing JSON:', e);
    }

    const div = document.createElement('div');
    div.classList.add('overlayFile');
    const table = document.createElement('table');
    table.classList.add('table', 'table-bordered', 'table-hover');
    const thead = document.createElement('thead');
    thead.classList.add('thead-dark');
    const headerRow = document.createElement('tr');

    if (waferCell.innerText !== '-') {
      const waferHeader = document.createElement('th');
      waferHeader.innerText = 'WAFER';
      headerRow.appendChild(waferHeader);

      const cornerHeader = document.createElement('th');
      cornerHeader.innerText = 'CORNER';
      headerRow.appendChild(cornerHeader);
    }

    const fileHeader = document.createElement('th');
    fileHeader.innerText = 'File Directory';
    headerRow.appendChild(fileHeader);
    thead.appendChild(headerRow);
    table.appendChild(thead);

    const tbody = document.createElement('tbody');

    wafers.forEach((wafer) => {
      const row = document.createElement('tr');

      if (waferCell.innerText !== '-') {
        const waferCell = document.createElement('td');
        waferCell.innerText = wafer;
        row.appendChild(waferCell);

        const cornerCell = document.createElement('td');
        cornerCell.innerText = existingPaths[wafer]?.corner || 'TTTT';
        cornerCell.addEventListener('click', () => openCornerOverlay(cornerCell));
        row.appendChild(cornerCell);
      }

      const fileCell = document.createElement('td');
      const fileInput = document.createElement('input');
      fileInput.type = 'text';
      fileInput.dataset.wafer = wafer;
      fileInput.value = existingPaths[wafer]?.path || generateFilePath(cell.parentElement.querySelector('td[data-field="Code"]').innerText, cell.parentElement.querySelector('td[data-field="Flow"]').innerText, cell.parentElement.querySelector('td[data-field="LOT"]').innerText, wafer, cell.parentElement.querySelector('td[data-field="Type"]').innerText);
      fileInput.placeholder = 'Enter directory path';
      fileInput.addEventListener('input', () => {
        existingPaths[wafer] = {
          corner: waferCell.innerText !== '-' ? row.querySelector('td + td').innerText : 'TTTT',
          path: fileInput.value,
        };
      });
      fileCell.appendChild(fileInput);
      row.appendChild(fileCell);
      tbody.appendChild(row);
    });

    table.appendChild(tbody);
    div.appendChild(table);

    const saveButton = document.createElement('button');
    saveButton.innerText = 'Save';
    saveButton.classList.add('btn', 'btn-primary');
    saveButton.addEventListener('click', () => {
      const filePath = {};
      tbody.querySelectorAll('tr').forEach((row) => {
        let wafer, corner, path;
        if (waferCell.innerText !== '-') {
          wafer = row.querySelector('td').innerText;
          corner = row.querySelector('td + td').innerText;
          path = row.querySelector('td + td + td input').value;
        } else {
          wafer = '-';
          corner = 'TTTT';
          path = row.querySelector('td input').value;
        }
        if (path.trim() !== '' && (wafer.trim() !== '' || wafers.length === 0) && corner.trim() !== '') {
          filePath[wafer] = {
            corner: corner,
            path: path, // Save the full directory path
          };
        }
      });
      cell.dataset.filePath = JSON.stringify(filePath);
      cell.innerText = 'Paths set'; // Update the cell text
      updateFileIcon(cell, cell.dataset.filePath); // Use the JSON string as filePath
      closeOverlay();
    });
    div.appendChild(saveButton);
    overlayContent.appendChild(div);
  }

  // Handle input event on table cells
  function handleCellInput(event) {
    const row = event.target.parentElement;
    const table = row.parentElement;
    const isLastRow = row.rowIndex === table.rows.length - 1;

    // Add a new empty row if the last row is filled
    if (isLastRow && allFieldsFilled(row)) {
      addEmptyRow(dataFields, table);
    }
  }

  // Check if all fields in a row are filled
  function allFieldsFilled(row) {
    const cells = row.getElementsByTagName('td');
    for (let i = 0; i < cells.length; i++) {
      if (!cells[i].innerText.trim() && !cells[i].querySelector('.checkbox-apple') && !cells[i].querySelector('.file-icon')) {
        return false;
      }
    }
    return true;
  }

  // Add event listener for cell click to open overlay
  document.addEventListener('click', function (event) {
    const target = event.target;
    if (target.tagName === 'TD' && target.dataset.field) {
      const field = target.dataset.field;
      if (field === 'Flow' || field === 'Type' || field === 'Wafer' || field === 'File') {
        openOverlay(field, target);
      }
    }
  });

  function openCornerOverlay(cell) {
    const overlay = document.getElementById('secondaryOverlay');
    const overlayContent = document.getElementById('secondaryOverlayContent');
    if (!overlayContent) return;
    overlayContent.innerHTML = '';

    const closeButton = document.createElement('div');
    closeButton.classList.add('close-container');
    closeButton.innerHTML = `
      <div class="leftright"></div>
      <div class="rightleft"></div>
    `;
    closeButton.addEventListener('click', () => closeSecondaryOverlay());
    overlayContent.appendChild(closeButton);

    const corners = ['TTTT', 'FFTT', 'F1TT', 'SSTT', 'S1TT', 'FSTT', 'SFTT', 'FFMM', 'SSXX'];
    corners.forEach((corner) => {
      const button = document.createElement('button');
      button.innerText = corner;
      button.addEventListener('click', function () {
        cell.innerText = corner;
        closeSecondaryOverlay();
      });
      overlayContent.appendChild(button);
    });

    // Aggiungi icona informativa
    const infoIcon = document.createElement('img');
    infoIcon.src = 'https://www.svgrepo.com/show/533722/circle-information.svg';
    infoIcon.alt = 'Informazioni';
    infoIcon.style.cursor = 'pointer';
    infoIcon.addEventListener('click', () => openInfoOverlay());
    overlayContent.appendChild(infoIcon);

    if (overlay) {
      overlay.style.display = 'block';
    }
  }

  function openInfoOverlay() {
    const infoOverlay = document.getElementById('infoOverlay');
    const infoOverlayContent = document.getElementById('infoOverlayContent');
    if (!infoOverlayContent) return;
    infoOverlayContent.innerHTML = '';

    const closeButton = document.createElement('div');
    closeButton.classList.add('close-container');
    closeButton.innerHTML = `
      <div class="leftright"></div>
      <div class="rightleft"></div>
    `;
    closeButton.addEventListener('click', () => closeInfoOverlay());
    infoOverlayContent.appendChild(closeButton);

    // Aggiungi il tuo testo HTML completo qui
    const infoText = document.createElement('div');
    infoText.innerHTML = `
      <!-- Inserisci qui il tuo testo HTML completo -->
      <div><table class="table table-bordered">
      <thead class="thead-dark">
        <tr>
          <th>Corner Type</th>
          <th>NMOS</th>
          <th>PMOS</th>
          <th>Resistors</th>
          <th>Capacitance</th>
        </tr>
      </thead>
  <tr>
    <td>TTTT (STD)</td>
    <td>STD</td>
    <td>STD</td>
    <td>STD</td>
    <td>STD</td>
  </tr>
  <tr>
    <td>FFTT</td>
    <td>FAST</td>
    <td>FAST</td>
    <td>STD</td>
    <td>STD</td>
  </tr>
  <tr>
    <td>F1TT (MidFast)</td>
    <td>midF</td>
    <td>midF</td>
    <td>STD</td>
    <td>STD</td>
  </tr>
  <tr>
    <td>SSTT</td>
    <td>SLOW</td>
    <td>SLOW</td>
    <td>STD</td>
    <td>STD</td>
  </tr>
  <tr>
    <td>S1TT (MidSlow)</td>
    <td>midS</td>
    <td>midS</td>
    <td>STD</td>
    <td>STD</td>
  </tr>
  <tr>
    <td>FSTT (N-Fast / P-Slow)</td>
    <td>FAST</td>
    <td>SLOW</td>
    <td>STD</td>
    <td>STD</td>
  </tr>
  <tr>
    <td>SFTT (N-Slow / P-Fast)</td>
    <td>SLOW</td>
    <td>FAST</td>
    <td>STD</td>
    <td>STD</td>
  </tr>
  <tr>
    <td>FFMM (RCmin)</td>
    <td>FAST</td>
    <td>FAST</td>
    <td>Rmin</td>
    <td>Cmin</td>
  </tr>
  <tr>
    <td>SSXX (RCmax)</td>
    <td>SLOW</td>
    <td>SLOW</td>
    <td>Rmax</td>
    <td>Cmax</td>
  </tr>
</table>
</div>
    `;
    infoOverlayContent.appendChild(infoText);

    if (infoOverlay) {
      infoOverlay.style.display = 'block';
    }
  }

  function closeInfoOverlay() {
    const infoOverlay = document.getElementById('infoOverlay');
    if (infoOverlay) {
      infoOverlay.style.display = 'none';
    }
  }

  function closeSecondaryOverlay() {
    const overlay = document.getElementById('secondaryOverlay');
    if (overlay) {
      overlay.style.display = 'none';
    }
  }

  // Function to close the overlay
  function closeOverlay() {
    const overlay = document.getElementById('overlay');
    overlay.style.display = 'none';
  }

  // Add event listener to close overlay when clicking outside of it
  document.getElementById('overlay').addEventListener('click', function (event) {
    if (event.target.id === 'overlay') {
      closeOverlay();
    }
  });

  function generateFilePath(code, flow, lot, wafer, type) {
    if (type === 'CONDITION') {
      return `\\\\gpm-pe-data.gnb.st.com\\ENGI_MCD_STDF\\${code}\\${flow}`;
    }
    if (type === 'TTIME' || type === 'YIELD') {
      type = 'VOLUME';
    }
    if (wafer.toString().length === 1) {
      wafer = '0' + wafer.toString();
    }
    return `\\\\gpm-pe-data.gnb.st.com\\ENGI_MCD_STDF\\${code}\\${flow}\\${lot}\\${lot}_${wafer}\\${type}`;
  }
});

function checkStatus() {
  fetch('/post.json')
    .then((response) => response.json())
    .then((data) => {
      // Check if all items have 'Run' set to '0'
      if (data.data.every((item) => item.Run === '1')) {
        window.location.href = '/loading';
      }
    })
    .catch((error) => console.error('Error:', error));
}

window.onload = function () {
  checkStatus();
};
