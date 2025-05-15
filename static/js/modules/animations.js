// radhashyam/static/js/modules/animation.js

// Product card hover effects
// animations.js - Revised version
export function initCardAnimations() {
    document.querySelectorAll('.product-card').forEach(card => {
        let animationFrame;

        const handleMove = (e) => {
            if (animationFrame) cancelAnimationFrame(animationFrame);

            animationFrame = requestAnimationFrame(() => {
                const rect = card.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;

                card.style.transform = `
                    perspective(1000px)
                    rotateX(${(y - rect.height / 2) / 15}deg)
                    rotateY(${-(x - rect.width / 2) / 15}deg)
                    scale(1.02)
                `;
            });
        };

        const handleLeave = () => {
            card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) scale(1)';
        };

        card.addEventListener('mousemove', handleMove);
        card.addEventListener('mouseleave', handleLeave);

        // Cleanup
        return () => {
            card.removeEventListener('mousemove', handleMove);
            card.removeEventListener('mouseleave', handleLeave);
        };
    });
}