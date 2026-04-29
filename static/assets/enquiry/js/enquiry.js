// enquiry.js

document.addEventListener("DOMContentLoaded", function () {

    // ================= AUTO HIDE ALERTS =================
    setTimeout(() => {
        document.querySelectorAll('.alert').forEach(el => el.style.display = 'none');
    }, 3000);


    // ================= GLOBAL INPUT VALIDATION (WORKS FOR DYNAMIC FIELDS) =================
    document.addEventListener("input", function (e) {

        if (
            e.target.name === "origin_pin[]" ||
            e.target.name === "destination_pin[]"
        ) {
            let value = e.target.value;

            // Remove non-digits
            value = value.replace(/\D/g, '');

            // Trim to 6 digits
            if (value.length > 6) {
                value = value.substring(0, 6);
            }

            e.target.value = value;
        }

    });
    document.addEventListener("paste", function (e) {
        if (
            e.target.name === "origin_pin[]" ||
            e.target.name === "destination_pin[]"
        ) {
            let pasteData = (e.clipboardData || window.clipboardData).getData('text');

            if (!/^\d{1,6}$/.test(pasteData)) {
                e.preventDefault();
            }
        }
    });


    // ================= DYNAMIC ORIGIN/DESTINATION =================
    const pickupInput = document.getElementById("pickups");
    const deliveryInput = document.getElementById("deliveries");
    const originContainer = document.getElementById("origin-container");
    const destinationContainer = document.getElementById("destination-container");


    function generateFields(container, count, type) {

        let html = `
            <h6 class="text-${type === 'origin' ? 'primary' : 'success'}">
                ${type.charAt(0).toUpperCase() + type.slice(1)}s
            </h6>
        `;

        for (let i = 0; i < count; i++) {
            html += `
            <div class="row g-3 mb-2 shadow-sm p-2 rounded bg-light">
                
                <div class="col-md-6">
                    <input 
                        name="${type}[]" 
                        class="form-control" 
                        placeholder="${type.charAt(0).toUpperCase() + type.slice(1)} ${i + 1}"
                    >
                </div>

                <div class="col-md-6">
                    <input 
                        name="${type}_pin[]" 
                        class="form-control" 
                        placeholder="PIN Code"
                        maxlength="6"
                    >
                </div>

            </div>`;
        }

        container.innerHTML = html;
    }


    // ================= INITIAL LOAD =================
    if (pickupInput && originContainer) {
        generateFields(originContainer, parseInt(pickupInput.value) || 1, 'origin');

        pickupInput.addEventListener("input", function () {
            generateFields(originContainer, parseInt(this.value) || 1, 'origin');
        });
    }

    if (deliveryInput && destinationContainer) {
        generateFields(destinationContainer, parseInt(deliveryInput.value) || 1, 'destination');

        deliveryInput.addEventListener("input", function () {
            generateFields(destinationContainer, parseInt(this.value) || 1, 'destination');
        });
    }

});


document.addEventListener("DOMContentLoaded", function () {

    document.querySelectorAll('input[type="text"]').forEach(function (input) {

        input.addEventListener("input", function () {
            this.value = this.value.toUpperCase();
        });

    });

});

