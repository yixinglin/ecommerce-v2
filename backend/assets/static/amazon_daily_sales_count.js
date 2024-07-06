// Add click event listener to Purchase Date labels
document.querySelectorAll('.tree label').forEach(function(label) {
label.addEventListener('click', function() {
  var ul = label.nextElementSibling;
  ul.style.display = ul.style.display === 'none' ? 'block' : 'none';
});
});

// Add event listener for Expand All button
document.getElementById('expandAll').addEventListener('click', function() {
document.querySelectorAll('.tree label ~ ul').forEach(function(ul) {
  ul.style.display = 'block';
});
});

// Add event listener for Collapse All button
document.getElementById('collapseAll').addEventListener('click', function() {
document.querySelectorAll('.tree label ~ ul').forEach(function(ul) {
  ul.style.display = 'none';
});
});