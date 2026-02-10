/**
 * Voyagent — AI-Powered Trip Planning
 * Frontend JavaScript: form handling, API calls, itinerary rendering,
 * editing, ICS export, and share features.
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
    initializeAutocomplete();
    attachEventListeners();
});

// Autocomplete state
let activeAutocomplete = null;
let autocompleteTimeout = null;

// Initialize autocomplete for location inputs
function initializeAutocomplete() {
    // Apply to origin input
    const originInput = document.getElementById('origin');
    if (originInput) {
        setupAutocomplete(originInput);
    }

    // Apply to destination inputs (initial and dynamically added)
    document.querySelectorAll('.destination-input').forEach(input => {
        setupAutocomplete(input);
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.autocomplete-wrapper')) {
            closeAllAutocomplete();
        }
    });
}

// Setup autocomplete for a single input
function setupAutocomplete(input) {
    // Wrap input if not already wrapped
    if (!input.parentElement.classList.contains('autocomplete-wrapper')) {
        const wrapper = document.createElement('div');
        wrapper.className = 'autocomplete-wrapper';
        input.parentNode.insertBefore(wrapper, input);
        wrapper.appendChild(input);

        // Create dropdown
        const dropdown = document.createElement('div');
        dropdown.className = 'autocomplete-dropdown';
        wrapper.appendChild(dropdown);
    }

    const dropdown = input.parentElement.querySelector('.autocomplete-dropdown');

    // Input event for typing
    input.addEventListener('input', (e) => {
        const query = e.target.value.trim();

        // Clear previous timeout
        if (autocompleteTimeout) {
            clearTimeout(autocompleteTimeout);
        }

        if (query.length < 2) {
            dropdown.classList.remove('visible');
            return;
        }

        // Debounce API calls
        autocompleteTimeout = setTimeout(() => {
            fetchAutocomplete(query, dropdown, input);
        }, 300);
    });

    // Keyboard navigation
    input.addEventListener('keydown', (e) => {
        const items = dropdown.querySelectorAll('.autocomplete-item');
        const active = dropdown.querySelector('.autocomplete-item.active');
        let index = Array.from(items).indexOf(active);

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            index = Math.min(index + 1, items.length - 1);
            items.forEach((item, i) => item.classList.toggle('active', i === index));
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            index = Math.max(index - 1, 0);
            items.forEach((item, i) => item.classList.toggle('active', i === index));
        } else if (e.key === 'Enter' && active) {
            e.preventDefault();
            input.value = active.textContent;
            dropdown.classList.remove('visible');
        } else if (e.key === 'Escape') {
            dropdown.classList.remove('visible');
        }
    });

    // Focus event
    input.addEventListener('focus', () => {
        if (input.value.length >= 2 && dropdown.children.length > 0) {
            dropdown.classList.add('visible');
        }
    });
}

// Fetch autocomplete suggestions
async function fetchAutocomplete(query, dropdown, input) {
    try {
        const response = await fetch(`${API_BASE}/places/autocomplete?q=${encodeURIComponent(query)}`);
        const data = await response.json();

        if (data.predictions && data.predictions.length > 0) {
            dropdown.innerHTML = data.predictions.map((p, i) => `
                <div class="autocomplete-item${i === 0 ? ' active' : ''}" data-place-id="${p.place_id}">
                    ${p.description}
                </div>
            `).join('');

            // Add click handlers
            dropdown.querySelectorAll('.autocomplete-item').forEach(item => {
                item.addEventListener('mousedown', (e) => {
                    e.preventDefault(); // Prevent blur/focus cycle
                    input.value = item.textContent.trim();
                    dropdown.classList.remove('visible');
                    dropdown.innerHTML = ''; // Clear so focus won't re-show
                });
            });

            dropdown.classList.add('visible');
        } else {
            dropdown.classList.remove('visible');
        }
    } catch (error) {
        console.error('Autocomplete error:', error);
        dropdown.classList.remove('visible');
    }
}

// Close all autocomplete dropdowns
function closeAllAutocomplete() {
    document.querySelectorAll('.autocomplete-dropdown').forEach(d => {
        d.classList.remove('visible');
    });
}

// Form initialization
function initializeForm() {
    const today = new Date();
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const defaultEnd = new Date();
    defaultEnd.setDate(defaultEnd.getDate() + 5);

    // Initialize Flatpickr for start date
    const startPicker = flatpickr('#start_date', {
        dateFormat: 'Y-m-d',
        altInput: true,
        altFormat: 'M j, Y',
        minDate: 'today',
        defaultDate: tomorrow,
        theme: 'dark',
        disableMobile: true,
        animate: true,
        onChange: function (selectedDates, dateStr) {
            // Update end date min to be >= start date
            if (selectedDates[0]) {
                endPicker.set('minDate', selectedDates[0]);
                // If end date is before new start date, update it
                const currentEnd = endPicker.selectedDates[0];
                if (currentEnd && currentEnd < selectedDates[0]) {
                    const newEnd = new Date(selectedDates[0]);
                    newEnd.setDate(newEnd.getDate() + 1);
                    endPicker.setDate(newEnd);
                }
            }
        }
    });

    // Initialize Flatpickr for end date
    const endPicker = flatpickr('#end_date', {
        dateFormat: 'Y-m-d',
        altInput: true,
        altFormat: 'M j, Y',
        minDate: tomorrow,
        defaultDate: defaultEnd,
        theme: 'dark',
        disableMobile: true,
        animate: true
    });

    // Store pickers for access
    window.startPicker = startPicker;
    window.endPicker = endPicker;
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

// Form submission handler — uses SSE streaming for real-time progress
async function handleFormSubmit(e) {
    e.preventDefault();

    const payload = buildPayload();

    showLoading();
    resetPipelineUI();

    try {
        const response = await fetch(`${API_BASE}/itineraries/stream`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });

        if (!response.ok) {
            // Try to parse error JSON, else use status text
            let msg = 'Failed to generate itinerary';
            try {
                const errorData = await response.json();
                if (response.status === 503 || errorData.code === 'gemini_not_configured' || (errorData.message && errorData.message.includes('API key'))) {
                    msg = "Gemini API Key Missing.\n\nPlease check your server console and README.md for setup instructions.";
                } else if (response.status === 429 || errorData.code === 'gemini_quota_exhausted') {
                    msg = "AI Capacity Reached.\n\nThe Gemini AI service is currently overloaded.\nPlease wait a few moments and try again.";
                } else {
                    msg = errorData.error || errorData.detail || msg;
                }
            } catch (_) { /* ignore parse errors */ }
            throw new Error(msg);
        }

        // Read the SSE stream
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop(); // keep incomplete line in buffer

            let eventType = 'message';
            for (const line of lines) {
                if (line.startsWith('event: ')) {
                    eventType = line.slice(7).trim();
                } else if (line.startsWith('data: ')) {
                    const dataStr = line.slice(6);
                    try {
                        const data = JSON.parse(dataStr);
                        handleSSEEvent(eventType, data);
                    } catch (_) { /* skip non-JSON */ }
                    eventType = 'message'; // reset after processing
                }
                // ignore comments (lines starting with ':')
            }
        }
    } catch (error) {
        console.error('Error:', error);
        stopAgentPipeline();
        showError(error.message);
    }
}

