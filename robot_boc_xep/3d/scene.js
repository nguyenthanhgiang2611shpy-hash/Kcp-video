// v2 - Minh họa 3D: 2 robot (đầu xe + đuôi xe), mỗi lần gắp 3 bao, xe container đã dỡ bạt.
// Đơn vị mét. x dọc xe (cabin ở x<0, cửa sau x=12,26), y lên, z ngang xe.
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';

const W = 1280, H = 720, DUR = 58.5;
const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setSize(W, H); renderer.setPixelRatio(1);
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.outputColorSpace = THREE.SRGBColorSpace;
document.body.prepend(renderer.domElement);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0xdfe3e6);
scene.fog = new THREE.Fog(0xdfe3e6, 40, 85);
const camera = new THREE.PerspectiveCamera(38, W / H, 0.1, 200);
scene.add(new THREE.HemisphereLight(0xffffff, 0x8a8f94, 1.5));
const sun = new THREE.DirectionalLight(0xffffff, 2.2);
sun.position.set(-8, 22, 14); sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048);
Object.assign(sun.shadow.camera, { left: -16, right: 24, top: 16, bottom: -16, near: 1, far: 60 });
sun.shadow.bias = -0.0006; scene.add(sun); scene.add(sun.target); sun.target.position.set(5, 0, 0);

const M = (c, o = {}) => new THREE.MeshStandardMaterial({ color: c, roughness: 0.7, metalness: 0.1, ...o });
function box(w, h, d, mat, x = 0, y = 0, z = 0, parent = scene) {
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat);
  m.position.set(x, y, z); m.castShadow = m.receiveShadow = true; parent.add(m); return m;
}
function cyl(r, h, mat, parent, axis = 'y') {
  const m = new THREE.Mesh(new THREE.CylinderGeometry(r, r, h, 24), mat);
  if (axis === 'x') m.rotation.z = Math.PI / 2; if (axis === 'z') m.rotation.x = Math.PI / 2;
  m.castShadow = m.receiveShadow = true; parent.add(m); return m;
}
const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
const ss = x => { x = clamp(x); return x * x * (3 - 2 * x); };
const seg = (t, a, b) => ss((t - a) / (b - a));
const lerp = (a, b, k) => a + (b - a) * k;
const V = (x, y, z) => new THREE.Vector3(x, y, z);

// ---------- nhà kho ----------
const floor = new THREE.Mesh(new THREE.PlaneGeometry(140, 80), M(0xb9bec2, { roughness: 0.95 }));
floor.rotation.x = -Math.PI / 2; floor.receiveShadow = true; scene.add(floor);
for (const z of [-1.9, 1.9]) box(60, 0.01, 0.1, M(0xf2c230), 12, 0.006, z);
for (let x = -8; x <= 22; x += 10) box(0.5, 9, 0.5, M(0x6f8596), x, 4.5, -9);

// ---------- xe container (đã dỡ bạt, còn khung cột) ----------
const BED_L = 12.26, BED_W = 2.35, BED_Y = 1.2, WALL = 0.8, ROOF = 2.15;
const steel = M(0x8c969e, { metalness: 0.4, roughness: 0.5 });
function makeTruck(cabColor) {
  const g = new THREE.Group(); scene.add(g);
  box(BED_L, 0.12, BED_W, M(0x6b5a4a), BED_L / 2, BED_Y - 0.06, 0, g);
  box(BED_L + 0.3, 0.3, 1.0, M(0x2b2f33), BED_L / 2 - 0.3, BED_Y - 0.3, 0, g);
  for (const z of [-1, 1]) box(BED_L, WALL, 0.05, steel, BED_L / 2, BED_Y + WALL / 2, z * BED_W / 2, g);
  box(0.06, ROOF, BED_W, steel, 0.03, BED_Y + ROOF / 2, 0, g);
  box(0.06, WALL, BED_W, steel, BED_L - 0.03, BED_Y + WALL / 2, 0, g);
  for (let i = 0; i <= 6; i++) for (const z of [-1, 1])
    box(0.08, ROOF, 0.08, steel, Math.min(i * BED_L / 6, BED_L - 0.04), BED_Y + ROOF / 2, z * (BED_W / 2 + 0.02), g);
  const cab = new THREE.Group(); g.add(cab); cab.position.set(-1.35, 0, 0);
  box(2.3, 2.3, 2.45, M(cabColor, { roughness: 0.4 }), 0, 1.95, 0, cab);
  box(0.05, 0.9, 2.1, M(0x1c2a35, { roughness: 0.1, metalness: 0.6 }), -1.16, 2.5, 0, cab);
  box(2.3, 0.35, 2.45, M(0xe6e6e6), 0, 0.95, 0, cab);
  const wm = M(0x1b1b1b, { roughness: 0.9 });
  for (const x of [-1.3, 7.6, 8.9, 10.2]) for (const z of [-1, 1]) cyl(0.5, 0.35, wm, g, 'z').position.set(x, 0.5, z * 1.05);
  return g;
}
const truck1 = makeTruck(0x2f6db3), truck2 = makeTruck(0x3a7d5c);

