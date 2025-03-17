////////////////////////// LOCATION CHART /////////////////////////////

const location_ctx = document.getElementById("location_chart");
var locationChart = new Chart(location_ctx, {
  type: "bar",
  data: {
    labels: UNIQUE_LOCATIONS,
    datasets: [
      {
        label: "Things",
        data: [],
        borderWidth: 1,
      },
    ],
  },
  options: {
    plugins: {
      legend: {
        display: false,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
      },
    },
  },
});

function set_location(burns) {
  // Construct location frequency mapping
  let locationCount = {};
  burns.forEach((burn) => {
    locationCount[burn.location] = (locationCount[burn.location] || 0) + 1;
  });

  // Convert object to array and sort by frequency (descending)
  let sortedLocations = Object.entries(locationCount).sort(
    (a, b) => b[1] - a[1],
  );

  // Create the lists for locations and their frequencies
  locationChart.data.labels = sortedLocations
    .map((item) => item[0])
    .slice(0, 5);
  locationChart.data.datasets[0].data = sortedLocations
    .map((item) => item[1])
    .slice(0, 5);
  locationChart.update();
}
////////////////////////// PROP CHART /////////////////////////////
const prop_ctx = document.getElementById("prop_chart");
var propChart = new Chart(prop_ctx, {
  type: "bar",
  data: {
    labels: UNIQUE_LOCATIONS,
    datasets: [
      {
        label: "Things",
        data: [],
        borderWidth: 1,
      },
    ],
  },
  options: {
    plugins: {
      legend: {
        display: false,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
      },
    },
  },
});

function set_props(burns) {
  // Construct location frequency mapping
  let propCount = {};
  burns.forEach((burn) => {
    propCount[burn.prop] = (propCount[burn.prop] || 0) + 1;
  });

  // Convert object to array and sort by frequency (descending)
  let sortedProps = Object.entries(propCount).sort((a, b) => b[1] - a[1]);

  // Create the lists for locations and their frequencies
  propChart.data.labels = sortedProps.map((item) => item[0]).slice(0, 5);
  propChart.data.datasets[0].data = sortedProps
    .map((item) => item[1])
    .slice(0, 5);
  propChart.update();
}

////////////////////////// BURNS OVER TIME /////////////////////////////
const time_ctx = document.getElementById("time_chart");
var timeChart = new Chart(time_ctx, {
  type: "line",
  data: {
    labels: UNIQUE_LOCATIONS,
    datasets: [
      {
        label: "Things",
        data: [],
        borderWidth: 1,
      },
    ],
  },
  options: {
    plugins: {
      legend: {
        display: false,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
      },
    },
  },
});

function set_time(burns) {
  // Aggregate burns by date
  const burnCounts = burns.reduce((acc, burn) => {
    const date = new Date(burn.time).toISOString().split("T")[0]; // Extract YYYY-MM-DD
    acc[date] = (acc[date] || 0) + 1;
    return acc;
  }, {}); // Construct location frequency mapping

  // Sort dates and format data
  const sortedDates = Object.keys(burnCounts).sort(
    (a, b) => new Date(a) - new Date(b),
  );
  const burnData = sortedDates.map((date) => burnCounts[date]);

  // Update chart
  timeChart.data.labels = sortedDates;
  timeChart.data.datasets[0].data = burnData;
  timeChart.update();
}

function get_filtered_burns() {
  return BURNS;
}

let burns = get_filtered_burns();
set_location(burns);
set_props(burns);
set_time(burns);