// Handle a single SSE event
function handleSSEEvent(eventType, data) {
    if (eventType === 'progress' || data.type === 'progress') {
        updatePipelineFromSSE(data.stage, data.status, data.detail || '');
    } else if (eventType === 'result' || data.type === 'result') {
        currentItinerary = data.data;
        stopAgentPipeline();
        showResult(data.data);
    } else if (eventType === 'error' || data.type === 'error') {
        stopAgentPipeline();
        showError(data.message || 'Generation failed');
    } else if (eventType === 'done') {
        stopAgentPipeline();
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
        },
        booking_links: {
            flights: [
                { provider: 'Google Flights', url: 'https://www.google.com/travel/flights?q=flights+from+Phoenix+to+Tempe', label: 'Search flights Phoenix to Tempe' },
                { provider: 'Skyscanner', url: 'https://www.skyscanner.com/transport/flights/phoenix/tempe/', label: 'Compare on Skyscanner' }
            ],
            hotels: [
                { provider: 'Google Hotels', url: 'https://www.google.com/travel/hotels?q=hotels+in+Tempe', label: 'Hotels in Tempe' },
                { provider: 'Booking.com', url: 'https://www.booking.com/searchresults.html?ss=Tempe%2C+AZ', label: 'Hotels on Booking.com' },
                { provider: 'Google Hotels', url: 'https://www.google.com/travel/hotels?q=hotels+in+Las+Vegas', label: 'Hotels in Las Vegas' }
            ],
            trains: [],
            transport: [
                { provider: 'Rome2Rio', url: 'https://www.rome2rio.com/map/Phoenix/Tempe', label: 'All transport options to Tempe' }
            ]
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
    document.getElementById('notes').value = 'Road trip through Arizona and Nevada! Interested in desert scenery, the Grand Canyon, and Las Vegas nightlife.';

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
    errorMessage.style.whiteSpace = 'pre-wrap'; // Ensure newlines render properly
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

    const bookingLinks = result.booking_links || null;

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
                        <button class="btn-calendar" onclick="downloadICS()">
                            📅 Add to Calendar
                        </button>
                        <button class="btn-pdf" onclick="downloadPDF()">
                            📄 Download PDF
                        </button>
                        <button class="btn-share-link" onclick="copyShareLink()">
                            🔗 Share Link
                        </button>
                        <button class="btn-share" onclick="shareItinerary()">
                            📋 Copy Text
                        </button>
                        <button class="btn-reset" onclick="resetPlanner()">
                            Start New Plan
                        </button>
                    </div>
                    
                    ${bookingLinks ? renderBookingLinksWidget(bookingLinks) : ''}
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

    return schedule.map((day, dayIndex) => `
        <div class="day-card glass-card" data-day-index="${dayIndex}">
            <div class="day-header">
                <div class="day-title">
                    <span class="day-badge">Day ${day.day_number}</span>
                    <span class="day-date">${formatDate(day.date)}</span>
                </div>
                ${day.weather_summary ? `<span class="weather-badge">🌤️ ${day.weather_summary}</span>` : ''}
            </div>
            
            ${day.theme ? `<h4 style="color: var(--color-purple-400); margin-bottom: 1rem;">${day.theme}</h4>` : ''}
            
            <div class="schedule-blocks">
                ${day.blocks.map((block, blockIndex) => renderBlock(block, dayIndex, blockIndex)).join('')}
            </div>
            <div class="day-footer-actions">
                <button class="btn-add-block" onclick="openAddBlockForm(${dayIndex})">
                    <span>+</span> Add Activity
                </button>
                <button class="btn-regenerate-day" onclick="regenerateDay(${dayIndex})">
                    🔄 Regenerate Day
                </button>
            </div>
        </div>
    `).join('');
}

// Render single block
function renderBlock(block, dayIndex, blockIndex) {
    const typeClass = block.block_type || 'activity';
    const microActivities = block.micro_activities || [];

    return `
        <div class="schedule-block ${typeClass}" data-day-index="${dayIndex}" data-block-index="${blockIndex}">
            <div class="block-header-row">
                <span class="block-time">${formatTime(block.start_time)} - ${formatTime(block.end_time)}</span>
                <button class="block-swap-btn" onclick="swapBlock(${dayIndex}, ${blockIndex})" title="Swap for alternatives">
                    🔄
                </button>
                <button class="block-edit-btn" onclick="openBlockEditor(${dayIndex}, ${blockIndex})" title="Edit this block">
                    ✏️
                </button>
                <button class="block-delete-btn" onclick="deleteBlock(${dayIndex}, ${blockIndex})" title="Delete this block">
                    🗑️
                </button>
            </div>
            <h5 class="block-title">${block.title}</h5>
            <p class="block-description">
                ${block.description}
                ${block.website ? `<br><a href="${block.website}" target="_blank" class="block-link">More Info 🔗</a>` : ''}
            </p>
            <div class="micro-activities">
                ${block.is_unique ? `<span class="micro-tag unique-tag">💎 Hidden Gem</span>` : ''}
                ${block.is_limited_time ? `<span class="micro-tag limited-tag">⏳ Limited Time</span>` : ''}
                ${microActivities.map(act => `
                    <span class="micro-tag">• ${typeof act === 'string' ? act : act.name}</span>
                `).join('')}
            </div>
        </div>
    `;
}

// ========== Block Editing ==========

function openBlockEditor(dayIndex, blockIndex) {
    const result = currentItinerary.result || currentItinerary;
    const block = result.daily_schedule[dayIndex].blocks[blockIndex];

    // Remove any existing editor
    closeBlockEditor();

    const editorHtml = `
        <div class="block-editor-overlay" id="block-editor-overlay" onclick="if(event.target===this) closeBlockEditor()">
            <div class="block-editor-modal">
                <div class="editor-header">
                    <h3>✏️ Edit Block</h3>
                    <button class="editor-close-btn" onclick="closeBlockEditor()">×</button>
                </div>

                <div class="editor-fields">
                    <div class="editor-row">
                        <div class="editor-field">
                            <label>Title</label>
                            <input type="text" id="edit-title" value="${block.title || ''}">
                        </div>
                    </div>
                    <div class="editor-row">
                        <div class="editor-field">
                            <label>Start Time</label>
                            <input type="time" id="edit-start-time" value="${block.start_time || ''}">
                        </div>
                        <div class="editor-field">
                            <label>End Time</label>
                            <input type="time" id="edit-end-time" value="${block.end_time || ''}">
                        </div>
                    </div>
                    <div class="editor-row">
                        <div class="editor-field">
                            <label>Location</label>
                            <input type="text" id="edit-location" value="${block.location || ''}">
                        </div>
                        <div class="editor-field">
                            <label>Type</label>
                            <select id="edit-block-type">
                                <option value="activity" ${block.block_type === 'activity' ? 'selected' : ''}>Activity</option>
                                <option value="meal" ${block.block_type === 'meal' ? 'selected' : ''}>Meal</option>
                                <option value="travel" ${block.block_type === 'travel' ? 'selected' : ''}>Travel</option>
                                <option value="rest" ${block.block_type === 'rest' ? 'selected' : ''}>Rest</option>
                            </select>
                        </div>
                    </div>
                    <div class="editor-row">
                        <div class="editor-field full-width">
                            <label>Description</label>
                            <textarea id="edit-description" rows="2">${block.description || ''}</textarea>
                        </div>
                    </div>
                </div>

                <div class="editor-divider">
                    <span>or let AI edit for you</span>
                </div>

                <div class="editor-ai-section">
                    <div class="editor-field full-width">
                        <label>🤖 AI Instruction</label>
                        <input type="text" id="edit-ai-instruction" placeholder="e.g. Make it a lunch instead, or change to 3 PM">
                    </div>
                    <button class="btn-ai-edit" id="btn-ai-edit" onclick="aiEditBlock(${dayIndex}, ${blockIndex})">
                        ✨ AI Edit
                    </button>
                </div>

                <div class="editor-actions">
                    <button class="btn-editor-cancel" onclick="closeBlockEditor()">Cancel</button>
                    <button class="btn-editor-save" onclick="saveBlockEdit(${dayIndex}, ${blockIndex})">Save Changes</button>
                </div>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', editorHtml);
    // Focus the title field
    setTimeout(() => document.getElementById('edit-title')?.focus(), 100);
}

function closeBlockEditor() {
    const overlay = document.getElementById('block-editor-overlay');
    if (overlay) overlay.remove();
}

function saveBlockEdit(dayIndex, blockIndex) {
    const result = currentItinerary.result || currentItinerary;
    const block = result.daily_schedule[dayIndex].blocks[blockIndex];

    block.title = document.getElementById('edit-title').value;
    block.start_time = document.getElementById('edit-start-time').value;
    block.end_time = document.getElementById('edit-end-time').value;
    block.location = document.getElementById('edit-location').value;
    block.block_type = document.getElementById('edit-block-type').value;
    block.description = document.getElementById('edit-description').value;

    closeBlockEditor();
    showResult(currentItinerary);
}

async function aiEditBlock(dayIndex, blockIndex) {
    const result = currentItinerary.result || currentItinerary;
    const block = result.daily_schedule[dayIndex].blocks[blockIndex];
    const destination = result.destination || 'Unknown';
    const instruction = document.getElementById('edit-ai-instruction').value.trim();

    if (!instruction) {
        document.getElementById('edit-ai-instruction').style.borderColor = 'var(--color-rose-400)';
        document.getElementById('edit-ai-instruction').placeholder = 'Please type an instruction first...';
        return;
    }

    const btn = document.getElementById('btn-ai-edit');
    btn.disabled = true;
    btn.innerHTML = '⏳ Thinking...';

    try {
        const response = await fetch(`${API_BASE}/edit/block`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                day_index: dayIndex,
                block_index: blockIndex,
                instruction: instruction,
                current_block: {
                    start_time: block.start_time,
                    end_time: block.end_time,
                    title: block.title,
                    location: block.location || '',
                    description: block.description || '',
                    block_type: block.block_type || 'activity',
                    travel_time_mins: block.travel_time_mins || 0,
                    buffer_mins: block.buffer_mins || 0,
                    micro_activities: block.micro_activities || []
                },
                destination: destination
            })
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error || 'AI edit failed');
        }

        const data = await response.json();
        if (data.block) {
            // Apply the AI-edited block
            Object.assign(result.daily_schedule[dayIndex].blocks[blockIndex], data.block);
            closeBlockEditor();
            showResult(currentItinerary);
        } else {
            throw new Error('AI returned no block data');
        }
    } catch (error) {
        console.error('AI edit error:', error);
        btn.disabled = false;
        btn.innerHTML = '✨ AI Edit';
        alert(`AI Edit failed: ${error.message}`);
    }
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

// Render booking links widget
function renderBookingLinksWidget(links) {
    const sections = [
        { key: 'flights', icon: '✈️', title: 'Flights' },
        { key: 'hotels', icon: '🏨', title: 'Hotels' },
        { key: 'trains', icon: '🚆', title: 'Trains' },
        { key: 'transport', icon: '🗺️', title: 'Transport' },
    ];

    let linksHtml = '';
    sections.forEach(function(sec) {
        const items = links[sec.key];
        if (!items || items.length === 0) return;
        items.forEach(function(item) {
            linksHtml += '<a href="' + item.url + '" target="_blank" rel="noopener" class="booking-link-item">'
                + '<span class="booking-link-icon">' + sec.icon + '</span>'
                + '<span class="booking-link-text">'
                + '<span class="booking-link-provider">' + item.provider + '</span>'
                + '<span class="booking-link-label">' + item.label + '</span>'
                + '</span>'
                + '<span class="booking-link-arrow">→</span>'
                + '</a>';
        });
    });

    if (!linksHtml) return '';

    return '<div class="sidebar-widget booking-links-widget">'
        + '<h3>🔗 Book Now</h3>'
        + '<div class="booking-links-list">' + linksHtml + '</div>'
        + '</div>';
}

// Reset planner
function resetPlanner() {
    currentItinerary = null;
    showForm();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Make resetPlanner global
window.resetPlanner = resetPlanner;

// ========== Trip Style Presets ==========

const TRIP_PRESETS = {
    backpacker: {
        label: '🎒 Backpacker',
        description: 'Budget-friendly, hostels, street food, max adventure',
        budget: { comfort_level: 'budget', total_budget: 1500 },
        interests: ['nature', 'adventure', 'food', 'culture'],
        cuisines: ['local', 'street_food'],
        dietary: [],
        pace: 'fast',
        lodging_type: 'hostel',
        max_distance: 10,
        notes: 'Traveling on a budget! Prefer free/cheap activities, street food, and meeting other travelers.',
    },
    family: {
        label: '👨‍👩‍👧‍👦 Family',
        description: 'Kid-friendly, comfortable, safe neighborhoods',
        budget: { comfort_level: 'midrange', total_budget: 5000 },
        interests: ['culture', 'nature', 'food', 'relaxation'],
        cuisines: ['local', 'western'],
        dietary: [],
        pace: 'slow',
        lodging_type: 'apartment',
        max_distance: 5,
        notes: 'Traveling with kids. Need family-friendly activities, comfortable stays, and not too packed schedule.',
    },
    luxury: {
        label: '💎 Luxury',
        description: 'Premium hotels, fine dining, exclusive experiences',
        budget: { comfort_level: 'luxury', total_budget: 10000 },
        interests: ['culture', 'food', 'art', 'relaxation', 'shopping'],
        cuisines: ['fine_dining', 'local'],
        dietary: [],
        pace: 'slow',
        lodging_type: 'boutique',
        max_distance: 3,
        notes: 'Looking for premium experiences, Michelin-star dining, and exclusive access.',
    },
    adventure: {
        label: '🧗 Adventure',
        description: 'Outdoor thrills, hiking, extreme sports',
        budget: { comfort_level: 'midrange', total_budget: 4000 },
        interests: ['adventure', 'nature', 'food'],
        cuisines: ['local', 'street_food'],
        dietary: [],
        pace: 'fast',
        lodging_type: 'any',
        max_distance: 15,
        notes: 'Looking for adrenaline! Hiking, water sports, rock climbing, zip-lining.',
    },
    cultural: {
        label: '🏛️ Cultural',
        description: 'Museums, history, local traditions, art',
        budget: { comfort_level: 'midrange', total_budget: 4000 },
        interests: ['culture', 'history', 'art', 'food'],
        cuisines: ['local', 'fine_dining'],
        dietary: [],
        pace: 'moderate',
        lodging_type: 'hotel',
        max_distance: 5,
        notes: 'Love museums, historical sites, art galleries, and immersing in local culture.',
    },
    romantic: {
        label: '💕 Romantic',
        description: 'Couple getaway, scenic spots, intimate dining',
        budget: { comfort_level: 'luxury', total_budget: 6000 },
        interests: ['food', 'art', 'relaxation', 'culture', 'nightlife'],
        cuisines: ['fine_dining', 'local'],
        dietary: [],
        pace: 'slow',
        lodging_type: 'boutique',
        max_distance: 3,
        notes: 'Romantic getaway for two. Scenic restaurants, sunset views, cozy experiences.',
    },
};

function applyPreset(presetKey) {
    const preset = TRIP_PRESETS[presetKey];
    if (!preset) return;

    // Budget
    document.getElementById('comfort_level').value = preset.budget.comfort_level;
    document.getElementById('total_budget').value = preset.budget.total_budget;

    // Interests
    const interestsGroup = document.getElementById('interests-group');
    interestsGroup.querySelectorAll('.toggle-btn').forEach(function(btn) {
        if (preset.interests.includes(btn.dataset.value)) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    // Cuisines
    const cuisinesGroup = document.getElementById('cuisines-group');
    cuisinesGroup.querySelectorAll('.toggle-btn').forEach(function(btn) {
        if (preset.cuisines.includes(btn.dataset.value)) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    // Dietary
    const dietaryGroup = document.getElementById('dietary-group');
    dietaryGroup.querySelectorAll('.toggle-btn').forEach(function(btn) {
        if (preset.dietary.includes(btn.dataset.value)) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    // Pace
    document.getElementById('pace').value = preset.pace;

    // Lodging
    document.getElementById('lodging_type').value = preset.lodging_type;
    document.getElementById('max_distance').value = preset.max_distance;
    document.getElementById('distance-value').textContent = preset.max_distance + ' km';

    // Notes
    document.getElementById('notes').value = preset.notes;

    // Visual feedback on the preset card
    document.querySelectorAll('.preset-card').forEach(function(card) {
        card.classList.remove('selected');
    });
    var selected = document.querySelector('.preset-card[data-preset="' + presetKey + '"]');
    if (selected) selected.classList.add('selected');

    // Smooth scroll to the budget section (first changed field)
    var budgetSection = document.getElementById('comfort_level');
    if (budgetSection) {
        budgetSection.closest('.glass-card').scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

// Make global
window.applyPreset = applyPreset;

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

    // Wire up autocomplete on the new input
    const newInput = row.querySelector('.destination-input');
    if (newInput) {
        setupAutocomplete(newInput);
    }

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

// ========== ICS Calendar Download ==========

function downloadICS() {
    if (!currentItinerary) return;
    const result = currentItinerary.result || currentItinerary;
    const schedule = result.daily_schedule || [];

    let ics = [
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//Voyagent//Trip Planner//EN',
        'CALSCALE:GREGORIAN',
        'METHOD:PUBLISH',
        `X-WR-CALNAME:${result.destination || 'Trip'}`
    ];

    schedule.forEach(day => {
        const dateStr = (day.date || '').replace(/-/g, '');
        if (!dateStr) return;

        (day.blocks || []).forEach(block => {
            const startTime = (block.start_time || '09:00').replace(':', '') + '00';
            const endTime = (block.end_time || '10:00').replace(':', '') + '00';
            const uid = `${dateStr}-${startTime}-${Math.random().toString(36).substr(2, 8)}@voyagent`;

            ics.push('BEGIN:VEVENT');
            ics.push(`DTSTART:${dateStr}T${startTime}`);
            ics.push(`DTEND:${dateStr}T${endTime}`);
            ics.push(`SUMMARY:${(block.title || 'Activity').replace(/,/g, '\\,')}`);
            ics.push(`DESCRIPTION:${(block.description || '').replace(/\n/g, '\\n').replace(/,/g, '\\,')}`);
            if (block.location) {
                ics.push(`LOCATION:${block.location.replace(/,/g, '\\,')}`);
            }
            ics.push(`UID:${uid}`);
            ics.push('END:VEVENT');
        });
    });

    ics.push('END:VCALENDAR');

    const blob = new Blob([ics.join('\r\n')], { type: 'text/calendar;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `voyagent-${(result.destination || 'trip').replace(/[^a-zA-Z0-9]/g, '-').toLowerCase()}.ics`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// ========== Share / Copy Itinerary ==========

function shareItinerary() {
    if (!currentItinerary) return;
    const result = currentItinerary.result || currentItinerary;
    const schedule = result.daily_schedule || [];

    let text = `✈️ ${result.destination || 'My Trip'}\n`;
    text += `📅 ${result.start_date} → ${result.end_date}\n`;
    text += `━━━━━━━━━━━━━━━━━━━━\n\n`;

    schedule.forEach(day => {
        text += `📌 Day ${day.day_number}: ${day.theme || formatDate(day.date)}\n`;
        if (day.weather_summary) text += `   🌤️ ${day.weather_summary}\n`;
        (day.blocks || []).forEach(block => {
            const icon = block.block_type === 'meal' ? '🍽️' : block.block_type === 'travel' ? '🚗' : '📍';
            text += `   ${icon} ${block.start_time}–${block.end_time}  ${block.title}\n`;
        });
        text += `\n`;
    });

    const budget = result.budget_breakdown;
    if (budget && budget.total) {
        text += `💰 Total Budget: ${budget.total.currency || '$'}${budget.total.amount}\n`;
    }
    text += `\n— Generated by Voyagent ✨`;

    navigator.clipboard.writeText(text).then(() => {
        // Show a brief "Copied!" feedback
        const btn = document.querySelector('.btn-share');
        if (btn) {
            const original = btn.innerHTML;
            btn.innerHTML = '✅ Copied to Clipboard!';
            btn.style.background = 'linear-gradient(135deg, var(--color-emerald-500), var(--color-cyan-400))';
            setTimeout(() => {
                btn.innerHTML = original;
                btn.style.background = '';
            }, 2000);
        }
    }).catch(() => {
        // Fallback: show text in a prompt for manual copy
        prompt('Copy this itinerary:', text);
    });
}

// ========== Delete Block ==========

function deleteBlock(dayIndex, blockIndex) {
    const result = currentItinerary.result || currentItinerary;
    const block = result.daily_schedule[dayIndex].blocks[blockIndex];

    if (!confirm(`Delete "${block.title}"?`)) return;

    result.daily_schedule[dayIndex].blocks.splice(blockIndex, 1);
    showResult(currentItinerary);
}

// ========== Add New Block ==========

function openAddBlockForm(dayIndex) {
    closeBlockEditor(); // Close any existing modal

    const editorHtml = `
        <div class="block-editor-overlay" id="block-editor-overlay" onclick="if(event.target===this) closeBlockEditor()">
            <div class="block-editor-modal">
                <div class="editor-header">
                    <h3>➕ Add New Activity</h3>
                    <button class="editor-close-btn" onclick="closeBlockEditor()">×</button>
                </div>

                <div class="editor-fields">
                    <div class="editor-row">
                        <div class="editor-field">
                            <label>Title</label>
                            <input type="text" id="add-title" placeholder="e.g. Visit the Museum">
                        </div>
                    </div>
                    <div class="editor-row">
                        <div class="editor-field">
                            <label>Start Time</label>
                            <input type="time" id="add-start-time" value="10:00">
                        </div>
                        <div class="editor-field">
                            <label>End Time</label>
                            <input type="time" id="add-end-time" value="12:00">
                        </div>
                    </div>
                    <div class="editor-row">
                        <div class="editor-field">
                            <label>Location</label>
                            <input type="text" id="add-location" placeholder="e.g. Downtown">
                        </div>
                        <div class="editor-field">
                            <label>Type</label>
                            <select id="add-block-type">
                                <option value="activity" selected>Activity</option>
                                <option value="meal">Meal</option>
                                <option value="travel">Travel</option>
                                <option value="rest">Rest</option>
                            </select>
                        </div>
                    </div>
                    <div class="editor-row">
                        <div class="editor-field full-width">
                            <label>Description</label>
                            <textarea id="add-description" rows="2" placeholder="Brief description..."></textarea>
                        </div>
                    </div>
                </div>

                <div class="editor-divider">
                    <span>or use Magic Fill ✨</span>
                </div>

                <div class="editor-ai-section">
                    <div class="editor-field full-width">
                        <label>🤖 AI Instruction</label>
                        <input type="text" id="magic-fill-instruction" placeholder="e.g. Suggest a top-rated sushi place for dinner">
                    </div>
                    <button class="btn-ai-edit" id="btn-magic-fill" onclick="magicFillBlock()">
                        ✨ Auto-Fill
                    </button>
                </div>

                <div class="editor-actions">
                    <button class="btn-editor-cancel" onclick="closeBlockEditor()">Cancel</button>
                    <button class="btn-editor-save" onclick="saveNewBlock(${dayIndex})">Add to Day</button>
                </div>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', editorHtml);
    setTimeout(() => document.getElementById('add-title')?.focus(), 100);
}

async function magicFillBlock() {
    const instruction = document.getElementById('magic-fill-instruction').value.trim();
    if (!instruction) {
        document.getElementById('magic-fill-instruction').style.borderColor = 'var(--color-rose-400)';
        return;
    }

    const btn = document.getElementById('btn-magic-fill');
    btn.disabled = true;
    btn.innerHTML = '⏳ Thinking...';

    try {
        // Send a template block to the existing edit endpoint
        // effectively asking AI to "edit" a blank block into what we want
        const response = await fetch(`${API_BASE}/edit/block`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                day_index: 0,
                block_index: 0,
                instruction: instruction,
                current_block: {
                    start_time: document.getElementById('add-start-time').value || "10:00",
                    end_time: document.getElementById('add-end-time').value || "12:00",
                    title: "New Activity",
                    location: "TBD",
                    description: "TBD",
                    block_type: "activity",
                    travel_time_mins: 0,
                    buffer_mins: 0,
                    micro_activities: []
                },
                destination: (currentItinerary.result || currentItinerary).destination || 'Unknown'
            })
        });

        if (!response.ok) {
            throw new Error('Magic Fill failed');
        }

        const data = await response.json();
        if (data.block) {
            // Populate form fields
            const b = data.block;
            document.getElementById('add-title').value = b.title || '';
            document.getElementById('add-start-time').value = b.start_time || '';
            document.getElementById('add-end-time').value = b.end_time || '';
            document.getElementById('add-location').value = b.location || '';
            document.getElementById('add-block-type').value = b.block_type || 'activity';
            document.getElementById('add-description').value = b.description || '';
        }
    } catch (error) {
        console.error('Magic Fill error:', error);
        alert('Could not auto-fill. Please try again or fill manually.');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '✨ Auto-Fill';
    }
}

