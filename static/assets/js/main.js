"use strict"

// Overlay Scripts
let overlayElem = document.querySelector('.overlay');

// Bootstrap Triggers
let tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
let tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
});

// =======================
// Cart Scripts
// =======================

let additionCountBtn = document.querySelectorAll('.addition');
let decreaseCountBtn = document.querySelectorAll('.decrease');
let cartParentDiv = document.querySelector('.cartParent');
let noProductInCartElem = document.querySelector('.noProductInCart');
let countOfProductsSpan = document.querySelector('.countOfProducts');

// Increase Count
additionCountBtn.forEach(function (additionBtn) {

    let countOfProductSpan = additionBtn.nextElementSibling;
    let decreaseBtnNext = countOfProductSpan ? countOfProductSpan.nextElementSibling : null;

    if (!countOfProductSpan || !decreaseBtnNext) return;

    additionBtn.addEventListener('click', function () {

        if (parseInt(countOfProductSpan.innerHTML) > 0 &&
            decreaseBtnNext.children.length > 0) {

            decreaseBtnNext.children[0].className = 'fas fa-minus';
        }

        countOfProductSpan.innerHTML++;
    });

});


// Decrease Count
decreaseCountBtn.forEach(function (decreaseBtn) {

    let countOfProductSpan = decreaseBtn.previousElementSibling;
    let countOfProductIcon = decreaseBtn.children[0];
    let decreaseCountBtnParent = decreaseBtn.parentElement?.parentElement?.parentElement;

    if (!countOfProductSpan || !countOfProductIcon || !decreaseCountBtnParent) return;

    decreaseBtn.addEventListener('click', function () {

        countOfProductSpan.innerHTML--;

        if (parseInt(countOfProductSpan.innerHTML) < 2) {
            countOfProductIcon.className = 'far fa-trash-alt';
            countOfProductSpan.innerHTML = 1;
        }

    });

    countOfProductIcon.addEventListener('click', function () {

        if (parseInt(countOfProductSpan.innerHTML) <= 1) {

            decreaseCountBtnParent.remove();

            if (countOfProductsSpan) {
                countOfProductsSpan.innerHTML--;
            }

        }

        if (
            cartParentDiv &&
            noProductInCartElem &&
            cartParentDiv.children.length < 2
        ) {
            noProductInCartElem.style.display = 'block';
        }

    });

});


// =======================
// Widget Scripts
// =======================

let openChatBoxBtnElem = document.querySelector('.openChatBoxBtn');
let chatWidgetBoxElem = document.querySelector('.chat-widget-box');
let closeChatWidgetBoxBtnElem = document.querySelector('.closeChatWidgetBoxBtn');
let WriteMsgInputElem = document.querySelector('.WriteMsgInput');
let chatBodyWrapperElem = document.querySelector('.ChatBodyWrapper');
let sendChatToCardBodyBtnElem = document.querySelector('.sendChatToCardBodyBtn');
let chatInfoBox = document.querySelector('.chat-info');
let chatSendFileElem = document.querySelector('.chatSendFile');
let sendFileToChatWrapperElem = document.querySelector('.send-file-to-chat-box');
let fileInputGetterElem = document.querySelector('#fileInputGetter');
let selectFileNameElem = document.querySelector('#fileName');
let sendFileBtnElem = document.querySelector('#sendFileBtn');
let closeSendFileBoxBtn = document.querySelector('#closeSendFileBoxBtn');

if (closeSendFileBoxBtn && sendFileToChatWrapperElem) {
    closeSendFileBoxBtn.addEventListener('click', function () {
        sendFileToChatWrapperElem.classList.add('d-none');
    });
}

if (fileInputGetterElem && selectFileNameElem && sendFileBtnElem) {
    fileInputGetterElem.addEventListener('change', function () {

        if (fileInputGetterElem.files.length > 0) {

            selectFileNameElem.innerHTML = fileInputGetterElem.files[0].name;
            selectFileNameElem.lang = 'en';
            sendFileBtnElem.classList.remove('d-none');

        }

    });
}

if (openChatBoxBtnElem && chatWidgetBoxElem) {
    openChatBoxBtnElem.addEventListener('click', function () {
        chatWidgetBoxElem.classList.add('showElem');
    });
}

if (closeChatWidgetBoxBtnElem && chatWidgetBoxElem) {
    closeChatWidgetBoxBtnElem.addEventListener('click', function () {
        chatWidgetBoxElem.classList.remove('showElem');
    });
}

if (WriteMsgInputElem && chatInfoBox) {

    WriteMsgInputElem.addEventListener('keyup', function (e) {

        if (WriteMsgInputElem.value && e.which === 13) {

            messageGenerator();
            chatInfoBox.classList.add('hidden');

        }

    });

}

if (sendChatToCardBodyBtnElem && WriteMsgInputElem && chatInfoBox) {

    sendChatToCardBodyBtnElem.addEventListener('click', function () {

        if (WriteMsgInputElem.value) {

            messageGenerator();
            chatInfoBox.classList.add('hidden');

        }

    });

}

if (chatSendFileElem && sendFileToChatWrapperElem) {

    chatSendFileElem.addEventListener('click', function () {

        sendFileToChatWrapperElem.classList.remove('d-none');

    });

}
if (WriteMsgInputElem && chatInfoBox) {
    WriteMsgInputElem.addEventListener('keyup', function (e) {
        if (WriteMsgInputElem.value && e.which === 13) {
            messageGenerator();
            chatInfoBox.classList.add('hidden');
        }
    });
}

if (sendChatToCardBodyBtnElem && WriteMsgInputElem && chatInfoBox) {
    sendChatToCardBodyBtnElem.addEventListener('click', function () {
        if (WriteMsgInputElem.value) {
            messageGenerator();
            chatInfoBox.classList.add('hidden');
        }
    });
}