// ---------- bao 50 kg (75 x 50 x 13 cm) ----------
function bagTexture() {
  const c = document.createElement('canvas'); c.width = 256; c.height = 170;
  const g = c.getContext('2d'); g.fillStyle = '#f4f1e8'; g.fillRect(0, 0, 256, 170);
  g.strokeStyle = 'rgba(0,0,0,0.05)'; for (let i = 0; i < 256; i += 4) { g.beginPath(); g.moveTo(i, 0); g.lineTo(i, 170); g.stroke(); }
  g.fillStyle = '#2f6db3'; g.fillRect(0, 22, 256, 10); g.fillRect(0, 138, 256, 10);
  g.font = 'bold 44px DejaVu Sans'; g.textAlign = 'center'; g.fillText('KCP', 128, 100);
  g.font = 'bold 20px DejaVu Sans'; g.fillStyle = '#c0392b'; g.fillText('ĐƯỜNG · 50 KG', 128, 126);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}
const BL = 0.75, BH = 0.13, SPC = 0.77;   // SPC: khoảng cách 3 đầu gắp
const bagGeo = new RoundedBoxGeometry(BL, BH, 0.5, 3, 0.05);
const bagMat = new THREE.MeshStandardMaterial({ map: bagTexture(), roughness: 0.95 });
function newBag(parent = scene) { const m = new THREE.Mesh(bagGeo, bagMat); m.castShadow = m.receiveShadow = true; parent.add(m); return m; }

// ---------- sơ đồ xếp: mỗi lần gắp = 1 hàng 3 bao nằm ngang thùng; đoạn 0,5 m; 8 lớp ----------
const SECT = 23, LAY = 8, SPLIT = 12;     // robot đầu: đoạn 0-11; robot đuôi: đoạn 22-12
const secX = s => 0.45 + 0.5 * s;
const layY = l => BED_Y + BH / 2 + l * BH;

// ---------- sàn thép cao + băng tải (theo clip 6) ----------
const yellow = M(0xf2b705, { roughness: 0.45, metalness: 0.2 }), dark = M(0x2b2f33, { roughness: 0.6 });
const DECK_Y = 1.6, PX0 = -11.0, PX1 = 23.4, PZ0 = 1.85, PZ1 = 5.1;
const CZ = 3.6, CY = DECK_Y + 0.45, RAILZ = [2.8, 4.4], RZ = CZ, BASE_Y = 3.05;
const BED_TOP = 2.4, BAG_BED = BED_TOP + BH / 2;      // trạm con lăn dưới cánh tay robot
const SLOT = [-0.95, -0.95 - SPC, -0.95 - 2 * SPC];   // 3 chỗ bao trên trạm (tính từ đế robot, phía băng dốc)
const RAMP_TOP = -2.95, RAMP_BOT = -4.5;              // băng dốc đưa bao từ băng tải lên trạm
const L1 = 2.4, L2 = 2.6, SH_A = 0.25, SH_Y = 0.6, G = 0.42, SAFE = 3.55;
function stripeTex() {
  const c = document.createElement('canvas'); c.width = 64; c.height = 256; const g = c.getContext('2d');
  for (let i = 0; i < 8; i++) { g.fillStyle = i % 2 ? '#1d1d1d' : '#f2c230'; g.fillRect(0, i * 32, 64, 32); }
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}
const stripe = new THREE.MeshStandardMaterial({ map: stripeTex(), roughness: 0.6 });
box(PX1 - PX0, 0.35, PZ1 - PZ0, M(0x5d6870, { roughness: 0.8 }), (PX0 + PX1) / 2, DECK_Y - 0.175, (PZ0 + PZ1) / 2);
for (let x = PX0 + 0.4; x <= PX1 - 0.3; x += 3.0) for (const z of [PZ0 + 0.35, PZ1 - 0.35])
  box(0.45, DECK_Y - 0.35, 0.45, stripe, x, (DECK_Y - 0.35) / 2, z);
