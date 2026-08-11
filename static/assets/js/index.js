var swiper2 = new Swiper('.bestSuggestionsSlider', {
    slidesPerView: 7,
    spaceBetween: 3,
    navigation: {
        nextEl: ".swiper-button-next",
        prevEl: ".swiper-button-prev",
    },
    breakpoints: {
        120: {
            slidesPerView: 2,
        },
        768: {
            slidesPerView: 4,
        },
        1024: {
            slidesPerView: 5,
        },
        1200: {
            slidesPerView: 6,
        },
    },
});

// var swiper3 = new Swiper('.storySlider', {
//     effect: "cube",
//     grabCursor: true,
//     cubeEffect: {
//         shadow: true,
//         slideShadows: true,
//         shadowOffset: 20,
//         shadowScale: 0.94,
//     }, navigation: {
//         nextEl: ".swiper-button-next",
//         prevEl: ".swiper-button-prev",
//     },
//     pagination: {
//         el: ".swiper-pagination",
//     }
// })

var swiper5 = new Swiper('.brandsSlider', {
    slidesPerView: 7,
    spaceBetween: 3,
    navigation: {
        nextEl: ".swiper-button-next",
        prevEl: ".swiper-button-prev",
    }, breakpoints: {
        120: {
            slidesPerView: 3,
        },
        768: {
            slidesPerView: 4,
        },
        1024: {
            slidesPerView: 6,
        },
        1200: {
            slidesPerView: 7,
        },
    }
})
var swiper6 = new Swiper('.bestSales', {
    slidesPerView: 7,
    spaceBetween: 3,
    navigation: {
        nextEl: ".swiper-button-next",
        prevEl: ".swiper-button-prev",
    }, breakpoints: {
        120: {
            slidesPerView: 1,
        },
        768: {
            slidesPerView: 2,
        },
        1024: {
            slidesPerView: 3,
        },
        1200: {
            slidesPerView: 4,
        },
    }
})
const story_other_prd = new Swiper(".modal-body .story-other-prd", {
    slidesPerView: 1,
    spaceBetween: 20,
    freeMode: true,
});

const storys = new Swiper(".storys", {
    slidesPerView: 12,

    freeMode: true,
    pagination: {
        el: ".swiper-pagination",
        clickable: true,
    },
    breakpoints: {
        // when window width is >= 320px
        320: {
            slidesPerView: 3,
            spaceBetween:0,
        },
        390: {
            slidesPerView: 4,

        },
        // when window width is >= 480px
        480: {
            slidesPerView: 5,

        },
        // when window width is >= 640px

        768: {
            slidesPerView: 7,

        },
        1000: {
            slidesPerView: 9,

        },
        1200: {
            slidesPerView: 12,

        },
        1500: {
            slidesPerView: 13,

        },
    }
});
const container = document.getElementById('story-slider'),
    sliders = document.querySelectorAll('[data-video]');

sliders.forEach(item => {
    item.addEventListener('click', () => container.src = item.dataset.video);
});
const story_img = document.querySelectorAll(".swiper-img");
const video = document.querySelector(".story-videos-box video");
const backdrop = document.querySelector(".modal");

story_img.forEach(function (item) {
    item.addEventListener("click", function () {

        if (!video) return;

        video.currentTime = 0;
        video.autoplay = true;
        video.load();

    });
});

if (backdrop && video) {

    backdrop.addEventListener('hidden.bs.modal', function () {
        video.pause();
        video.currentTime = 0;
    });

}

const banners = document.querySelectorAll('.banner-item');

banners.forEach(banner => {
    const inner = banner.querySelector('.banner-inner');

    banner.addEventListener('mousemove', (e) => {
        const rect = banner.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        const centerX = rect.width / 2;
        const centerY = rect.height / 2;

        const rotateX = ((y - centerY) / centerY) * 10;
        const rotateY = ((x - centerX) / centerX) * -10;

        inner.style.transform = `rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.05,1.05,1.05)`;
    });

    banner.addEventListener('mouseleave', () => {
        inner.style.transform = 'rotateX(0deg) rotateY(0deg) scale3d(1,1,1)';
    });
});
const banner = document.querySelectorAll('.banner-item'); // NodeList جمعی از همه بنرها

banner.forEach(b => {
    const inner = b.querySelector('.banner-inner');

    b.addEventListener('mousemove', (e) => {
        const rect = b.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        const centerX = rect.width / 2;
        const centerY = rect.height / 2;

        const rotateX = ((y - centerY) / centerY) * 10;
        const rotateY = ((x - centerX) / centerX) * -10;

        inner.style.transform = `rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.05,1.05,1.05)`;
    });

    b.addEventListener('mouseleave', () => {
        inner.style.transform = 'rotateX(0deg) rotateY(0deg) scale3d(1,1,1)';
    });
});
