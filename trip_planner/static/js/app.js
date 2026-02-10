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

// Form submission handler
async function handleFormSubmit(e) {
    e.preventDefault();

    const payload = buildPayload();

    showLoading();
    startAgentPipeline();

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

            // Handle Quota Exhaustion (429)
            if (response.status === 429 || errorData.code === 'gemini_quota_exhausted') {
                throw new Error("🚫 AI Capacity Reached.\n\nThe Gemini AI service is currently overloaded (Quota Exhausted).\nPlease wait a few moments and try again.");
            }

            throw new Error(errorData.error || errorData.detail || 'Failed to generate itinerary');
        }

        const data = await response.json();
        currentItinerary = data;
        stopAgentPipeline();
        showResult(data);

    } catch (error) {
        console.error('Error:', error);
        stopAgentPipeline();
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
                        <button class="btn-share" onclick="shareItinerary()">
                            📋 Copy & Share
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
            <button class="btn-add-block" onclick="openAddBlockForm(${dayIndex})">
                <span>+</span> Add Activity
            </button>
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

// ========== Agent Pipeline Progress ==========

const AGENT_PIPELINE = [
    { name: 'ResearchAgent', icon: '🔍', label: 'Researching options...' },
    { name: 'PlannerAgent', icon: '📋', label: 'Planning your days...' },
    { name: 'WeatherAgent', icon: '🌤️', label: 'Checking weather...' },
    { name: 'AttractionsAgent', icon: '🏛️', label: 'Finding attractions...' },
    { name: 'SchedulerAgent', icon: '⏰', label: 'Building schedule...' },
    { name: 'FoodAgent', icon: '🍽️', label: 'Planning meals...' },
    { name: 'BudgetAgent', icon: '💰', label: 'Calculating costs...' },
    { name: 'ValidatorAgent', icon: '✅', label: 'Validating plan...' },
];

let pipelineInterval = null;
let pipelineStep = 0;

function startAgentPipeline() {
    pipelineStep = 0;
    updatePipelineUI();
    pipelineInterval = setInterval(() => {
        pipelineStep++;
        if (pipelineStep < AGENT_PIPELINE.length) {
            updatePipelineUI();
        } else {
            // Loop back slowly or stay on last
            clearInterval(pipelineInterval);
        }
    }, 3500); // Each agent "works" for ~3.5 seconds
}

function stopAgentPipeline() {
    if (pipelineInterval) {
        clearInterval(pipelineInterval);
        pipelineInterval = null;
    }
}

function updatePipelineUI() {
    const loadingText = document.querySelector('.loading-text');
    if (!loadingText) return;

    const agent = AGENT_PIPELINE[pipelineStep];
    if (!agent) return;

    loadingText.innerHTML = `
        <h3>${agent.icon} ${agent.label}</h3>
        <p class="agent-name">${agent.name}</p>
        <div class="pipeline-progress">
            ${AGENT_PIPELINE.map((a, i) => `
                <div class="pipeline-dot ${i < pipelineStep ? 'done' : ''} ${i === pipelineStep ? 'active' : ''}" title="${a.name}">
                    <span>${a.icon}</span>
                </div>
            `).join('')}
        </div>
    `;
}
