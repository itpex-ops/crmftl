// enquiry.js

document.addEventListener("DOMContentLoaded", function () {

    // ================= MOBILE VALIDATION =================
    const customerContact = document.querySelector("input[name='customer_contact']");
    if (customerContact) {
        customerContact.addEventListener("input", function () {
            this.value = this.value.replace(/[^0-9]/g, '').slice(0, 10);
        });
    }

    const pinInputs = document.querySelectorAll("input[name='origin_pin'], input[name='destination_pin']");
    pinInputs.forEach(input => {
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
            <div class="row g-3 mb-2 shadow-sm p-2 rounded bg-light">
                <div class="col-md-6">
                    <input name="${type}[]" class="form-control" placeholder="${type.charAt(0).toUpperCase() + type.slice(1)} ${i + 1}">
                </div>
                <div class="col-md-6">
                    <input name="${type}_pin[]" class="form-control" placeholder="PIN Code">
                </div>
            </div>`;
        }
        container.innerHTML = html;
    }

    // Initialize on page load if there is a value
    if (pickupInput) {
        generateFields(originContainer, parseInt(pickupInput.value) || 1, 'origin');
        pickupInput.addEventListener("input", function () {
            generateFields(originContainer, parseInt(this.value) || 1, 'origin');
        });
    }

    if (deliveryInput) {
        generateFields(destinationContainer, parseInt(deliveryInput.value) || 1, 'destination');
        deliveryInput.addEventListener("input", function () {
            generateFields(destinationContainer, parseInt(this.value) || 1, 'destination');
        });
    }

});