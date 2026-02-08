/**
 * Trip Planner - Frontend JavaScript
 * Handles form submission, API calls, and result rendering
 */

// API base URL
const API_BASE = '/api';

// State
let currentItinerary = null;

// DOM Elements
const tripForm = document.getElementById('trip-form');
const formSection = document.getElementById('form-section');
const loadingSection = document.getElementById('loading-section');
const errorSection = document.getElementById('error-section');
const resultSection = document.getElementById('result-section');
const errorMessage = document.getElementById('error-message');
const submitBtn = document.getElementById('submit-btn');
const demoBtn = document.getElementById('demo-btn');
const fillTestBtn = document.getElementById('fill-test-btn');
const retryBtn = document.getElementById('retry-btn');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeForm();
    initializeToggleButtons();
    initializeRangeSlider();
    attachEventListeners();
});

// Form initialization
function initializeForm() {
    // Set minimum dates
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('start_date').min = today;
    document.getElementById('end_date').min = today;

    // Set default dates (tomorrow to 5 days later)
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const endDate = new Date();
    endDate.setDate(endDate.getDate() + 5);

    document.getElementById('start_date').value = tomorrow.toISOString().split('T')[0];
    document.getElementById('end_date').value = endDate.toISOString().split('T')[0];
}

// Toggle buttons for interests, cuisines, dietary
function initializeToggleButtons() {
    document.querySelectorAll('.toggle-group').forEach(group => {
        group.querySelectorAll('.toggle-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                btn.classList.toggle('active');
            });
        });
    });
}

// Range slider for distance
function initializeRangeSlider() {
    const slider = document.getElementById('max_distance');
    const valueDisplay = document.getElementById('distance-value');

    slider.addEventListener('input', () => {
        valueDisplay.textContent = `${slider.value} km`;
    });
}

// Event listeners
function attachEventListeners() {
    // Form submit
    tripForm.addEventListener('submit', handleFormSubmit);

    // Demo button
    demoBtn.addEventListener('click', handleDemoClick);

    // Fill test data button
    fillTestBtn.addEventListener('click', fillTestData);

    // Retry button
    retryBtn.addEventListener('click', handleRetry);
}

// Number stepper function
function adjustNumber(fieldId, delta) {
    const input = document.getElementById(fieldId);
    const min = parseInt(input.min) || 0;
    const max = parseInt(input.max) || 99;
    let value = parseInt(input.value) + delta;
    value = Math.max(min, Math.min(max, value));
    input.value = value;
}

// Make adjustNumber global
window.adjustNumber = adjustNumber;

// Get selected toggle values
function getToggleValues(groupId) {
    const group = document.getElementById(groupId);
    const selected = [];
    group.querySelectorAll('.toggle-btn.active').forEach(btn => {
        selected.push(btn.dataset.value);
    });
    return selected;
}

// Build request payload
function buildPayload() {
    // Collect destinations
    let destinationVal = '';
    const destInputs = document.querySelectorAll('.destination-input');
    if (destInputs.length > 0) {
        const dests = Array.from(destInputs)
            .map(input => input.value.trim())
            .filter(val => val.length > 0);

        if (dests.length > 1) {
            destinationVal = dests.join(' -> ');
        } else if (dests.length === 1) {
            destinationVal = dests[0];
        }
    } else {
        // Fallback for single mode if something goes wrong, though inputs should be there
        destinationVal = document.getElementById('destination')?.value || '';
    }

    return {
        destination: destinationVal,
        start_date: document.getElementById('start_date').value,
        end_date: document.getElementById('end_date').value,
        origin_location: document.getElementById('origin').value || null,
        travelers: {
            adults: parseInt(document.getElementById('adults').value),
            children: parseInt(document.getElementById('children').value)
        },
        budget: {
            currency: document.getElementById('currency').value,
            total_budget: parseFloat(document.getElementById('total_budget').value),
            comfort_level: document.getElementById('comfort_level').value
        },
        activity_preferences: {
            interests: getToggleValues('interests-group'),
            pace: document.getElementById('pace').value,
            accessibility_needs: []
        },
        food_preferences: {
            cuisines: getToggleValues('cuisines-group'),
            dietary_restrictions: getToggleValues('dietary-group'),
            avoid_ingredients: []
        },
        lodging_preferences: {
            lodging_type: document.getElementById('lodging_type').value,
            max_distance_km_from_center: parseFloat(document.getElementById('max_distance').value)
        },
        daily_start_time: document.getElementById('daily_start').value,
        daily_end_time: document.getElementById('daily_end').value,
        notes: document.getElementById('notes').value || null
    };
}