if (chatSendFileElem && sendFileToChatWrapperElem) {
    chatSendFileElem.addEventListener('click', function () {
        sendFileToChatWrapperElem.classList.remove('d-none');
    });
}

function messageGenerator() {

    if (!chatBodyWrapperElem || !WriteMsgInputElem) return;

    let chatWrapper = document.createElement('div');
    chatWrapper.className = 'chat-widget-msg mb-4 customer-msg float-start';

    let chatText = document.createElement('p');
    chatText.className = 'py-2 px-3 border-radius-3-1-br';
    chatText.innerText = WriteMsgInputElem.value;

    let breakRowElem = document.createElement('div');
    breakRowElem.className = 'clearfix';

    chatWrapper.appendChild(chatText);

    let chatResponseWrapper = document.createElement('div');
    chatResponseWrapper.className = 'chat-widget-msg mb-4 operator-msg float-end';

    let chatResponseText = document.createElement('p');
    chatResponseText.className = 'py-2 px-3 border-radius-3-1-bl';
    chatResponseText.innerText = "پاسخ آزمایشی از سرور";

    let breakRowResponseElem = document.createElement('div');
    breakRowResponseElem.className = 'clearfix';

    chatResponseWrapper.appendChild(chatResponseText);

    chatBodyWrapperElem.append(chatWrapper, breakRowElem);
    chatBodyWrapperElem.append(chatResponseWrapper, breakRowResponseElem);

    WriteMsgInputElem.value = '';
}


// ======================
// Navbar In Mobile Scripts
// ======================

let navbarOpenBtnElem = document.querySelector('.openNavbarBtn');
let navbarCloseBtnElem = document.querySelector('.navbar-items-mobile-close-btn');
let navbarItemMobileELem = document.querySelector('.navbar-items-mobile');
let navbarItemFirstAElem = document.querySelectorAll('.showSubMenu');
let backToProductCategoriesElem = document.querySelectorAll('.backToProductCategories');

navbarItemFirstAElem.forEach(function (childItem) {

    childItem.addEventListener('click', function (e) {

        e.preventDefault();

        if (childItem.nextElementSibling) {
            childItem.nextElementSibling.classList.add('showElem');
        }

    });

});

backToProductCategoriesElem.forEach(function (navItem) {

    navItem.addEventListener('click', function () {

        if (navItem.parentElement && navItem.parentElement.parentElement) {
            navItem.parentElement.parentElement.classList.remove('showElem');
        }

    });

});

if (navbarOpenBtnElem && navbarItemMobileELem && overlayElem) {

    navbarOpenBtnElem.addEventListener('click', function () {

        navbarItemMobileELem.classList.add('showElem');
        overlayElem.classList.add('showElem');

    });

}

if (navbarCloseBtnElem && navbarItemMobileELem && overlayElem) {

    navbarCloseBtnElem.addEventListener('click', function () {

        navbarItemMobileELem.classList.remove('showElem');
        overlayElem.classList.remove('showElem');

    });

}


// ======================
// Navbar Scroll
// ======================

let customNavbar = document.querySelector('#customNavbar');
let mainNavbar = document.querySelector('#mainNavbar');
let topMobileNavbar = document.querySelector('#topMobileNavbar');

let lastScrollTop = 0;

document.addEventListener('scroll', function () {

    if (!customNavbar) return;

    if (document.documentElement.scrollTop > 100) {
        customNavbar.classList.add('fixed');
    } else {
        customNavbar.classList.remove('fixed');
    }

});

document.addEventListener('scroll', function () {

    if (!mainNavbar || !topMobileNavbar) return;

    if (window.pageYOffset > 100) {

        let scrollTop = window.pageYOffset || document.documentElement.scrollTop;

        if (scrollTop > lastScrollTop) {

            mainNavbar.classList.add('hidden-main-navbar');
            topMobileNavbar.style.border = '0';

        } else {

            mainNavbar.classList.remove('hidden-main-navbar');
            topMobileNavbar.style.borderBottom = '1px solid #F1F2F4';

        }

        lastScrollTop = scrollTop;

    }

});
// ======================
// Navbar Hover
// ======================

if (mainNavbar) {

    mainNavbar.addEventListener('mouseenter', function () {
        this.classList.add('is-active');
    });

    mainNavbar.addEventListener('mouseleave', function () {
        this.classList.remove('is-active');
    });

}


// ======================
// Search Scripts
// ======================

let mainSearchWrapper = document.querySelector('.main-search');
let searchInput = document.querySelector('#mainSearchInput');
let searchResultsBox = document.querySelector('.search-results');

if (searchInput && searchResultsBox) {

    searchInput.addEventListener('keyup', function (e) {

        searchResultsBox.style.display = 'block';
        e.target.classList.add('search-fired');

    });

    searchInput.addEventListener('click', function (e) {

        searchResultsBox.style.display = 'block';
        e.target.classList.add('search-fired');

    });

    document.addEventListener('click', function (e) {

        // اگر روی خود سرچ کلیک شد، نتایج بسته نشه
        if (
            mainSearchWrapper &&
            mainSearchWrapper.contains(e.target)
        ) {
            return;
        }

        searchResultsBox.style.display = 'none';
        searchInput.classList.remove('search-fired');

    });

}


// ======================
// To Top Scripts
// ======================

let toTopElem = document.querySelector('.to-top');

if (toTopElem) {

    window.addEventListener('scroll', function () {

        if (window.scrollY > 200) {
            toTopElem.classList.add('showElem');
        } else {
            toTopElem.classList.remove('showElem');
        }

    });

}