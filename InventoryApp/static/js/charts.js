/**
 * Chart initialization and utility functions
 */

/**
 * Create a pie chart
 * @param {string} elementId - The canvas element ID
 * @param {Array} labels - The chart labels
 * @param {Array} data - The chart data
 * @param {string} title - The chart title
 * @returns {Chart} The created chart
 */
function createPieChart(elementId, labels, data, title) {
    const ctx = document.getElementById(elementId).getContext('2d');
    
    return new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: [
                    'rgba(54, 162, 235, 0.7)',
                    'rgba(255, 99, 132, 0.7)',
                    'rgba(255, 206, 86, 0.7)',
                    'rgba(75, 192, 192, 0.7)',
                    'rgba(153, 102, 255, 0.7)',
                    'rgba(255, 159, 64, 0.7)',
                    'rgba(199, 199, 199, 0.7)',
                    'rgba(83, 102, 255, 0.7)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'right',
                },
                title: {
                    display: true,
                    text: title
                }
            }
        }
    });
}

/**
 * Create a line chart
 * @param {string} elementId - The canvas element ID
 * @param {Array} labels - The chart labels
 * @param {Array} data - The chart data
 * @param {string} title - The chart title
 * @param {string} yAxisLabel - The y-axis label
 * @returns {Chart} The created chart
 */
function createLineChart(elementId, labels, data, title, yAxisLabel = '') {
    const ctx = document.getElementById(elementId).getContext('2d');
    
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: yAxisLabel,
                data: data,
                borderColor: 'rgba(54, 162, 235, 1)',
                backgroundColor: 'rgba(54, 162, 235, 0.2)',
                borderWidth: 2,
                tension: 0.1,
                fill: true
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: title
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

/**
 * Create a bar chart
 * @param {string} elementId - The canvas element ID
 * @param {Array} labels - The chart labels
 * @param {Array} data - The chart data
 * @param {string} title - The chart title
 * @param {string} yAxisLabel - The y-axis label
 * @returns {Chart} The created chart
 */
function createBarChart(elementId, labels, data, title, yAxisLabel = '') {
    const ctx = document.getElementById(elementId).getContext('2d');
    
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: yAxisLabel,
                data: data,
                backgroundColor: 'rgba(54, 162, 235, 0.7)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: title
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

/**
 * Format currency values
 * @param {number} value - The value to format
 * @returns {string} The formatted currency string
 */
function formatCurrency(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(value);
}

/**
 * Get random colors for charts
 * @param {number} count - Number of colors needed
 * @returns {Array} Array of color strings
 */
function getRandomColors(count) {
    const colors = [];
    for (let i = 0; i < count; i++) {
        const r = Math.floor(Math.random() * 255);
        const g = Math.floor(Math.random() * 255);
        const b = Math.floor(Math.random() * 255);
        colors.push(`rgba(${r}, ${g}, ${b}, 0.7)`);
    }
    return colors;
}

/**
 * Load chart data from API
 * @param {string} url - The API URL
 * @returns {Promise} Promise that resolves with the data
 */
async function loadChartData(url) {
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Error loading chart data:', error);
        return null;
    }
}

/**
 * Update charts with new data
 * @param {string} apiUrl - The API endpoint to fetch data from
 * @param {function} chartFunction - Function to call with the new data
 */
function updateChart(apiUrl, chartFunction) {
    fetch(apiUrl)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            chartFunction(data);
        })
        .catch(error => {
            console.error('Error updating chart:', error);
        });
}