for (const z of RAILZ) box(PX1 - PX0, 0.1, 0.1, M(0x555b60, { metalness: 0.7 }), (PX0 + PX1) / 2, DECK_Y + 0.05, z);
// 2 băng tải riêng trên cùng một đường: A từ đầu sàn tới robot đầu xe, B từ cuối sàn tới robot đuôi xe
const BELTS = [[PX0, 1.4], [11.0, PX1]];
for (const [x0, x1] of BELTS) {
  box(x1 - x0, 0.06, 0.82, M(0x2f7d4a, { roughness: 0.8 }), (x0 + x1) / 2, CY - 0.03, CZ);
  for (const dz of [-0.45, 0.45]) box(x1 - x0, 0.16, 0.06, M(0x7b8288, { metalness: 0.5 }), (x0 + x1) / 2, CY - 0.02, CZ + dz);
  for (const xe of [x0, x1]) cyl(0.09, 0.84, dark, scene, 'z').position.set(xe, CY - 0.06, CZ);
  for (let x = x0 + 0.3; x <= x1; x += 1.5) for (const dz of [-0.4, 0.4]) box(0.07, 0.42, 0.07, steel, x, DECK_Y + 0.21, CZ + dz);
}

// ---------- robot: khung xe con trùm lên băng tải, chạy trên ray; bao lên băng dốc vào trạm dưới cánh tay ----------
function makeRobot(home, off, sections, d) {
  const g = new THREE.Group(); scene.add(g);
  const car = new THREE.Group(); car.scale.x = d; g.add(car);          // d=+1: băng dốc phía -x; d=-1: đối xứng
  const frame = M(0x8a949c, { metalness: 0.5, roughness: 0.45 });
  const legs = [[0.45, 2.95], [-0.45, 2.95], [-0.7, BED_TOP - 0.1], [-2.9, BED_TOP - 0.1], [-4.4, CY + 0.1]];
  for (const [x, top] of legs) for (const z of RAILZ) {
    box(0.15, top - DECK_Y - 0.1, 0.15, frame, x, (top + DECK_Y + 0.1) / 2, z, car);
    cyl(0.12, 0.12, dark, car, 'z').position.set(x, DECK_Y + 0.15, z);
  }
  for (const z of RAILZ) box(5.1, 0.12, 0.12, frame, -2.0, DECK_Y + 0.28, z, car);                  // dầm dọc chân
  box(1.25, 0.16, RAILZ[1] - RAILZ[0] + 0.3, frame, 0, 2.95, CZ, car);                               // mặt đỡ đế robot
  for (const z of [CZ - 0.47, CZ + 0.47]) box(2.5, 0.2, 0.06, frame, -1.8, BED_TOP + 0.05, z, car); // thành trạm con lăn
  for (const z of RAILZ) box(2.4, 0.1, 0.1, frame, -1.8, BED_TOP - 0.1, z, car);
  for (let x = -0.65; x >= -2.95; x -= 0.18) cyl(0.04, 0.88, M(0x6c757c, { metalness: 0.6 }), car, 'z').position.set(x, BED_TOP - 0.04, CZ);
  const rl = Math.hypot(RAMP_TOP - RAMP_BOT, BED_TOP - CY), ra = Math.atan2(BED_TOP - CY, RAMP_TOP - RAMP_BOT);
  const ramp = new THREE.Group(); ramp.position.set((RAMP_TOP + RAMP_BOT) / 2, (BED_TOP + CY) / 2 + 0.02, CZ); ramp.rotation.z = ra; car.add(ramp);
  box(rl, 0.05, 0.78, M(0x2f7d4a, { roughness: 0.8 }), 0, 0, 0, ramp);                               // băng dốc
  for (const dz of [-0.44, 0.44]) box(rl, 0.14, 0.05, frame, 0, 0.03, dz, ramp);
  const turret = new THREE.Group(); turret.position.set(0, BASE_Y, RZ); g.add(turret);
  cyl(0.45, 0.3, yellow, turret).position.set(0, 0.15, 0);
  box(0.7, 0.5, 0.6, yellow, 0.05, 0.5, 0, turret);
  const shoulder = new THREE.Group(); shoulder.position.set(SH_A, SH_Y, 0); turret.add(shoulder);
  box(L1, 0.28, 0.3, yellow, L1 / 2, 0, 0, shoulder); cyl(0.2, 0.42, dark, shoulder, 'z');
  const elbow = new THREE.Group(); elbow.position.set(L1, 0, 0); shoulder.add(elbow);
  cyl(0.17, 0.4, dark, elbow, 'z'); box(L2, 0.2, 0.22, yellow, L2 / 2, 0, 0, elbow);
  const wrist = new THREE.Group(); wrist.position.set(L2, 0, 0); elbow.add(wrist);
  const grip = new THREE.Group(); wrist.add(grip);
  cyl(0.07, G - 0.14, dark, grip).position.set(0, -(G - 0.14) / 2, 0);
  box(2.0, 0.1, 0.12, M(0x9aa3aa, { metalness: 0.6 }), 0, -G + 0.16, 0, grip);
  const fingers = [];
  for (const hx of [-SPC, 0, SPC]) {
    box(0.08, 0.1, 0.08, dark, hx, -G + 0.1, 0, grip);
    box(0.5, 0.05, 0.32, M(0xd9774b, { roughness: 0.5 }), hx, -G + 0.04, 0, grip);
    for (const s of [-1, 1]) for (const k of [-0.18, 0, 0.18]) {
      const f = box(0.04, 0.24, 0.04, dark, hx + k, -G - 0.08, s * 0.3, grip); f.userData.s = s; fingers.push(f);
    }
  }
  const picks = [];
  for (const s of sections) for (let l = 0; l < LAY; l++) picks.push({ x: secX(s), y: layY(l), s, l });
  const N = picks.length, T = [];
  for (let k = 0; k < N; k++) {
    if (k === 0) T.push(21); else if (k === 1) T.push(26);
    else if (k < 8) T.push(26 + (k - 1) * (8 / 7));
    else T.push(34 + (k - 7) * (12 / (N - 7)));
  }
  const placed = picks.map(() => [0, 1, 2].map(() => { const b = newBag(truck1); b.visible = false; return b; }));
  const bed = [0, 1, 2].map(() => newBag());
  const feed = Array.from({ length: 16 }, () => newBag());
  return { RZ, CZ, home, off, d, g, turret, shoulder, elbow, wrist, grip, fingers, picks, N, T, placed, bed, feed };
}
const robA = makeRobot(-1.0, -0.45, [...Array(SPLIT).keys()], 1);
const robB = makeRobot(13.5, 0.45, [...Array(SECT - SPLIT).keys()].map(i => SECT - 1 - i), -1);
const ROBOTS = [robA, robB];
const bedCenter = r => r.rx + r.d * SLOT[1];

