// Dropdown functionality
function toggleEntityDropdown() {
    document.getElementById('entityCategoryOptions').classList.toggle('show');
}

function toggleAllEntityCategories() {
    const checkboxes = document.querySelectorAll('#entityCategoryOptions input[type="checkbox"]:not(#toggleAllEntity)');
    const toggleAll = document.getElementById('toggleAllEntity');
    const isChecked = toggleAll.checked;

    checkboxes.forEach(checkbox => {
        checkbox.checked = isChecked;
    });

    updateSelectedEntityCategories();
}

function updateSelectedEntityCategories() {
    const checkboxes = document.querySelectorAll('#entityCategoryOptions input[type="checkbox"]:not(#toggleAllEntity)');
    const selected = Array.from(checkboxes)
        .filter(checkbox => checkbox.checked)
        .map(checkbox => checkbox.value);

    const toggleAll = document.getElementById('toggleAllEntity');
    toggleAll.checked = selected.length === checkboxes.length && checkboxes.length > 0;

    const selectedText = selected.length === 0 ?
        'No entity categories selected' :
        (selected.length === checkboxes.length ? 'All entity categories' : selected.join(', '));

    document.getElementById('selectedEntityCategories').textContent =
        `Currently selected: ${selectedText}`;
}

function toggleDropdown() {
    document.getElementById('categoryOptions').classList.toggle('show');
}

function toggleTimeDropdown() {
    document.getElementById('timeRangeOptions').classList.toggle('show');
}

// 更新时间范围显示
function updateSelectedTimeRange() {
    const selectedRadio = document.querySelector('#timeRangeOptions input[type="radio"]:checked');
    if (selectedRadio) {
        const selectedLabel = selectedRadio.nextElementSibling.textContent;
        document.querySelector('.time-range-dropdown .category-select').textContent = selectedLabel;
        document.getElementById('selectedTimeRange').textContent = `Currently selected: ${selectedLabel}`;
    }
}

// Close dropdown when clicking outside
window.onclick = function(event) {
    if (!event.target.closest('.category-dropdown')) {
        document.querySelectorAll(".category-options").forEach(dropdown => {
            dropdown.classList.remove('show');
        });
    }
}

// Toggle all categories
function toggleAllCategories() {
    const checkboxes = document.querySelectorAll('#categoryOptions input[type="checkbox"]:not(#toggleAll)');
    const toggleAll = document.getElementById('toggleAll');
    const isChecked = toggleAll.checked;

    checkboxes.forEach(checkbox => {
        checkbox.checked = isChecked;
    });

    updateSelectedCategories();
}

function updateSelectedCategories() {
    const checkboxes = document.querySelectorAll('#categoryOptions input[type="checkbox"]:not(#toggleAll)');
    const selected = Array.from(checkboxes)
        .filter(checkbox => checkbox.checked)
        .map(checkbox => checkbox.value);

    const toggleAll = document.getElementById('toggleAll');
    toggleAll.checked = selected.length === checkboxes.length && checkboxes.length > 0;

    const selectedText = selected.length === 0 ?
        'No categories selected' :
        (selected.length === checkboxes.length ? 'All categories' : selected.join(', '));

    document.getElementById('selectedCategories').textContent =
        `Currently selected: ${selectedText}`;
}

// Initialize event listeners
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('#categoryOptions input[type="checkbox"]').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            if (this.id !== 'toggleAll') {
                updateSelectedCategories();
            }
        });
    });
    document.querySelectorAll('#entityCategoryOptions input[type="checkbox"]').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            if (this.id !== 'toggleAllEntity') {
                updateSelectedEntityCategories();
            }
        });
    });
    document.querySelectorAll('#timeRangeOptions input[type="radio"]').forEach(radio => {
        radio.addEventListener('change', updateSelectedTimeRange);
    });
    const entityRadios = document.querySelectorAll('input[name="entity_count"]');
    entityRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            if (this.value === 'one') {
                document.getElementById('oneEntityContent').style.display = 'block';
                document.getElementById('twoEntityContent').style.display = 'none';
            } else if (this.value === 'two') {
                document.getElementById('oneEntityContent').style.display = 'none';
                document.getElementById('twoEntityContent').style.display = 'block';
            }
        });
    });
});


// Add styling for path elements
document.addEventListener('DOMContentLoaded', function () {
    // Mermaid check
    if (typeof mermaid !== 'undefined') {
        mermaid.initialize({
            startOnLoad: false,  // IMPORTANT: we'll call render manually
            theme: 'default',
            flowchart: {
                useMaxWidth: false,
                htmlLabels: true,
                curve: 'basis'
            }
        });

        // Manually render Mermaid diagrams
        const diagrams = document.querySelectorAll('.mermaid');
        diagrams.forEach((el, index) => {
            const originalCode = el.textContent;
            const id = `mermaid-${index}`;
            el.id = id;
            mermaid.render(id, originalCode, (svgCode) => {
                el.innerHTML = svgCode;
            });
        });
    }

    // Mermaid styles for nodes and relations — safe to keep
    document.querySelectorAll('.node').forEach(node => {
        node.style.color = '#3498db';
        node.style.fontWeight = '500';
    });

    document.querySelectorAll('.relation').forEach(rel => {
        rel.style.color = '#e74c3c';
        rel.style.fontStyle = 'italic';
    });
});

document.addEventListener('DOMContentLoaded', function() {
    // 摘要展开/折叠
    const summaryToggle = document.getElementById('toggleSummary');
    const summaryContent = document.getElementById('summaryContent');

    if (summaryToggle && summaryContent) {
        summaryToggle.addEventListener('click', function() {
            summaryContent.classList.toggle('collapsed');
            summaryContent.classList.toggle('expanded');
            this.textContent = summaryContent.classList.contains('collapsed') ? 'Read More' : 'Read Less';
        });
    }

    // 新闻展开/折叠
    const newsToggle = document.getElementById('toggleNews');
    const newsContent = document.getElementById('newsContent');

    if (newsToggle && newsContent) {
        newsToggle.addEventListener('click', function() {
            newsContent.classList.toggle('collapsed');
            newsContent.classList.toggle('expanded');
            this.textContent = newsContent.classList.contains('collapsed') ? 'Read More' : 'Read Less';
        });
    }
});



// Add click handler for graph section
document.querySelector('.graph-section').addEventListener('click', function() {
  document.getElementById('graphModal').style.display = 'block';
  // Re-render mermaid in modal to ensure proper sizing
  mermaid.init(undefined, '.modal-mermaid');
});

// Close modal when clicking X
document.querySelector('.modal-close').addEventListener('click', function() {
  document.getElementById('graphModal').style.display = 'none';
});

// Close modal when clicking outside content
window.addEventListener('click', function(event) {
  if (event.target == document.getElementById('graphModal')) {
    document.getElementById('graphModal').style.display = 'none';
  }
});


