
const selectedBatchOptions = [];
const selectedDestiOptions = [];
const selectedTimeOptions = [];
const selectedStartOptions = [];
let selected_Date;


function clear_filter() {
  fetch(`${subpath}/viewBookingRedirect`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json'
    }
  })
    .then(response => {
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      // Assuming the response is an HTML page to render
      window.location.href = `${subpath}/viewBookingRedirect`; // Redirect to the route
    })
    .catch(error => {
      console.error('There was a problem with the fetch operation:', error);
    });
}



function createDropdown(selectId, itemsClass, btnTextClass, selectedOptionsArray) {
  const selectBtn = document.getElementById(selectId);
  const items = document.querySelectorAll(`.${itemsClass}`);

  selectBtn.addEventListener("click", () => {
    selectBtn.classList.toggle("open");
  });

  items.forEach(item => {
    item.addEventListener("click", () => {
      item.classList.toggle("checked");

      const checkedItems = document.querySelectorAll(`.${itemsClass}.checked`);
      const btnText = document.querySelector(`.${btnTextClass}`);

      if (checkedItems.length > 0) {
        selectedOptionsArray.length = 0; // Clear the array before updating
        checkedItems.forEach(checkedItem => {
          const option = checkedItem.querySelector(`.item-text_${selectId}`).innerText;
          selectedOptionsArray.push(option); // Push selected option into array
        });
        btnText.innerText = `${checkedItems.length} Selected`;
        console.log("Selected Options:", selectedOptionsArray);
      } else {
        btnText.innerText = `Select ${selectId}`;
        selectedOptionsArray.length = 0; // Clear the array if no options are selected
      }
      console.log("batch:" + selectedBatchOptions)
      console.log("destination:" + selectedDestiOptions)
      console.log("time:" + selectedTimeOptions)
      console.log("Start:" + selectedStartOptions)

    });
  });
}

createDropdown("batch", "item_batch", "btn-text_batch", selectedBatchOptions);
createDropdown("destination", "item_destination", "btn-text_destination", selectedDestiOptions);
createDropdown("time", "item_time", "btn-text_time", selectedTimeOptions);
createDropdown("start", "item_start", "btn-text_start", selectedStartOptions);


function sendEmail(email, destination, time, date, name, sender) {
  var subject = "Let's travel together!";
  var body = "Hey there,\n\nI'm reaching out because I'm planning a trip to " + destination + " on " + date + " at " + time + ". Since we're both headed in the same direction, I thought it might be convenient for us to travel together.\n\nIf you're interested and have space available in your cab, it would be great to share the ride and split the travel expenses.\n\nLooking forward to hearing from you soon!\n\nBest regards,\n" + sender;
  var mailtoLink = "mailto:" + email + "?subject=" + encodeURIComponent(subject) + "&body=" + encodeURIComponent(body);
  window.location.href = mailtoLink;
}


const selectedDateInput = document.getElementById("selectedDate");

selectedDateInput.addEventListener("change", (event) => {
  selected_Date = event.target.value;
  console.log("Selected Date:", selected_Date);
});


document.querySelector(".submit_button").addEventListener("click", function () {
  // Gather selected options
  const selectedBatch = selectedBatchOptions.join(',');
  const selectedDestination = selectedDestiOptions.join(',');
  const selectedTime = selectedTimeOptions.join(',');
  const selectedStart = selectedStartOptions.join(',');
  const selectedDate = selected_Date
  // Check if all filter lists are empty
  if (!selectedBatch && !selectedDestination && !selectedTime && !selectedStart && !selected_Date) {
    alert("Please choose filters first.");
    return; // Exit the function early
  }

  // Prepare data to send to Flask
  const data = {
    selectedBatch: selectedBatch,
    selectedDestination: selectedDestination,
    selectedTime: selectedTime,
    selectedStart: selectedStart,
    selectedDate: selected_Date
  };

  // Send data to Flask using Fetch API
  fetch(`${subpath}/apply_filters`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(data)
  })
    .then(response => {
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      return response.json();
    })
    .then(filteredData => {
      // Handle response from Flask
      console.log('Filtered Data:', filteredData);

      // Update the frontend with the filtered data
      updateBookingOptions(filteredData.available_options);
      console.log("\n\n\n\n\n\n filters \n\n\n\n" + filteredData);

    })
    .catch(error => {
      console.error('There was a problem with the fetch operation:', error);
    });
});

function updateBookingOptions(availableOptions) {

  const bookingContainer = document.querySelector(".booking-container");
  bookingContainer.innerHTML = ""; // Clear existing options

  console.log(availableOptions)
  if (!availableOptions) {
    bookingContainer.innerHTML = '<span class="no_plan_msg">No one with the current specifications is heading in that direction.<br> Please add your own card so that others can find you!</span>'; // Clear existing options        
  }
  else {
    availableOptions.forEach(entry => {
      const card = `
        <div class="booking-card flex align-c">
            <div class="booking-card-content-left">
              <h3>Name: ${entry[3]}</h3>
              <p>Batch: ${entry[5]}</p>
              <p>Gender: ${entry[4]}</p>
              <p>Email: ${entry[8]}</p>
            </div>
            <div class="booking-card-content-right">
              <h3>From: ${entry[7]}</h3>
              <h3>To: ${entry[6]}</h3>
              <p>Time: ${entry[1]}</p>
              <p>Date: ${entry[0]}</p>
              <!-- Add the button here -->
              <button
                class="mail_btn cursor-p"11:59:8
                onclick="sendEmail('${entry[8]}', '${entry[6]}', '${entry[1]}', '${entry[0]}', '${entry[3]}')"
              >
                Send Email
              </button>
            </div>
        </div>`;

      bookingContainer.insertAdjacentHTML('beforeend', card);
    });
  }
}