function idxAt(r, t) { let k = 0; while (k < r.N - 1 && r.T[k] <= t) k++; return k; }
const cycStart = (r, k) => (k === 0 ? 16 : r.T[k - 1]);
function carriageX(r, t) {
  const p0 = r.picks[0].x + r.off, pl = r.picks[r.N - 1].x + r.off;
  if (t < 16) return r.home;
  if (t < 34) return lerp(r.home, p0, seg(t, 16, 17.6));
  if (t < 46) { const k = idxAt(r, t); const kf = k - 1 + clamp((t - r.T[k - 1]) / (r.T[k] - r.T[k - 1]));
    const sf = Math.min(kf, r.N - 1) / LAY; return p0 + Math.sign(pl - p0 || 1) * 0.5 * sf; }
  return lerp(pl, r.home, seg(t, 46, 49));
}
function cyclePose(r, k, u, rx) {
  const pk = r.picks[k];
  const bx = rx + r.d * SLOT[1], P = V(bx, BAG_BED + 0.02, r.CZ), Hp = V(bx, SAFE, r.CZ);
  const Tg = V(pk.x, pk.y, 0), Ht = V(pk.x, SAFE + 0.2, 0);
  const pv = k > 0 ? r.picks[k - 1] : null;
  const L0 = pv ? V(pv.x, SAFE, 0) : V(rx + r.d * SLOT[1], 3.9, 2.45);
  const keys = [[0, L0, k > 0 ? 1 : 0], [0.2, Hp, 0], [0.3, P, 0], [0.36, P, 0], [0.46, Hp, 0], [0.7, Ht, 1], [0.84, Tg, 1], [0.9, Tg, 1], [1, V(pk.x, SAFE, 0), 1]];
  let i = 0; while (i < keys.length - 2 && u > keys[i + 1][0]) i++;
  const [u0, a, ra] = keys[i], [u1, b, rb] = keys[i + 1]; const e = ss((u - u0) / (u1 - u0));
  return { pos: a.clone().lerp(b, e), rot: lerp(ra, rb, e), hold: u >= 0.33 && u < 0.87, close: u >= 0.3 && u < 0.88 ? 1 : 0 };
}
function solveArm(r, rx, target, gYaw, close) {
  r.g.position.x = rx;
  const base = V(rx, BASE_Y, r.RZ), wp = target.clone().add(V(0, BH / 2 + G + 0.06, 0));
  const dx = wp.x - base.x, dz = wp.z - base.z, yaw = Math.atan2(-dz, dx);
  r.turret.rotation.y = yaw;
  const rr = Math.hypot(dx, dz) - SH_A, h = wp.y - (base.y + SH_Y);
  const d = clamp(Math.hypot(rr, h), Math.abs(L1 - L2) + 0.05, L1 + L2 - 0.02);
  const e = Math.acos(clamp((d * d - L1 * L1 - L2 * L2) / (2 * L1 * L2), -1, 1));
  const p1 = Math.atan2(h, rr) + Math.atan2(L2 * Math.sin(e), L1 + L2 * Math.cos(e)), p2 = p1 - e;
  r.shoulder.rotation.z = p1; r.elbow.rotation.z = p2 - p1; r.wrist.rotation.z = -p2;
  r.grip.rotation.y = gYaw - yaw;
  for (const f of r.fingers) f.position.z = f.userData.s * lerp(0.36, 0.27, close);
}
// vị trí 3 bao trong 1 lần gắp (tâm nhóm c, góc nhóm a): bao i lệch (i-1)*SPC theo trục nhóm
function groupBag(c, a, i) { const d = (i - 1) * SPC; return V(c.x + Math.cos(a) * d, c.y, c.z - Math.sin(a) * d); }

