// ======================================
// IMAGINE SHELTER
// script.js
// Part 1
// ======================================

// DOM ELEMENTS

const ventText = document.getElementById("ventText");
const submitBtn = document.getElementById("submitBtn");
const charCount = document.getElementById("charCount");

const ventFeed = document.getElementById("ventFeed");

const durationSelect = document.getElementById("durationSelect");

const dynamicPriceDisplay =
document.getElementById("dynamicPriceDisplay");

const bookingConfirmation =
document.getElementById("bookingConfirmation");

const roomLink =
document.getElementById("roomLink");

const slotsGrid =
document.getElementById("slotsGrid");

const menuToggle = document.getElementById("menuToggle");
const navLinks = document.querySelector(".nav-links");

// ======================================
// PAYMENT MODAL
// ======================================

const paymentModal = document.getElementById("paymentModal");

const closePaymentModalBtn = document.getElementById("closePaymentModal");

const confirmBookingBtn = document.getElementById("confirmBookingBtn");

const copyUpiBtn = document.getElementById("copyUpiBtn");

const upiIdInput = document.getElementById("upiId");

const customerEmail = document.getElementById("customerEmail");

const customerPhone = document.getElementById("customerPhone");

const utrNumber = document.getElementById("utrNumber");

let currentBooking = {
    slotId: null
};

closePaymentModalBtn.addEventListener("click", () => {
    closePaymentModal();
});

// ======================================
// TOAST NOTIFICATIONS
// ======================================

const toast = document.getElementById("toast");

function showToast(message, type = "success") {

    if (!toast) return;

    toast.textContent = message;

    toast.className = `toast ${type} show`;

    setTimeout(() => {

        toast.classList.remove("show");

    }, 3000);

}


// ======================================
// CHARACTER COUNTER
// ======================================

if (ventText) {

    ventText.addEventListener("input", () => {

        charCount.textContent =
        `${ventText.value.length} / 1000`;

    });

}


// ======================================
// COUNTRY DETECTION
// ======================================

let userCountry = "IN";

let currency = "₹";

let bookingInProgress = false;

const pricing = {

    IN: {

        currency: "₹",

        15:49,

        30:149,

        60:299

    },

    US:{

        currency:"$",

        15:5,

        30:10,

        60:18

    },

    DEFAULT:{

        currency:"₹",

        15:49,

        30:149,

        60:299

    }

};

async function detectCountry(){

    try{

        const response = await fetch(
            "https://ipapi.co/json/"
        );

        const data = await response.json();

        if(pricing[data.country_code]){

            userCountry=data.country_code;

        }

    }

    catch{

        userCountry="IN";

    }

    updatePrice();

}


// ======================================
// PRICE UPDATE
// ======================================

function updatePrice(){

    if(!durationSelect || !dynamicPriceDisplay){
        return;
    }

    const duration = durationSelect.value;

    const plan = pricing[userCountry] || pricing.DEFAULT;

    currency = plan.currency;

    dynamicPriceDisplay.textContent =
        currency + plan[duration];

}


if(durationSelect){

    durationSelect.addEventListener(

        "change",

        updatePrice

    );

}

// ======================================
// SUBMIT A STORY
// ======================================

async function submitStory() {

    const message = ventText.value.trim();

    if (message.length === 0) {

        showToast("Please write something first.","error");

        return;

    }

    submitBtn.disabled = true;

    submitBtn.textContent = "Sharing...";

    try {

        const response = await fetch("/api/vents", {

            method: "POST",

            headers: {

                "Content-Type": "application/json"

            },

            body: JSON.stringify({

                content: message

            })

        });

        const data = await response.json();

        if (data.status === "success") {

            ventText.value = "";

            charCount.textContent = "0 / 1000";

            showToast(
    "🤍 Your story has been shared anonymously.",
    "success"
);

            loadStories();

        }

        else {

            showToast(data.error || "Something went wrong.","error");

        }

    }

    catch (error) {

        console.error(error);

        bookingInProgress = false;

        showToast(
    "Unable to connect to the server.",
    "error"
);

    }

    submitBtn.disabled = false;

    submitBtn.textContent = "Release Into The Universe";

}

if (submitBtn) {

    submitBtn.addEventListener("click", submitStory);

}


// ======================================
// OPEN PAYMENT MODAL
// ======================================

function openPaymentModal(slotId){

    currentBooking.slotId = slotId;
    
    paymentModal.classList.remove("hidden");

}


// ======================================
// CLOSE PAYMENT MODAL
// ======================================

