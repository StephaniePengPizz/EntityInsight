// Dropdown functionality
function toggleDropdown() {
    document.getElementById('categoryOptions').classList.toggle('show');
}

// Close dropdown when clicking outside
window.onclick = function(event) {
    if (!event.target.matches('.category-select') && !event.target.matches('.category-option *')) {
        var dropdowns = document.getElementsByClassName("category-options");
        for (var i = 0; i < dropdowns.length; i++) {
            var openDropdown = dropdowns[i];
            if (openDropdown.classList.contains('show')) {
                openDropdown.classList.remove('show');
            }
        }
    }
}

// Toggle all categories
function toggleAllCategories() {
    const checkboxes = document.querySelectorAll('.category-options input[type="checkbox"]:not(#toggleAll)');
    const toggleAll = document.getElementById('toggleAll');
    const isChecked = toggleAll.checked;

    checkboxes.forEach(checkbox => {
        checkbox.checked = isChecked;
    });

    updateSelectedCategories();
}

// Update selected categories display
function updateSelectedCategories() {
    const checkboxes = document.querySelectorAll('.category-options input[type="checkbox"]:not(#toggleAll)');
    const selected = Array.from(checkboxes)
        .filter(checkbox => checkbox.checked)
        .map(checkbox => checkbox.value);

    const toggleAll = document.getElementById('toggleAll');
    toggleAll.checked = selected.length === checkboxes.length;

    const selectedText = selected.length === checkboxes.length ?
        'All categories' :
        selected.join(', ');

    document.getElementById('selectedCategories').textContent =
        `Currently selected: ${selectedText}`;
}

// Initialize event listeners
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.category-options input[type="checkbox"]').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            if (this.id !== 'toggleAll') {
                updateSelectedCategories();
            }
        });
    });

    // Initialize Mermaid if on results page
    if (typeof mermaid !== 'undefined') {
        mermaid.initialize({
            startOnLoad: true,
            theme: 'default',
            flowchart: {
                useMaxWidth: false,
                htmlLabels: true,
                curve: 'basis'
            }
        });
    }
});


// Add styling for path elements
document.querySelectorAll('.node').forEach(node => {
        node.style.color = '#3498db';
        node.style.fontWeight = '500';
    });

document.querySelectorAll('.relation').forEach(rel => {
    rel.style.color = '#e74c3c';
    rel.style.fontStyle = 'italic';
});