// ---------- LiDAR ----------
const LID = V(-4.4, 6.0, 0);
box(0.16, 6.0, 0.16, steel, LID.x, 3.0, LID.z); box(1.2, 0.12, 0.16, steel, LID.x + 0.5, 5.9, 0);
const lidarHead = new THREE.Group(); lidarHead.position.copy(LID); scene.add(lidarHead);
cyl(0.22, 0.3, M(0x1d2b3a), lidarHead); cyl(0.23, 0.08, M(0x28d17c, { emissive: 0x1a9e5c }), lidarHead).position.y = 0.02;
const green = 0x28d17c;
const beamGeo = new THREE.BufferGeometry(); beamGeo.setAttribute('position', new THREE.Float32BufferAttribute(new Float32Array(60), 3));
const beams = new THREE.LineSegments(beamGeo, new THREE.LineBasicMaterial({ color: green, transparent: true, opacity: 0.9 }));
scene.add(beams);
const pulse = new THREE.Mesh(new THREE.SphereGeometry(0.09, 16, 12), new THREE.MeshBasicMaterial({ color: 0x9dffc9 }));
scene.add(pulse);
const hit = new THREE.Mesh(new THREE.RingGeometry(0.05, 0.16, 24), new THREE.MeshBasicMaterial({ color: green, side: THREE.DoubleSide, transparent: true }));
scene.add(hit);
const scanPlane = new THREE.Mesh(new THREE.PlaneGeometry(BED_W + 0.2, ROOF + 0.1),
  new THREE.MeshBasicMaterial({ color: green, transparent: true, opacity: 0.22, side: THREE.DoubleSide, depthWrite: false }));
