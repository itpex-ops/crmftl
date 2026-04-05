// enquiry.js

// ================= MOBILE VALIDATION =================
document.querySelector("input[name='customer_contact']")
    .addEventListener("input", function () {
        this.value = this.value.replace(/[^0-9]/g, '').slice(0, 10);
    });

document.querySelectorAll("input[name='origin_pin'], input[name='destination_pin']")
    .forEach(input => {
        input.addEventListener("input", function () {
            this.value = this.value.replace(/[^0-9]/g, '').slice(0, 6);
        });
    });

// ================= AUTO HIDE ALERTS =================
setTimeout(() => {
    document.querySelectorAll('.alert').forEach(el => el.style.display = 'none');
}, 3000);

// ================= DYNAMIC ORIGIN/DESTINATION =================
const pickupInput = document.getElementById("pickups");
const deliveryInput = document.getElementById("deliveries");
const originContainer = document.getElementById("origin-container");
const destinationContainer = document.getElementById("destination-container");

function generateFields(container, count, type) {
    let html = `<h6 class="text-${type === 'origin' ? 'primary' : 'success'}">${type.charAt(0).toUpperCase() + type.slice(1)}s</h6>`;
    for (let i = 0; i < count; i++) {
        html += `
        <div class="row g-3 mb-2">
            <div class="col-md-4">
                <input name="${type}[]" class="form-control" placeholder="${type.charAt(0).toUpperCase() + type.slice(1)} ${i + 1}">
            </div>
            <div class="col-md-4">
                <input name="${type}_pin[]" class="form-control" placeholder="PIN Code">
            </div>
        </div>`;
    }
    container.innerHTML = html;
}

pickupInput.addEventListener("input", function () {
    generateFields(originContainer, parseInt(this.value) || 1, 'origin');
});

deliveryInput.addEventListener("input", function () {
    generateFields(destinationContainer, parseInt(this.value) || 1, 'destination');
});