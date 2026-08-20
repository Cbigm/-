const canvas = document.querySelector('#fireworks');
const ctx = canvas.getContext('2d');
const counter = document.querySelector('#counter');
const soundButton = document.querySelector('#soundButton');
const fullscreenButton = document.querySelector('#fullscreenButton');

const particles = [];
const stars = [];
const palette = ['#ffd787', '#ff9f63', '#ff7199', '#a77dff', '#66d9ff', '#f9f2dc'];
let width = 0;
let height = 0;
let dpr = 1;
let lastMove = 0;
let fireworkCount = 0;
let audioContext;
let soundEnabled = false;

function resize() {
  dpr = Math.min(window.devicePixelRatio || 1, 2);
  width = window.innerWidth;
  height = window.innerHeight;
  canvas.width = width * dpr;
  canvas.height = height * dpr;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  stars.length = 0;
  const count = Math.floor((width * height) / 10500);
  for (let i = 0; i < count; i++) {
    stars.push({ x: Math.random() * width, y: Math.random() * height, r: Math.random() * 1.15, a: .15 + Math.random() * .45, phase: Math.random() * 6 });
  }
}

class Particle {
  constructor(x, y, options = {}) {
    const angle = options.angle ?? Math.random() * Math.PI * 2;
    const speed = options.speed ?? 1 + Math.random() * 3;
    this.x = x;
    this.y = y;
    this.vx = Math.cos(angle) * speed;
    this.vy = Math.sin(angle) * speed;
    this.color = options.color || palette[Math.floor(Math.random() * palette.length)];
    this.life = options.life || 60 + Math.random() * 35;
    this.maxLife = this.life;
    this.size = options.size || 1.3 + Math.random() * 1.8;
    this.gravity = options.gravity ?? .035;
    this.drag = options.drag ?? .985;
    this.twinkle = Math.random() * 6;
    this.trail = [];
  }

  update() {
    if (this.life % 2 > 1) this.trail.push({ x: this.x, y: this.y });
    if (this.trail.length > 5) this.trail.shift();
    this.vx *= this.drag;
    this.vy = this.vy * this.drag + this.gravity;
    this.x += this.vx;
    this.y += this.vy;
    this.life--;
  }

  draw() {
    const alpha = Math.max(0, this.life / this.maxLife);
    ctx.save();
    ctx.globalAlpha = alpha * .35;
    ctx.strokeStyle = this.color;
    ctx.lineWidth = this.size * .6;
    ctx.beginPath();
    this.trail.forEach((point, i) => i ? ctx.lineTo(point.x, point.y) : ctx.moveTo(point.x, point.y));
    ctx.lineTo(this.x, this.y);
    ctx.stroke();
    ctx.globalAlpha = alpha * (.65 + Math.sin(this.life * .35 + this.twinkle) * .3);
    ctx.shadowBlur = 12;
    ctx.shadowColor = this.color;
    ctx.fillStyle = this.color;
    ctx.beginPath();
    ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }
}

function burst(x, y, large = false) {
  const color = palette[Math.floor(Math.random() * (palette.length - 1))];
  const count = large ? 150 : 10;
  for (let i = 0; i < count; i++) {
    const ring = large && i < 100;
    const speed = ring ? 3.2 + Math.random() * 3.4 : .8 + Math.random() * (large ? 5 : 2);
    particles.push(new Particle(x, y, {
      angle: ring ? (i / 100) * Math.PI * 2 + (Math.random() - .5) * .035 : Math.random() * Math.PI * 2,
      speed,
      color: Math.random() < .78 ? color : palette[Math.floor(Math.random() * palette.length)],
      life: large ? 72 + Math.random() * 45 : 30 + Math.random() * 22,
      size: large ? 1.2 + Math.random() * 2 : .8 + Math.random() * 1.2,
      gravity: large ? .045 : .025
    }));
  }
  if (large) {
    fireworkCount++;
    counter.textContent = fireworkCount;
    playPop();
  }
}

function playPop() {
  if (!soundEnabled) return;
  audioContext ||= new AudioContext();
  const now = audioContext.currentTime;
  const gain = audioContext.createGain();
  const oscillator = audioContext.createOscillator();
  oscillator.type = 'sine';
  oscillator.frequency.setValueAtTime(130, now);
  oscillator.frequency.exponentialRampToValueAtTime(42, now + .42);
  gain.gain.setValueAtTime(.2, now);
  gain.gain.exponentialRampToValueAtTime(.001, now + .45);
  oscillator.connect(gain).connect(audioContext.destination);
  oscillator.start(now);
  oscillator.stop(now + .46);
}

function animate(time) {
  ctx.clearRect(0, 0, width, height);
  for (const star of stars) {
    ctx.globalAlpha = star.a * (.7 + Math.sin(time * .001 + star.phase) * .3);
    ctx.fillStyle = '#dfe7ff';
    ctx.fillRect(star.x, star.y, star.r, star.r);
  }
  ctx.globalAlpha = 1;
  for (let i = particles.length - 1; i >= 0; i--) {
    particles[i].update();
    particles[i].draw();
    if (particles[i].life <= 0) particles.splice(i, 1);
  }
  requestAnimationFrame(animate);
}

window.addEventListener('pointermove', (event) => {
  const now = performance.now();
  if (now - lastMove > 28) {
    burst(event.clientX, event.clientY);
    lastMove = now;
  }
});

window.addEventListener('pointerdown', (event) => {
  if (event.target.closest('button, a')) return;
  burst(event.clientX, event.clientY, true);
});

soundButton.addEventListener('click', () => {
  soundEnabled = !soundEnabled;
  soundButton.setAttribute('aria-pressed', String(soundEnabled));
  soundButton.setAttribute('aria-label', soundEnabled ? '关闭声音' : '开启声音');
});

fullscreenButton.addEventListener('click', async () => {
  if (!document.fullscreenElement) await document.documentElement.requestFullscreen();
  else await document.exitFullscreen();
});

window.addEventListener('resize', resize);
resize();
requestAnimationFrame(animate);

setTimeout(() => {
  burst(width * .2, height * .25, true);
  setTimeout(() => burst(width * .82, height * .28, true), 500);
}, 650);