scanPlane.rotation.y = Math.PI / 2; scene.add(scanPlane);
// đám mây điểm: sàn, 2 thành, vách đầu, cửa sau
const pts = []; const rnd = (() => { let s = 7; return () => (s = (s * 16807) % 2147483647) / 2147483647; })();
for (let i = 0; i < 2600; i++) pts.push([rnd() * BED_L, BED_Y + 0.01, (rnd() - 0.5) * BED_W]);
for (let i = 0; i < 1400; i++) pts.push([rnd() * BED_L, BED_Y + rnd() * WALL, (rnd() < 0.5 ? -1 : 1) * (BED_W / 2 - 0.03)]);
for (let i = 0; i < 500; i++) pts.push([0.07, BED_Y + rnd() * ROOF, (rnd() - 0.5) * BED_W]);
for (let i = 0; i < 260; i++) pts.push([BED_L - 0.07, BED_Y + rnd() * WALL, (rnd() - 0.5) * BED_W]);
pts.sort((a, b) => a[0] - b[0]);
const cloudGeo = new THREE.BufferGeometry(); cloudGeo.setAttribute('position', new THREE.Float32BufferAttribute(pts.flat(), 3));
const cloud = new THREE.Points(cloudGeo, new THREE.PointsMaterial({ color: green, size: 0.06, transparent: true }));
scene.add(cloud);
const outline = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(BED_L, ROOF, BED_W)),
  new THREE.LineBasicMaterial({ color: green, transparent: true }));
outline.position.set(BED_L / 2, BED_Y + ROOF / 2, 0); scene.add(outline);
const PULSE_TGT = V(0.07, 2.9, 0.5);

// ---------- camera: từng đoạn, trộn 0,9 giây ở chỗ nối ----------
const truckX = t => t < 49.5 ? lerp(26, 0, ss(clamp(t / 4.6))) : lerp(0, 46, ss(clamp((t - 49.5) / 4.0)));
const truck2X = t => lerp(30, 0, ss(clamp((t - 53.4) / 4.4)));
const mv = (p0, p1, l0, l1, t0, t1) => t => { const k = seg(t, t0, t1); return [p0.clone().lerp(p1, k), l0.clone().lerp(l1, k)]; };
const CAMS = [
  [0, t => [V(-1.5, 2.6, -7.6), V(Math.min(truckX(t), 14) + 1.0, 1.8, 0)]],
  [4.8, mv(V(-7.2, 7.4, 6.6), V(-6.6, 7.0, 6.0), V(-1.6, 4.6, 0), V(-1.4, 4.4, 0), 4.8, 9)],
  [9.2, mv(V(-4.5, 9.8, 10.0), V(-2.0, 10.4, 8.8), V(5.0, 1.8, 0), V(5.5, 1.8, 0), 9.2, 16)],
  [16, mv(V(1.6, 6.6, 10.6), V(1.0, 6.8, 10.0), V(-2.0, 2.6, 2.6), V(-1.8, 2.6, 2.4), 16, 26)],
  [26, mv(V(10.4, 6.4, -8.6), V(11.0, 6.6, -8.0), V(13.6, 2.6, 1.8), V(13.6, 2.5, 1.8), 26, 34)],
  [34, mv(V(5.8, 14.5, 8.5), V(5.8, 12.5, 7.4), V(5.8, 1.2, 0), V(5.8, 1.4, 0), 34, 46)],
  [46, mv(V(16.5, 7.6, -6.5), V(15.8, 7.2, -6.0), V(6.0, 1.9, 0.5), V(6.0, 1.9, 0.5), 46, 49.5)],
  [49.5, mv(V(10, 5.0, -14.5), V(6.0, 5.4, -14.0), V(12, 1.8, 0), V(5.0, 1.8, 0), 49.5, 58.5)],
];
function camAt(t) {
  let i = 0; while (i < CAMS.length - 1 && t >= CAMS[i + 1][0]) i++;
  const cur = CAMS[i][1](t);
  if (i > 0 && t - CAMS[i][0] < 0.9) {
    const prev = CAMS[i - 1][1](t), k = ss((t - CAMS[i][0]) / 0.9);
    return [prev[0].lerp(cur[0], k), prev[1].lerp(cur[1], k)];
  }
  return cur;
}

// ---------- nhãn ----------
const STEPS = [[0, 4.8, 1, 'Xe vào vị trí (đã dỡ bạt)'], [4.8, 9.2, 2, 'LiDAR là gì?'], [9.2, 16, 3, 'Quét thùng xe bằng LiDAR'],
  [16, 26, 4, 'Robot đầu xe · mỗi lần gắp 3 bao'], [26, 34, 5, 'Robot đuôi xe cùng xếp'],
  [34, 46, 6, 'Hai robot xếp dồn vào giữa'], [46, 58.5, 7, 'Xe đầy lùi ra · xe khác vào']];
