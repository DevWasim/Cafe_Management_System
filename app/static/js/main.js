document.addEventListener("DOMContentLoaded", function () {

    // GSAP Defaults
    gsap.registerPlugin(ScrollTrigger);

    // Navbar entrance
    gsap.from(".navbar", { duration: 1, y: -50, opacity: 0, ease: "power3.out" });

    // Header / Hero Stagger
    gsap.utils.toArray(".fade-in").forEach((element, i) => {
        gsap.from(element, {
            duration: 1,
            y: 30,
            opacity: 0,
            delay: i * 0.2, // Stagger effect based on order
            ease: "power3.out"
        });
    });

    // Scroll Reveal for Cards
    gsap.utils.toArray(".scroll-reveal").forEach((element) => {
        gsap.from(element, {
            scrollTrigger: {
                trigger: element,
                start: "top 85%", // Start when top of element is at 85% viewport height
                toggleActions: "play none none reverse"
            },
            duration: 0.8,
            y: 50,
            opacity: 0,
            ease: "back.out(1.7)"
        });
    });

    // Alert Close Logic
    const closeBtns = document.querySelectorAll('.close-alert');
    closeBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const alertBox = e.target.parentElement;
            gsap.to(alertBox, {
                opacity: 0,
                y: -10,
                duration: 0.3,
                onComplete: () => alertBox.remove()
            });
        });
    });

    // Mobile Menu Toggle
    const mobileToggle = document.querySelector('.mobile-toggle');
    const navLinks = document.querySelector('.nav-links');

    if (mobileToggle) {
        mobileToggle.addEventListener('click', () => {
            navLinks.classList.toggle('active');
            // Animate links in if active
            if (navLinks.classList.contains('active')) {
                gsap.from(".nav-links li", {
                    duration: 0.5,
                    x: -20,
                    opacity: 0,
                    stagger: 0.1
                });
            }
        });
    }

});