// Form submission handler
async function handleFormSubmit(e) {
    e.preventDefault();

    const payload = buildPayload();

    showLoading();

    try {
        const response = await fetch(`${API_BASE}/itineraries/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const errorData = await response.json();

            // Handle specific Gemini configuration error
            if (response.status === 503 || errorData.code === 'gemini_not_configured' || (errorData.message && errorData.message.includes('API key'))) {
                throw new Error("⚠️ Gemini API Key Missing.\n\nPlease check your server console and README.md for setup instructions.");
            }

            throw new Error(errorData.error || errorData.detail || 'Failed to generate itinerary');
        }

        const data = await response.json();
        currentItinerary = data;
        showResult(data);

    } catch (error) {
        console.error('Error:', error);
        showError(error.message);
    }
}

// Demo data - Arizona Road Trip
const DEMO_ITINERARY = {
    id: 'demo-az-123',
    status: 'completed',
    request: {
        destination: 'Tempe -> Grand Canyon -> Las Vegas',
        start_date: '2026-04-01',
        end_date: '2026-04-05'
    },
    result: {
        destination: 'Tempe -> Grand Canyon -> Las Vegas',
        start_date: '2026-04-01',
        end_date: '2026-04-05',
        daily_schedule: [
            {
                date: '2026-04-01',
                day_number: 1,
                theme: 'Tempe & ASU Vibes',
                weather_summary: 'Sunny, 28°C',
                blocks: [
                    {
                        start_time: '14:00',
                        end_time: '16:00',
                        title: 'Explore Mill Avenue',
                        description: 'Walk through the vibrant Mill Avenue District near ASU.',
                        block_type: 'activity',
                        location: 'Tempe, AZ',
                        micro_activities: ['Shop at local boutiques', 'Visit ASU campus', 'Coffee at Cartel']
                    },
                    {
                        start_time: '16:30',
                        end_time: '18:00',
                        title: 'Papago Park Sunset',
                        description: 'Easy hike to Hole-in-the-Rock for scenic views.',
                        block_type: 'activity',
                        location: 'Papago Park',
                        micro_activities: ['Hike Hole-in-the-Rock', 'Desert Botanical Garden view']
                    },
                    {
                        start_time: '19:00',
                        end_time: '21:00',
                        title: 'Dinner at Culinary Dropout',
                        description: 'Enjoy gastropub fare and games.',
                        block_type: 'meal',
                        location: 'Tempe',
                        micro_activities: []
                    }
                ]
            },
            {
                date: '2026-04-02',
                day_number: 2,
                theme: 'Drive to the Grand Canyon',
                weather_summary: 'Clear, 22°C (cooler at elevation)',
                blocks: [
                    {
                        start_time: '08:00',
                        end_time: '12:00',
                        title: 'Drive to South Rim',
                        description: 'Scenic drive north through Sedona and Flagstaff.',
                        block_type: 'travel',
                        location: 'En route',
                        travel_time_mins: 240
                    },
                    {
                        start_time: '13:00',
                        end_time: '17:00',
                        title: 'Grand Canyon South Rim',
                        description: 'First views of the canyon and Rim Trail walk.',
                        block_type: 'activity',
                        location: 'Grand Canyon Village',
                        micro_activities: ['Mather Point', 'Yavapai Geology Museum', 'Rim Trail']
                    },
                    {
                        start_time: '18:00',
                        end_time: '20:00',
                        title: 'Dinner at El Tovar',
                        description: 'Historic dining with canyon views (reservation needed).',
                        block_type: 'meal',
                        location: 'Grand Canyon Village',
                        micro_activities: []
                    }
                ]
            },
            {
                date: '2026-04-03',
                day_number: 3,
                theme: 'Canyon Morning & Vegas Lights',
                weather_summary: 'Sunny, 15°C -> 30°C in Vegas',
                blocks: [
                    {
                        start_time: '06:00',
                        end_time: '08:00',
                        title: 'Sunrise at Hopi Point',
                        description: 'Watch the sunrise light up the canyon walls.',
                        block_type: 'activity',
                        location: 'Hermit Road',
                        micro_activities: []
                    },
                    {
                        start_time: '10:00',
                        end_time: '15:00',
                        title: 'Drive to Las Vegas via Hoover Dam',
                        description: 'Drive west, stopping at Hoover Dam.',
                        block_type: 'travel',
                        location: 'En route',
                        travel_time_mins: 300,
                        micro_activities: ['Hoover Dam photo op']
                    },
                    {
                        start_time: '19:00',
                        end_time: '22:00',
                        title: 'Las Vegas Strip',
                        description: 'Walk the strip and see the Bellagio Fountains.',
                        block_type: 'activity',
                        location: 'Las Vegas Strip',
                        micro_activities: ['Bellagio Fountains', 'Caesars Palace', 'The Linq Promenade']
                    }
                ]
            }
        ],
        transport_analysis: {
            recommended_mode: 'Rental Car',
            reasoning: 'Essential for multi-city travel in the Southwest.',
            options: [
                {
                    mode: 'rental_car',
                    cost_estimate: '$300 total',
                    duration_estimate: 'Flexible',
                    description: 'SUV recommended for comfort.'
                }
            ]
        },
        budget_breakdown: {
            accommodation: { amount: 800, currency: 'USD' },
            transportation: { amount: 400, currency: 'USD' },
            food: { amount: 500, currency: 'USD' },
            activities: { amount: 300, currency: 'USD' },
            miscellaneous: { amount: 200, currency: 'USD' },
            total: { amount: 2200, currency: 'USD' }
        }
    }
};

// Demo click handler
function handleDemoClick() {
    currentItinerary = DEMO_ITINERARY;
    showResult(DEMO_ITINERARY);
}

// Fill test data handler
function fillTestData() {
    // Switch to Multi-City and clear
    toggleTripType('multi');
    const container = document.getElementById('destinations-container');
    container.innerHTML = '';

    // Add destinations
    const destinations = ['Tempe, AZ', 'Grand Canyon, AZ', 'Las Vegas, NV'];

    destinations.forEach((dest, index) => {
        addDestinationInput();
        // Update valid input
        const inputs = document.querySelectorAll('.destination-input');
        inputs[inputs.length - 1].value = dest;
    });

    document.getElementById('origin').value = 'Phoenix, AZ';

    // Set dates (7 days from now, 5-day trip)
    const startDate = new Date();
    startDate.setDate(startDate.getDate() + 7);
    const endDate = new Date();
    endDate.setDate(endDate.getDate() + 12);

    document.getElementById('start_date').value = startDate.toISOString().split('T')[0];
    document.getElementById('end_date').value = endDate.toISOString().split('T')[0];

    // Set travelers
    document.getElementById('adults').value = 2;
    document.getElementById('children').value = 1;

    // Set budget
    document.getElementById('currency').value = 'USD';
    document.getElementById('total_budget').value = 5000;
    document.getElementById('comfort_level').value = 'midrange';

    // Set interests (activate toggle buttons)
    const interestValues = ['culture', 'food', 'history', 'nature'];
    const interestsGroup = document.getElementById('interests-group');
    interestsGroup.querySelectorAll('.toggle-btn').forEach(btn => {
        if (interestValues.includes(btn.dataset.value)) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    // Set cuisines (activate toggle buttons)
    const cuisineValues = ['local', 'asian', 'street_food'];
    const cuisinesGroup = document.getElementById('cuisines-group');
    cuisinesGroup.querySelectorAll('.toggle-btn').forEach(btn => {
        if (cuisineValues.includes(btn.dataset.value)) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    // Clear dietary restrictions
    const dietaryGroup = document.getElementById('dietary-group');
    dietaryGroup.querySelectorAll('.toggle-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    // Set pace
    document.getElementById('pace').value = 'moderate';

    // Set accommodation
    document.getElementById('lodging_type').value = 'hotel';
    document.getElementById('max_distance').value = 5;
    document.getElementById('distance-value').textContent = '5 km';

    // Set daily schedule
    document.getElementById('daily_start').value = '09:00';
    document.getElementById('daily_end').value = '21:00';

    // Set notes
    document.getElementById('notes').value = 'First time visiting Japan! Interested in cherry blossoms and traditional temples.';

    // Scroll to form and show a brief animation
    document.getElementById('trip-form').scrollIntoView({ behavior: 'smooth' });

    // Flash effect on the form to indicate it was filled
    const form = document.getElementById('trip-form');
    form.style.transition = 'box-shadow 0.3s ease';
    form.style.boxShadow = '0 0 20px rgba(168, 85, 247, 0.5)';
    setTimeout(() => {
        form.style.boxShadow = '';
    }, 500);
}

// Retry handler
function handleRetry() {
    showForm();
}

// UI State functions
function showForm() {
    formSection.classList.remove('hidden');
    loadingSection.classList.add('hidden');
    errorSection.classList.add('hidden');
    resultSection.classList.add('hidden');
}

function showLoading() {
    formSection.classList.add('hidden');
    loadingSection.classList.remove('hidden');
    errorSection.classList.add('hidden');
    resultSection.classList.add('hidden');
    // REMOVED: window.scrollTo({ top: 0, behavior: 'smooth' }); to prevent jumping
}

function showError(message) {
    formSection.classList.remove('hidden');
    loadingSection.classList.add('hidden');
    errorSection.classList.remove('hidden');
    resultSection.classList.add('hidden');
    errorMessage.textContent = message;
}

function showResult(data) {
    formSection.classList.add('hidden');
    loadingSection.classList.add('hidden');
    errorSection.classList.add('hidden');
    resultSection.classList.remove('hidden');
    renderItinerary(data);
    // Only scroll to results when successfully generated
    resultSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Format time helper
function formatTime(timeStr) {
    if (!timeStr) return '';
    const [hours, minutes] = timeStr.split(':');
    const hour = parseInt(hours);
    const ampm = hour >= 12 ? 'PM' : 'AM';
    const hour12 = hour % 12 || 12;
    return `${hour12}:${minutes} ${ampm}`;
}

// Format date helper
function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
        weekday: 'long',
        month: 'short',
        day: 'numeric'
    });
}

// Render itinerary
function renderItinerary(data) {
    const result = data.result || data;
    const request = data.request || {};

    const destination = result.destination || request.destination || 'Your Trip';
    const startDate = result.start_date || request.start_date;
    const endDate = result.end_date || request.end_date;
    const schedule = result.daily_schedule || [];
    const transport = result.transport_analysis;
    const budget = result.budget_breakdown;

    let html = `
        <div class="itinerary-container animate-fadeIn">
            <div class="itinerary-header">
                <h2>Your Trip to <span class="destination-gradient">${destination}</span></h2>
                <p class="meta">${formatDate(startDate)} — ${formatDate(endDate)} • ${schedule.length} days</p>
            </div>
            
            <div class="itinerary-layout">
                <div class="schedule-column">
                    ${renderDays(schedule)}
                </div>
                
                <div class="sidebar-column">
                    <div class="action-buttons">
                        <button class="btn-calendar" onclick="alert('Calendar download coming soon!')">
                            📅 Add to Calendar
                        </button>
                        <button class="btn-reset" onclick="resetPlanner()">
                            Start New Plan
                        </button>
                    </div>
                    
                    ${transport ? renderTransportWidget(transport) : ''}
                    ${budget ? renderBudgetWidget(budget) : ''}
                </div>
            </div>
        </div>
    `;

    resultSection.innerHTML = html;
}

// Render days
function renderDays(schedule) {
    if (!schedule || schedule.length === 0) {
        return '<p>No schedule available.</p>';
    }

    return schedule.map(day => `
        <div class="day-card glass-card">
            <div class="day-header">
                <div class="day-title">
                    <span class="day-badge">Day ${day.day_number}</span>
                    <span class="day-date">${formatDate(day.date)}</span>
                </div>
                ${day.weather_summary ? `<span class="weather-badge">🌤️ ${day.weather_summary}</span>` : ''}
            </div>
            
            ${day.theme ? `<h4 style="color: var(--color-purple-400); margin-bottom: 1rem;">${day.theme}</h4>` : ''}
            
            <div class="schedule-blocks">
                ${day.blocks.map(block => renderBlock(block)).join('')}
            </div>
        </div>
    `).join('');
}

// Render single block
function renderBlock(block) {
    const typeClass = block.block_type || 'activity';
    const microActivities = block.micro_activities || [];

    return `
        <div class="schedule-block ${typeClass}">
            <span class="block-time">${formatTime(block.start_time)} - ${formatTime(block.end_time)}</span>
            <h5 class="block-title">${block.title}</h5>
            <p class="block-description">${block.description}</p>
            ${microActivities.length > 0 ? `
                <div class="micro-activities">
                    ${microActivities.map(act => `
                        <span class="micro-tag">• ${typeof act === 'string' ? act : act.name}</span>
                    `).join('')}
                </div>
            ` : ''}
        </div>
    `;
}

// Render transport widget
function renderTransportWidget(transport) {
    return `
        <div class="sidebar-widget">
            <h3>🚆 Transport Recommendations</h3>
            ${transport.recommended_mode ? `
                <span class="recommended-badge">${transport.recommended_mode}</span>
                <p style="font-style: italic; color: var(--color-slate-300); font-size: 0.875rem; margin-bottom: 1rem;">
                    "${transport.reasoning}"
                </p>
            ` : ''}
            ${transport.options ? transport.options.map(opt => `
                <div class="transport-option">
                    <div class="header">
                        <span class="mode">${opt.mode.replace('_', ' ')}</span>
                        <span class="cost">${opt.cost_estimate}</span>
                    </div>
                    <p class="duration">${opt.duration_estimate}</p>
                    <p class="description">${opt.description}</p>
                </div>
            `).join('') : ''}
        </div>
    `;
}

// Render budget widget
function renderBudgetWidget(budget) {
    const categories = [
        { key: 'accommodation', label: '🏨 Accommodation' },
        { key: 'transportation', label: '🚗 Transportation' },
        { key: 'food', label: '🍽️ Food & Dining' },
        { key: 'activities', label: '🎯 Activities' },
        { key: 'miscellaneous', label: '📦 Miscellaneous' }
    ];

    const total = budget.total || {};

    return `
        <div class="sidebar-widget">
            <h3>💵 Budget Breakdown</h3>
            ${categories.map(cat => {
        const item = budget[cat.key];
        if (!item) return '';
        return `
                    <div class="budget-item">
                        <span class="label">${cat.label}</span>
                        <span class="value">${item.currency || '$'}${item.amount}</span>
                    </div>
                `;
    }).join('')}
            <div class="budget-total">
                <span class="label">Total Estimated</span>
                <span class="value">${total.currency || '$'}${total.amount}</span>
            </div>
        </div>
    `;
}

// Reset planner
function resetPlanner() {
    currentItinerary = null;
    showForm();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Make resetPlanner global
window.resetPlanner = resetPlanner;

// --- Multi-City Functions ---

function toggleTripType(type) {
    const singleBtn = document.getElementById('type-single');
    const multiBtn = document.getElementById('type-multi');
    const addBtn = document.getElementById('add-dest-btn');
    const container = document.getElementById('destinations-container');

    if (type === 'single') {
        singleBtn.classList.add('active');
        multiBtn.classList.remove('active');
        addBtn.classList.add('hidden');

        // Reset to one input
        const firstValue = container.querySelector('.destination-input')?.value || '';
        container.innerHTML = '';
        addDestinationInput(firstValue); // Add one fresh input
    } else {
        singleBtn.classList.remove('active');
        multiBtn.classList.add('active');
        addBtn.classList.remove('hidden');

        // Ensure at least one input
        if (container.children.length === 0) {
            addDestinationInput();
        }
    }
}

function addDestinationInput(value = '') {
    const container = document.getElementById('destinations-container');
    const count = container.children.length + 1;

    const row = document.createElement('div');
    row.className = 'destination-row animate-fadeIn';
    row.innerHTML = `
        <span class="input-icon">${count}</span>
        <input type="text" name="destination[]" class="destination-input" placeholder="e.g., Destination ${count}" value="${value}" required>
        ${count > 1 ? `<button type="button" class="remove-dest-btn" onclick="removeDestinationInput(this)">×</button>` : ''}
    `;

    container.appendChild(row);
    updateDestinationIcons();
}

function removeDestinationInput(btn) {
    const row = btn.parentElement;
    const container = document.getElementById('destinations-container');
    container.removeChild(row);
    updateDestinationIcons();
}

function updateDestinationIcons() {
    const container = document.getElementById('destinations-container');
    const rows = Array.from(container.children);

    rows.forEach((row, index) => {
        const icon = row.querySelector('.input-icon');
        const input = row.querySelector('.destination-input');

        // Update number
        icon.textContent = index + 1;
        input.placeholder = `e.g., Destination ${index + 1}`;

        // Reset classes
        icon.classList.remove('start', 'end', 'intermediate');

        // Apply new classes
        if (index === 0) {
            icon.classList.add('start');
            icon.title = "Start Point";
        } else if (index === rows.length - 1) {
            icon.classList.add('end');
            icon.textContent = '🏁'; // Flag for end
            icon.title = "End Point";
        } else {
            icon.classList.add('intermediate');
        }
    });
}

// Make global
window.toggleTripType = toggleTripType;
window.addDestinationInput = addDestinationInput;
window.removeDestinationInput = removeDestinationInput;