const TAGS = [[5.2, 7.0, 'LiDAR là máy quét bằng tia laser'],
  [7.1, 9.0, 'Máy phát tia laser, tia chạm vào thùng xe rồi dội ngược lại'],
  [9.1, 11.3, 'Đo thời gian tia quay về, máy biết khoảng cách tới từng điểm'],
  [11.4, 13.6, 'Quét hàng nghìn điểm mỗi giây, máy dựng được hình 3D thùng xe'],
  [13.8, 16, 'Robot đã biết kích thước và vị trí thùng xe'], [16.6, 19.6, 'Bao chạy lên băng dốc, vào trạm ngay dưới robot'], [19.8, 23, '3 đầu gắp · 1 lần gắp = 3 bao'], [23.2, 26, 'Chân robot chạy trên ray dọc sàn'],
  [26.6, 30, 'Robot đuôi xếp từ cửa sau vào'], [46.3, 49.5, 'Xe đã đầy'], [50, 53.4, 'Xe lùi ra'], [54, 58.5, 'Xe tiếp theo vào vị trí']];
const $ = id => document.getElementById(id);
const stepEl = $('step'), ffEl = $('ff'), card = $('card'), tag = $('tag'), paras = card.querySelectorAll('p');

window.renderAt = function (t) {
  truck1.position.x = truckX(t); truck2.position.x = truck2X(t); truck2.visible = t > 53.5;

  // --- LiDAR ---
  lidarHead.rotation.y = t * 4;
  const pulseOn = t > 5.4 && t < 9.4;
  const ph = ((t - 5.4) / 1.3) % 1;
  pulse.visible = hit.visible = pulseOn;
  const sweepK = seg(t, 9.6, 13.4);
  const fanOn = t > 9.5 && t < 13.6;
  beams.visible = pulseOn || fanOn; scanPlane.visible = fanOn;
  const arr = beamGeo.attributes.position.array; arr.fill(0);
  if (pulseOn) {
    const k = ph < 0.5 ? ph * 2 : 2 - ph * 2;           // đi ra rồi dội về
    pulse.position.copy(LID).lerp(PULSE_TGT, k);
    hit.position.copy(PULSE_TGT).add(V(-0.02, 0, 0)); hit.rotation.y = Math.PI / 2;
    hit.material.opacity = ph > 0.42 && ph < 0.75 ? 1 - (ph - 0.42) / 0.33 : 0;
    hit.scale.setScalar(1 + 2 * clamp((ph - 0.42) / 0.33));
    arr.set([LID.x, LID.y, LID.z, PULSE_TGT.x, PULSE_TGT.y, PULSE_TGT.z], 0);
  }
  if (fanOn) {
    const x = lerp(0.1, BED_L - 0.1, sweepK);
    scanPlane.position.set(x, BED_Y + ROOF / 2, 0);
    const cs = [[-1, 0], [1, 0], [-1, 1], [1, 1], [0, 0]].map(([a, b]) => V(x, BED_Y + b * ROOF, a * BED_W / 2));
    let j = 0; for (const c of cs) { arr.set([LID.x, LID.y, LID.z, c.x, c.y, c.z], j); j += 6; }
  }
  beamGeo.attributes.position.needsUpdate = true;
  let nPts = 0; const sx = lerp(0.1, BED_L - 0.1, sweepK);
  if (t > 9.5) { while (nPts < pts.length && pts[nPts][0] <= sx) nPts++; }
  cloudGeo.setDrawRange(0, nPts);
  cloud.visible = t > 9.5 && t < 17; cloud.material.opacity = 1 - seg(t, 15.6, 17);
  outline.visible = t > 13.2 && t < 16.6;
  outline.material.opacity = Math.min(seg(t, 13.2, 13.8), 1 - seg(t, 15.8, 16.6)) * (0.65 + 0.35 * Math.sin(t * 11));

  // --- robot ---
  for (const r of ROBOTS) {
    const rx = carriageX(r, t); let pose, hold = -1;
    const rest = V(rx + r.d * SLOT[1], 3.9, 2.45);   // tư thế chờ: trên trạm, ngoài làn xe
    if (t < 16) pose = { pos: rest, rot: 0, close: 0 };
    else if (t >= 46) { const pl = r.picks[r.N - 1]; const k = seg(t, 46, 48); pose = { pos: V(pl.x, SAFE, 0).lerp(rest, k), rot: 1 - k, close: 0 }; }
    else if (t < 34) { const k = idxAt(r, t), u = clamp((t - cycStart(r, k)) / (r.T[k] - cycStart(r, k)));
      pose = cyclePose(r, k, u, rx); if (pose.hold) hold = k; }
    else { const k = idxAt(r, t), u = ((t - 34) * 1.4) % 1; pose = cyclePose(r, k, 0.2 + u * 0.7, rx); }
    const gy = pose.rot * Math.PI / 2;
    solveArm(r, rx, pose.pos, gy, pose.close);
    for (let k = 0; k < r.N; k++) for (let i = 0; i < 3; i++) {
      const b = r.placed[k][i], pk = r.picks[k];
      if (k === hold) { b.visible = true; const p = groupBag(pose.pos, gy, i); b.position.set(p.x - truck1.position.x, p.y, p.z); b.rotation.set(0, gy, 0); }
      else if (t >= r.T[k]) {
        const drop = t >= 34 && t < 46 ? (1 - seg(t, r.T[k], r.T[k] + 0.12)) * 0.25 : 0;
        const p = groupBag(V(pk.x, pk.y + drop, 0), Math.PI / 2, i); b.position.copy(p); b.rotation.set(0, Math.PI / 2, 0); b.visible = true;
      } else b.visible = false;
    }
    r.rx = rx;
    // trạm con lăn dưới cánh tay: 3 bao; gắp xong, 3 bao mới chạy từ băng tải lên băng dốc vào trạm
    const slotX = i => rx + r.d * SLOT[2 - i];          // bao 0 vào trước, nằm sâu nhất (gần đế robot)
    const pathAt = (i, p) => {                          // p: 0 = chân băng dốc, 1 = đúng chỗ trên trạm
      const xb = rx + r.d * RAMP_BOT, xt = rx + r.d * RAMP_TOP, xs = rx + r.d * SLOT[i];
      if (p < 0.45) { const k = p / 0.45; return V(lerp(xb, xt, k), lerp(CY, BED_TOP, k) + BH / 2 + 0.02, CZ); }
      return V(lerp(xt, xs, (p - 0.45) / 0.55), BAG_BED + 0.02, CZ);
    };
    let enter = [1, 1, 1];
    if (t >= 16 && t < 34) { const k = idxAt(r, t), u = clamp((t - cycStart(r, k)) / (r.T[k] - cycStart(r, k)));
      if (u >= 0.33) enter = [0, 1, 2].map(i => (u - (0.4 + 0.1 * i)) / 0.3); }
    r.bed.forEach((b, i) => {
      const p = enter[i]; b.visible = p >= 0 && t < 46;
      b.position.copy(pathAt(i, clamp(p))); b.rotation.set(0, 0, p > 0 && p < 0.45 ? r.d * Math.atan2(BED_TOP - CY, RAMP_TOP - RAMP_BOT) : 0);
    });
    // băng tải cố định: bao chạy từ đầu sàn về phía chân băng dốc
    const start = r.d > 0 ? PX0 + 0.4 : PX1 - 0.4, stop = rx + r.d * RAMP_BOT;
    r.feed.forEach((b, j) => {
      const x = start + r.d * ((t * 1.3 + j * 1.05) % (PX1 - PX0));
      b.position.set(x, CY + BH / 2 + 0.02, CZ); b.rotation.set(0, 0, 0);
      b.visible = r.d * (stop - x) > 0.4 && t < 47;
    });
  }

  // --- chữ ---
  const st = STEPS.find(s => t >= s[0] && t < s[1]) || STEPS[STEPS.length - 1];
  stepEl.innerHTML = `<b>${st[2]}</b>${st[3]}`;
  stepEl.style.opacity = Math.min(seg(t, st[0], st[0] + 0.4), st[2] === 7 ? 1 : 1 - seg(t, st[1] - 0.25, st[1]));
  ffEl.style.opacity = t >= 34.3 && t < 46 ? 1 : 0;
  card.style.opacity = 0;   // bỏ bảng chữ: thay bằng từng dòng chữ hiện rồi mất ở đáy màn hình
  const tg = TAGS.find(s => t >= s[0] && t < s[1]);
  tag.textContent = tg ? tg[2] : ''; tag.style.opacity = tg ? Math.min(seg(t, tg[0], tg[0] + 0.3), 1 - seg(t, tg[1] - 0.3, tg[1])) : 0;

  const [cp, cl] = camAt(t); camera.position.copy(cp); camera.lookAt(cl);
  renderer.render(scene, camera);
  return true;
};
window.DUR = DUR; window.ready = true;
