// Copied from https://github.com/jeffreyquan/flip-card-wc/tree/main

var css_248z = ":host {\n  display: block; }\n\n.flip-card {\n  position: relative;\n  perspective: 100rem;\n  height: var(--flip-card-height, 100px); }\n  .flip-card__side {\n    height: var(--flip-card-height, 100px);\n    transition: all var(--flip-card-transition-duration, 800ms) var(--flip-card-transition-timing-function, ease);\n    position: absolute;\n    top: 0;\n    left: 0;\n    width: 100%;\n    -webkit-backface-visibility: hidden;\n            backface-visibility: hidden;\n    border-radius: var(--flip-card-border-radius, 4px);\n    overflow: hidden;\n    box-shadow: var(--flip-card-box-shadow, 0 15px 40px rgba(0, 0, 0, 0.15)); }\n    .flip-card__side--front {\n      background-color: var(--flip-card-background-color-front, white); }\n    .flip-card__side--back {\n      background-color: var(--flip-card-background-color-back, white);\n      transform: rotateY(180deg); }\n  .flip-card:hover .flip-card__side--front.hover {\n    transform: rotateY(-180deg); }\n  .flip-card:hover .flip-card__side--back.hover {\n    transform: rotateY(0); }\n\n.clicked--front {\n  transform: rotateY(-180deg); }\n\n.clicked--back {\n  transform: rotateY(0); }\n\n/*# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJzb3VyY2VzIjpbInN0eWxlLmNzcyJdLCJuYW1lcyI6W10sIm1hcHBpbmdzIjoiQUFBQTtFQUNFLGNBQWMsRUFBRTs7QUFFbEI7RUFDRSxrQkFBa0I7RUFDbEIsbUJBQW1CO0VBQ25CLHNDQUFzQyxFQUFFO0VBQ3hDO0lBQ0Usc0NBQXNDO0lBQ3RDLDZHQUE2RztJQUM3RyxrQkFBa0I7SUFDbEIsTUFBTTtJQUNOLE9BQU87SUFDUCxXQUFXO0lBQ1gsbUNBQTJCO1lBQTNCLDJCQUEyQjtJQUMzQixrREFBa0Q7SUFDbEQsZ0JBQWdCO0lBQ2hCLHdFQUF3RSxFQUFFO0lBQzFFO01BQ0UsZ0VBQWdFLEVBQUU7SUFDcEU7TUFDRSwrREFBK0Q7TUFDL0QsMEJBQTBCLEVBQUU7RUFDaEM7SUFDRSwyQkFBMkIsRUFBRTtFQUMvQjtJQUNFLHFCQUFxQixFQUFFOztBQUUzQjtFQUNFLDJCQUEyQixFQUFFOztBQUUvQjtFQUNFLHFCQUFxQixFQUFFIiwiZmlsZSI6InN0eWxlLmNzcyIsInNvdXJjZXNDb250ZW50IjpbIjpob3N0IHtcbiAgZGlzcGxheTogYmxvY2s7IH1cblxuLmZsaXAtY2FyZCB7XG4gIHBvc2l0aW9uOiByZWxhdGl2ZTtcbiAgcGVyc3BlY3RpdmU6IDEwMHJlbTtcbiAgaGVpZ2h0OiB2YXIoLS1mbGlwLWNhcmQtaGVpZ2h0LCAxMDBweCk7IH1cbiAgLmZsaXAtY2FyZF9fc2lkZSB7XG4gICAgaGVpZ2h0OiB2YXIoLS1mbGlwLWNhcmQtaGVpZ2h0LCAxMDBweCk7XG4gICAgdHJhbnNpdGlvbjogYWxsIHZhcigtLWZsaXAtY2FyZC10cmFuc2l0aW9uLWR1cmF0aW9uLCA4MDBtcykgdmFyKC0tZmxpcC1jYXJkLXRyYW5zaXRpb24tdGltaW5nLWZ1bmN0aW9uLCBlYXNlKTtcbiAgICBwb3NpdGlvbjogYWJzb2x1dGU7XG4gICAgdG9wOiAwO1xuICAgIGxlZnQ6IDA7XG4gICAgd2lkdGg6IDEwMCU7XG4gICAgYmFja2ZhY2UtdmlzaWJpbGl0eTogaGlkZGVuO1xuICAgIGJvcmRlci1yYWRpdXM6IHZhcigtLWZsaXAtY2FyZC1ib3JkZXItcmFkaXVzLCA0cHgpO1xuICAgIG92ZXJmbG93OiBoaWRkZW47XG4gICAgYm94LXNoYWRvdzogdmFyKC0tZmxpcC1jYXJkLWJveC1zaGFkb3csIDAgMTVweCA0MHB4IHJnYmEoMCwgMCwgMCwgMC4xNSkpOyB9XG4gICAgLmZsaXAtY2FyZF9fc2lkZS0tZnJvbnQge1xuICAgICAgYmFja2dyb3VuZC1jb2xvcjogdmFyKC0tZmxpcC1jYXJkLWJhY2tncm91bmQtY29sb3ItZnJvbnQsIHdoaXRlKTsgfVxuICAgIC5mbGlwLWNhcmRfX3NpZGUtLWJhY2sge1xuICAgICAgYmFja2dyb3VuZC1jb2xvcjogdmFyKC0tZmxpcC1jYXJkLWJhY2tncm91bmQtY29sb3ItYmFjaywgd2hpdGUpO1xuICAgICAgdHJhbnNmb3JtOiByb3RhdGVZKDE4MGRlZyk7IH1cbiAgLmZsaXAtY2FyZDpob3ZlciAuZmxpcC1jYXJkX19zaWRlLS1mcm9udC5ob3ZlciB7XG4gICAgdHJhbnNmb3JtOiByb3RhdGVZKC0xODBkZWcpOyB9XG4gIC5mbGlwLWNhcmQ6aG92ZXIgLmZsaXAtY2FyZF9fc2lkZS0tYmFjay5ob3ZlciB7XG4gICAgdHJhbnNmb3JtOiByb3RhdGVZKDApOyB9XG5cbi5jbGlja2VkLS1mcm9udCB7XG4gIHRyYW5zZm9ybTogcm90YXRlWSgtMTgwZGVnKTsgfVxuXG4uY2xpY2tlZC0tYmFjayB7XG4gIHRyYW5zZm9ybTogcm90YXRlWSgwKTsgfVxuIl19 */";

