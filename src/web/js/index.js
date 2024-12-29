document.addEventListener('DOMContentLoaded', function () {
  const authorTable = document.getElementById('authorTable').getElementsByTagName('tbody')[0];
  const dataTable = document.getElementById('dataTable').getElementsByTagName('tbody')[0];
  const submitForm = document.getElementById('submitForm');
  const authorFields = ['Author', 'Mail', 'Site', 'Group'];
  let dataFields = [];

  // Load existing data from JSON file
  fetch('/post.json')
    .then((response) => {
      if (!response.ok) {
        throw new Error('Network response was not ok ' + response.statusText);
      }
      return response.json();
    })
    .then((jsonData) => {
      const authorInfo = jsonData.authorInfo;
      const data = jsonData.data;

      if (data.length > 0) {
        dataFields = Object.keys(data[0]).filter((field) => !authorFields.includes(field));
      }
      console.log('Fields detected from JSON:', dataFields); // Debug log
      console.log('Data loaded from JSON:', data); // Debug log

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

    let allAuthorFieldsFilled = true;
    authorFields.forEach((field, j) => {
      const value = authorRow.getElementsByTagName('td')[j].innerText.trim();
      if (!value) {
        allAuthorFieldsFilled = false;
      }
      authorData[field] = value;
    });

    if (!allAuthorFieldsFilled) {
      alert('Please fill all author fields.');
      return;
    }

    for (let i = 0; i < dataRows.length; i++) {
      const cells = dataRows[i].getElementsByTagName('td');
      const rowData = {};
      let allFieldsFilled = true;

      dataFields.forEach((field, j) => {
        if (field === 'Run') {
          const checkbox = cells[j].querySelector('.yep');
          rowData[field] = checkbox.checked ? '1' : '0';
        } else {
          const value = cells[j].innerText.trim();
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

    console.log('Data to be submitted:', { authorInfo: authorData, data: data }); // Debug log

    // Redirect to loading page immediately after form submission
    window.location.href = '/loading';

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
            // window.location.href = '/loading'; // This line is no longer needed
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
      } else {
        cell.contentEditable = editable;
        cell.innerText = rowData[field] || '';
        if (editable) {
          cell.addEventListener('input', handleCellInput);
        }
      }
    });
    console.log('Row added:', rowData); // Debug log
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
      } else {
        cell.contentEditable = true;
        cell.innerText = '';
        cell.addEventListener('input', handleCellInput);
      }
    });
    console.log('Empty row added'); // Debug log
  }

  // Handle input event on table cells
  function handleCellInput(event) {
    const row = event.target.parentElement;
    const table = row.parentElement;
    const isLastRow = row.rowIndex === table.rows.length - 1;

    if (isLastRow && allFieldsFilled(row)) {
      addEmptyRow(dataFields, table);
    }
  }

  // Check if all fields in a row are filled
  function allFieldsFilled(row) {
    const cells = row.getElementsByTagName('td');
    for (let i = 0; i < cells.length; i++) {
      if (!cells[i].innerText.trim() && !cells[i].querySelector('.checkbox-apple')) {
        return false;
      }
    }
    return true;
  }
});