function saveNewBlock(dayIndex) {
    const title = document.getElementById('add-title').value.trim();
    if (!title) {
        document.getElementById('add-title').style.borderColor = 'var(--color-rose-400)';
        return;
    }

    const result = currentItinerary.result || currentItinerary;
    const newBlock = {
        title: title,
        start_time: document.getElementById('add-start-time').value,
        end_time: document.getElementById('add-end-time').value,
        location: document.getElementById('add-location').value,
        block_type: document.getElementById('add-block-type').value,
        description: document.getElementById('add-description').value,
        micro_activities: []
    };

    result.daily_schedule[dayIndex].blocks.push(newBlock);

    // Sort blocks by start_time
    result.daily_schedule[dayIndex].blocks.sort((a, b) => {
        return (a.start_time || '').localeCompare(b.start_time || '');
    });

    closeBlockEditor();
    showResult(currentItinerary);
}

// ========== PDF Download ==========

function downloadPDF() {
    window.print();
}

// Make global
window.downloadPDF = downloadPDF;

// ========== Share Link ==========

function copyShareLink() {
    if (!currentItinerary) return;
    const itineraryId = currentItinerary.itinerary_id || currentItinerary.id;
    if (!itineraryId || itineraryId === 'demo-az-123') {
        // Fallback: copy text for demo
        shareItinerary();
        return;
    }

    const shareUrl = `${window.location.origin}/share/${itineraryId}/`;
    navigator.clipboard.writeText(shareUrl).then(() => {
        const btn = document.querySelector('.btn-share-link');
        if (btn) {
            const original = btn.innerHTML;
            btn.innerHTML = '✅ Link Copied!';
            btn.style.background = 'linear-gradient(135deg, var(--color-emerald-500), var(--color-cyan-400))';
            setTimeout(() => {
                btn.innerHTML = original;
                btn.style.background = '';
            }, 2000);
        }
    }).catch(() => {
        prompt('Copy this share link:', shareUrl);
    });
}