var template = "<div class=\"flip-card\">\n  <div class=\"flip-card__side flip-card__side--front\">\n    <div><slot name=\"front\"></div>\n  </div>\n  <div class=\"flip-card__side flip-card__side--back\">\n    <div>\n      <slot name=\"back\">\n    </div>\n  </div>\n</div>\n";

const flipCardTemplate = document.createElement("template");
flipCardTemplate.innerHTML = `
<style>${css_248z}</style>
${template}
`;
class FlipCard extends HTMLElement {
    constructor() {
        super();
        this._shadowRoot = this.attachShadow({ mode: "open" });
        this._shadowRoot.appendChild(flipCardTemplate.content.cloneNode(true));
    }
    connectedCallback() {
        if (!this.hasAttribute("variant")) {
            this.variant = "hover";
        }
        this.attachEventListeners();
        this._upgradeProperty('variant');
    }
    _upgradeProperty(prop) {
        if (this.hasOwnProperty(prop)) {
            let value = this[prop];
            delete this[prop];
            this[prop] = value;
        }
    }
    static get observedAttributes() {
        return ['variant'];
    }
    attributeChangedCallback(attrName, oldVal, newVal) {
        if (oldVal !== newVal) {
            this.attachEventListeners();
        }
    }
    get variant() {
        return this.getAttribute("variant");
    }
    set variant(newValue) {
        if (newValue) {
            this.setAttribute("variant", newValue);
        }
    }
    attachEventListeners() {
        const cardFront = this._shadowRoot.querySelector(".flip-card__side--front");
        const cardBack = this._shadowRoot.querySelector(".flip-card__side--back");
        if (this.variant === "click") {
            if (cardFront) {
                cardFront.style.cursor = "pointer";
            }
            if (cardBack) {
                cardBack.style.cursor = "pointer";
            }
            cardFront === null || cardFront === void 0 ? void 0 : cardFront.classList.remove("hover");
            cardBack === null || cardBack === void 0 ? void 0 : cardBack.classList.remove("hover");
            cardFront === null || cardFront === void 0 ? void 0 : cardFront.addEventListener('click', function (event) {
                cardFront === null || cardFront === void 0 ? void 0 : cardFront.classList.add("clicked--front");
                cardBack === null || cardBack === void 0 ? void 0 : cardBack.classList.add("clicked--back");
            });
            cardBack === null || cardBack === void 0 ? void 0 : cardBack.addEventListener('click', function (event) {
                cardFront === null || cardFront === void 0 ? void 0 : cardFront.classList.remove("clicked--front");
                cardBack === null || cardBack === void 0 ? void 0 : cardBack.classList.remove("clicked--back");
            });
        }
        if (this.variant === "hover") {
            cardFront === null || cardFront === void 0 ? void 0 : cardFront.classList.add("hover");
            cardFront === null || cardFront === void 0 ? void 0 : cardFront.classList.remove("clicked--front");
            cardBack === null || cardBack === void 0 ? void 0 : cardBack.classList.add('hover');
            cardBack === null || cardBack === void 0 ? void 0 : cardBack.classList.remove('clicked--back');
        }
    }
}
window.customElements.define("flip-card", FlipCard);
//# sourceMappingURL=flip-card-wc.js.map