function closePaymentModal(){

    paymentModal.classList.add("hidden");

}

// ======================================
// CONFIRM BOOKING
// ======================================

confirmBookingBtn.addEventListener("click", async () => {

    const email = customerEmail.value.trim();
    const phone = customerPhone.value.trim();
    const utr = utrNumber.value.trim();

    if (!email || !phone || !utr) {
        showToast("Please fill in all the fields.", "error");
        return;
    }

    try {

        const response = await fetch("/api/book-session", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({

                slot_id: currentBooking.slotId,
                email: email,
                phone: phone,
                utr: utr

            })

        });

        const data = await response.json();

        if (data.error) {

            showToast(data.error, "error");
            return;

        }

        showToast(
            "🤍 Booking received! We'll verify your payment shortly.",
            "success"
        );

        closePaymentModal();

        customerEmail.value = "";
        customerPhone.value = "";
        utrNumber.value = "";

        loadSlots();

    }
    catch (err) {

        console.error(err);

        showToast(
            "Something went wrong. Please try again.",
            "error"
        );

    }

});


// ======================================
// LOAD STORIES
// ======================================

async function loadStories() {

    if (!ventFeed) return;

    ventFeed.innerHTML =

    `<div class="loading-card">
    
    
    
             <div class="loading-card">

    🌿 Gathering stories...

        </div>
    
    
    
    
    </div>`;

    try {

        const response = await fetch("/api/vents");

        const stories = await response.json();

        if (!stories.length) {

            ventFeed.innerHTML = `

<div class="loading-card">

    <h3>🌿 Nothing has been shared yet</h3>

    <p>

        The first step is often the hardest.

        Your story could remind someone

        they're not alone.

    </p>

</div>

`;

            return;

        }

        ventFeed.innerHTML = "";

        stories.forEach(story => {

            const card = document.createElement("div");

            card.className = "story-card";

            card.innerHTML = `

    <div class="story-header">

        🤍 Anonymous

    </div>

    <p class="story-text">

        ${story.content}

    </p>

    <div class="story-footer">

        Shared safely with Imagine Shelter

    </div>

`;
            ventFeed.appendChild(card);

        });

    }

    catch (error) {

        console.error(error);

       ventFeed.innerHTML = `

<div class="loading-card">

    <h3>Connection Lost</h3>

    <p>

        We couldn't reach the shelter right now.

        Please try again in a moment.

    </p>

</div>

`;

    }

}

// ======================================
// START WEBSITE
// ======================================

document.addEventListener("DOMContentLoaded", () => {

    if(durationSelect){
        detectCountry();
    }

    if(ventFeed){
        loadStories();
    }

    if(slotsGrid){
        loadSlots();
    }

});

 // ======================================
// LOAD AVAILABLE SLOTS
// ======================================

async function loadSlots() {

    slotsGrid.innerHTML =

    `<div class="loading-card">

          🌿 Looking for available sessions...

    </div>`;

    try {

        const response = await fetch("/api/slots");

        const slots = await response.json();

        const availableSlots = slots.filter(
    slot => slot.status !== "booked"
);

        slotsGrid.innerHTML = "";

             if (availableSlots.length === 0) {

    slotsGrid.innerHTML = `

    <div class="loading-card">

        <h3>🤍 All sessions are currently booked</h3>

        <p>

            Thank you for your patience.

            New listening sessions are added regularly.

            Please check back soon.

        </p>

    </div>

    `;

    return;

}

        slots.forEach(slot => {

            const card = document.createElement("div");

            card.className = "slot-card";

            if(slot.status === "booked"){

                card.classList.add("booked");

            }

            card.innerHTML = `

                <h3>${slot.date}</h3>

                <p>${slot.time}</p>

                <span>

                    ${slot.status}

                </span>

            `;

            if(slot.status !== "booked"){

                card.addEventListener(

                    "click",

                    ()=>openPaymentModal(slot.id)

                );

            }

            slotsGrid.appendChild(card);

        });

    }

    catch(error){

        console.error(error);

           slotsGrid.innerHTML = `

<div class="loading-card">

    <h3>Unable to reach our schedule</h3>

    <p>

        Please refresh the page

        or try again in a moment.

    </p>

</div>

`;

    }

}


// ======================================
// MOBILE MENU
// ======================================

if(menuToggle && navLinks){

    menuToggle.addEventListener("click", ()=>{

        navLinks.classList.toggle("show");

        if(navLinks.classList.contains("show")){

            menuToggle.textContent = "✕";

        }

        else{

            menuToggle.textContent = "☰";

        }

    });

}