// Make global
window.copyShareLink = copyShareLink;

// ========== Swap Block (Get Alternatives) ==========

async function swapBlock(dayIndex, blockIndex) {
    const result = currentItinerary.result || currentItinerary;
    const block = result.daily_schedule[dayIndex].blocks[blockIndex];
    const destination = result.destination || 'Unknown';

    // Show loading overlay
    const overlayHtml = `
        <div class="swap-alternatives-overlay" id="swap-overlay" onclick="if(event.target===this) closeSwapOverlay()">
            <div class="swap-alternatives-modal">
                <div class="editor-header">
                    <h3>🔄 Finding Alternatives...</h3>
                    <button class="editor-close-btn" onclick="closeSwapOverlay()">×</button>
                </div>
                <div class="swap-loading">
                    <div class="loading-spinner" style="width:3rem;height:3rem;margin:2rem auto;">
                        <div class="ring outer"></div>
                        <div class="ring inner"></div>
                        <div class="ring reverse"></div>
                        <span class="center-icon">🔄</span>
                    </div>
                    <p style="text-align:center;color:var(--color-slate-400);">Our AI is finding 3 alternatives for "<strong>${block.title}</strong>"</p>
                </div>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', overlayHtml);

    try {
        const response = await fetch(`${API_BASE}/edit/swap`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                current_block: {
                    start_time: block.start_time,
                    end_time: block.end_time,
                    title: block.title,
                    location: block.location || '',
                    description: block.description || '',
                    block_type: block.block_type || 'activity',
                },
                destination: destination,
                block_type: block.block_type || 'activity',
                day_date: result.daily_schedule[dayIndex].date || '',
                preferences: '',
            })
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error || 'Swap failed');
        }

        const data = await response.json();
        showSwapAlternatives(dayIndex, blockIndex, block, data.alternatives || []);

    } catch (error) {
        console.error('Swap error:', error);
        closeSwapOverlay();
        alert(`Swap failed: ${error.message}`);
    }
}

function showSwapAlternatives(dayIndex, blockIndex, originalBlock, alternatives) {
    const overlay = document.getElementById('swap-overlay');
    if (!overlay) return;

    const modal = overlay.querySelector('.swap-alternatives-modal');

    let cardsHtml = '';
    alternatives.forEach((alt, i) => {
        const badgeLabel = i === 0 ? '⭐ Popular' : i === 1 ? '💎 Hidden Gem' : '🎨 Creative';
        const locationHtml = alt.location ? '<span class="swap-alt-location">📍 ' + alt.location + '</span>' : '';
        const whyHtml = alt.why ? '<p class="swap-alt-why">' + alt.why + '</p>' : '';
        cardsHtml += '<div class="swap-alternative-card" onclick="pickAlternative(' + dayIndex + ',' + blockIndex + ',' + i + ')">'
            + '<div class="swap-alt-header">'
            + '<span class="swap-alt-badge">' + badgeLabel + '</span>'
            + '<span class="swap-alt-time">' + formatTime(alt.start_time) + ' - ' + formatTime(alt.end_time) + '</span>'
            + '</div>'
            + '<h4 class="swap-alt-title">' + alt.title + '</h4>'
            + '<p class="swap-alt-desc">' + alt.description + '</p>'
            + locationHtml
            + whyHtml
            + '</div>';
    });

    modal.innerHTML = '<div class="editor-header">'
        + '<h3>🔄 Pick an Alternative</h3>'
        + '<button class="editor-close-btn" onclick="closeSwapOverlay()">×</button>'
        + '</div>'
        + '<p style="color:var(--color-slate-400);font-size:0.875rem;margin-bottom:1rem;">'
        + 'Replacing: <strong style="color:white;">' + originalBlock.title + '</strong>'
        + ' (' + formatTime(originalBlock.start_time) + ' - ' + formatTime(originalBlock.end_time) + ')'
        + '</p>'
        + '<div class="swap-alternatives-list">' + cardsHtml + '</div>'
        + '<div class="editor-actions">'
        + '<button class="btn-editor-cancel" onclick="closeSwapOverlay()">Keep Original</button>'
        + '</div>';

    // Store alternatives for picking
    window._swapAlternatives = alternatives;
}

function pickAlternative(dayIndex, blockIndex, altIndex) {
    const alt = window._swapAlternatives[altIndex];
    if (!alt) return;

    const result = currentItinerary.result || currentItinerary;
    // Apply the alternative
    result.daily_schedule[dayIndex].blocks[blockIndex] = {
        ...result.daily_schedule[dayIndex].blocks[blockIndex],
        start_time: alt.start_time,
        end_time: alt.end_time,
        title: alt.title,
        location: alt.location,
        description: alt.description,
        block_type: alt.block_type,
        micro_activities: alt.micro_activities || [],
    };

    closeSwapOverlay();
    showResult(currentItinerary);
}

function closeSwapOverlay() {
    const overlay = document.getElementById('swap-overlay');
    if (overlay) overlay.remove();
    window._swapAlternatives = null;
}

// Make global
window.swapBlock = swapBlock;
window.closeSwapOverlay = closeSwapOverlay;
window.pickAlternative = pickAlternative;

// ========== Regenerate Day ==========

async function regenerateDay(dayIndex) {
    const result = currentItinerary.result || currentItinerary;
    const day = result.daily_schedule[dayIndex];
    const destination = result.destination || 'Unknown';

    if (!confirm('Regenerate the entire schedule for Day ' + (day.day_number || dayIndex + 1) + '? This will replace all current activities.')) {
        return;
    }

    // Show loading on the day card
    const dayCard = document.querySelector('[data-day-index="' + dayIndex + '"]');
    const regenBtn = dayCard?.querySelector('.btn-regenerate-day');
    if (regenBtn) {
        regenBtn.disabled = true;
        regenBtn.innerHTML = '⏳ Regenerating...';
    }

    try {
        const response = await fetch(API_BASE + '/edit/regenerate-day', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                day: {
                    date: day.date,
                    day_number: day.day_number,
                    theme: day.theme || '',
                    blocks: day.blocks || [],
                },
                destination: destination,
                weather_summary: day.weather_summary || '',
                preferences: {},
            })
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error || 'Regeneration failed');
        }

        const data = await response.json();
        if (data.day) {
            // Replace the day in the schedule
            result.daily_schedule[dayIndex] = {
                ...result.daily_schedule[dayIndex],
                theme: data.day.theme || day.theme,
                blocks: data.day.blocks || [],
            };
            showResult(currentItinerary);
        }

    } catch (error) {
        console.error('Regenerate day error:', error);
        alert('Regeneration failed: ' + error.message);
        if (regenBtn) {
            regenBtn.disabled = false;
            regenBtn.innerHTML = '🔄 Regenerate Day';
        }
    }
}

// Make global
window.regenerateDay = regenerateDay;

// ========== Agent Pipeline Progress (SSE-driven) ==========

const AGENT_PIPELINE = [
    { stage: 'research',              icon: '🔍',    label: 'Researching options...' },
    { stage: 'planner',               icon: '📋',    label: 'Planning your days...' },
    { stage: 'weather_attractions',   icon: '🌤️🏛️', label: 'Weather & attractions (parallel)...' },
    { stage: 'scheduler',             icon: '⏰',    label: 'Building schedule...' },
    { stage: 'food_validator',        icon: '🍽️✅',  label: 'Meals & validation (parallel)...' },
    { stage: 'budget',                icon: '💰',    label: 'Calculating costs...' },
    { stage: 'finalizing',            icon: '✨',    label: 'Finalizing your itinerary...' },
];

// Track which stages are done
let pipelineState = {};   // stage -> 'started' | 'done'
let pipelineInterval = null;

function resetPipelineUI() {
    pipelineState = {};
    renderPipelineUI('research', 'Preparing your trip...');
}

function startAgentPipeline() { /* no-op, driven by SSE now */ }

function stopAgentPipeline() {
    if (pipelineInterval) {
        clearInterval(pipelineInterval);
        pipelineInterval = null;
    }
}

function updatePipelineFromSSE(stage, status, detail) {
    pipelineState[stage] = status;
    const pipelineEntry = AGENT_PIPELINE.find(p => p.stage === stage);
    const label = detail || (pipelineEntry ? pipelineEntry.label : stage);
    renderPipelineUI(stage, label);
}

function renderPipelineUI(activeStage, label) {
    const loadingText = document.querySelector('.loading-text');
    if (!loadingText) return;

    const activeEntry = AGENT_PIPELINE.find(p => p.stage === activeStage);
    const icon = activeEntry ? activeEntry.icon : '⏳';

    let dotsHtml = AGENT_PIPELINE.map(a => {
        const state = pipelineState[a.stage];
        let cls = '';
        if (state === 'done') cls = 'done';
        else if (state === 'started') cls = 'active';
        return '<div class="pipeline-dot ' + cls + '" title="' + a.stage + '"><span>' + a.icon + '</span></div>';
    }).join('');

    loadingText.innerHTML = '<h3>' + icon + ' ' + label + '</h3>'
        + '<p class="agent-name">' + (activeEntry ? activeEntry.stage : activeStage) + '</p>'
        + '<div class="pipeline-progress">' + dotsHtml + '</div>';
}
